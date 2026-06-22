from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import APIGatewayHttpResolver
from aws_lambda_powertools.utilities.typing import LambdaContext
import boto3
from botocore.exceptions import ClientError

logger = Logger()
tracer = Tracer()
app = APIGatewayHttpResolver()

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('MyTable')

@app.get('/hello')
@tracer.capture_method
def hello(name: str = 'World'):
    logger.info('Processing hello request', extra={'name': name})
    return {'message': f'Hello {name} from Lambda!'}

@app.post('/save')
@tracer.capture_method
def save_item(item: dict):
    try:
        table.put_item(Item=item)
        logger.info('Item saved', extra={'item_id': item.get('id')})
        return {'status': 'saved', 'item': item}
    except ClientError as e:
        logger.error('DynamoDB error', extra={'error': str(e)})
        raise

@logger.inject_lambda_context(correlation_id_path='requestContext.requestId')
@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)