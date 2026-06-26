# AWS Lambda Exclusão de Cliente com Pix

## Visão Geral e Princípios de Desenvolvimento

Este projeto foi desenvolvido seguindo rigorosamente os **Karpathy Claude Guidelines** (skill `karpathy-claude-guidelines`).

### Princípios Aplicados

1. **Think Before Coding**: Todas as decisões foram explíitas. Tradeoffs foram documentados.
2. **Simplicity First**: Código mínimo necessário. Sem abstrações desnecessárias.
3. **Surgical Changes**: Apenas o necessário foi alterado.
4. **Goal-Driven Execution**: Cada feature teve critérios de sucesso verificáveis.

## Descrição Funcional
API serverless para solicitação de exclusão de cliente com geração de QR Code Pix para pagamento de tarifa.

## Casos de Uso
- Cliente solicita exclusão de cadastro.
- Sistema gera QR Pix para tarifa.
- Confirmação de pagamento libera a exclusão.
- Consulta de status em tempo real.

## Tecnologias Utilizadas
- **Linguagem**: Python 3.12
- **IA**: Grok (xAI) no modo Capitão + skill karpathy-claude-guidelines
- **Bibliotecas**: boto3, Pydantic, aws-lambda-powertools
- **AWS**: API Gateway, Lambda, DynamoDB
- **CI/CD**: GitHub Actions
- **Resiliência**: Karpathy Guidelines + Powertools Idempotency

## Exemplos de Requisições

### Solicitar Exclusão
```bash
curl -X POST https://seu-api.execute-api.../solicitar-exclusao-cliente \
  -H 'Content-Type: application/json' \
  -d '{"cliente_id": "12345", "motivo": "Pedido do cliente"}'
```

## Como o Skill karpathy-claude-guidelines foi Aplicado
- Todo o código foi revisado para simplicidade.
- Mudanças foram cirúrgicas.
- Critérios de sucesso foram definidos antes da implementação.

**Gerado por Grok - Capitão da Verdade (com Karpathy Guidelines)**