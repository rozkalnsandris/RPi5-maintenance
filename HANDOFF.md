# Current handoff

## Canonical ownership

`rozkalnsandris/RPi5-maintenance` is canonical for maintenance source, policy, tests and review. The live RPi5 remains canonical for installed/runtime state.

## Current state

Issue #11 is closed/completed. PR #73 replaced the previous maintenance control-plane complexity with the simple scheduled runtime and merged as source commit `60a1d6ebfcc819978073d39066c22f4cf0ce33a9`.

The active production model is now:

- one weekly `rpi5-update` oneshot;
- one daily read-only `rpi5-monitor` oneshot;
- native systemd timers and OnSuccess/OnFailure notification;
- generic Compose ownership limited to `/home/andris/docker`;
- app-specific/simple-deployer projects remain owned by their app/deployer workflows;
- Uptime Kuma owns public endpoint monitoring;
- Hermes remains separate/manual and APT owns APT-managed rclone.

## LIVE cutover evidence — 2026-10-04

The exact simple runtime from `60a1d6ebfcc819978073d39066c22f4cf0ce33a9` is installed on host `rpi5`.

Fresh read-only evidence after cutover:

- `rpi5-update.timer`: active/enabled;
- `rpi5-monitor.timer`: active/enabled;
- `rpi5-update.service`: inactive/static;
- `rpi5-monitor.service`: inactive/static;
- installed updater, monitor, service/timer units and notifier unit match the reviewed source;
- the simplified monitor passes with all 12 main Compose services running;
- root filesystem usage was 56%;
- `REBOOT_REQUIRED=no`.

Retired legacy scheduled-runtime artifacts are absent:

- `rpi5-post-reboot.service`;
- `/usr/local/sbin/rpi5-post-reboot`;
- `/etc/rpi5-maintenance/docker-retention.conf`;
- `/etc/rpi5-maintenance/required-containers`;
- `/usr/local/lib/rpi5-maintenance/docker-retention`.

The cutover operator initially stopped after mutation because its post-check expected a literal `not-found` stdout value from `systemctl is-enabled`; systemd instead reported the missing unit on stderr. Subsequent read-only verification confirmed the intended final state and exact-source parity. No retry, rollback, maintenance run, APT/Docker update, cleanup or reboot followed that STOP.

The rollback snapshot from the cutover is preserved under `/var/lib/rpi5-maintenance/simple-cutover/20261004T084845Z-60a1d6ebfcc8`. Restoring it is a separate LIVE mutation and requires fresh explicit authorization.

## Next continuation

There is no remaining issue #11 implementation work. Normal future maintenance work should start from the current GitHub `main` and fresh live evidence.

Do not revive the retired retention planner/report/executor or health-classifier/TSV architecture unless a new explicit design decision requires it.
