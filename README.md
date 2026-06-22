# AWS Lambda Exclusão Cliente

**Status**: Main atualizada e sincronizada com API Gateway CDK.

Ver integração: https://github.com/patote85/aws-api-gateway-cdk

## Exemplos de Requisições

POST /solicitar-exclusao-cliente
```bash
curl -X POST https://seu-api.execute-api.us-east-1.amazonaws.com/solicitar-exclusao-cliente -H 'Content-Type: application/json' -d '{"cliente_id": "123", "motivo": "Teste"}'
```

Mais exemplos no repo CDK.