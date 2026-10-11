# Tests in active CI

`make validate` runs bootstrap/static checks and seven focused tests:

- `test-simple-update.sh` (source contract, bounded DNS readiness)
- `test-simple-monitor.sh`
- `test-simple-systemd.sh`
- `test-simple-shared-lock.sh` (backup/update mutual exclusion)
- `test-simple-repo-scope.sh` (no retired runtime)
- `test-maintenance-telegram-credentials.py`
- `test-github-api-access-contract.py`

Tests use local fixtures/mocks only. No production Docker socket, host
credentials, APT mutation, backups or service restarts are required.
Historical parity and activation tests remain in Git history.
