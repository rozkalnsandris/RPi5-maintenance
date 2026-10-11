#!/usr/bin/env bash
set -euo pipefail
root="${1:-.}"
required=(
  README.md AGENTS.md HANDOFF.md LICENSE SECURITY.md
  Makefile
  docs/ARCHITECTURE.md docs/MAINTENANCE_LIFECYCLE.md docs/OPERATIONS_RUNBOOK.md
  docs/README-LV.md docs/CONFIGURATION.md docs/REFERENCES.md
  config/rpi-update.conf.example
  ops/bin/rpi5-update ops/bin/rpi5-monitor ops/bin/rpi5-maintenance-notify
  ops/bin/rpi5-backup ops/bin/rpi5-backup-serialized
  ops/lib/rpi5-maintenance-locks.sh ops/lib/rpi5-maintenance-telegram.py
  ops/systemd/rpi5-update.service ops/systemd/rpi5-update.timer
  ops/systemd/rpi5-monitor.service ops/systemd/rpi5-monitor.timer
  ops/systemd/rpi5-maintenance-notify@.service
)
for f in "${required[@]}"; do
  [[ -f "$root/$f" ]] || { echo "missing active file: $f" >&2; exit 1; }
done
echo "simple maintenance bootstrap PASS"
