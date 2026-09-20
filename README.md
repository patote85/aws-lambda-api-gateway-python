# AWS Lambda Exclusão de Cliente com Pix

## Visão Geral
API serverless para solicitação de exclusão de cliente com geração de QR Code Pix para pagamento de tarifa.

**Este projeto segue rigorosamente os Karpathy Claude Guidelines**.

## Melhorias Implementadas
- Tabela DynamoDB criada via CDK
- Configuração via env vars
- Health Check endpoint
- Throttling no API Gateway

**Code Review:** Aprovado seguindo Karpathy Guidelines.

**Merge realizado para main.**

## Architecture Decision Records

- [ADR-001 — Unificar exclusão Pix (CDK + Lambda)](docs/adr/ADR-001-unificar-exclusao-pix.md) — **Accepted** (CAB 2026-09-20). Este repo é o canônico; `aws-api-gateway-cdk` será arquivado após migrar o stack. Access pattern Dynamo: pointer `LATEST`. Auth (PR3): Cognito JWT.
