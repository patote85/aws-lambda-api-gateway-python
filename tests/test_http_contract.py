"""
HTTP contract tests via lambda_handler + realistic API Gateway HTTP API events.

    pip install -r requirements.txt
    PYTHONPATH=. pytest tests/test_http_contract.py -v

Import style matches Lambda Code.from_asset("lambda"): app + domain_dynamo
as top-level modules (lambda/ on sys.path).
"""

from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path
from typing import Any

import boto3
import pytest
from moto import mock_aws

ROOT = Path(__file__).resolve().parents[1]
LAMBDA_DIR = ROOT / "lambda"
sys.path.insert(0, str(LAMBDA_DIR))

os.environ["TABLE_NAME"] = "ExclusaoClientes"
os.environ["PIX_FEE"] = "50.00"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
os.environ["POWERTOOLS_TRACE_DISABLED"] = "true"
os.environ["POWERTOOLS_METRICS_NAMESPACE"] = "ExclusaoClienteTest"


def _app():
    return importlib.import_module("app")


def _domain():
    return importlib.import_module("domain_dynamo")


class _LambdaContext:
    function_name = "exclusao-cliente-test"
    memory_limit_in_mb = 128
    invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test"
    aws_request_id = "test-request-id"


def make_http_event(
    method: str,
    path: str,
    body: dict[str, Any] | None = None,
    path_parameters: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Minimal API Gateway HTTP API (payload 2.0) event for Powertools."""
    event: dict[str, Any] = {
        "version": "2.0",
        "routeKey": f"{method} {path}",
        "rawPath": path,
        "rawQueryString": "",
        "headers": {"content-type": "application/json"},
        "requestContext": {
            "accountId": "123456789012",
            "apiId": "api-id",
            "domainName": "localhost",
            "domainPrefix": "localhost",
            "http": {
                "method": method,
                "path": path,
                "protocol": "HTTP/1.1",
                "sourceIp": "127.0.0.1",
                "userAgent": "pytest",
            },
            "requestId": "test-request-id",
            "routeKey": f"{method} {path}",
            "stage": "$default",
            "time": "01/Jan/2026:00:00:00 +0000",
            "timeEpoch": 1767225600000,
        },
        "isBase64Encoded": False,
    }
    if body is not None:
        event["body"] = json.dumps(body)
    if path_parameters is not None:
        event["pathParameters"] = path_parameters
    return event


def _invoke(method: str, path: str, body: dict | None = None, **kwargs) -> dict:
    app_module = _app()
    return app_module.lambda_handler(
        make_http_event(method, path, body=body, **kwargs), _LambdaContext()
    )


def _body(resp: dict) -> dict:
    return json.loads(resp["body"])


@pytest.fixture
def dynamodb_table():
    with mock_aws():
        ddb = boto3.resource("dynamodb", region_name="us-east-1")
        tbl = ddb.create_table(
            TableName="ExclusaoClientes",
            KeySchema=[
                {"AttributeName": "cliente_id", "KeyType": "HASH"},
                {"AttributeName": "request_id", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "cliente_id", "AttributeType": "S"},
                {"AttributeName": "request_id", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        domain = _domain()
        domain.TABLE_NAME = "ExclusaoClientes"
        domain.table = tbl
        domain.dynamodb = ddb

        app_module = _app()
        app_module.TABLE_NAME = domain.TABLE_NAME
        app_module.table = domain.table
        app_module.dynamodb = domain.dynamodb
        app_module.LATEST_SK = domain.LATEST_SK
        app_module._get_latest = domain.get_latest
        app_module._put_solicitacao_with_latest = domain.put_solicitacao_with_latest
        app_module._confirm_payment = domain.confirm_payment

        yield tbl


def test_get_health_returns_200_healthy(dynamodb_table):
    resp = _invoke("GET", "/health")
    assert resp["statusCode"] == 200
    assert _body(resp) == {"status": "healthy"}


def test_solicitar_missing_cliente_id_returns_400(dynamodb_table):
    resp = _invoke("POST", "/solicitar-exclusao-cliente", body={"motivo": "x"})
    assert resp["statusCode"] == 400
    assert _body(resp) == {"error": "cliente_id is required"}


def test_happy_path_request_status_confirm(dynamodb_table):
    # 1) solicitar
    created = _invoke(
        "POST",
        "/solicitar-exclusao-cliente",
        body={"cliente_id": "cli-http-1", "motivo": "contrato"},
    )
    assert created["statusCode"] == 201
    created_body = _body(created)
    assert created_body["message"] == "Solicitação registrada"
    assert created_body["fee"] == 50.0
    request_id = created_body["request_id"]
    assert isinstance(request_id, str) and request_id
    assert created_body["qr_code"].startswith("pix-emv-stub://cli-http-1/")

    # 2) status
    status = _invoke(
        "GET",
        "/status-exclusao/cli-http-1",
        path_parameters={"cliente_id": "cli-http-1"},
    )
    assert status["statusCode"] == 200
    assert _body(status) == {
        "cliente_id": "cli-http-1",
        "status": "PENDING_PAYMENT",
        "request_id": request_id,
    }

    # 3) confirm
    confirmed = _invoke(
        "POST",
        "/confirmar-pagamento",
        body={"cliente_id": "cli-http-1", "request_id": request_id},
    )
    assert confirmed["statusCode"] == 200
    assert _body(confirmed) == {"message": "Pagamento confirmado"}

    # 4) status after pay
    status_paid = _invoke(
        "GET",
        "/status-exclusao/cli-http-1",
        path_parameters={"cliente_id": "cli-http-1"},
    )
    assert status_paid["statusCode"] == 200
    assert _body(status_paid)["status"] == "PAID"
    assert _body(status_paid)["request_id"] == request_id
