from aws_lambda_powertools import Logger
logger = Logger()

def health_check(dynamodb_table):
    try:
        dynamodb_table.meta.client.describe_table(TableName=dynamodb_table.name)
        return {"status": "healthy", "checks": {"dynamodb": "ok"}}
    except Exception as e:
        logger.error(str(e))
        return {"status": "unhealthy", "error": str(e)}