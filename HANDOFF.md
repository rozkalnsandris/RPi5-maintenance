# Current handoff

## Current state

`RPi5-maintenance` is the independent maintenance source/control-plane repository.

GitHub release/tag **`0.2.0`** remains bound to exact release commit `7a5685908e06cc35aa4bb623dd9fa6a3081c4416` (tree `3e6ef8913b64a48d5eb3ba90f13c74c5a7083d67`). The separately authorized production activation completed successfully on 2026-09-06 using the reviewed operator from `main` commit `a0daa87cbd6a34a1f4a49648798c45587cdf43de`.

Production runs the exact V28 updater/helper identities from release `0.2.0` plus the separately reviewed PR #7 post-reboot notifier hotfix. Stable-production proof was established by the normal scheduled maintenance run `20260920_022000` and its natural reboot/post-reboot path.

## Exact production identity

- release/tag: `0.2.0`;
- release commit: `7a5685908e06cc35aa4bb623dd9fa6a3081c4416`;
- activation operator source commit: `a0daa87cbd6a34a1f4a49648798c45587cdf43de`;
- activation operator SHA256: `0384eb3b544883a1e979c7711cde351cd5597c28819054d07406e2bf770f959a`;
- activation operator Git blob: `be0473e43d37271096a0461df2780f9e62effb67`;
- `/usr/local/sbin/rpi5-update` SHA256: `3a7898c1f06f7bd5b4136dd6875edf5c7178dad9c8ea4099ef065ce9b1c20882`, owner/mode `root:root 0750`;
- `/usr/local/lib/rpi5-maintenance/rpi5-update-compose-policy.sh` SHA256: `5ee19cbf09f5fa06853d1c121fea8216e1ae245aaa17af81e2affe6ab3aaae4f`, owner/mode `root:root 0644`;
- `/usr/local/lib/rpi5-maintenance/rpi5-update-docker-evidence.sh` SHA256: `f133adb38eb5499e1e582532f142f1b892ba99755262ce0612d8b21e96716456`, owner/mode `root:root 0644`;
- `/usr/local/sbin/rpi5-maintenance-notify` SHA256: `46241a4c73245379de53844fc148d38bab558337845f41911012a04ffeb58703`, owner/mode `root:root 0755`;
- `/etc/systemd/system/rpi5-post-reboot.service` SHA256: `467e1c0b5825e62bbd9eee7fce1df4d4f7b33ca88bd4e90b9be13cf7135f606c`, owner/mode `root:root 0644`;
- exact release-commit `validate` push CI run `34023964012`: SUCCESS;
- activation-operator merged-main `validate` push CI run `34025290660`: SUCCESS.

## Activation and notifier continuity

The 2026-09-06 activation established V28 production identity without APT, Docker, systemd, cleanup or reboot mutation outside the reviewed activation itself. Root-only activation evidence remains under `/root/rpi5-v28-activation-20260906-115620.8f7xwf`.

On 2026-09-07 the boot-time `rpi5-post-reboot.service` itself succeeded, but its notification incorrectly reported a failure with `unknown` monitor metadata because the same notifier instance had been configured for both `OnSuccess=` and `OnFailure=`.

PR **#7** fixed that ambiguity by using distinct success/failure notifier instances and an instance-name fallback in `rpi5-maintenance-notify`. PR #7 merged as `115a8162ed650e7b153124b49be30f499d4af47f`; exact PR head `88b143b3faef6b8ebd5f4e6c668b4b9116b1720a` passed `validate` run `34147197655`. A separately authorized LIVE deployment installed only that reviewed notifier fix plus `systemctl daemon-reload`.

## 2026-09-13 scheduled-run outcome

The first normal scheduled stability-proof run after cutover, run id `20260913_022000`, did **not** establish stable-production proof.

The run exercised intended V28 fail-closed behavior: APT succeeded, Docker main pull changed images, and target selection stopped on `reason=config-drift`, `service=homeassistant`, `rc=3`. Docker CV was skipped; final main/CV health and local/public endpoint gates remained healthy; automatic reboot was blocked. Issue **#32** captured the incident.

The owner later performed the narrow Home Assistant reconciliation documented in #32. Fresh read-only evidence then showed running/local Home Assistant image and Compose config hashes converged, local endpoint HTTP 200, public endpoint HTTP 302, main/CV runtime healthy, `/run/reboot-required` absent, and the V28 selection blocker cleared. Issue #32 is closed.

## Stable-production proof — 2026-09-20

The normal scheduled maintenance run `20260920_022000` completed successfully under the reviewed V28 policy and exercised the natural `if-needed` reboot path.

Fresh read-only evidence collected after the run and reboot showed:

- `rpi5-update.service`: `Result=success`, `ExecMainStatus=0`;
- evidence directory `/var/log/rpi5-maintenance/20260920_022000` present with V28 run-scoped Docker evidence;
- main Docker `pull`, `target-selection`, `reconcile`: `outcome=succeeded`, `rc=0`, `mutation=changed`;
- main Docker `final-health`: `outcome=healthy`, `rc=0`;
- CV Docker `pull`, `target-selection`, `reconcile`: `outcome=succeeded`, `rc=0`, `mutation=none`;
- CV Docker `final-health`: `outcome=healthy`, `rc=0`;
- final main/CV evidence lists all expected containers running, with healthcheck-equipped containers healthy;
- APT simulation reported `20` upgradable and `0` removable packages, followed by the reviewed `upgrade --with-new-pkgs --no-remove` path;
- rclone remained APT/dpkg-managed;
- cleanup remained under the reviewed 14-day policy; autoremove candidates were informational only and were not deleted automatically;
- Hermes remained manual-only; the run reported `12137` commits behind `origin/main` and performed no Hermes update;
- kernel/firmware package change triggered the reviewed automatic `if-needed` reboot;
- after reboot `/run/reboot-required` is absent;
- `rpi5-update.timer` is `enabled/active`, next scheduled elapse `2026-09-27 02:20 CEST`;
- `rpi5-post-reboot.service`: `Result=success`, `ExecMainStatus=0`, readiness PASS on attempt `2/30`;
- systemd triggered `OnSuccess=` and started `rpi5-maintenance-notify@success-rpi5-post-reboot.service`; the notifier instance completed successfully;
- the prior `unknown`/trigger-source ambiguity did not recur;
- the installed V28 updater/helper hashes and PR #7 notifier/service hashes exactly match the reviewed production baseline above.

This closes the post-cutover stability gate for the installed `0.2.0` maintenance control-plane plus PR #7 notifier hotfix. No manual maintenance run or manufactured reboot was used to establish the proof.

## Current lane — Phase 9 duplicated maintenance-source cleanup

Issue **#24** is the active continuation lane. The stable-production prerequisite is satisfied; #24 remains open for the actual cleanup work.

Proceed source-first and fail-closed:

1. Inventory only duplicated maintenance source/policy remaining in `RPi5_main` whose canonical ownership is now `RPi5-maintenance`.
2. Identify systemd `Documentation=`/operator docs/provenance pointers that still reference predecessor ownership.
3. Prove from source and minimum read-only runtime evidence that no active deployment/runtime path depends on files proposed for removal.
4. Prepare the smallest coherent reviewed source PR(s), preserving rollback/recovery documentation.
5. Do not merge without explicit MERGE authorization.
6. Do not remove, deploy, rewrite, restart, reload, clean up or otherwise mutate the live RPi5 without separate explicit LIVE authorization.

P2 transaction classification/continuation and P3 doctor/backoff remain separate later behavior milestones and require their own scoped work items.
