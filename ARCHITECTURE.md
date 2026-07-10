# Arquitetura Detalhada

## Visão Geral
Ver README.md para diagrama simplificado.

## Componentes
- API Gateway
- Lambda
- DynamoDB
- Futuro: Step Functions + SNS/SQS para processamento assíncrono

## Decisões de Arquitetura
- Serverless first
- Idempotência no nível da aplicação
- Separação entre código e infraestrutura (dois repositórios)