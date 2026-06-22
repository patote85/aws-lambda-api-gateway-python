# AWS Lambda Exclusão Cliente com Pix

## Visão Geral
Arquitetura serverless completa: API Gateway + Lambda Python + DynamoDB + Pix QR Code para tarifa de exclusão.

## Repositórios Relacionados
- **API Gateway CDK**: https://github.com/patote85/aws-api-gateway-cdk

## Funcionalidades
- Solicitação de exclusão com geração de Pix QR Code
- Consulta de status
- Confirmação de pagamento
- Idempotência, resiliência e observabilidade (Powertools + Datadog-ready)

## Exemplos de Uso

### 1. Solicitar Exclusão
```bash
curl -X POST https://seu-api.execute-api.us-east-1.amazonaws.com/solicitar-exclusao-cliente \
  -H 'Content-Type: application/json' \
  -d '{"cliente_id": "12345", "motivo": "Pedido do cliente"}'
```

### 2. Ver Status
```bash
curl https://seu-api.execute-api.us-east-1.amazonaws.com/status-exclusao/12345
```

## Deploy
1. Deploy Lambda
2. Deploy CDK (API Gateway)

## CI/CD
Pipeline GitHub Actions ativa com testes e deploy.

## Contato
@patote85