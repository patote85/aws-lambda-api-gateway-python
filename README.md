# AWS Lambda Exclusão de Cliente com Pix

## Arquitetura

![Arquitetura Serverless - Exclusão de Cliente com Pix](https://github.com/patote85/aws-lambda-api-gateway-python/blob/main/docs/arquitetura.png?raw=true)

**Diagrama gerado por Grok Imagine**

### Componentes Principais
- **API Gateway HTTP API** (com throttling e custom domain)
- **Lambda Python** (com Powertools: Logger, Tracer, Metrics, Idempotency)
- **DynamoDB** (tabela de solicitações com idempotência)
- **Geração de QR Code Pix** para tarifa de exclusão
- **Observabilidade**: CloudWatch + X-Ray (pronto para Datadog)

## Criação e Implementação com IA

Este projeto foi **inteiramente gerado e orquestrado por Grok (xAI)** no modo **Capitão absoluto**.

**Detalhes Técnicos**:
- Agent Toolkit for AWS (aws-core + MCP Server)
- Skills: Powertools, custom skills para Pix e exclusão
- Ferramentas: GitHub connected tools para branches, PRs e merges
- Processo: Múltiplas branches feature, code review rigoroso, merges controlados

## Casos de Uso
- Cliente solicita exclusão de cadastro
- Sistema gera QR Pix para pagamento de tarifa
- Confirmação de pagamento libera a exclusão
- Consulta de status em tempo real

## Regras de Negócio
- Idempotência: Não permite solicitações duplicadas
- Prazo de validade do QR Code: 7 dias
- Tarifa fixa ou configurável via env var
- Exclusão só após confirmação de pagamento

## Como Executar

### 1. Deploy da Lambda
```bash
# No repositório da Lambda
sam deploy --guided
```

### 2. Deploy do API Gateway
```bash
# No repositório CDK
cdk deploy
```

### 3. Teste
```bash
curl -X POST https://seu-api.execute-api.../solicitar-exclusao-cliente \
  -H "Content-Type: application/json" \
  -d '{"cliente_id": "12345", "motivo": "Teste"}'
```

## Repositórios Relacionados
- **API Gateway CDK**: https://github.com/patote85/aws-api-gateway-cdk

**Gerado por Grok - Capitão da Verdade**