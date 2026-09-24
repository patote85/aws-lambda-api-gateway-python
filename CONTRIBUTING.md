# Contributing

## Local checks

```bash
pip install -r requirements.txt -r requirements-dev.txt
pip install -r cdk/requirements.txt   # for synth
make verify   # HTTP contracts (prove-it-works)
make check    # lint + typecheck + all tests + cdk synth (no deploy)
```

## Pull requests

1. Branch from `main`.
2. Keep PRs small and focused.
3. CI must be green (`lint`, `test`, `verify`, `synth`) before merge.
4. No deploy from CI; production deploy requires CAB.
