#!/usr/bin/env python3
"""CDK app — exclusão Pix (ADR-001 PR2).

Single stack: DynamoDB table + Lambda + HTTP API.
No Cognito (PR3). No from_function_name.
"""
from aws_cdk import (
    App,
    CfnOutput,
    Duration,
    RemovalPolicy,
    Stack,
    aws_apigatewayv2 as apigwv2,
    aws_apigatewayv2_integrations as apigwv2_integrations,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
)
from constructs import Construct


class ExclusaoClienteStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        table = dynamodb.Table(
            self,
            "ExclusaoClientesTable",
            partition_key=dynamodb.Attribute(
                name="cliente_id", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="request_id", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Handler: lambda/app.py → lambda_handler (CI uses Python 3.12)
        # Powertools packaging/layer left for follow-up (asset is source only).
        fn = _lambda.Function(
            self,
            "ExclusaoClienteLambda",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="app.lambda_handler",
            code=_lambda.Code.from_asset("lambda"),
            timeout=Duration.seconds(30),
            memory_size=256,
            environment={
                "TABLE_NAME": table.table_name,
                "PIX_FEE": "50.00",
            },
        )

        table.grant_read_write_data(fn)

        http_api = apigwv2.HttpApi(
            self,
            "ExclusaoClienteHttpApi",
            description="API Gateway para Exclusão de Cliente com Pix",
            cors_preflight=apigwv2.CorsPreflightOptions(
                allow_origins=["*"],
                allow_methods=[apigwv2.CorsHttpMethod.ANY],
            ),
            create_default_stage=False,
        )

        # Mirror aws-api-gateway-cdk: rate 100 / burst 200
        apigwv2.HttpStage(
            self,
            "DefaultStage",
            http_api=http_api,
            stage_name="$default",
            auto_deploy=True,
            throttle=apigwv2.ThrottleSettings(rate_limit=100, burst_limit=200),
        )

        integration = apigwv2_integrations.HttpLambdaIntegration(
            "LambdaIntegration", fn
        )

        http_api.add_routes(
            path="/solicitar-exclusao-cliente",
            methods=[apigwv2.HttpMethod.POST],
            integration=integration,
        )
        http_api.add_routes(
            path="/status-exclusao/{cliente_id}",
            methods=[apigwv2.HttpMethod.GET],
            integration=integration,
        )
        http_api.add_routes(
            path="/confirmar-pagamento",
            methods=[apigwv2.HttpMethod.POST],
            integration=integration,
        )
        http_api.add_routes(
            path="/health",
            methods=[apigwv2.HttpMethod.GET],
            integration=integration,
        )

        CfnOutput(self, "ApiUrl", value=http_api.url or "")
        CfnOutput(self, "ApiId", value=http_api.api_id)
        CfnOutput(self, "DynamoTableName", value=table.table_name)
        CfnOutput(self, "LambdaName", value=fn.function_name)


app = App()
ExclusaoClienteStack(app, "ExclusaoClienteStack")
app.synth()
