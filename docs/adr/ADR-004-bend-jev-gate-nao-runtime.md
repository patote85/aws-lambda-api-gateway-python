# ADR-004 — Bend (e JEV) são gate de verificação no CI, não runtime em produção

- **Status:** Accepted (CAB 2026-10-18)
- **Data:** 2026-10-18
- **Escopo:** todos os repos que usam Bend ou JEV
- **Decisor:** Chefe via CAB (aprovação) / Arquiteto (proposta)

## Contexto

`patote85/crud-api-bend` reimplementa em Bend 2 o contrato HTTP de `aws-crud-api-lambda-dynamodb` e diz no README que "**não** é um port de Lambda, DynamoDB ou API Gateway". O que o repo tem de fato:

- **Leis e provas:** `LAWS.bend` + `PROOF.bend` (18 leis: create/get/delete/options, dois items, JSON, persist, envelope da lista, PUT parcial). `AGENTS.md`: "Do not weaken or delete a law to make a proof pass. The human owns LAWS.bend."
- **CI:** `.github/workflows/proof.yml` instala Bend e roda `test.sh` (`bend PROOF.bend` + demo em processo) em push/PR. "Sem TCP no CI."
- **Runtime de brinquedo:** processo único TCP `:8080`, HTTP mínimo, canal tamanho 1, store em `store.json` gravado a cada pedido, sem TLS, sem auth, `price` inteiro, `id` contador.

JEV não aparece em `crud-api-bend`; entra aqui pela mesma lógica de gate.

Ou seja: o valor do repo está nas leis verificadas, não no servidor.

## Decisão

1. **Bend é gate de CI:** leis do contrato em `LAWS.bend`, provas em `PROOF.bend`, rodadas em todo PR. Prova falhou, PR não passa o CAB.
2. **Bend não roda em produção.** A runtime de produção continua sendo HttpApi + Lambda Python + DynamoDB (ADR-003). O servidor Bend é só demo local.
3. **JEV entra no mesmo papel:** juiz tipado no CI/review, nunca no caminho de request. Chave só via secret-request (`JEV_API_KEY`).
4. **Leis são do humano:** enfraquecer ou apagar lei para passar prova é proibido e vale como ressalva no CAB.

## Por quê (o que não dá pra ver no código)

- O servidor Bend não tem o que produção exige: TLS, auth (ADR-002), concorrência real (canal tamanho 1), persistência durável e multi-instância (`store.json` local), observabilidade, nem caminho de deploy gerenciado na AWS.
- A força do Bend é provar propriedades do contrato (tipos dependentes, `match` exaustivo) **antes do merge**. Isso é verificação, e cabe no CI sem custo de cloud.
- Usar como runtime criaria um segundo stack para operar, sem SLA nem suporte da AWS, e trocaria "provar o contrato" por "manter um servidor HTTP feito à mão".

## Consequências / trade-offs

- (+) Gate formal barato (GitHub Actions, sem AWS) e contrato com prova, não só teste de exemplo.
- (−) Duas implementações do mesmo contrato (Python e Bend) podem divergir; a lei só prova o modelo Bend, não a Lambda.
- (−) Toolchain instalada via `curl | sh` no CI, sem versão fixada (risco de supply chain e de quebra). Fixar versão/checksum é follow-up.
- (−) Bend 2 é novo: curva de aprendizado e ecossistema pequeno.

## Princípios do pstack aplicados

- **Encode Lessons in Structure:** a regra de negócio vira lei verificável em `LAWS.bend`, não prosa. Mudou: o contrato do CRUD está em lei + prova no CI.
- **Prove It Works:** `test.sh` roda prova + demo a cada PR. Mudou: "pronto" = prova verde, não autodeclaração.
- **Type System Discipline:** tipos dependentes tornam estados ilegais irrepresentáveis no modelo. Mudou: `id`/`price` como `Nat`.
- **Subtract Before You Add:** nada de runtime Bend na AWS. Mudou: zero infra nova.

## Alternativas descartadas

- **Bend como runtime (container/ECS ou custom runtime Lambda):** ver "Por quê"; custo de operar sem ganho.
- **Só pytest, sem Bend:** perde a prova formal; continua valendo para a Lambda, mas não substitui as leis.
- **JEV no caminho de request:** latência, custo por chamada e dependência externa em produção.

**Pendente:** fixar a versão do Bend no `proof.yml`; ligar as leis ao contrato da Lambda (ex.: mesmo conjunto de casos em `test_http_contract.py`). Dev, quando o Chefe pedir.
