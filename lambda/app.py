"""HTTP handlers — Dynamo access lives in domain_dynamo (boundary discipline)."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta

from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.event_handler import APIGatewayHttpResolver
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
from aws_lambda_powertools.utilities.typing import LambdaContext

# Sibling import: Code.from_asset("lambda") loads app + domain_dynamo as top-level.
# Tests put lambda/ on sys.path the same way (see tests/test_exclusao.py).
import domain_dynamo as domain

logger = Logger(service="exclusao-cliente-lambda")
tracer = Tracer()
metrics = Metrics(namespace="ExclusaoCliente")
app = APIGatewayHttpResolver()

# Re-export for moto fixtures / callers that patch app.table
TABLE_NAME = domain.TABLE_NAME
PIX_FEE = domain.PIX_FEE
LATEST_SK = domain.LATEST_SK
dynamodb = domain.dynamodb
table = domain.table
_get_latest = domain.get_latest
_put_solicitacao_with_latest = domain.put_solicitacao_with_latest
_confirm_payment = domain.confirm_payment
generate_pix_qr_code = domain.generate_pix_qr_code


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

    existing = domain.get_latest(cliente_id)
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
    qr_code_data = domain.generate_pix_qr_code(cliente_id, domain.PIX_FEE, request_id)

    domain.put_solicitacao_with_latest(
        cliente_id=cliente_id,
        request_id=request_id,
        motivo=motivo,
        qr_code_data=qr_code_data,
        fee_amount=domain.PIX_FEE,
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
                "fee": float(domain.PIX_FEE),
            }
        ),
    }


@app.get("/health")
@tracer.capture_method
def health_check():
    try:
        domain.table.meta.client.describe_table(TableName=domain.TABLE_NAME)
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
        item = domain.get_latest(cliente_id)
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
        domain.confirm_payment(cliente_id, request_id)
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
