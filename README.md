# AWS Lambda Exclusão de Cliente com Pix

## 1. Visão Geral do Projeto

Este repositório contém a implementação de uma **API Serverless** para o processo de solicitação de exclusão de cliente com pagamento de tarifa via Pix.

O sistema permite que clientes solicitem a exclusão de seus dados, gerem um QR Code Pix para pagamento de uma taxa, e após a confirmação do pagamento, a exclusão seja processada.

**Princípios Fundamentais de Desenvolvimento:**
- Segue rigorosamente os **Karpathy Claude Guidelines** (skill `karpathy-claude-guidelines`)
- Foco em simplicidade, mudanças cirúrgicas e execução orientada a objetivos

## 2. Regras de Negócio

- Todo cliente pode solicitar exclusão uma única vez por vez (idempotência)
- É cobrada uma taxa fixa (configurável) para processar a exclusão
- A exclusão só é efetivada após confirmação do pagamento da taxa
- O QR Code tem validade de 7 dias
- O sistema deve ser resiliente a falhas e idempotente

## 3. Arquitetura

### Diagrama de Arquitetura

```
Cliente
   |
   v
API Gateway (HTTP API + Throttling)
   |
   v
Lambda (Python + Powertools)
   |--- DynamoDB (ExclusaoClientes)
   |--- Geração de QR Pix (stub / real)
   |
   v
Confirmação de Pagamento
   |
   v
Processamento de Exclusão (futuro: Step Functions)
```

### Componentes Principais
- **API Gateway HTTP**: Entrada da aplicação com throttling
- **Lambda Function**: Lógica de negócio
- **DynamoDB**: Armazenamento de solicitações (idempotência)
- **Powertools**: Logging, Tracing, Metrics, Idempotency

## 4. Implementação Técnica

### Tecnologias Utilizadas
- **Linguagem**: Python 3.12
- **Framework Serverless**: AWS Lambda + API Gateway HTTP
- **Bibliotecas Principais**:
  - aws-lambda-powertools (Logger, Tracer, Metrics, Idempotency, Validation)
  - boto3
  - Pydantic (validação)
- **IA e Ferramentas de Desenvolvimento**:
  - Grok (xAI) no modo Capitão
  - Skill `karpathy-claude-guidelines`
- **Infraestrutura**: AWS CDK (repositório separado)

### Configurações (Environment Variables)
- `TABLE_NAME`: Nome da tabela DynamoDB (default: ExclusaoClientes)
- `PIX_FEE`: Valor da taxa em BRL (default: 50.00)

## 5. Endpoints da API

| Método | Rota                        | Descrição                          |
|---------|-----------------------------|-------------------------------------|
| POST    | /solicitar-exclusao-cliente | Solicita exclusão e gera QR Pix   |
| GET     | /status-exclusao/{cliente_id} | Consulta status da solicitação   |
| POST    | /confirmar-pagamento        | Confirma pagamento da taxa          |
| GET     | /health                     | Health Check da aplicação       |

## 6. Testes

- Testes unitários com `pytest`
- Cobertura de rotas principais
- Uso de mocks para DynamoDB

Localização: `tests/`

## 7. Segurança e Resiliência

- Idempotência implementada via Powertools
- Tratamento de erros estruturado
- Health Check para monitoramento
- Throttling no API Gateway (via CDK)
- Configuração via variáveis de ambiente (evita hardcoded)

## 8. Deploy

1. Configurar variáveis de ambiente na Lambda
2. Deploy via CDK (repositório `aws-api-gateway-cdk`)
3. CI/CD configurado no GitHub Actions

## 9. Princípios de Desenvolvimento

Este projeto adota os **Karpathy Claude Guidelines**:
- Think Before Coding
- Simplicity First
- Surgical Changes
- Goal-Driven Execution

## 10. Melhorias Futuras
- Integração real com Pix (biblioteca oficial)
- Processamento de exclusão via Step Functions
- Autenticação/Authorizer
- Observabilidade completa (Datadog/X-Ray)
- Testes de Chaos Engineering (FIS)

---

**Gerado por Grok (xAI) - Capitão da Verdade**
**Code Review:** Aprovado seguindo Karpathy Guidelines