# Deployment

Passos e comandos vivem no [README](README.md) (seção CDK / Deploy + Cognito lab).

Resumo:

1. `make check` (lint + types + pytest + `cdk synth`) — sem AWS
2. `npx aws-cdk@2 deploy` **só** com CAB aprovado / conta lab

Não há deploy em dois repos: o canônico é este (ADR-001).
