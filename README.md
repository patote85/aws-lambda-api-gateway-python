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

Cada solicitação grava **dois** itens (TransactWrite):

| SK | Papel |
|----|--------|
| UUID da solicitação | Histórico imutável daquele pedido |
| `LATEST` | Ponteiro do estado atual (`active_request_id`, `status`, …) |

- **Dedup / status** leem só `LATEST` (não mais um UUID que nunca existia como SK=`LATEST`).
- **Confirmar pagamento** atualiza histórico + `LATEST` no mesmo TransactWrite (só se `active_request_id` bater).

### Testes

```bash
pip install -r requirements.txt
PYTHONPATH=. pytest tests/test_exclusao.py -v
```

Usa **moto** (sem AWS real).
