# Issue #12 health-gates activation

This document defines the bounded production activation boundary for issue #12.

## Reviewed source

Activation must use `ops/bin/rpi5-health-gates-activate` from the exact merged `main` SHA supplied with `--source-sha`. The operator verifies that the SHA is current remote `main` and has a successful exact-main push `validate` run before any mutation.

## Mutation scope

The operator installs exactly six reviewed artifacts:

1. `/usr/local/lib/rpi5-maintenance/rpi5-service-health.sh`
2. `/etc/rpi5-maintenance/service-health.tsv`
3. `/usr/local/lib/rpi5-maintenance/rpi5-update-compose-health.sh`
4. `/usr/local/sbin/rpi5-post-reboot`
5. `/usr/local/sbin/rpi5-monitor`
6. `/etc/systemd/system/rpi5-monitor.service`

It then runs `systemctl daemon-reload` and performs a direct `rpi5-monitor` verification. It does not start, stop, restart, enable or disable services/timers; mutate Docker/APT/Hermes; or reboot.

## Preconditions

The exact reviewed live pre-state hashes are embedded in the operator. Existing shared health runtime, V28 core and monitor timer must match the supplied source SHA. Monitor, post-reboot and updater services must be quiescent; monitor/update timers must remain enabled and active; `/run/reboot-required` must be absent; and updater/backup/shared maintenance locks must be acquirable.

## Failure and rollback

Before replacing targets, apply mode preserves the previous six-target state under `/var/lib/rpi5-maintenance/health-gates-activation/`. Targets that were absent are recorded with `.MISSING` markers.

If any error occurs after mutation starts, the operator fails closed and performs no automatic retry, rollback, cleanup, restart or reboot. Rollback requires fresh explicit LIVE authorization: restore preserved targets, remove targets represented by `.MISSING` markers, and run `systemctl daemon-reload`.

No reboot is required by this activation itself.
