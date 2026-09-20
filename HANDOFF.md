# Current handoff

## Canonical ownership

`rozkalnsandris/RPi5-maintenance` is the canonical source repository for the RPi5 maintenance implementation, policy, tests, systemd source, release metadata and recovery lineage.

GitHub is canonical for source/review/CI/continuity state. The live RPi5 is canonical only for actual installed/runtime state. Repository source does not prove deployment.

## Current repository state

- current `main` SHA is intentionally not stored in this handoff; resolve it fresh from the GitHub `main` branch before using this continuity state;
- SHA values retained below are historical source/runtime identities and must not be interpreted as the current repository head unless freshly verified against GitHub;
- open pull requests at the 2026-09-20 audit refresh: none;
- issue #26 `/tmp` NVMe cutover: closed/completed;
- issue #11 Docker image/build-cache retention: current maintenance-owned P1 continuation;
- parent audit index #10 remains open and must use this handoff plus current child-issue state instead of historical phase ordering.

## Reviewed production baseline

The normal scheduled run `20260920_022000` completed successfully under the reviewed V28 policy and exercised the natural `if-needed` reboot path. Fresh read-only evidence after that run/reboot established successful maintenance, Docker reconciliation, conservative APT behavior, APT-managed rclone, 14-day cleanup, manual-only Hermes handling, successful post-reboot verification and no residual `/run/reboot-required` state.

The `/tmp` NVMe policy from issue #26 is also production-complete: `/tmp` is disk-backed on root ext4/NVMe with mode `1777`; the legacy tmpfs fstab entry is disabled; the reviewed tmpfiles policy and `tmp.mount -> /dev/null` mask remain installed; post-reboot verification passed. The host's pre-existing Weather-owned degraded systemd/public-weather conditions remain outside maintenance ownership.

## Docker retention / Phase 6 production state

Issue #11 has advanced beyond the historical Phase 1/2 source-only state. Reviewed source chain through current `main` includes:

1. planner policy PR #46;
2. sanitized runtime inventory PR #48;
3. timeout-bounded report/collector PR #49;
4. fail-closed exact-image-ID executor PR #50;
5. BuildKit/buildx cache planner PR #52;
6. staged production integration PR #53;
7. untagged/container-referenced inventory fix PR #54;
8. zero-target executor dry-run fix PR #55, merged as source baseline `756319db3b347d0d1c8c366eb3e343cbde6cfbbf`.

Privileged production proof against exact current source passed:

- 261 images inventoried;
- 26 protected, 235 ignored, 0 delete candidates;
- `hermes-blog` is correctly protected as `container-referenced`;
- executor dry-run passed with zero requested/delete results;
- build-cache plan returned `noop` at 5.324 GB used against the 8 GiB cap;
- no image deletion, executor `--apply`, Buildx/builder/system prune, systemd mutation or reboot occurred.

A separately authorized prerequisite changed `/etc/rpi-update.conf` from `DOCKER_CLEANUP=yes` to `DOCKER_CLEANUP=no`, preserving the remaining private config and mode `0600`.

A separately authorized Phase 6 staged install then passed from exact source `756319db3b347d0d1c8c366eb3e343cbde6cfbbf`:

- installed wrapper `/usr/local/sbin/rpi5-update` SHA256 `664c16c74d5f796d560c5e7a6daca740e9bfa2d3d8c436ac4e68793d0d3a947c`;
- installed V28 core SHA256 `3a7898c1f06f7bd5b4136dd6875edf5c7178dad9c8ea4099ef065ce9b1c20882`;
- Phase 3–5 tooling installed with reviewed identities;
- timer remained active/enabled and service inactive;
- no maintenance run, cleanup/prune, Docker restart, systemd restart/reload/enable/disable or reboot occurred during install.

A final config-only LIVE gate activated report mode without running maintenance:

- `RETENTION_MODE=report`;
- `RETENTION_MAIN_PROJECT_DIR=/home/andris/docker`;
- `RETENTION_CV_PROJECT_DIR=/home/andris/docker/cv`;
- `RETENTION_TRUSTED_EVIDENCE_RUNS=20260913_022000,20260920_022000`;
- bounded dangling-image cleanup and the other reviewed policy values were preserved;
- wrapper/core/systemd identities remained unchanged;
- no maintenance run, image delete, executor `--apply`, Buildx prune, systemd mutation or reboot occurred.

## Current continuation

Issue #11 remains open only for observation of the first normal scheduled report-mode run and review of its durable evidence.

Do **not** manually start `rpi5-update.service` in this lane.

After the next normal `rpi5-update.timer` execution, perform a minimum-sufficient read-only review of:

1. service result and timer baseline;
2. newest `/var/log/rpi5-maintenance/retention/<run-id>` planner/executor/build-cache evidence;
3. planner delete candidates and protected identities;
4. build-cache action/reason;
5. proof that executor remained dry-run and neither `docker buildx prune` nor the legacy broad `docker builder prune -a` path executed;
6. normal V28 maintenance, health and reboot outcome;
7. `/run/reboot-required` state.

If the scheduled report-mode run fails, gather only the minimum read-only evidence needed and STOP. Do not manually retry the maintenance run without a new explicit LIVE authorization.

If the scheduled report-mode run passes, review the durable evidence before deciding whether any future exact-image deletion or BuildKit cache prune policy is warranted. Those remain separate reviewed and explicitly authorized LIVE gates.

## Runtime/source boundary

Installed production artifacts and live host state remain separate from repository source. Any future maintenance deployment, rollback, cleanup, systemd mutation, package/Docker mutation, backup shared-lock migration, manual maintenance run or destructive retention action requires its own exact LIVE authorization and fresh preflight.
