# Current handoff

## Current state

`rpi5-maintenance` is the independent maintenance source repository. P1/V28 Docker evidence hardening and the release/shadow gate are merged on `main`. GitHub release/tag **`0.2.0`** is published and resolves to exact commit `7a5685908e06cc35aa4bb623dd9fa6a3081c4416` (tree `3e6ef8913b64a48d5eb3ba90f13c74c5a7083d67`). Production has **not** been activated from this release.

The current lane is **V28 / `0.2.0` production-activation contract**. This lane prepares a reviewed, exact-release-bound operator; it does not itself authorize or perform production mutation.

## Exact release identity

- tag/version: `0.2.0`;
- release commit: `7a5685908e06cc35aa4bb623dd9fa6a3081c4416`;
- updater SHA256: `3a7898c1f06f7bd5b4136dd6875edf5c7178dad9c8ea4099ef065ce9b1c20882`;
- updater Git blob: `1b647c26ba91d75aad29cf50ddc8d33a21c5e9c2`;
- V28 Compose-policy SHA256: `5ee19cbf09f5fa06853d1c121fea8216e1ae245aaa17af81e2affe6ab3aaae4f`;
- V28 Docker-evidence helper SHA256: `f133adb38eb5499e1e582532f142f1b892ba99755262ce0612d8b21e96716456`;
- exact release-commit `validate` push CI run `34023964012`: SUCCESS;
- release metadata records `production_activation_authorized=false`.

## Current read-only production evidence

Minimum activation-scope evidence from the live RPi5:

- `/usr/local/sbin/rpi5-update`: `root:root`, mode `0750`, size `46805`; exact SHA is not readable to the non-root remote session and must be verified by the root activation preflight before any write;
- all V28 runtime helpers already match release `0.2.0` except the intended activation delta:
  - live `rpi5-update-compose-policy.sh` SHA256 `bc11a4f487efd791e23dc48f325e1aa396da14b67fc6e7429e300545ce954516`, which matches the reviewed pre-P1/V27 repository source;
  - live `rpi5-update-docker-evidence.sh` is absent, as expected for the V27 predecessor;
- `rpi5-update.timer`: active;
- `rpi5-monitor.timer`: active;
- `docker.service`: active;
- `rpi5-update.service`: sticky `failed` from the 2026-09-06 incident and must not be cleared merely for cosmetic state;
- no active matching maintenance locks were visible in `lslocks`; lock files exist and are root-owned;
- `/run/reboot-required`: absent.

The existing GitHub App read-token broker did not return a token for the new repository. Because this repository/release is public, the V28 activation operator deliberately avoids a new credential/configuration dependency and verifies remote `main`/tag with read-only `git ls-remote` plus the public GitHub Release/Actions APIs.

## Activation operator contract

`ops/bin/rpi5-maintenance-v28-activate` is version-specific and must remain bound to release `0.2.0`.

- `--preflight` performs release/source/live-state/CI/lock checks and must not write production state;
- `--apply` is the only mutation mode;
- preflight accepts only the exact reviewed V27 updater predecessor or an already-current exact V28 installation;
- unchanged runtime helpers must byte-match release `0.2.0`;
- planned mutation scope is only:
  1. `rpi5-update-compose-policy.sh` -> V28 release bytes;
  2. add `rpi5-update-docker-evidence.sh` -> V28 release bytes;
  3. `/usr/local/sbin/rpi5-update` -> V28 release bytes;
- before-state is preserved under a root-only activation evidence directory;
- staged V28 `--check` must preserve APT-list fingerprints before updater replacement;
- timer state, unrelated helper bytes and backup bytes must remain unchanged;
- no systemd start/stop/restart/reset-failed/daemon-reload, Docker mutation, APT mutation, cleanup or reboot is part of activation;
- after the first write, any failure is fail-closed: preserve evidence and STOP with no automatic retry, rollback, cleanup, reboot or alternate mutation.

## Current gate

1. Prove the V28 activation operator and transaction contract with `make validate` and exact-head CI.
2. Review exact release/source bindings and planned live delta.
3. Merge requires explicit owner authorization.
4. After merge, perform a fresh **root read-only `--preflight`** against exact current `main` + release `0.2.0`; this does not consume LIVE authorization.
5. Only after successful preflight may an explicit LIVE authorization bind the exact operator source identity + release `0.2.0` and permit `--apply`.
6. Reboot is not part of this activation scope unless separately authorized.

P2 transaction classification/continuation and P3 doctor/backoff remain later work; do not mix them into this activation gate.
