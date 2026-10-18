# ADR-003 — Padrão serverless: API Gateway HttpApi + Lambda, IaC em CDK Python

- **Status:** Accepted (CAB 2026-10-18)
- **Data:** 2026-10-18
- **Escopo:** todos os repos serverless do Rodrigo (padrão da squad)
- **Decisor:** Chefe via CAB (aprovação) / Arquiteto (proposta)

## Contexto

As duas APIs AWS já usam **HttpApi (v2)**, não REST API: o canônico `aws-lambda-api-gateway-python` (`aws_apigatewayv2.HttpApi` em `cdk/app.py`) e `aws-crud-api-lambda-dynamodb` (`AWS::Serverless::HttpApi` em `template.yaml`, comentário "cheaper & simpler than REST API"). O IaC diverge: o canônico é **CDK Python** (ADR-001 PR2, PR #5; CI `make check` + `cdk synth` sem deploy, PR #9); o CRUD é **SAM** (`sam validate --lint`, PR #2). A ADR-001 já fixou "Terraform: não" para a exclusão Pix. Falta o padrão geral.

## Decisão

1. API pública/síncrona = **API Gateway HttpApi + Lambda (Python 3.12)** com integração proxy.
2. IaC padrão de app serverless = **CDK Python**, um stack por bounded context, no mesmo repo do código (`cdk/` + `lambda/` + `tests/`).
3. CI obrigatório sem credenciais AWS: `make check` = lint + typecheck + testes + `cdk synth`. Deploy só com CAB.
4. Throttle no stage e CORS sem `*` (já testado por `test_cdk_cors_ban.py`).
5. SAM e Terraform não entram em repo novo de app serverless. O CRUD em SAM fica como está (demo/referência) até o Chefe pedir migração.

## Consequências / trade-offs

- (+) **Custo:** HttpApi é bem mais barato por milhão de requests que REST API (ordem de ~70% menos, pela tabela pública da AWS; conferir a região antes de citar valor).
- (+) **Latência e simplicidade:** menos overhead, JWT authorizer nativo (ADR-002), CORS nativo.
- (+) CDK Python: mesma linguagem da Lambda, grants tipados (`grant_read_write_data`), `cdk synth` testável no CI.
- (−) **Perde features do REST API:** usage plans e API keys, **WAF associado direto ao stage**, request validation por modelo, caching, transformação de request/response (VTL), endpoint privado/edge. Validação de payload fica na Lambda (Powertools / tipos).
- (−) Precisa WAF ou usage plan? Reabrir com ADR nova (REST API ou CloudFront + WAF na frente).
- (−) CDK exige Node no CI (`npx aws-cdk@2`) e bootstrap da conta no primeiro deploy (Infra).
- Dívida: dois sabores de IaC convivendo (CDK no canônico, SAM no CRUD).

## Princípios do pstack aplicados

- **Laziness Protocol / Subtract Before You Add:** um IaC e um tipo de API só; não manter SAM, CDK e Terraform lado a lado em repo novo. Mudou: SAM e Terraform saem do padrão.
- **Prove It Works:** `cdk synth` no CI prova o IaC sem deploy. Mudou: o `synth` entra no `make check` como gate obrigatório.
- **Encode Lessons in Structure:** CORS sem `*` já é teste; o padrão de IaC deve virar check de CI, não só ADR. Mudou: follow-up de check em Pendente.

## Alternativas descartadas

- **REST API (v1):** mais features, mas custo e latência maiores sem uso real de usage plans/WAF/VTL hoje.
- **SAM:** ótimo para demo, mas mistura YAML e Python e não tem grants tipados. Fica só no CRUD legado.
- **Terraform:** bom para plataforma, mas para app serverless separa IaC do código e repete o problema da ADR-001 (IaC órfã).
- **Lambda Function URL:** sem authorizer JWT, throttle por rota nem CORS gerenciado no mesmo nível.

**Pendente:** decidir se o CRUD migra para CDK (Chefe) e criar o check de "IaC padrão" no template de repo (Dev/Infra).
