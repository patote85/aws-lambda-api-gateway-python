# Arquitetura — exclusão Pix (canônico)

**Fonte da verdade:** [ADR-001](docs/adr/ADR-001-unificar-exclusao-pix.md) (Accepted) + [README](README.md).
Este arquivo **não** substitui o ADR; só resume o desenho atual pra agents/humanos.

## Bounded context

Um repo, um stack deployável: `patote85/aws-lambda-api-gateway-python`.

| Pasta | Papel |
|-------|--------|
| `lambda/` | Handler Powertools (HTTP API) |
| `cdk/` | Cognito + DynamoDB + Lambda + HttpApi (JWT) |
| `tests/` | pytest + moto (sem AWS) |
| `docs/adr/` | Decisões versionadas |

`aws-api-gateway-cdk` está **arquivado** (banner no README dele) — não usar pra deploy.

## Componentes (hoje)

- **HTTP API** — throttle 100 rps / burst 200; CORS lab localhost (sem `*`)
- **Lambda** Python 3.12 — `app.lambda_handler`
- **DynamoDB** — PK `cliente_id` / SK `request_id`, pointer `LATEST`
- **Cognito User Pool** — JWT nas rotas mutáveis/status; `GET /health` público

## Access pattern Dynamo (obrigatório)

1. Histórico: `SK = <uuid>`
2. Ponteiro: `SK = LATEST` (espelho do estado corrente)
3. Status/dedup leem só `LATEST`
4. Confirmação de pagamento atualiza uuid **e** `LATEST`

## Verificação agent-friendly

```bash
make check   # ruff + mypy(tests) + pytest + cdk synth
```

## Não-objetivos (ainda)

- Step Functions / SNS/SQS (event-driven) — ADR futuro
- WAF / ACM / domínio custom
- Pix real (stub de lab)
- Unificar com `aws-crud-api-lambda-dynamodb` (outro BC)
