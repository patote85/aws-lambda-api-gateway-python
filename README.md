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

CI (GitHub Actions): job `test` (pytest+moto, Python 3.12) e job `synth` (`npx aws-cdk@2 synth`, sem deploy) em todo PR/`push` na `main` — sem credenciais AWS no runner.

### Check local

```bash
pip install -r requirements.txt -r cdk/requirements.txt
make check   # pytest (igual ao CI) + npx aws-cdk@2 synth (sem deploy)
```

Requer Node (para `npx`). Só `make test` ou `make synth` se quiser isolar.

---

## CDK / Deploy

Stack único em `cdk/app.py` (ADR-001): **Cognito + DynamoDB + Lambda + HTTP API** no mesmo stack — sem `from_function_name`.

- Tabela: PK `cliente_id` / SK `request_id`, on-demand; `grant_read_write_data` na Lambda.
- Env: `TABLE_NAME` (nome da tabela), `PIX_FEE` (default `50.00`).
- Handler: `app.lambda_handler` (código em `lambda/`).
- Throttle HTTP API: **100 rps / burst 200**.
- Auth: Cognito JWT nas rotas mutáveis/status; **`GET /health` público**.
- CORS lab: `http://localhost:3000` e `http://127.0.0.1:3000` (sem `*`). Override via CDK context `corsOrigins` (lista de origins).
- Rotas: `POST /solicitar-exclusao-cliente`, `GET /status-exclusao/{cliente_id}`, `POST /confirmar-pagamento`, `GET /health`.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r cdk/requirements.txt
npx aws-cdk@2 synth    # requer Node + AWS CDK CLI
# npx aws-cdk@2 deploy  # só com CAB / conta lab
```

Outputs úteis após deploy: `ApiUrl`, `UserPoolId`, `UserPoolClientId`, `JwtIssuer`.

**Nota:** o asset Lambda é o source em `lambda/` — empacotar Powertools (layer ou bundle) fica em follow-up; este PR só faz o wiring IaC.

---

## Cognito JWT — obter token e testar (lab)

Após `cdk deploy` (com CAB), anote `UserPoolId`, `UserPoolClientId` e `ApiUrl`.

### 1) Criar usuário (lab)

```bash
aws cognito-idp sign-up \
  --client-id "$CLIENT_ID" \
  --username "lab@example.com" \
  --password 'LabPass123' \
  --user-attributes Name=email,Value=lab@example.com

# Confirmar (lab — admin; self-sign-up exige confirmação de e-mail ou admin-confirm)
aws cognito-idp admin-confirm-sign-up \
  --user-pool-id "$USER_POOL_ID" \
  --username "lab@example.com"
```

### 2) Obter IdToken

```bash
aws cognito-idp initiate-auth \
  --client-id "$CLIENT_ID" \
  --auth-flow USER_PASSWORD_AUTH \
  --auth-parameters USERNAME=lab@example.com,PASSWORD='LabPass123'
```

Use o campo `AuthenticationResult.IdToken` (não o AccessToken) no header.

### 3) Chamar API

```bash
# Público
curl -s "$API_URL/health"

# Protegido
PAYLOAD='{"cliente_id":"c1","motivo":"lab"}'
curl -s -X POST "$API_URL/solicitar-exclusao-cliente" \
  -H "Authorization: Bearer $ID_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD"

curl -s "$API_URL/status-exclusao/c1" \
  -H "Authorization: Bearer $ID_TOKEN"
```

Sem Bearer nas rotas protegidas → API Gateway responde **401** antes da Lambda.
