from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.event_handler import APIGatewayHttpResolver
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.idempotency import idempotent
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent

import boto3
import json
import uuid
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

# Datadog integration note: Use Datadog Lambda Extension + ddtrace for full metrics/logs
# For now, structured logging + Powertools Metrics (can forward to Datadog)
logger = Logger(service="exclusao-cliente-lambda")
tracer = Tracer()
metrics = Metrics(namespace="ExclusaoCliente")
app = APIGatewayHttpResolver()

# DynamoDB
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('ExclusaoClientes')  # Table with PK: cliente_id, SK: request_id

PIX_FEE = 50.00  # Tarifa em BRL

@idempotent  # Powertools idempotency
@app.post('/solicitar-exclusao-cliente')
@tracer.capture_method
def solicitar_exclusao(event: APIGatewayProxyEvent):
    body = event.json_body
    cliente_id = body.get('cliente_id')
    motivo = body.get('motivo', 'Não informado')
    
    if not cliente_id:
        return {'statusCode': 400, 'body': json.dumps({'error': 'cliente_id required'})}
    
    request_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()
    
    # Check if already requested (idempotency via DynamoDB)
    try:
        response = table.get_item(Key={'cliente_id': cliente_id, 'request_id': 'LATEST'})
        if 'Item' in response:
            existing = response['Item']
            if existing.get('status') in ['PENDING_PAYMENT', 'PAID']:
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'message': 'Solicitação já existe',
                        'request_id': existing.get('request_id'),
                        'status': existing.get('status'),
                        'qr_code': existing.get('qr_code_data')
                    })
                }
    except ClientError:
        pass  # Continue to create new
    
    # Generate Pix QR Code (simple EMV stub - in production use real Pix library or bank API)
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
    
    # Metrics to Datadog (via Powertools or extension)
    metrics.add_metric(name="exclusao_solicitada", unit="Count", value=1)
    logger.info("Solicitação de exclusão criada", extra={"cliente_id": cliente_id, "request_id": request_id})
    
    return {
        'statusCode': 201,
        'body': json.dumps({
            'message': 'Solicitação de exclusão registrada. Pague a tarifa via Pix para prosseguir.',
            'request_id': request_id,
            'qr_code': qr_code_data,
            'fee': PIX_FEE,
            'status': 'PENDING_PAYMENT'
        })
    }

def generate_pix_qr_code(cliente_id: str, amount: float, request_id: str) -> str:
    # Stub for Pix EMV QR Code - replace with real generator (e.g. emv-qrcode lib or bank integration)
    # In production: Use https://github.com/fernandopontesdev/pix-qrcode or similar
    emv = f"00020101021226{len('0014br.gov.bcb.pix01')+len(cliente_id):02d}0014br.gov.bcb.pix01{len(cliente_id):02d}{cliente_id}52040000530398654{int(amount*100):010d}5802BR5913ExclusaoCliente6009SaoPaulo62070503***6304ABCD"  # Simplified
    return emv  # Return EMV string; client generates QR image

@app.get('/status-exclusao/{cliente_id}')
@tracer.capture_method
def get_status(cliente_id: str):
    try:
        response = table.get_item(Key={'cliente_id': cliente_id, 'request_id': 'LATEST'})
        if 'Item' in response:
            item = response['Item']
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'cliente_id': cliente_id,
                    'status': item.get('status'),
                    'request_id': item.get('request_id'),
                    'qr_code': item.get('qr_code_data'),
                    'created_at': item.get('created_at')
                })
            }
        return {'statusCode': 404, 'body': json.dumps({'error': 'Nenhuma solicitação encontrada'})}
    except Exception as e:
        logger.error(str(e))
        return {'statusCode': 500, 'body': json.dumps({'error': 'Erro interno'})}

@app.post('/confirmar-pagamento')
@tracer.capture_method
def confirmar_pagamento(event: APIGatewayProxyEvent):
    body = event.json_body
    request_id = body.get('request_id')
    # In production: Validate Pix webhook or manual confirmation
    # Update status to PAID and trigger actual deletion process (e.g. via Step Functions or another Lambda)
    
    try:
        # Update item
        table.update_item(
            Key={'cliente_id': body.get('cliente_id'), 'request_id': request_id},
            UpdateExpression='SET #status = :paid, updated_at = :ts',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':paid': 'PAID', ':ts': datetime.utcnow().isoformat()}
        )
        metrics.add_metric(name="exclusao_paga", unit="Count", value=1)
        logger.info("Pagamento confirmado", extra={"request_id": request_id})
        return {'statusCode': 200, 'body': json.dumps({'message': 'Pagamento confirmado. Exclusão em processamento.'})}
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}

@logger.inject_lambda_context(correlation_id_path="requestContext.requestId")
@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)