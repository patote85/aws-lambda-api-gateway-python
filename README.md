# AWS Lambda Exclusão Cliente

## Integração com API Gateway
Ver repositório: https://github.com/patote85/aws-api-gateway-cdk

## Exemplos de Requisições

### 1. Solicitar Exclusão
```bash
curl -X POST https://api.exemplo.com/solicitar-exclusao-cliente \
  -H 'Content-Type: application/json' \
  -d '{"cliente_id": "12345", "motivo": "Pedido do cliente"}'
```

### 2. Status
```bash
curl https://api.exemplo.com/status-exclusao/12345
```

Link para API Gateway repo: https://github.com/patote85/aws-api-gateway-cdk