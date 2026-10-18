# Índice de ADRs (atualizado 2026-10-18)

ADRs ficam em `docs/adr/` do repo canônico `patote85/aws-lambda-api-gateway-python`. Só ganha ADR o que vira padrão pra mais de um sistema ou um porquê que não aparece no código.

## ADRs

| ADR | Título | Status | Escopo |
|-----|--------|--------|--------|
| [ADR-001](./ADR-001-unificar-exclusao-pix.md) | Unificar exclusão Pix (CDK + Lambda) | Accepted (CAB 2026-09-20) | Exclusão Pix |
| [ADR-002](./ADR-002-auth-cognito-jwt-httpapi.md) | Auth padrão: Cognito JWT authorizer no HttpApi | Accepted (CAB 2026-10-18) | Todos os repos |
| [ADR-003](./ADR-003-httpapi-lambda-cdk-python.md) | HttpApi + Lambda, IaC em CDK Python | Accepted (CAB 2026-10-18) | Todos os repos |
| [ADR-004](./ADR-004-bend-jev-gate-nao-runtime.md) | Bend (e JEV) como gate no CI, não runtime | Accepted (CAB 2026-10-18) | Repos com Bend/JEV |

## Decisões registradas sem ADR (já estão no código ou são fato consumado)

| Decisão | Onde está | Link |
|---------|-----------|------|
| `aws-crud-api-lambda-dynamodb`: modelo de dados (tabela `Items`, PK `id`, on-demand) e CI (pytest + moto, `sam validate --lint`, `make check` = lint + mypy + testes + sam validate) | `template.yaml`, `Makefile`, `tests/` | [PR #1 pytest+moto](https://github.com/patote85/aws-crud-api-lambda-dynamodb/pull/1), [PR #2 sam validate](https://github.com/patote85/aws-crud-api-lambda-dynamodb/pull/2), [PR #3 make check](https://github.com/patote85/aws-crud-api-lambda-dynamodb/pull/3) |
| `aws-api-gateway-cdk` arquivado; stack migrado pro canônico (ADR-001) | banner "Arquivado" no README do repo antigo | [aws-api-gateway-cdk PR #1](https://github.com/patote85/aws-api-gateway-cdk/pull/1) (banner), [canônico PR #5](https://github.com/patote85/aws-lambda-api-gateway-python/pull/5) (migração do CDK) |

Nota: o CI "`make check` + `cdk synth` (sem deploy)" é o [PR #9 do canônico](https://github.com/patote85/aws-lambda-api-gateway-python/pull/9), não do CRUD. O CRUD usa SAM, não CDK (ver ADR-003).
