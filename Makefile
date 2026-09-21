# Agent-friendly check: shortest path = correct path.
# No deploy. Requires: pip install -r requirements.txt -r requirements-dev.txt
# and -r cdk/requirements.txt; Node for npx.

.PHONY: check test synth lint typecheck

test:
	PYTHONPATH=. pytest tests/test_exclusao.py -v

lint:
	ruff check lambda tests cdk

typecheck:
	mypy tests

synth:
	npx --yes aws-cdk@2 synth

check: lint typecheck test synth
