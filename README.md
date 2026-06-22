# AWS Lambda Exclusão de Cliente com Pix

## Descrição Funcional
API serverless para solicitação de exclusão de cliente com pagamento de tarifa via Pix.

## Casos de Uso
- Cliente solicita exclusão do cadastro
- Geração de QR Code Pix para tarifa
- Confirmação de pagamento libera a exclusão
- Consulta de status em tempo real

## Tecnologias Utilizadas
- **Linguagem**: Python 3.12
- **IA**: Grok (xAI) no modo Capitão absoluto
- **Ferramentas**: Agent Toolkit for AWS (MCP Server), Powertools for AWS Lambda (Logger, Tracer, Metrics, Idempotency, Validation)
- **Bibliotecas**: boto3, Pydantic, tenacity (para retry)
- **AWS Services**: API Gateway, Lambda, DynamoDB, (futuro: FIS, Resilience Hub, Systems Manager)
- **CI/CD**: GitHub Actions

## Exemplos de Requisições

POST /solicitar-exclusao-cliente
```bash
curl -X POST https://seu-api.../solicitar-exclusao-cliente \
  -H 'Content-Type: application/json' \
  -d '{"cliente_id": "12345", "motivo": "Pedido do cliente"}'
```

## Instruções de Geração de READMEs Futuros
Ver README_TEMPLATE.md

**Gerado por Grok - Capitão da Verdade**