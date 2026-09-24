# Feature map — exclusão Pix API (agent-friendly)

Factual map for agents. Do not invent routes/auth. Sources: `lambda/app.py`, `lambda/domain_dynamo.py`, `cdk/app.py`, README, SECURITY.md, ADR-001.

## Auth (base)

- **Cognito JWT** (ADR-001 / PR3): send `Authorization: Bearer <IdToken>` (IdToken, not AccessToken).
- Protected at API Gateway (JWT authorizer) before Lambda.
- **Public:** `GET /health` only.

Pointers: [ADR-001](adr/ADR-001-unificar-exclusao-pix.md), [SECURITY.md](../SECURITY.md), [ARCHITECTURE.md](../ARCHITECTURE.md).

## Routes → handlers

| Method + path | Auth | Handler | Behavior |
|---------------|------|---------|----------|
| `POST /solicitar-exclusao-cliente` | Cognito JWT | `solicitar_exclusao` | Body: `cliente_id` (required), `motivo` (optional). Reads Dynamo `LATEST`; if status is `PENDING_PAYMENT` or `PAID`, returns 200 with existing `request_id`. Else creates history row + `LATEST` pointer (`PENDING_PAYMENT`), stub Pix QR, returns 201. |
| `GET /status-exclusao/{cliente_id}` | Cognito JWT | `get_status` | Reads `LATEST` only; 200 with status/`active_request_id`, or 404. |
| `POST /confirmar-pagamento` | Cognito JWT | `confirmar_pagamento` | Body: `cliente_id` + `request_id`. Updates history UUID then `LATEST` to `PAID` (condition on `active_request_id`). |
| `GET /health` | Public | `health_check` | Describes Dynamo table; 200 healthy / 503 unhealthy. |

HTTP lives in `lambda/app.py`. Dynamo LATEST helpers in `lambda/domain_dynamo.py` (boundary discipline).

### Dynamo access pattern (obrigatório)

- PK `cliente_id`, SK `request_id`
- History: `SK = <uuid>`; pointer: `SK = LATEST` (`active_request_id`, `status`, …)
- Dedup/status read **only** `LATEST`; payment confirm updates uuid **and** `LATEST`

## Env vars

| Var | Where | Default / notes |
|-----|--------|-----------------|
| `TABLE_NAME` | Lambda env (CDK) | Table name from stack |
| `PIX_FEE` | Lambda env (CDK) | `"50.00"` (Decimal in domain) |

No secrets in repo. Cognito IDs / `ApiUrl` only via CloudFormation outputs after deploy (CAB).

## Pre-reqs — tests / verify / check

Prove-it-works path for agents: **`make verify`** (HTTP contracts in `tests/test_http_contract.py` via `lambda_handler`, including `GET /health` → 200). Full gate: **`make check`**.

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt   # ruff + mypy
pip install -r cdk/requirements.txt   # for synth
make verify  # HTTP contracts (health + request/status/confirm)
make check   # lint + typecheck + all tests + cdk synth (no deploy)
```

CI jobs on PR/`push` to `main`: **lint** (ruff + mypy), **test** (pytest/moto), **verify** (`make verify`), **synth** (`npx aws-cdk@2 synth`).

## Hard constraints (encoded)

- Datetimes: `datetime.now(timezone.utc)` — ruff **DTZ** bans `utcnow`
- CORS: CDK localhost only — no `AllowOrigins: "*"` in `cdk/`

## Doc index

| Doc | Role |
|-----|------|
| [ADR-001](adr/ADR-001-unificar-exclusao-pix.md) | Canonical decision (monorepo, LATEST, Cognito) |
| [ARCHITECTURE.md](../ARCHITECTURE.md) | Bounded context + components |
| [SECURITY.md](../SECURITY.md) | Auth/CORS/throttle honesty |
| [README.md](../README.md) | Deploy, Cognito lab curls, make verify / make check |
