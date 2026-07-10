# AWS Lambda Exclusão de Cliente com Pix

## Visão Geral
API serverless para solicitação de exclusão de cliente com geração de QR Code Pix para pagamento de tarifa.

**Este projeto segue rigorosamente os Karpathy Claude Guidelines** (skill `karpathy-claude-guidelines`).

## Princípios Aplicados
- Think Before Coding
- Simplicity First
- Surgical Changes
- Goal-Driven Execution

## Melhorias Implementadas nesta versão
- Configuração via variáveis de ambiente (tabela DynamoDB e taxa Pix)
- Health Check endpoint
- Validação de input aprimorada
- Tratamento de erros mais robusto
- Métricas e logs estruturados

## Tecnologias
- Python 3.12 + AWS Lambda Powertools
- API Gateway HTTP
- DynamoDB
- Grok (xAI) + Karpathy Guidelines

## Exemplos de Requisições
Ver seção de rotas no código ou API.md