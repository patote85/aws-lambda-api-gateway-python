# AWS Lambda Exclusão Cliente com Pix

## Criação e Implementação com IA

Este repositório foi **inteiramente gerado e orquestrado por Grok (xAI)** no modo **Capitão absoluto**, seguindo regras estritas de verdade, ordem natural e disciplina.

### Detalhes Técnicos da Geração
- **Agente Principal**: Grok com skills integradas (Powertools, idempotency, logging estruturado).
- **Agent Toolkit for AWS**: aws-core plugin + MCP Server (Model Context Protocol) para acesso seguro a 300+ serviços AWS.
- **Skills utilizadas**: 
  - aws-core (CDK, Lambda, API Gateway, DynamoDB)
  - Powertools (Logger, Tracer, Metrics, Idempotency)
  - Custom skills para Pix QR Code e exclusão de cliente.
- **Ferramentas MCP**: Integração com GitHub via connected tools para criação de branches, push, merges e PRs.
- **Processo**: Criação de múltiplas branches feature, code review interno, merges controlados, documentação enriquecida.
- **Observabilidade**: Preparado para Datadog via Powertools + Lambda Extension.

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

**Gerado por Grok - Capitão da Verdade**