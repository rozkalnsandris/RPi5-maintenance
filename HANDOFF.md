# Current handoff

## Canonical ownership

`rozkalnsandris/RPi5-maintenance` is the canonical source repository for the RPi5 maintenance implementation, policy, tests, systemd source, release metadata and recovery lineage.

GitHub is canonical for source/review/CI/continuity state. The live RPi5 is canonical only for actual installed/runtime state. Repository source does not prove deployment.

## Current repository state

- current `main` SHA is intentionally not stored in this handoff; resolve it fresh from the GitHub `main` branch before using this continuity state;
- SHA values retained below are reviewed/historical source or runtime identities and must not be interpreted as the current repository head unless freshly verified against GitHub;
- issue #26 `/tmp` NVMe cutover is closed/completed;
- issue #11 Docker image/build-cache retention is waiting for the first normal scheduled report-mode run; it is not the immediately actionable lane before that timer run;
- issue #12 explicit production service health gates is the current actionable maintenance-owned P1 lane and is at a LIVE activation gate after reviewed source completion;
- parent audit index #10 remains open and must use this handoff plus fresh child-issue state rather than historical phase ordering;
- issue #22 remains an unresolved governance gap: fresh audit evidence still reports `main` as unprotected and repository rulesets empty;
- #37–#41 are a separate P3 observability/Hermes workstream. Historical wording inside #37 that calls #24 the current Phase 9 lane is stale; #24 is already closed/completed.

## Reviewed production baseline

The normal scheduled run `20260920_022000` completed successfully under the reviewed V28 policy and exercised the natural `if-needed` reboot path. Fresh read-only evidence after that run/reboot established successful maintenance, Docker reconciliation, conservative APT behavior, APT-managed rclone, 14-day cleanup, manual-only Hermes handling, successful post-reboot verification and no residual `/run/reboot-required` state.

The `/tmp` NVMe policy from issue #26 is production-complete: `/tmp` is disk-backed on root ext4/NVMe with mode `1777`; the legacy tmpfs fstab entry is disabled; the reviewed tmpfiles policy and `tmp.mount -> /dev/null` mask remain installed; post-reboot verification passed. Weather-owned degraded state remains outside maintenance ownership.

## Issue #11 — Docker retention waiting lane

Reviewed source through PR #55 established deterministic retention planning, exact-image-ID execution, BuildKit/buildx cache policy and staged production integration. Source baseline `756319db3b347d0d1c8c366eb3e343cbde6cfbbf` was used for the reviewed Phase 6 production install.

Production state already proven for #11:

- `/etc/rpi-update.conf` has `DOCKER_CLEANUP=no` under separate authorization;
- installed wrapper `/usr/local/sbin/rpi5-update` SHA256 `664c16c74d5f796d560c5e7a6daca740e9bfa2d3d8c436ac4e68793d0d3a947c`;
- installed V28 core SHA256 `3a7898c1f06f7bd5b4136dd6875edf5c7178dad9c8ea4099ef065ce9b1c20882`;
- `/etc/rpi5-maintenance/docker-retention.conf` is in `RETENTION_MODE=report` with the reviewed main/CV project identities;
- prior privileged dry-run evidence found 261 images, 26 protected, 235 ignored, 0 delete candidates;
- build-cache planning returned `noop` at 5.324 GB used against the 8 GiB cap;
- no image deletion, executor `--apply`, Buildx/builder/system prune, Docker restart or reboot was authorized by those gates.

Fresh read-only audit evidence on 2026-09-20 confirms:

- `rpi5-update.timer` is enabled and active;
- its next normal run is `2026-09-27 02:20:00 CEST`;
- `RETENTION_MODE=report` remains active;
- no first scheduled report-mode retention evidence directory exists yet.

Therefore #11 is blocked by time, not by a source or runtime defect. Do **not** manually start `rpi5-update.service` in this lane. After the 2026-09-27 scheduled run, review the newest durable retention evidence read-only before considering any destructive retention gate.

## Issue #12 — current actionable health-gates lane

Reviewed source for explicit service-health ownership is merged through PRs #59–#65. The implementation now includes:

- canonical `ops/config/service-health.tsv` and `docs/SERVICE_HEALTH_MATRIX.md`;
- shared `ops/lib/rpi5-service-health.sh` classification with `PASS`, `TRANSIENT`, `FAIL_PERSISTENT` and `OBSERVE` states;
- policy-driven `rpi5-monitor` and `rpi5-post-reboot` behavior;
- updater Compose convergence bound to the same canonical health ownership;
- bounded activation operator `ops/bin/rpi5-health-gates-activate` with exact-main CI binding, pre-state guards, preserved backup state, lock coordination, six reviewed targets, `systemctl daemon-reload`, monitor verification, no service restart and no automatic rollback;
- regression coverage for starting/unhealthy/missing/exited/probe failure and probe-infrastructure-error classification; the historical `/tmp` ENOSPC remediation contract is separately regression-tested by the `/tmp` policy tests.

The last reviewed source identity before this handoff refresh was `38a9d278a4063106030f06a353b58cc73dc34925`, with exact-main `validate #208` SUCCESS. Always refresh current `main` and exact-main CI before using that identity operationally.

Fresh read-only RPi5 preflight against that reviewed identity passed with exit code 0:

- `HEALTH_GATES_PREFLIGHT=PASS`;
- `/usr/local/lib/rpi5-maintenance/rpi5-service-health.sh` is still missing;
- `/etc/rpi5-maintenance/service-health.tsv` is still missing;
- the existing updater Compose-health helper, `rpi5-post-reboot`, `rpi5-monitor` and `rpi5-monitor.service` still match the activator's expected old pre-state;
- `rpi5-monitor.service`, `rpi5-post-reboot.service` and `rpi5-update.service` are inactive;
- `rpi5-monitor.timer` and `rpi5-update.timer` are active;
- the three maintenance lock files are absent, which is an allowed pre-state handled safely by the merged activator;
- `/run/reboot-required` is absent.

No #12 LIVE activation has occurred yet. The earlier failed preflight happened before any host mutation and was corrected by PR #65; the fresh post-fix preflight passes. Issue #12 remains OPEN until the reviewed six-artifact activation and post-activation runtime verification are completed.

## Current continuation

Primary current lane: **issue #12 LIVE activation**.

Before asking for or consuming a LIVE authorization:

1. resolve current `main` fresh from GitHub;
2. require exact-main `validate` SUCCESS;
3. run the merged `rpi5-health-gates-activate --preflight` read-only against that exact SHA on host `rpi5`;
4. verify the six expected target pre-states, prerequisite identities, quiescent maintenance services, active timers, lock availability and `/run/reboot-required` state.

If that preflight passes, STOP at an explicit LIVE gate for the bounded activation only: materialize missing lock files if required, preserve pre-state, install exactly six reviewed artifacts, run `systemctl daemon-reload`, run `rpi5-monitor` verification, no service restart, no Docker/APT/Hermes mutation and no reboot. If any error occurs after the first host mutation, fail closed with no retry or automatic rollback.

Secondary waiting lane: **issue #11 scheduled report-mode observation** after the normal `2026-09-27 02:20 CEST` timer run. Do not substitute a manual maintenance run.

After #12 runtime activation/verification is complete, close or update #12 only from fresh evidence and then select the next actionable audit child from #10 using current ownership/priority, not stale historical ordering.

## Runtime/source boundary

Installed production artifacts and live host state remain separate from repository source. Repository source, merged PRs and passing CI do not prove deployment. Any future maintenance deployment, rollback, cleanup, systemd mutation, package/Docker mutation, backup shared-lock migration, manual maintenance run or destructive retention action requires its own exact LIVE authorization and fresh preflight.
