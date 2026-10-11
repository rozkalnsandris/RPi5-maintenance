#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"

# Source scope is intentionally small: five entrypoints, two libraries and
# five systemd units. No retired activators or alternate update engines.
[[ "$(find "$ROOT/ops/bin" -maxdepth 1 -type f | wc -l)" -eq 5 ]]
[[ "$(find "$ROOT/ops/lib" -maxdepth 1 -type f | wc -l)" -eq 2 ]]
[[ "$(find "$ROOT/ops/systemd" -maxdepth 1 -type f | wc -l)" -eq 5 ]]
[[ -f "$ROOT/ops/bin/rpi5-backup-serialized" ]]
[[ -f "$ROOT/ops/lib/rpi5-maintenance-locks.sh" ]]
[[ ! -e "$ROOT/ops/maintenance/updater-source-provenance.json" ]]
[[ ! -e "$ROOT/scripts/extract_from_rpi5_main.sh" ]]
[[ ! -e "$ROOT/config/rpi5-maintenance.conf.example" ]]
[[ ! -e "$ROOT/docs/HEALTH_AND_VERIFICATION.md" ]]

# Work-cycle and secret-handling governance stay in the repository.
[[ -f "$ROOT/.github/agent-bootstrap.json" ]]
[[ -f "$ROOT/.github/workflows/work-cycle-v23-conformance.yml" ]]
[[ -f "$ROOT/SECURITY.md" ]]
[[ -f "$ROOT/AGENTS.md" ]]
printf '%s\n' 'simple repository scope PASS'
