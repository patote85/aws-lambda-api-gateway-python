"""Dynamo access — LATEST pointer (ADR-001). HTTP stays in app.py."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from decimal import Decimal

import boto3

TABLE_NAME = os.environ.get("TABLE_NAME", "ExclusaoClientes")
PIX_FEE = Decimal(str(os.environ.get("PIX_FEE", "50.00")))
LATEST_SK = "LATEST"

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


def get_latest(cliente_id: str) -> dict | None:
    """Read the LATEST pointer row for a cliente."""
    response = table.get_item(Key={"cliente_id": cliente_id, "request_id": LATEST_SK})
    return response.get("Item")


def put_solicitacao_with_latest(
    *,
    cliente_id: str,
    request_id: str,
    motivo: str,
    qr_code_data: str,
    fee_amount: Decimal,
    created_at: str,
    expires_at: str,
) -> None:
    """Write history (SK=uuid) then LATEST pointer (SK=LATEST).

    Ordered puts keep the PR small and moto-friendly. TransactWrite can
    replace this later if we need stronger atomicity.
    """
    history = {
        "cliente_id": cliente_id,
        "request_id": request_id,
        "status": "PENDING_PAYMENT",
        "motivo": motivo,
        "qr_code_data": qr_code_data,
        "fee_amount": fee_amount,
        "created_at": created_at,
        "expires_at": expires_at,
    }
    latest = {
        "cliente_id": cliente_id,
        "request_id": LATEST_SK,
        "active_request_id": request_id,
        "status": "PENDING_PAYMENT",
        "motivo": motivo,
        "qr_code_data": qr_code_data,
        "fee_amount": fee_amount,
        "created_at": created_at,
        "expires_at": expires_at,
    }
    table.put_item(Item=history)
    table.put_item(Item=latest)


def confirm_payment(cliente_id: str, request_id: str) -> None:
    """Mark history + LATEST as PAID when pointer matches request_id."""
    ts = datetime.now(timezone.utc).isoformat()
    table.update_item(
        Key={"cliente_id": cliente_id, "request_id": request_id},
        UpdateExpression="SET #status = :paid, updated_at = :ts",
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues={":paid": "PAID", ":ts": ts},
        ConditionExpression="attribute_exists(cliente_id)",
    )
    table.update_item(
        Key={"cliente_id": cliente_id, "request_id": LATEST_SK},
        UpdateExpression="SET #status = :paid, updated_at = :ts",
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues={
            ":paid": "PAID",
            ":ts": ts,
            ":rid": request_id,
        },
        ConditionExpression="active_request_id = :rid",
    )


def generate_pix_qr_code(cliente_id: str, amount: Decimal, request_id: str) -> str:
    return f"pix-emv-stub://{cliente_id}/{amount}/{request_id}"
