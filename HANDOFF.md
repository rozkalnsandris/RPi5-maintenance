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
- no later source-only merge by itself authorizes or proves a live deployment change.

## Stable-production proof

The normal scheduled run `20260920_022000` completed successfully under the reviewed V28 policy and exercised the natural `if-needed` reboot path.

Fresh read-only evidence after that run/reboot established successful maintenance, Docker reconciliation, conservative APT behavior, APT-managed rclone, 14-day cleanup, manual-only Hermes handling, successful post-reboot verification and no residual `/run/reboot-required` state.

## Phase 9 duplicated-source cleanup — completed

Issue #24 is closed. Reviewed source chain:

1. `RPi5-maintenance` PR #43 — canonicalized maintenance systemd `Documentation=` provenance; merged as `5728a45827dc1c3523ea95093e784969b673ce23`.
2. `RPi5_main` PR #654 — removed predecessor active maintenance runtime source ownership and added the explicit integration contract; merged as `811884275d4859e185ea4b12c5dac8dd92d0f1c8`.
3. `RPi5_main` PR #656 — removed residual duplicated maintenance helper/policy copies and orphan implementation tests; merged as `caef0b0b29a824b8c9d3ad2ff3e8b80430d460d0`.
4. `RPi5-maintenance` PR #44 — closed Phase 9 continuity; merged as `a1b4f297d02c6bc19431c209b5cb4abd07479e21`.

The retained `RPi5_main` source exception remains only `ops/lib/rpi5-maintenance-locks.sh` for the separately retained backup controlled-deploy boundary. It must not be generalized to restore maintenance implementation ownership there.

## `/tmp` NVMe cutover — production completed

Issue #26 tracks the reviewed PR #9 policy that prevents recurrence of the 2 GiB `/tmp` tmpfs exhaustion incident.

Source identity used for production activation:

- canonical source main: `a1b4f297d02c6bc19431c209b5cb4abd07479e21`;
- operator: `ops/bin/rpi5-tmp-policy-activate`;
- Git blob: `0ca77ca93a60218d9bd5e456e36194cfa616f0d0`;
- exact raw-source SHA256: `e3774a6e20510e5655ec8ff53830ee60b8f39b9281ff226e1af9c7012599bb53`.

Owner-authorized LIVE staging completed successfully on 2026-09-20:

- `TMP_POLICY_STAGE=PASS`;
- the exact legacy `/etc/fstab` tmpfs line was disabled with the reviewed marker;
- `/etc/tmpfiles.d/tmp.conf` was installed as `root:root 0644` with `D /tmp 1777 root root 14d`;
- `/etc/systemd/system/tmp.mount -> /dev/null` was installed;
- rollback/evidence state was preserved at `/root/rpi5-tmp-policy-lBWABBdX`;
- no unmount/remount, cleanup, unrelated restart or reboot occurred during staging.

A separately owner-authorized reboot/cutover then completed. Fresh post-boot read-only verification established:

- `TMP_POLICY_PERSISTENT_STATE=policy-installed`;
- `TMP_POLICY_RUNTIME_STATE=disk-backed`;
- `TMP_POLICY_POST_REBOOT_VERIFY=PASS`;
- `/tmp` resolves to the root `ext4` filesystem on NVMe and has mode `1777`;
- the legacy fstab line count is `0`, the canonical disabled marker count is `1`, and the reviewed tmpfiles/mask artifacts remain exact;
- `rpi5-update.service`, `rpi5-monitor.service` and `rpi5-post-reboot.service` report `Result=success` for the relevant executions;
- `rpi5-update.timer`, `rpi5-monitor.timer` and `docker.service` are active;
- nine inspected Docker healthcheck-enabled containers are healthy with fresh post-boot samples and `FailingStreak=0`;
- `/run/reboot-required` is absent.

The host remains `systemd=degraded` because of the pre-existing `rozkalns-weather-operator-v7-dispatch-caller.service` failure, and `rozkalns-weather-public-weather-1` remains pre-existing `unhealthy`. Those conditions were present outside the `/tmp` cutover scope and are not evidence of a cutover regression.

No rollback, cleanup or other post-cutover mutation was performed.

## Runtime/source boundary

Installed production artifacts and live host state remain separate from repository source. Any future maintenance deployment, rollback, cleanup, systemd mutation, backup shared-lock migration or other runtime change requires its own exact LIVE authorization and fresh preflight.

## Current continuation

Issue #26 has completed its production acceptance criteria. After this continuity update merges, close #26 as `completed`, mark #26 complete in parent audit index #10, and run a fresh `START RPi5-maintenance` to select exactly one next lane from canonical GitHub state.

Do not silently roll unrelated Weather remediation, P2 transaction classification/continuation or P3 doctor/backoff work into #26.
