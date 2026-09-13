# Current handoff

## Current state

`rpi5-maintenance` is the independent maintenance source repository. P1/V28 Docker evidence hardening, the release/shadow gate and the V28 production-activation operator are merged on `main`.

GitHub release/tag **`0.2.0`** remains bound to exact release commit `7a5685908e06cc35aa4bb623dd9fa6a3081c4416` (tree `3e6ef8913b64a48d5eb3ba90f13c74c5a7083d67`). The separately authorized production activation completed successfully on 2026-09-06 using the reviewed operator from `main` commit `a0daa87cbd6a34a1f4a49648798c45587cdf43de`.

Production runs the exact V28 updater/helper identities from release `0.2.0`, plus the separately reviewed post-reboot notifier hotfix from PR #7. Release publication itself did not authorize production; LIVE mutations remained separately owner-gated.

## Exact production identity

- release/tag: `0.2.0`;
- release commit: `7a5685908e06cc35aa4bb623dd9fa6a3081c4416`;
- activation operator source commit: `a0daa87cbd6a34a1f4a49648798c45587cdf43de`;
- activation operator SHA256: `0384eb3b544883a1e979c7711cde351cd5597c28819054d07406e2bf770f959a`;
- activation operator Git blob: `be0473e43d37271096a0461df2780f9e62effb67`;
- `/usr/local/sbin/rpi5-update` SHA256: `3a7898c1f06f7bd5b4136dd6875edf5c7178dad9c8ea4099ef065ce9b1c20882`, owner/mode `root:root 0750`;
- `rpi5-update-compose-policy.sh` SHA256: `5ee19cbf09f5fa06853d1c121fea8216e1ae245aaa17af81e2affe6ab3aaae4f`, owner/mode `root:root 0644`;
- `rpi5-update-docker-evidence.sh` SHA256: `f133adb38eb5499e1e582532f142f1b892ba99755262ce0612d8b21e96716456`, owner/mode `root:root 0644`;
- exact release-commit `validate` push CI run `34023964012`: SUCCESS;
- activation-operator merged-main `validate` push CI run `34025290660`: SUCCESS.

## Activation evidence

The authorized root `--apply` completed with:

- `V28_ACTIVATION_PREFLIGHT=PASS`;
- predecessor updater SHA256 `f9c83acdd72131d6b696900972aa11d24978645b931846ff4ea8e6a8ed80bdc2`;
- `V28_HOST_ACTIVATION=PASS`;
- `V28_NON_MUTATING_APT_CHECK=PASS`;
- identical APT-list fingerprints before/after the staged check: `37c0274e1f63e4680336e4a7b96279b74ddde31b4e859e77f1a08de49c860d04`;
- `MAINTENANCE_BOUNDARIES_UNCHANGED=PASS`;
- root-only evidence directory `/root/rpi5-v28-activation-20260906-115620.8f7xwf` preserved and present.

No APT mutation, Docker mutation, systemd mutation, cleanup or reboot was part of the V28 activation itself.

## Post-reboot notifier incident and live fix

On 2026-09-07 the normal boot-time `rpi5-post-reboot.service` completed successfully (`Result=success`, `ExecMainStatus=0`, readiness PASS on attempt 3/30), but its Telegram notification incorrectly reported a maintenance failure with `unknown` monitor metadata. Read-only journal evidence showed systemd skipped monitor-result propagation because the same notifier instance had been configured for both `OnSuccess=` and `OnFailure=`.

PR **#7** fixed the ambiguity by using distinct success/failure notifier instances and adding an instance-name fallback in `rpi5-maintenance-notify`. PR #7 merged to `main` as `115a8162ed650e7b153124b49be30f499d4af47f`; exact PR head `88b143b3faef6b8ebd5f4e6c668b4b9116b1720a` passed `validate` run `34147197655`.

A separately authorized LIVE deployment on 2026-09-07 installed only the reviewed notifier fix plus `systemctl daemon-reload`; no service restart, manual maintenance run, cleanup or reboot was performed. Verified live identities after deployment:

- `/etc/systemd/system/rpi5-post-reboot.service` SHA256 `467e1c0b5825e62bbd9eee7fce1df4d4f7b33ca88bd4e90b9be13cf7135f606c`, owner/mode `root:root 0644`;
- `/usr/local/sbin/rpi5-maintenance-notify` SHA256 `46241a4c73245379de53844fc148d38bab558337845f41911012a04ffeb58703`, owner/mode `root:root 0755`;
- effective `OnSuccess=rpi5-maintenance-notify@success-rpi5-post-reboot.service`;
- effective `OnFailure=rpi5-maintenance-notify@failure-rpi5-post-reboot.service`.

The corrected post-reboot notification path still has not been manually triggered merely to manufacture evidence; manual execution remains outside the stability-proof lane without separate LIVE authorization.

## 2026-09-13 scheduled-run outcome

The first normal scheduled stability-proof run after cutover, run id `20260913_022000`, **did not establish stable-production proof**.

Fresh read-only evidence showed:

- `rpi5-update.service`: `Result=exit-code`, `ExecMainStatus=1`;
- cleanup: PASS, 14-day retention, reported 164 MB delta;
- APT: 9 packages upgraded successfully;
- Docker main pull: succeeded with `mutation=changed`;
- Docker main target selection: failed closed with `rc=3`, `reason=config-drift`, `service=homeassistant`;
- Docker CV: skipped because main failed;
- main and CV final-health checks: healthy;
- local/public endpoint gates: PASS;
- automatic reboot: blocked because the run had an error;
- `/run/reboot-required`: absent after the run;
- `rpi5-update.timer`: active/waiting for the next normal run.

The failure was an intended V28 safety behavior, not evidence to weaken the guard: a registry image had changed while the running Home Assistant container's `com.docker.compose.config-hash` differed from the current rendered Compose hash. Issue **#32** captured the incident and remediation evidence.

## Home Assistant reconciliation

On 2026-09-13 the owner manually executed the narrowly scoped reconciliation previously documented in #32:

```sh
cd /home/andris/docker
docker compose up -d --pull never --no-build --wait --wait-timeout 240 --no-deps homeassistant
```

The command completed successfully. No additional LIVE mutation was initiated by ChatGPT after that owner-executed command.

Fresh read-only verification after reconciliation:

- running Home Assistant image: `sha256:a1bc133af84ee6505fe2c266d9805b7c75b780dfdc188edfee3b11e8f3cd8efe`;
- local `ghcr.io/home-assistant/home-assistant:stable`: same exact image ID;
- Home Assistant version label: `2026.9.2`;
- running Compose config hash: `997f6bd4a88112bb607ef18015c64c7c68b64cf862331ebf75e8039aa66e2b60`;
- current desired `docker compose config --hash homeassistant`: same exact hash;
- Home Assistant local endpoint: HTTP 200;
- Home Assistant public endpoint: HTTP 302, matching the established redirect/auth expectation;
- main Compose: all services running; healthcheck-equipped services healthy;
- CV Compose: `cv` running, `cvbot` healthy;
- `/run/reboot-required`: absent;
- installed V28 Compose-selection policy: PASS; the Home Assistant `config-drift` blocker is gone.

The policy currently sees newer pulled registry images pending for `autoheal`, `grafana`, `grafana-renderer`, and `uptime-kuma`. They were intentionally left untouched after the narrow Home Assistant reconciliation and remain for the normal scheduled maintenance path.

Issue **#32** is closed as completed after the verified Home Assistant reconciliation.

## Current lane — post-cutover stability proof

The immediate lane remains **read-only post-cutover stability proof**. Do not start P2/P3 behavior changes or remove duplicated maintenance source from `RPi5_main` inside this lane.

The 2026-09-13 run exercised the V28 failure-domain evidence and fail-closed behavior successfully, but the run itself failed; therefore it cannot be used as stable-production proof.

Current gate:

1. Preserve the exact production identity above as the cutover baseline, including the separately reviewed PR #7 notifier hotfix identity.
2. Do not manually run full maintenance or `rpi5-post-reboot.service` merely to manufacture stability evidence; either manual run requires separate LIVE authorization.
3. The next normal `rpi5-update.timer` run is scheduled for **2026-09-20 02:20 CEST**. After that run, collect minimum read-only evidence for:
   - updater run result and exit status;
   - V28 run-scoped Docker evidence presence/shape when Docker phases execute;
   - main/CV Compose runtime health;
   - relevant local/public health gates if the run touched them;
   - timer/service state;
   - reboot-required/result state;
   - any failure-domain behavior actually exercised;
   - if a reboot/post-reboot path actually occurs, the corrected notifier result and absence of the prior trigger-source ambiguity.
4. If that scheduled run is healthy, record stable-production proof in canonical continuity.
5. Only after stable operation may Phase 9 removal of duplicated maintenance source from `RPi5_main` be considered.

P2 transaction classification/continuation and P3 doctor/backoff remain separate later behavior milestones and require their own scoped work items.
