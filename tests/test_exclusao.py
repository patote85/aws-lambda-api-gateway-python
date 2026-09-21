"""
Moto tests for DynamoDB LATEST pointer + history alignment.

    pip install -r requirements.txt
    PYTHONPATH=. pytest tests/test_exclusao.py -v

Import style matches Lambda Code.from_asset("lambda"): app + domain_dynamo
as top-level modules (lambda/ on sys.path).
"""

import importlib
import os
import sys
from decimal import Decimal
from pathlib import Path

import boto3
import pytest
from botocore.exceptions import ClientError
from moto import mock_aws

ROOT = Path(__file__).resolve().parents[1]
LAMBDA_DIR = ROOT / "lambda"
# Same layout as the Lambda zip root
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


def test_put_creates_latest_and_history(dynamodb_table):
    app = _app()

    app._put_solicitacao_with_latest(
        cliente_id="c1",
        request_id="req-aaa",
        motivo="teste",
        qr_code_data="pix-stub",
        fee_amount=Decimal("50.00"),
        created_at="2026-01-01T00:00:00",
        expires_at="2026-01-08T00:00:00",
    )

    latest = app._get_latest("c1")
    assert latest is not None
    assert latest["request_id"] == app.LATEST_SK
    assert latest["active_request_id"] == "req-aaa"
    assert latest["status"] == "PENDING_PAYMENT"

    history = dynamodb_table.get_item(
        Key={"cliente_id": "c1", "request_id": "req-aaa"}
    )["Item"]
    assert history["status"] == "PENDING_PAYMENT"
    assert history["motivo"] == "teste"


def test_get_latest_missing(dynamodb_table):
    assert _app()._get_latest("nobody") is None


def test_confirm_payment_updates_latest_and_history(dynamodb_table):
    app = _app()

    app._put_solicitacao_with_latest(
        cliente_id="c2",
        request_id="req-bbb",
        motivo="ok",
        qr_code_data="pix",
        fee_amount=Decimal("50.00"),
        created_at="2026-01-01T00:00:00",
        expires_at="2026-01-08T00:00:00",
    )
    app._confirm_payment("c2", "req-bbb")

    latest = app._get_latest("c2")
    assert latest["status"] == "PAID"
    assert latest["active_request_id"] == "req-bbb"

    history = dynamodb_table.get_item(
        Key={"cliente_id": "c2", "request_id": "req-bbb"}
    )["Item"]
    assert history["status"] == "PAID"
    assert "updated_at" in history


def test_confirm_payment_wrong_request_fails(dynamodb_table):
    app = _app()

    app._put_solicitacao_with_latest(
        cliente_id="c3",
        request_id="req-ccc",
        motivo="ok",
        qr_code_data="pix",
        fee_amount=Decimal("50.00"),
        created_at="2026-01-01T00:00:00",
        expires_at="2026-01-08T00:00:00",
    )
    with pytest.raises(ClientError):
        app._confirm_payment("c3", "req-WRONG")
