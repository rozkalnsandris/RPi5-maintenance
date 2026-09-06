# Changelog

## Unreleased — V28 production activation gate

- Add a version-specific `0.2.0`/V28 activation operator with explicit read-only `--preflight` and mutation-only `--apply`.
- Bind activation to tag `0.2.0`, exact release commit, updater/helper SHA/blob identities, public release metadata and exact-release `validate` CI.
- Limit the planned production delta to the updater plus the reviewed Compose-policy and Docker-evidence helpers; preserve unrelated helper bytes, timer state, backup bytes and reboot state.
- Fail closed after the first write with preserved before-state and no automatic retry/rollback/cleanup/reboot.
- Production activation completed successfully on 2026-09-06 from reviewed operator source commit `a0daa87cbd6a34a1f4a49648798c45587cdf43de`.
- Post-activation verification confirmed exact V28 updater/helper hashes, unchanged timer boundaries, healthy main/CV Compose runtime and no reboot-required state.

## 0.2.0 — 2026-09-06

- Add deterministic exact-ref release manifest generation for the planned `0.2.0` milestone.
- Add a read-only RPi5 shadow verifier for candidate identity, Docker/Compose health, systemd state and reboot-required evidence.
- Keep release publication separate from production activation; no LIVE mutation is part of this gate.

### P1 Docker evidence hardening

- Added run-scoped root-only Docker evidence with structured phase records and exact command exit/output capture.
- Added immutable Compose container/image state snapshots before and after Docker work.
- Added explicit target-selection failure reasons, including stopped/missing running containers.
- Added the sanitized executable 2026-09-06 Docker-daemon-restart regression fixture.
- Corrected the incident record to distinguish observed facts from the reconstructed post-pull failure path.
- Preserved existing Docker update/rollback policy; no new automatic remediation or production activation is included.

## 0.1.0 — 2026-09-06

Extraction/parity milestone.

- Extracted the reviewed RPi5 maintenance control-plane source from `rozkalnsandris/RPi5_main` baseline `e949f7835898fc207aa137cb26ffb6dfc701a497`.
- Expanded the extraction boundary to include shared-lock backup ownership dependencies (`rpi5-backup` and `rpi5-backup-serialized`).
- Preserved the reviewed updater Git blob identity and executable mode.
- Imported the maintenance contracts, updater, helper libraries, systemd units, provenance manifest, activation/cutover operators and maintenance tests.
- Proved the imported source with the canonical maintenance parity suite before publishing it to `main`.
- Added independent repository governance, architecture, failure model, observability, migration, release, security and operations documentation.
- Added permanent read-only GitHub Actions validation and pinned `actions/checkout` to an immutable commit.
- Added CODEOWNERS, Dependabot configuration, issue forms and PR template.
- No production RPi5 activation or runtime mutation is part of this release state.

## 0.0.0-bootstrap — 2026-09-06

- Defined the independent `rpi5-maintenance` product boundary.
- Recorded extraction baseline from `RPi5_main`.
- Defined target update/verify/doctor architecture and failure model.
- Added the 2026-09-06 maintenance incident as a regression scenario.
- Added migration, release, security, observability and test plans.
- No production activation was part of the bootstrap version.
