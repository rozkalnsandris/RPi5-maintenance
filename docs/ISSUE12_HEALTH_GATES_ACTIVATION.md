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

If any of the three shared coordination lock files are absent, apply mode may also materialize the missing path as a root-owned, non-group/world-writable empty lock file before acquiring it:

- `/run/lock/rpi5-update.lock`
- `/run/lock/rpi5-backup.lock`
- `/run/lock/rpi5-maintenance-exclusive.lock`

Missing lock files are normal after boot; the weekly updater and shared lock helpers also create their lock path on demand. The activator uses exclusive no-follow creation semantics and fails closed if an existing path is not a safe root-owned regular file.

After locks are held, the operator installs the six artifacts, runs `systemctl daemon-reload` and performs a direct `rpi5-monitor` verification. It does not start, stop, restart, enable or disable services/timers; mutate Docker/APT/Hermes; or reboot.

## Preconditions

The exact reviewed live pre-state hashes are embedded in the operator. Existing shared health runtime, V28 core and monitor timer must match the supplied source SHA. Monitor, post-reboot and updater services must be quiescent; monitor/update timers must remain enabled and active; `/run/reboot-required` must be absent; and updater/backup/shared maintenance locks must be acquirable.

Preflight treats a missing lock path as available without creating it. If a lock path already exists, it must be a safe root-owned regular file and must be acquirable non-blocking. Apply mode safely materializes any still-missing lock path immediately before acquisition; that creation is the first live mutation and therefore activates fail-closed semantics.

## Failure and rollback

Before replacing targets, apply mode preserves the previous six-target state under `/var/lib/rpi5-maintenance/health-gates-activation/`. Targets that were absent are recorded with `.MISSING` markers.

If any error occurs after mutation starts, including after creation of a previously missing lock file, the operator fails closed and performs no automatic retry, rollback, cleanup, restart or reboot. Lock files already materialized under `/run/lock` are coordination state and are not automatically deleted.

Rollback requires fresh explicit LIVE authorization: restore preserved targets, remove targets represented by `.MISSING` markers, and run `systemctl daemon-reload`. Lock-file cleanup, if ever desired, is a separate live mutation and is not part of automatic rollback.

No reboot is required by this activation itself.
