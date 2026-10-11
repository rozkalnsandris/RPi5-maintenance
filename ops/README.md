# Active production source and backup lock

Scheduled runtime:
- `bin/rpi5-update` — weekly APT/Compose/cleanup/monitor/reboot decision.
- `bin/rpi5-monitor` — daily read-only checks.
- `bin/rpi5-maintenance-notify` and `lib/rpi5-maintenance-telegram.py`.
- Five `systemd` service/timer units under `systemd/`.

Shared backup scope (retained, not started by maintenance timers):
- `bin/rpi5-backup-serialized` — backup wrapper holding the shared lock.
- `bin/rpi5-backup` — historical backup core source.
- `lib/rpi5-maintenance-locks.sh` — common backup lock primitives.

Retired activation/transaction/health-classifier artifacts are accessible
in Git history, not in the active source tree.
