# ADR-NNN — Título curto da decisão

<!--
Modelo de ADR da squad. Copie para docs/adr/ADR-NNN-slug.md.
Só ganha ADR o que vira padrão pra mais de um sistema ou um porquê que não aparece no código.
Seções com "(obrigatória)" são checadas no CI; não apague o cabeçalho delas.
Curto: cada seção em poucas linhas. Sem jargão de slide.
-->

- **Status:** Proposed | Accepted (CAB AAAA-MM-DD) | Superseded por ADR-NNN | Deprecated
- **Data:** AAAA-MM-DD
- **Escopo:** sistema(s) / repo(s) afetados
- **Decisor:** Chefe via CAB (aprovação) / Arquiteto (proposta)

## Contexto (obrigatória)

O problema, o que existe hoje (com caminho de arquivo ou PR) e por que decidir agora.

## Decisão (obrigatória)

O que fica decidido, em itens numerados e verificáveis.

## Efeitos colaterais (obrigatória)

O que muda fora do escopo direto. Responda cada linha, mesmo que seja "nenhum":

- **Custo:** serviço novo, custo fixo mensal, driver de custo (→ FinOps).
- **Segurança / IAM / secrets:** role, policy ou secret novo.
- **Exposição pública:** rota, bucket ou endpoint novo acessível de fora.
- **Dados:** migração, retenção, ação irreversível.
- **Operação:** alarme, runbook, dependência nova.

Qualquer item diferente de "nenhum" em custo relevante, IAM/secrets, exposição pública ou ação irreversível sobe ao Rodrigo via Chefe antes do Accepted.

## Consequências / trade-offs (obrigatória)

- (+) ganho
- (−) custo ou risco aceito
- Dívida: o que fica pra depois e quem cuida.

## Alternativas descartadas (obrigatória)

- **Alternativa:** por que não, em uma linha.

## Princípios do pstack aplicados

- **Princípio:** como entrou na decisão. Mudou: o que muda no código ou no processo.

## Verificação

Como provar que a decisão está no código (teste de synth, check de CI, /statechart). Se for regra, deve virar teste, não só prosa.
