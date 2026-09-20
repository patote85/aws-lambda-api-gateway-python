# AWS Lambda Exclusão de Cliente com Pix

## Visão Geral
API serverless para solicitação de exclusão de cliente com geração de QR Code Pix para pagamento de tarifa.

**Este projeto segue rigorosamente os Karpathy Claude Guidelines**.

## Melhorias Implementadas
- Tabela DynamoDB criada via CDK
- Configuração via env vars
- Health Check endpoint
- Throttling no API Gateway

**Code Review:** Aprovado seguindo Karpathy Guidelines.

**Merge realizado para main.**

## Architecture Decision Records

- [ADR-001 — Unificar exclusão Pix (CDK + Lambda)](docs/adr/ADR-001-unificar-exclusao-pix.md) — **Accepted** (CAB 2026-09-20). Este repo é o canônico; `aws-api-gateway-cdk` será arquivado após migrar o stack. Access pattern Dynamo: pointer `LATEST`. Auth (PR3): Cognito JWT.

---

## DynamoDB — ponteiro LATEST

Tabela: PK `cliente_id`, SK `request_id`.

Cada solicitação grava **dois** itens (histórico depois ponteiro):

| SK | Papel |
|----|--------|
| UUID da solicitação | Histórico daquele pedido |
| `LATEST` | Ponteiro do estado atual (`active_request_id`, `status`, …) |

- **Dedup / status** leem só `LATEST` (antes o código gravava UUID e lia SK=`LATEST` — nunca achava).
- **Confirmar pagamento** atualiza histórico e depois `LATEST` (condition em `active_request_id`).
- Writes ordenados (`put`/`update`) de propósito neste PR — TransactWrite fica pra um follow-up se precisar atomicidade forte.

### Testes

```bash
pip install -r requirements.txt
PYTHONPATH=. pytest tests/test_exclusao.py -v
```

Usa **moto** (sem AWS real). O pacote `lambda/` importa via `importlib` (nome reservado).

CI (GitHub Actions): mesmo comando em Python 3.12 em todo PR/`push` na `main` — sem credenciais AWS no runner.

---

## CDK / Deploy

Stack único em `cdk/app.py` (ADR-001 PR2): **DynamoDB + Lambda + HTTP API** no mesmo stack — sem `from_function_name`, sem Cognito (PR3).

- Tabela: PK `cliente_id` / SK `request_id`, on-demand; `grant_read_write_data` na Lambda.
- Env: `TABLE_NAME` (nome da tabela), `PIX_FEE` (default `50.00`).
- Handler: `app.lambda_handler` (código em `lambda/`).
- Throttle HTTP API: **100 rps / burst 200** (espelha `aws-api-gateway-cdk`).
- Rotas: `POST /solicitar-exclusao-cliente`, `GET /status-exclusao/{cliente_id}`, `POST /confirmar-pagamento`, `GET /health`.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r cdk/requirements.txt
npx aws-cdk@2 synth    # requer Node + AWS CDK CLI
# npx aws-cdk@2 deploy  # só com CAB / conta lab
```

**Nota:** o asset Lambda é o source em `lambda/` — empacotar Powertools (layer ou bundle) fica em follow-up; este PR só faz o wiring IaC.
