.PHONY: bootstrap-check extraction-check static test validate

bootstrap-check:
	./scripts/bootstrap_validate.sh .

extraction-check:
	./scripts/verify_extraction.sh .

static:
	find ops scripts tests -type f -name '*.sh' -print0 | xargs -0 -r -n1 bash -n
	python3 -m compileall -q ops scripts tests
	git diff --check

test:
	bash ./tests/test-maintenance-updater-status.sh
	bash ./tests/test-maintenance-updater-locks.sh
	bash ./tests/test-maintenance-updater-reboot.sh
	bash ./tests/test-maintenance-updater-compose-health.sh
	bash ./tests/test-maintenance-updater-compose-policy.sh
	bash ./tests/test-maintenance-updater-docker-evidence.sh
	python3 ./tests/test-maintenance-compose-policy-activation.py
	bash ./tests/test-maintenance-updater-space-policy.sh
	bash ./tests/test-maintenance-updater-origin-policy.sh
	bash ./tests/test-maintenance-updater-http-health.sh
	bash ./tests/test-maintenance-updater-apt-policy.sh
	python3 ./tests/test-maintenance-v27-activation.py
	python3 ./tests/test-maintenance-v27-activation-transaction.py
	bash ./tests/test-maintenance-updater-provenance.sh
	bash ./tests/test-maintenance-updater-source.sh
	python3 ./tests/test-maintenance-updater-source-validator.py
	python3 ./tests/test-maintenance-updater-telegram.py
	bash ./tests/test-maintenance-health.sh
	bash ./tests/test-maintenance-health-entrypoints.sh
	python3 ./tests/test-maintenance-telegram-credentials.py
	bash ./tests/test-maintenance-systemd-units.sh
	python3 ./tests/test-maintenance-systemd-cutover.py
	bash ./tests/test-maintenance-systemd-notify.sh
	bash ./tests/test-maintenance-cleanup-policy.sh
	python3 ./tests/test-maintenance-cleanup-source.py
	bash ./tests/test-maintenance-shared-lock.sh
	python3 ./tests/test-maintenance-shared-lock-source.py
	python3 ./tests/test-maintenance-lock-cutover.py

validate: bootstrap-check extraction-check static test
