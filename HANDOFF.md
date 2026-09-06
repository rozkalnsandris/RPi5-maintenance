# Current handoff

## Current state

`rpi5-maintenance` is the independent maintenance source repository. P1/V28 Docker evidence hardening is merged on `main`. Production still runs the previously installed maintenance implementation; the independent repository has not been activated on the RPi5.

V28 corresponds to the planned `0.2.0` evidence/error-capture milestone. Runtime behavior changes from P1 are complete; the current lane is **immutable release metadata + read-only shadow-verification tooling**.

## Current lane

Prepare the source-level release gate without publishing a release or mutating production:

- deterministic release manifest from an exact Git ref;
- exact updater/provenance identity validation;
- explicit `production_activation_authorized=false` metadata;
- read-only host shadow verifier for Docker daemon, main/CV Compose completeness/runtime health, systemd state and reboot-required state;
- CI tests enforcing that the shadow verifier contains no mutation path.

## Current read-only shadow evidence

The 2026-09-06 post-P1 shadow preflight from the source checkout showed:

- V28 candidate provenance matches tracked source;
- Docker daemon available;
- main Compose: all expected services present, no bad containers;
- CV Compose: all expected services present, no bad containers;
- `rpi5-update.timer` active;
- `/run/reboot-required` absent;
- historical `rpi5-update.service` remains in sticky `failed` state from the prior maintenance incident;
- installed updater SHA was not readable with the non-root shadow execution and must be captured during the later authorized/exact release preflight if required.

Do not clear the failed unit merely to make shadow output green; current runtime health and historical run state are separate evidence.

## Current gate

1. Prove release/shadow tooling with `make validate` and exact-head CI.
2. Review that the shadow verifier is read-only and release manifest is exact-ref/provenance bound.
3. Merge requires explicit owner authorization.
4. After merge, generate manifest from the exact merged commit and request explicit owner authorization before creating the immutable `0.2.0` tag/GitHub release.
5. Publishing the release does not authorize production installation.
6. Production install/cutover requires a separate explicit LIVE authorization bound to the exact reviewed release/commit.

P2 transaction classification/continuation and P3 doctor/backoff remain later work; do not mix them into this release gate.
