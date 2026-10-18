# ADR-002 — Auth padrão: Cognito JWT authorizer no HttpApi

- **Status:** Proposed
- **Data:** 2026-10-18
- **Escopo:** todos os repos serverless do Rodrigo (padrão da squad)
- **Decisor:** Chefe via CAB (aprovação) / Arquiteto (proposta)

## Contexto

A decisão de auth existe hoje só dentro da ADR-001 (PR3, CAB 2026-09-20) e só para a exclusão Pix. Na main do canônico (`cdk/app.py`, PR #6): Cognito User Pool + `HttpJwtAuthorizer` com issuer do pool e audience = app client; `POST /solicitar-exclusao-cliente`, `GET /status-exclusao/{cliente_id}` e `POST /confirmar-pagamento` com authorizer; `GET /health` público; sem WAF/ACM; CORS restrito a localhost (ou context `corsOrigins`). Em `aws-crud-api-lambda-dynamodb` (`template.yaml`) **não há auth** ("add auth later"). Sem um padrão escrito, cada repo novo reabre a discussão.

## Decisão

1. Toda API HttpApi usa **JWT authorizer nativo apontando para um Cognito User Pool**.
2. **Todas as rotas protegidas, exceto `GET /health`** (probe/smoke). Rota pública nova = exceção de exposição pública → sobe ao Rodrigo via Chefe.
3. **Um User Pool simples por ambiente/lab**, por stack: login por e-mail, app client sem secret (`USER_PASSWORD` + `USER_SRP`), `RemovalPolicy.DESTROY` só em lab.
4. **Sem WAF por enquanto.** Proteção de lab = JWT + throttle do stage (100 rps / burst 200 no canônico) + CORS sem `*`.
5. SECURITY.md só descreve o que o IaC tem.

## Consequências / trade-offs

- (+) Validação de token no API Gateway, sem código de auth na Lambda; custo de Cognito baixo em lab.
- (+) Um padrão só: issuer + audience, fácil de revisar em PR.
- (−) Autorização fina (escopos/claims por rota) fica para a app ou para ADR futura.
- (−) `self_sign_up_enabled=True` no canônico: qualquer um com o client id cria usuário. Aceito em lab; **produção exige revisão** (desligar sign-up ou ADR nova).
- (−) Sem WAF: sem rate limit por IP nem regras gerenciadas. Revisitar antes de qualquer exposição pública real.
- Dívida: `aws-crud-api-lambda-dynamodb` está fora do padrão (sem auth). Adequar em PR próprio quando o Chefe pedir.

## Princípios do pstack aplicados

- **Encode Lessons in Structure:** a regra "toda rota tem authorizer, exceto /health" deve virar teste de synth (no estilo de `tests/test_cdk_cors_ban.py`), não só esta prosa. Mudou: follow-up pro Dev listado em Pendente.
- **Boundary Discipline:** auth validada na borda (API Gateway), a Lambda confia no evento. Mudou: nenhum código de JWT na app.
- **Subtract Before You Add:** WAF, domínio custom e Lambda authorizer ficaram fora. Mudou: escopo do padrão = o que já está na main.

## Alternativas descartadas

- **Lambda authorizer próprio:** mais código, latência e custo, sem ganho em lab.
- **IAM auth (SigV4):** bom para máquina-a-máquina, ruim para cliente web/mobile.
- **API key / usage plans:** não existe no HttpApi e não é autenticação.
- **WAF já agora:** custo fixo mensal por Web ACL sem tráfego real que justifique.

**Pendente:** teste de synth "authorizer em toda rota exceto /health" (Dev, quando o Chefe pedir).
