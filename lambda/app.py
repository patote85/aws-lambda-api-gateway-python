from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.event_handler import APIGatewayHttpResolver
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
import boto3
import json
import uuid
import os
from datetime import datetime, timedelta
from decimal import Decimal
from boto3.dynamodb.types import TypeSerializer

logger = Logger(service="exclusao-cliente-lambda")
tracer = Tracer()
metrics = Metrics(namespace="ExclusaoCliente")
app = APIGatewayHttpResolver()

TABLE_NAME = os.environ.get("TABLE_NAME", "ExclusaoClientes")
PIX_FEE = Decimal(str(os.environ.get("PIX_FEE", "50.00")))
LATEST_SK = "LATEST"

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)
_ddb_client = dynamodb.meta.client
_serializer = TypeSerializer()


def _serialize_item(item: dict) -> dict:
    return {k: _serializer.serialize(v) for k, v in item.items()}


def _get_latest(cliente_id: str) -> dict | None:
    """Read the LATEST pointer row for a cliente."""
    response = table.get_item(Key={"cliente_id": cliente_id, "request_id": LATEST_SK})
    return response.get("Item")


def _put_solicitacao_with_latest(
    *,
    cliente_id: str,
    request_id: str,
    motivo: str,
    qr_code_data: str,
    fee_amount: Decimal,
    created_at: str,
    expires_at: str,
) -> None:
    """Atomically write history (SK=uuid) + LATEST pointer (SK=LATEST)."""
    history = {
        "cliente_id": cliente_id,
        "request_id": request_id,
        "status": "PENDING_PAYMENT",
        "motivo": motivo,
        "qr_code_data": qr_code_data,
        "fee_amount": fee_amount,
        "created_at": created_at,
        "expires_at": expires_at,
    }
    latest = {
        "cliente_id": cliente_id,
        "request_id": LATEST_SK,
        "active_request_id": request_id,
        "status": "PENDING_PAYMENT",
        "motivo": motivo,
        "qr_code_data": qr_code_data,
        "fee_amount": fee_amount,
        "created_at": created_at,
        "expires_at": expires_at,
    }
    _ddb_client.transact_write_items(
        TransactItems=[
            {
                "Put": {
                    "TableName": TABLE_NAME,
                    "Item": _serialize_item(history),
                }
            },
            {
                "Put": {
                    "TableName": TABLE_NAME,
                    "Item": _serialize_item(latest),
                }
            },
        ]
    )


def _confirm_payment(cliente_id: str, request_id: str) -> None:
    """Mark history + LATEST as PAID when pointer matches request_id."""
    ts = datetime.utcnow().isoformat()
    _ddb_client.transact_write_items(
        TransactItems=[
            {
                "Update": {
                    "TableName": TABLE_NAME,
                    "Key": _serialize_item(
                        {"cliente_id": cliente_id, "request_id": request_id}
                    ),
                    "UpdateExpression": "SET #status = :paid, updated_at = :ts",
                    "ExpressionAttributeNames": {"#status": "status"},
                    "ExpressionAttributeValues": _serialize_item(
                        {":paid": "PAID", ":ts": ts}
                    ),
                    "ConditionExpression": "attribute_exists(cliente_id)",
                }
            },
            {
                "Update": {
                    "TableName": TABLE_NAME,
                    "Key": _serialize_item(
                        {"cliente_id": cliente_id, "request_id": LATEST_SK}
                    ),
                    "UpdateExpression": "SET #status = :paid, updated_at = :ts",
                    "ExpressionAttributeNames": {"#status": "status"},
                    "ExpressionAttributeValues": _serialize_item(
                        {
                            ":paid": "PAID",
                            ":ts": ts,
                            ":rid": request_id,
                        }
                    ),
                    "ConditionExpression": "active_request_id = :rid",
                }
            },
        ]
    )


def generate_pix_qr_code(cliente_id: str, amount: Decimal, request_id: str) -> str:
    return f"pix-emv-stub://{cliente_id}/{amount}/{request_id}"


@app.post("/solicitar-exclusao-cliente")
@tracer.capture_method
def solicitar_exclusao(event: APIGatewayProxyEvent):
    body = event.json_body or {}
    cliente_id = body.get("cliente_id")
    motivo = body.get("motivo", "Não informado")

    if not cliente_id:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "cliente_id is required"}),
        }

    existing = _get_latest(cliente_id)
    if existing and existing.get("status") in ("PENDING_PAYMENT", "PAID"):
        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Solicitação já existe",
                    "request_id": existing.get("active_request_id"),
                    "status": existing.get("status"),
                }
            ),
        }

    request_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()
    expires_at = (datetime.utcnow() + timedelta(days=7)).isoformat()
    qr_code_data = generate_pix_qr_code(cliente_id, PIX_FEE, request_id)

    _put_solicitacao_with_latest(
        cliente_id=cliente_id,
        request_id=request_id,
        motivo=motivo,
        qr_code_data=qr_code_data,
        fee_amount=PIX_FEE,
        created_at=timestamp,
        expires_at=expires_at,
    )

    metrics.add_metric(name="exclusao_solicitada", unit="Count", value=1)
    logger.info("Solicitação criada", extra={"cliente_id": cliente_id})

    return {
        "statusCode": 201,
        "body": json.dumps(
            {
                "message": "Solicitação registrada",
                "request_id": request_id,
                "qr_code": qr_code_data,
                "fee": float(PIX_FEE),
            }
        ),
    }


@app.get("/health")
@tracer.capture_method
def health_check():
    try:
        table.meta.client.describe_table(TableName=TABLE_NAME)
        return {"statusCode": 200, "body": json.dumps({"status": "healthy"})}
    except Exception as e:
        return {
            "statusCode": 503,
            "body": json.dumps({"status": "unhealthy", "error": str(e)}),
        }


@app.get("/status-exclusao/{cliente_id}")
@tracer.capture_method
def get_status(cliente_id: str):
    try:
        item = _get_latest(cliente_id)
        if item:
            return {
                "statusCode": 200,
                "body": json.dumps(
                    {
                        "cliente_id": cliente_id,
                        "status": item.get("status"),
                        "request_id": item.get("active_request_id"),
                    }
                ),
            }
        return {"statusCode": 404, "body": json.dumps({"error": "Não encontrado"})}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}


@app.post("/confirmar-pagamento")
@tracer.capture_method
def confirmar_pagamento(event: APIGatewayProxyEvent):
    body = event.json_body or {}
    cliente_id = body.get("cliente_id")
    request_id = body.get("request_id")
    if not cliente_id or not request_id:
        return {
            "statusCode": 400,
            "body": json.dumps(
                {"error": "cliente_id and request_id are required"}
            ),
        }
    try:
        _confirm_payment(cliente_id, request_id)
        metrics.add_metric(name="exclusao_paga", unit="Count", value=1)
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Pagamento confirmado"}),
        }
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}


@logger.inject_lambda_context(correlation_id_path="requestContext.requestId")
@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
