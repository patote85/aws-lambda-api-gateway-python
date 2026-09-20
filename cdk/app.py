#!/usr/bin/env python3
"""CDK app — exclusão Pix (ADR-001 PR3).

Single stack: Cognito User Pool + DynamoDB + Lambda + HTTP API (JWT).
Health is public; mutable/status routes require Cognito JWT.
No WAF/ACM in this stack.
"""
from aws_cdk import (
    App,
    CfnOutput,
    Duration,
    RemovalPolicy,
    Stack,
    aws_apigatewayv2 as apigwv2,
    aws_apigatewayv2_authorizers as apigwv2_authorizers,
    aws_apigatewayv2_integrations as apigwv2_integrations,
    aws_cognito as cognito,
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

        # Lab Cognito: email sign-in, USER_PASSWORD + USER_SRP (no client secret).
        user_pool = cognito.UserPool(
            self,
            "ExclusaoClienteUserPool",
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(email=True),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=False,
            ),
            removal_policy=RemovalPolicy.DESTROY,
        )

        user_pool_client = user_pool.add_client(
            "ExclusaoClienteAppClient",
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True,
            ),
            generate_secret=False,
        )

        jwt_issuer = (
            f"https://cognito-idp.{self.region}.amazonaws.com/"
            f"{user_pool.user_pool_id}"
        )
        jwt_authorizer = apigwv2_authorizers.HttpJwtAuthorizer(
            "CognitoJwtAuthorizer",
            jwt_issuer,
            jwt_audience=[user_pool_client.user_pool_client_id],
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

        # Lab CORS: no wildcard. Browser callers must use localhost (or override
        # via CDK context key corsOrigins = ["https://app.example"]).
        cors_origins = self.node.try_get_context("corsOrigins") or [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]

        http_api = apigwv2.HttpApi(
            self,
            "ExclusaoClienteHttpApi",
            description="API Gateway para Exclusão de Cliente com Pix",
            cors_preflight=apigwv2.CorsPreflightOptions(
                allow_origins=cors_origins,
                allow_methods=[
                    apigwv2.CorsHttpMethod.GET,
                    apigwv2.CorsHttpMethod.POST,
                    apigwv2.CorsHttpMethod.OPTIONS,
                ],
                allow_headers=["Authorization", "Content-Type"],
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

        # Protected (Cognito JWT): mutáveis + status
        http_api.add_routes(
            path="/solicitar-exclusao-cliente",
            methods=[apigwv2.HttpMethod.POST],
            integration=integration,
            authorizer=jwt_authorizer,
        )
        http_api.add_routes(
            path="/status-exclusao/{cliente_id}",
            methods=[apigwv2.HttpMethod.GET],
            integration=integration,
            authorizer=jwt_authorizer,
        )
        http_api.add_routes(
            path="/confirmar-pagamento",
            methods=[apigwv2.HttpMethod.POST],
            integration=integration,
            authorizer=jwt_authorizer,
        )
        # Public: health (probes / lab smoke)
        http_api.add_routes(
            path="/health",
            methods=[apigwv2.HttpMethod.GET],
            integration=integration,
        )

        CfnOutput(self, "ApiUrl", value=http_api.url or "")
        CfnOutput(self, "ApiId", value=http_api.api_id)
        CfnOutput(self, "DynamoTableName", value=table.table_name)
        CfnOutput(self, "LambdaName", value=fn.function_name)
        CfnOutput(self, "UserPoolId", value=user_pool.user_pool_id)
        CfnOutput(
            self, "UserPoolClientId", value=user_pool_client.user_pool_client_id
        )
        CfnOutput(self, "JwtIssuer", value=jwt_issuer)


app = App()
ExclusaoClienteStack(app, "ExclusaoClienteStack")
app.synth()
