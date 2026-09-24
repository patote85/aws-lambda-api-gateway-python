# Agent-friendly check: shortest path = correct path.
# No deploy. Requires: pip install -r requirements.txt -r requirements-dev.txt
# and -r cdk/requirements.txt; Node for npx.
#
# make verify  = prove-it-works (HTTP contracts via lambda_handler, incl. GET /health)
# make check   = full gate (lint + typecheck + all tests + cdk synth)

.PHONY: check test synth lint typecheck verify

verify:
	PYTHONPATH=. pytest tests/test_http_contract.py -v

test:
	PYTHONPATH=. pytest tests/ -v

lint:
	ruff check lambda tests cdk

typecheck:
	mypy

synth:
	npx --yes aws-cdk@2 synth

check: lint typecheck test synth
