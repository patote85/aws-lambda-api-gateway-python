# Agent-friendly check: shortest path = correct path (pytest + cdk synth).
# No deploy. Requires: pip install -r requirements.txt and -r cdk/requirements.txt; Node for npx.

.PHONY: check test synth

test:
	PYTHONPATH=. pytest tests/test_exclusao.py -v

synth:
	npx --yes aws-cdk@2 synth

check: test synth
