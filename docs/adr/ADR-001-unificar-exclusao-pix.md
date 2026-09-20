# ADR-001 — Unificar exclusão Pix (CDK + Lambda)

- **Status:** Accepted
- **CAB:** 2026-09-20 (Rodrigo)
- **Data:** 2026-09-20
- **Repos:** `patote85/aws-api-gateway-cdk` + `patote85/aws-lambda-api-gateway-python`
- **Decisor:** Rodrigo via CAB (aprovação) / Arquiteto (proposta)

## Contexto

Dois repos cobrem o mesmo bounded context (“Exclusão de Cliente com Pix”):

| Repo | O que tem na main | Lacuna |
|------|-------------------|--------|
| `aws-lambda-api-gateway-python` | Handler Powertools (`lambda/app.py`), testes, docs, `ARCHITECTURE.md` | `cdk/app.py` é stub (“complete in next step”) |
| `aws-api-gateway-cdk` | HttpApi + tabela Dynamo + throttle; Lambda **importada por nome** | Tabela criada e **não wired** à Lambda (sem `grant_*`, sem `TABLE_NAME`); WAF/ACM/authorizer só no SECURITY.md |

`ARCHITECTURE.md` hoje diz “dois repositórios”. Na prática: deploy quebrado, contrato Dynamo inconsistente, docs de segurança à frente do código.

Bug de access pattern (evidência em `lambda/app.py`):

- `put_item` grava `request_id = uuid`
- dedup e `GET /status-exclusao/{cliente_id}` leem `request_id = 'LATEST'`
- **`LATEST` nunca é escrito** → status sempre 404 / dedup morto
- `POST /confirmar-pagamento` atualiza pelo `request_id` do body (uuid) — ok se o cliente guardar o uuid, mas o ponteiro LATEST não acompanha

Throttle no CDK: 100 rps / burst 200. CORS `*`. Auth: nenhuma na main.

## Decisão

### 1) Um repo, não dois

**Canônico:** `patote85/aws-lambda-api-gateway-python` (já tem código, testes e docs).

**Arquivar:** `patote85/aws-api-gateway-cdk` **após** migrar o stack CDK para `cdk/` do canônico (README vivo: seção “Arquivado — ver …” no repo antigo; **não** substituir o README inteiro). Aprovado no CAB 2026-09-20.

Motivo: um bounded context = um artefato deployável. Split IaC/código só vale com contrato e pipeline maduros; aqui o split gerou IaC órfã. Monorepo pequeno (cdk/ + lambda/ + tests/) cabe em PRs pequenos.

Alternativa rejeitada: manter dois repos e “só amarrar” por nome de Lambda — continua drift de versão e CAB impossível de rastrear.

### 2) Access patterns Dynamo

Tabela: **PK `cliente_id` (S) + SK `request_id` (S)**, on-demand (já no CDK).

**Padrão obrigatório (pointer LATEST):**

1. Item de histórico: `SK = <uuid>` — payload completo (`status`, `motivo`, `qr_code_data`, `fee_amount`, `created_at`, `expires_at`, …).
2. Item ponteiro: `SK = LATEST` — espelho mínimo do estado corrente (`current_request_id`, `status`, `updated_at`). Escrito/atualizado em **toda** transição (`PENDING_PAYMENT`, `PAID`, …) na mesma unidade lógica (TransactWrite quando possível).
3. `GET status` e dedup leem **só** `LATEST`.
4. `confirmar-pagamento` atualiza o item `uuid` **e** o ponteiro `LATEST`.

GSI: não agora. Query por status fica pra ADR futuro se volume/ops pedirem.

Pix continua stub até ADR de integração real (fora deste ADR).

### 3) Auth e throttle

- **Throttle:** manter 100/200 no HttpApi (lab); documentar no README incremental. Não é proteção de abuso sozinho.
- **Auth (PR3, CAB 2026-09-20):** JWT authorizer no HttpApi com **Cognito User Pool**. CORS aberto (`*`) só enquanto lab; com Cognito, restringir origins.
- **Fora do escopo deste ADR (próximo):** WAF, ACM/domínio custom, alarms/X-Ray — não prometer no SECURITY.md até existir no CDK.
- **Filas / Step Functions:** previstos no ARCHITECTURE.md; **não** entram nos PRs abaixo. Confirmação de pagamento síncrona fica explícita como limitação de lab até ADR event-driven.

### 4) PRs pequenos depois (ordem)

| PR | Escopo | Repo / branch |
|----|--------|----------------|
| **PR1** | Corrigir access pattern LATEST (handler + testes moto). Sem mudança de API pública além de status passar a funcionar. README: seção “Dynamo access patterns”. | canônico, branch `fix/dynamo-latest-pointer` |
| **PR2** | Trazer stack CDK do outro repo pro canônico; **wire** tabela→Lambda (`grant_read_write_data`, env `TABLE_NAME`); remover `from_function_name`. Deploy de um `cdk deploy`. README incremental no canônico; no repo CDK, só acrescentar banner “Arquivado”. | canônico + touch no CDK a arquivar |
| **PR3** | Cognito JWT no HttpApi + CORS menos aberto; alinhar SECURITY.md ao que o CDK realmente tem (sem inventar WAF). | canônico, branch `feat/httpapi-cognito` |

Ninguém mergeia main sem CAB do Chefe ao Rodrigo. Arquiteto revisa desenho nos PRs; não mergeia.

## Consequências

**Positivas:** um caminho de deploy; bug LATEST some; SECURITY deixa de mentir; PRs revertíveis; auth Cognito definida.

**Negativas / custo:** histórico do repo CDK vira ponteiro; Cognito User Pool exige conta/config (Infra).

**Riscos residuais:** Pix stub + pagamento síncrono continuam — não vender como Core. Bend/JEV não entram neste bounded context (gate fica em skills-core / crud-api-bend).

## Não-objetivos

- Código de aplicação além do necessário pro contrato Dynamo (Dev implementa).
- Terraform (stack é CDK Python).
- Unificar com `aws-crud-api-lambda-dynamodb` (CRUD Item é outro BC; só referência de estilo SAM/demo).
- Mudança em `grok-skills-core`.

## Referências

- Avaliação Arquiteto 2026-09-20 (notas 2/5 nos dois repos).
- CAB 2026-09-20 — Accepted (Cognito JWT; arquivar CDK após migrar; canônico = este repo).
- `lambda/app.py` (LATEST vs uuid), `cdk/app.py` do repo CDK (tabela sem grant).
