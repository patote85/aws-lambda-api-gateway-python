# Segurança

## O que este stack CDK cria (honesto)

Recursos em `cdk/app.py` hoje:

| Controle | Status |
|----------|--------|
| Cognito User Pool + App Client (lab) | **Sim** — email sign-in; `USER_PASSWORD` + `USER_SRP`; sem client secret |
| HTTP API JWT authorizer (Cognito) | **Sim** — nas rotas protegidas |
| `/health` público | **Sim** — sem authorizer (probes / smoke lab) |
| Throttle HTTP API | **Sim** — 100 rps / burst 200 |
| CORS | **Restrito a localhost** (`http://localhost:3000`, `http://127.0.0.1:3000`); override via CDK context `corsOrigins` |
| DynamoDB on-demand + IAM grant mínimo na Lambda | **Sim** |
| Validação / idempotência no handler | **Sim** (código Lambda) |
| WAF | **Não** — fora do CDK; não prometer |
| ACM / domínio custom / mTLS | **Não** — fora do CDK |
| Secrets no repositório | **Não** — User Pool / Client IDs só via CloudFormation outputs |

### Rotas

| Rota | Auth |
|------|------|
| `POST /solicitar-exclusao-cliente` | Cognito JWT |
| `GET /status-exclusao/{cliente_id}` | Cognito JWT |
| `POST /confirmar-pagamento` | Cognito JWT |
| `GET /health` | Público |

Enviar `Authorization: Bearer <IdToken>` nas rotas protegidas.

## Limitações de lab (aceitáveis até próximo ADR)

- User Pool com self sign-up e remoção `DESTROY` — adequado só a conta lab.
- Throttle ≠ proteção de abuso (sem WAF / rate por cliente).
- Pix continua stub; QR não é canal autenticado.
- CORS sem `*`, mas origins de lab são localhost; frontends em outro host precisam de `corsOrigins` no deploy.

## Melhorias planejadas (não implementadas neste PR)

- WAF / AWS Shield
- ACM + custom domain
- Alarmes / X-Ray
- Restringir self sign-up / MFA em ambientes não-lab
