# Current handoff

## Canonical ownership

`rozkalnsandris/RPi5-maintenance` is the canonical source repository for the RPi5 maintenance implementation, policy, tests, systemd source, release metadata and recovery lineage.

GitHub is canonical for source/review/CI/continuity state. The live RPi5 is canonical only for actual installed/runtime state. Repository source does not prove deployment.

## Reviewed production baseline

- release/tag: `0.2.0`;
- release commit: `7a5685908e06cc35aa4bb623dd9fa6a3081c4416`;
- V28 activation operator source commit: `a0daa87cbd6a34a1f4a49648798c45587cdf43de`;
- production activation completed successfully on 2026-09-06 under separate LIVE authorization;
- PR #7 post-reboot notifier fix was separately deployed on 2026-09-07;
- no later source-only cleanup merge by itself authorizes or proves any live deployment change.

## Stable-production proof

The normal scheduled run `20260920_022000` completed successfully under the reviewed V28 policy and exercised the natural `if-needed` reboot path.

Fresh read-only evidence after the run/reboot established:

- `rpi5-update.service`: `Result=success`, `ExecMainStatus=0`;
- V28 run-scoped Docker evidence present under `/var/log/rpi5-maintenance/20260920_022000`;
- main and CV Docker pull/selection/reconcile phases succeeded and final health was healthy;
- APT used the reviewed `upgrade --with-new-pkgs --no-remove` path;
- rclone remained APT/dpkg-managed;
- cleanup remained under the reviewed 14-day policy;
- Hermes remained manual-only and was not updated;
- kernel/firmware changes triggered the reviewed automatic `if-needed` reboot;
- after reboot `/run/reboot-required` was absent;
- `rpi5-post-reboot.service` succeeded and the distinct success notifier path completed successfully;
- the prior notifier trigger-source ambiguity did not recur.

This satisfies the post-cutover stability prerequisite for Phase 9.

## Phase 9 duplicated-source cleanup — completed source outcome

Issue #24 tracked removal of predecessor maintenance ownership from `rozkalnsandris/RPi5_main` after stable-production proof.

Completed reviewed source chain:

1. `RPi5-maintenance` PR #43 — canonicalized maintenance systemd `Documentation=` provenance to `rozkalnsandris/RPi5-maintenance`; merged as `5728a45827dc1c3523ea95093e784969b673ce23`.
2. `RPi5_main` PR #654 — removed predecessor active maintenance runtime source ownership and added the explicit maintenance integration contract; merged as `811884275d4859e185ea4b12c5dac8dd92d0f1c8`.
3. `RPi5_main` PR #656 — removed the remaining duplicated maintenance helper/policy copies and orphan implementation tests, and strengthened the extraction boundary; merged as `caef0b0b29a824b8c9d3ad2ff3e8b80430d460d0`.

The `RPi5_main` integration contract now records:

- canonical repository: `rozkalnsandris/RPi5-maintenance`;
- runtime source model: `installed-artifacts-no-checkout-dependency`;
- retained local ownership only for backup and host/control-plane integrations;
- one explicit source exception: `ops/lib/rpi5-maintenance-locks.sh`, consumed by `ops/deploy/targets.json#maintenance-lock-lib` for the separately retained backup controlled-deploy boundary;
- `live_mutation_authorized=false`.

The shared-lock exception is intentional and must not be generalized to restore other maintenance implementation copies into `RPi5_main`.

Source search after #656 found no remaining duplicated `rpi5-update` / `rpi5-maintenance` implementation residue outside that documented exception. Canonical maintenance systemd source no longer points `Documentation=` at predecessor ownership.

## Runtime boundary after Phase 9 source cleanup

Phase 9 source cleanup did **not** mutate the live host.

Previously collected minimum read-only runtime proof established that production maintenance runs installed artifacts from `/usr/local/sbin` and units from `/etc/systemd/system`, not repository checkout symlinks. The source cleanup PRs therefore did not remove active production files.

No deployment, systemd reload, filesystem removal, cleanup, reboot or other LIVE mutation was authorized by PR #43, #654 or #656.

Any future deployment of the canonicalized unit source, removal/rebinding of installed artifacts, backup shared-lock migration or other runtime change requires a separate explicit LIVE authorization with fresh source and live-state verification.

## Current continuation

Phase 9 issue #24 is ready to close after this continuity update merges.

Do not silently roll P2 transaction classification/continuation or P3 doctor/backoff into #24. They are separate behavior milestones and require their own current work item and review scope.

After #24 is closed, run a fresh `START RPi5-maintenance` to select exactly one next lane from canonical GitHub state. No LIVE action is implied by that transition.
