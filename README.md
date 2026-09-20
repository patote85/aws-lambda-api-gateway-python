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
