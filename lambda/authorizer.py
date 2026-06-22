from aws_lambda_powertools.utilities.typing import LambdaContext

def lambda_handler(event, context: LambdaContext):
    # Simple token authorizer example
    token = event.get('authorizationToken', '')
    if token == 'valid-secret-token':  # Replace with real validation (JWT, Cognito etc.)
        return {
            'principalId': 'user',
            'policyDocument': {
                'Version': '2012-10-17',
                'Statement': [{
                    'Action': 'execute-api:Invoke',
                    'Effect': 'Allow',
                    'Resource': event.get('methodArn')
                }]
            }
        }
    return {
        'principalId': 'user',
        'policyDocument': {
            'Version': '2012-10-17',
            'Statement': [{
                'Action': 'execute-api:Invoke',
                'Effect': 'Deny',
                'Resource': event.get('methodArn')
            }]
        }
    }