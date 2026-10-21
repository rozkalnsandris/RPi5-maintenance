.PHONY: bootstrap-check static test validate

bootstrap-check:
	./scripts/bootstrap_validate.sh .

static:
	bash -n ops/bin/rpi5-update ops/bin/rpi5-monitor ops/bin/rpi5-maintenance-notify
	bash -n ops/bin/rpi5-backup ops/bin/rpi5-backup-serialized ops/lib/rpi5-maintenance-locks.sh
	python3 -m compileall -q ops/lib/rpi5-maintenance-telegram.py tests
	git diff --check

test:
	bash ./tests/test-simple-update.sh
	bash ./tests/test-simple-monitor.sh
	bash ./tests/test-simple-systemd.sh
	bash ./tests/test-simple-shared-lock.sh
	bash ./tests/test-simple-repo-scope.sh
	python3 ./tests/test-maintenance-telegram-credentials.py
	python3 ./tests/test-github-api-access-contract.py
	python3 ./tests/test-github-first-rdc-v1.py

validate: bootstrap-check static test
