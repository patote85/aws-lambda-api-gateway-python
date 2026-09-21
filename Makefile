.PHONY: check test synth

# Same pytest command as CI job `test`
test:
	PYTHONPATH=. pytest tests/test_exclusao.py -v

# Requires: pip install -r cdk/requirements.txt + Node (npx)
synth:
	npx --yes aws-cdk@2 synth

check: test synth
