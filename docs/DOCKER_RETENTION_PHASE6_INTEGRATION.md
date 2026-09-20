# Docker retention Phase 6 staged integration

## Status

Source-only integration for issue #11. Production remains unchanged until a separate LIVE authorization installs the reviewed artifacts.

The production preflight on 2026-09-20 found a source/runtime gap: Phase 3–5 planners/executor existed in GitHub, but the scheduled V28 updater still directly ran `docker builder prune -a -f --filter until=...`, and the new retention commands were not installed on `rpi5`.

Phase 6 closes that source gap without activating tagged-image deletion or BuildKit cache pruning.

## Integration shape

`ops/bin/rpi5-update` remains the exact reviewed V28 core source. A new `ops/bin/rpi5-update-scheduled` wrapper is installed as `/usr/local/sbin/rpi5-update`, while the V28 core is installed under `/usr/local/lib/rpi5-maintenance/rpi5-update-v28-core`.

The wrapper:

1. verifies the root-owned V28 core identity;
2. requires the legacy private config to be compatible with `DOCKER_CLEANUP=no`, then exports that value before starting the core;
3. optionally runs the provenance-aware Phase 3–5 toolchain in `RETENTION_MODE=report`;
4. preserves only the previous bounded dangling-image cleanup using `docker image prune -f --filter until=<retention>`;
5. executes the unchanged V28 core for APT, rclone, Compose update/evidence, health, Hermes advisory checking and reboot policy.

The V28 core still contains its historical `docker builder prune -a` implementation for extraction/parity, but the reviewed scheduled wrapper makes that path unreachable because the core runs with Docker cleanup disabled.

## Staged policy

`ops/config/docker-retention.conf` defaults to:

- `RETENTION_MODE=off`;
- bounded dangling-image cleanup enabled;
- one extra superseded image retained per lineage;
- root high-watermark evidence at 80%;
- build-cache maximum 8 GiB;
- Buildx builder `default`;
- 15-second read-only command timeout;
- no project paths or trusted evidence run IDs.

The intentionally empty project/evidence identities mean the default staged install cannot silently enter report mode.

Switching to `RETENTION_MODE=report` is a separate reviewed LIVE config mutation after privileged read-only evidence validates exact project paths and trusted V28 evidence run IDs.

## Report mode

Report mode is still non-destructive with respect to tagged images and BuildKit cache. Before the V28 core runs, it creates a root-only evidence directory under `/var/log/rpi5-maintenance/retention/<run-id>` and writes:

- the Phase 3 runtime inventory/planner result;
- the Phase 4 exact-image executor **dry-run** result;
- the Phase 5 build-cache plan.

No `--apply` is passed to the image executor. The wrapper never executes `docker buildx prune`.

A report failure blocks the maintenance run before any Phase 6 dangling-image cleanup or V28 core mutation begins.

`--check` does not create durable Phase 6 evidence files.

## Production refresh operator

`ops/bin/rpi5-maintenance-retention-refresh` is the reviewed upgrade path for the already-active systemd scheduler. It is deliberately separate from the historical cron-to-systemd cutover operator.

The refresh operator:

- requires the exact reviewed V28 live updater identity or the exact current wrapper;
- verifies the active/enabled `rpi5-update.timer` baseline and refuses while `rpi5-update.service` is active;
- refuses an explicitly enabled legacy `DOCKER_CLEANUP` setting rather than silently rewriting `/etc/rpi-update.conf`;
- installs the mode-off policy and Phase 3–5 runtime dependencies first;
- replaces `/usr/local/sbin/rpi5-update` with the wrapper last;
- verifies exact installed bytes;
- does not start/restart/reload/enable/disable systemd units;
- does not run cleanup or Docker prune.

Running `--install` is a LIVE filesystem/scheduled-policy mutation and requires explicit owner authorization.

## Fail-closed boundaries

Phase 6 does not:

- delete tagged images;
- invoke the image executor with `--apply`;
- execute `docker buildx prune` or `docker builder prune` through the scheduled wrapper;
- prune volumes, containers or networks;
- use disk/cache pressure as image ownership authority;
- repair the unrelated pre-existing Weather HTTP 503 condition;
- use the stale live Git checkout as deployment source.

Actual exact-image deletion, BuildKit cache prune, policy switch to report mode, config changes, deploy/refresh and any reboot remain separately authorized LIVE work.
