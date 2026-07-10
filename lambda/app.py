from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.event_handler import APIGatewayHttpResolver
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.idempotency import idempotent
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
import boto3
import json
import uuid
import os
from datetime import datetime, timedelta

logger = Logger(service="exclusao-cliente-lambda")
tracer = Tracer()
metrics = Metrics(namespace="ExclusaoCliente")
app = APIGatewayHttpResolver()

TABLE_NAME = os.environ.get('TABLE_NAME', 'ExclusaoClientes')
PIX_FEE = float(os.environ.get('PIX_FEE', '50.00'))

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(TABLE_NAME)

@idempotent
@app.post('/solicitar-exclusao-cliente')
@tracer.capture_method
def solicitar_exclusao(event: APIGatewayProxyEvent):
    body = event.json_body or {}
    cliente_id = body.get('cliente_id')
    motivo = body.get('motivo', 'Não informado')

    if not cliente_id:
        return {'statusCode': 400, 'body': json.dumps({'error': 'cliente_id is required'})}

    request_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()

    try:
        response = table.get_item(Key={'cliente_id': cliente_id, 'request_id': 'LATEST'})
        if 'Item' in response:
            existing = response['Item']
            if existing.get('status') in ['PENDING_PAYMENT', 'PAID']:
                return {'statusCode': 200, 'body': json.dumps({'message': 'Solicitação já existe', 'request_id': existing.get('request_id'), 'status': existing.get('status')})}
    except Exception:
        pass

    qr_code_data = generate_pix_qr_code(cliente_id, PIX_FEE, request_id)

    item = {
        'cliente_id': cliente_id,
        'request_id': request_id,
        'status': 'PENDING_PAYMENT',
        'motivo': motivo,
        'qr_code_data': qr_code_data,
        'fee_amount': PIX_FEE,
        'created_at': timestamp,
        'expires_at': (datetime.utcnow() + timedelta(days=7)).isoformat()
    }
    table.put_item(Item=item)

    metrics.add_metric(name="exclusao_solicitada", unit="Count", value=1)
    logger.info("Solicitação criada", extra={"cliente_id": cliente_id})

    return {'statusCode': 201, 'body': json.dumps({'message': 'Solicitação registrada', 'request_id': request_id, 'qr_code': qr_code_data, 'fee': PIX_FEE})}

def generate_pix_qr_code(cliente_id: str, amount: float, request_id: str) -> str:
    return f"pix-emv-stub://{cliente_id}/{amount}/{request_id}"

@app.get('/health')
@tracer.capture_method
def health_check():
    try:
        table.meta.client.describe_table(TableName=TABLE_NAME)
        return {'statusCode': 200, 'body': json.dumps({'status': 'healthy'})}
    except Exception as e:
        return {'statusCode': 503, 'body': json.dumps({'status': 'unhealthy', 'error': str(e)})}

@app.get('/status-exclusao/{cliente_id}')
@tracer.capture_method
def get_status(cliente_id: str):
    try:
        response = table.get_item(Key={'cliente_id': cliente_id, 'request_id': 'LATEST'})
        if 'Item' in response:
            item = response['Item']
            return {'statusCode': 200, 'body': json.dumps({'cliente_id': cliente_id, 'status': item.get('status'), 'request_id': item.get('request_id')})}
        return {'statusCode': 404, 'body': json.dumps({'error': 'Não encontrado'})}
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}

@app.post('/confirmar-pagamento')
@tracer.capture_method
def confirmar_pagamento(event: APIGatewayProxyEvent):
    body = event.json_body or {}
    try:
        table.update_item(
            Key={'cliente_id': body.get('cliente_id'), 'request_id': body.get('request_id')},
            UpdateExpression='SET #status = :paid, updated_at = :ts',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':paid': 'PAID', ':ts': datetime.utcnow().isoformat()}
        )
        metrics.add_metric(name="exclusao_paga", unit="Count", value=1)
        return {'statusCode': 200, 'body': json.dumps({'message': 'Pagamento confirmado'})}
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}

@logger.inject_lambda_context(correlation_id_path="requestContext.requestId")
@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)