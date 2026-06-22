# Lambda Exclusão de Cliente com Pix

## Funcionalidades
- POST /solicitar-exclusao-cliente : Inicia processo de exclusão + gera QR Pix para tarifa
- GET /status-exclusao/{cliente_id} : Consulta status
- POST /confirmar-pagamento : Confirma pagamento e avança exclusão

## Resiliência & Idempotência
- Idempotency via Powertools + DynamoDB check
- Error handling + logging estruturado
- DLQ recomendado no Lambda

## Observabilidade
- Powertools Metrics + Logger (forward to Datadog via extension)
- Recomendado: Datadog Lambda Extension + ddtrace

## Deploy
cdk deploy

## Testes
pytest tests/