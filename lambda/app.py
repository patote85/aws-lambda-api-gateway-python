from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.event_handler import APIGatewayHttpResolver
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.idempotency import idempotent
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
from aws_lambda_powertools.utilities.validation import validate
from pydantic import BaseModel
import boto3
import json
import uuid
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
import os

logger = Logger(service="exclusao-cliente-lambda")
tracer = Tracer()
metrics = Metrics(namespace="ExclusaoCliente")
app = APIGatewayHttpResolver()

# Environment
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('TABLE_NAME', 'ExclusaoClientes')
table = dynamodb.Table(table_name)
PIX_FEE = float(os.environ.get('PIX_FEE', 50.00))

class ExclusaoRequest(BaseModel):
    cliente_id: str
    motivo: str = 'Não informado'

@idempotent
@app.post('/solicitar-exclusao-cliente')
@tracer.capture_method
def solicitar_exclusao(event: APIGatewayProxyEvent):
    body = validate(event.json_body, ExclusaoRequest)
    cliente_id = body.cliente_id
    motivo = body.motivo
    
    request_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()
    
    # Idempotency check
    try:
        response = table.get_item(Key={'cliente_id': cliente_id, 'request_id': 'LATEST'})
        if 'Item' in response:
            existing = response['Item']
            if existing.get('status') in ['PENDING_PAYMENT', 'PAID']:
                return {'statusCode': 200, 'body': json.dumps({
                    'message': 'Solicitação já existe',
                    'request_id': existing.get('request_id'),
                    'status': existing.get('status')
                })}
    except ClientError:
        pass
    
    # Real Pix QR (stub - replace with real lib)
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
    logger.info("Solicitação criada", extra={"cliente_id": cliente_id, "request_id": request_id})
    
    return {'statusCode': 201, 'body': json.dumps({
        'message': 'Solicitação registrada. Pague via Pix.',
        'request_id': request_id,
        'qr_code': qr_code_data,
        'fee': PIX_FEE
    })}

def generate_pix_qr_code(cliente_id: str, amount: float, request_id: str) -> str:
    # TODO: Replace with real Pix library (pix-qrcode or bank API)
    return f"pix-emv://{cliente_id}/{amount}/{request_id}"  # Placeholder

@app.get('/status-exclusao/{cliente_id}')
@tracer.capture_method
def get_status(cliente_id: str):
    try:
        response = table.get_item(Key={'cliente_id': cliente_id, 'request_id': 'LATEST'})
        if 'Item' in response:
            return {'statusCode': 200, 'body': json.dumps(response['Item'])}
        return {'statusCode': 404, 'body': json.dumps({'error': 'Não encontrado'})}
    except Exception as e:
        logger.error(str(e))
        return {'statusCode': 500, 'body': json.dumps({'error': 'Erro interno'})}

@app.post('/confirmar-pagamento')
@tracer.capture_method
def confirmar_pagamento(event: APIGatewayProxyEvent):
    body = event.json_body
    # Production: Validate webhook signature
    try:
        table.update_item(
            Key={'cliente_id': body.get('cliente_id'), 'request_id': body.get('request_id')},
            UpdateExpression='SET #status = :paid, updated_at = :ts',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':paid': 'PAID', ':ts': datetime.utcnow().isoformat()}
        )
        metrics.add_metric(name="exclusao_paga", unit="Count", value=1)
        logger.info("Pagamento confirmado")
        return {'statusCode': 200, 'body': json.dumps({'message': 'Exclusão em processamento'})}
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}

@logger.inject_lambda_context(correlation_id_path="requestContext.requestId")
@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)