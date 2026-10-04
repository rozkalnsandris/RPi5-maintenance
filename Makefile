.PHONY: bootstrap-check static test validate

bootstrap-check:
	./scripts/bootstrap_validate.sh .

static:
	bash -n ops/bin/rpi5-update ops/bin/rpi5-monitor ops/bin/rpi5-maintenance-notify
	python3 -m compileall -q ops/lib/rpi5-maintenance-telegram.py tests
	git diff --check

test:
	bash ./tests/test-simple-update.sh
	bash ./tests/test-simple-monitor.sh
	bash ./tests/test-simple-systemd.sh
	python3 ./tests/test-maintenance-telegram-credentials.py
	python3 ./tests/test-github-api-access-contract.py

validate: bootstrap-check static test
