# AWS Lambda + API Gateway Python

## CI/CD
Pipeline GitHub Actions configurada:
- Testes automáticos em PR e push
- Deploy CDK automático na main (com secrets AWS)

## Como usar
1. Configure secrets no repo: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
2. Push para main → deploy automático