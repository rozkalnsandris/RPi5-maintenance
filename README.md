# rpi5-maintenance

Safety-first maintenance control plane for a production Raspberry Pi 5 host.

This repository is being extracted from `rozkalnsandris/RPi5_main` so that host maintenance can be versioned, tested, released and audited as an independent software product instead of remaining an incidental subsystem inside the host monorepo.

## Mission

`rpi5-maintenance` owns **maintenance orchestration**, not the applications it maintains. It coordinates package updates, Docker Compose reconciliation, health verification, bounded recovery, reboot decisions, evidence capture and notifications while keeping production mutation explicit, reversible and observable.

The target lifecycle is:

```text
PRECHECK -> UPDATE -> VERIFY -> CLASSIFY -> BOUNDED DOCTOR -> VERIFY AGAIN -> FINAL STATE
```

The final state is one of `SUCCESS`, `RECOVERED`, `DEGRADED`, or `CRITICAL`.

## Why this repository exists

The maintenance subsystem in `RPi5_main` already contains a large updater, policy libraries, systemd units, activation/cutover tooling, provenance controls, health checks, Telegram reporting and a substantial test suite. That is an independent operational product with its own failure model and release lifecycle.

A separate repository gives it:

- an explicit trust boundary and ownership model;
- independent CI and regression tests;
- semantic releases and pinned production versions;
- a clean separation between source development and production activation;
- evidence-based incident handling;
- a place for the verifier/doctor layer without turning `RPi5_main` into an increasingly coupled control plane.

See [docs/WHY_SEPARATE_REPO.md](docs/WHY_SEPARATE_REPO.md).

## Extraction baseline

Initial extraction is intentionally **extract, don't rewrite**. The canonical source baseline is:

- source repository: `rozkalnsandris/RPi5_main`
- source branch: `main`
- source commit: `e949f7835898fc207aa137cb26ffb6dfc701a497`
- source tree: `bde4469517650594fbab6838f60af4c9ab472830`

The exact files intended for phase-1 extraction are listed in [`SOURCE_EXTRACTION_MANIFEST.txt`](SOURCE_EXTRACTION_MANIFEST.txt).

No production cutover is implied by extracting source. Production continues to use the existing installed maintenance implementation until a separately authorized, exact-release migration passes all gates.

## Core safety rules

1. GitHub source and release metadata are canonical for this project.
2. A merge is not a production deployment authorization.
3. Production must never track arbitrary `main`; it must use a pinned release/commit.
4. No secret is stored in this repository.
5. No automatic doctor action may invent shell commands or change configuration.
6. Destructive Docker operations are not generic recovery primitives.
7. Every mutating maintenance phase must leave enough evidence to explain what happened.
8. A failed update is not automatically a failed system; classification is based on mutation state plus verified service health.

## Documentation map

Start with:

- [Governance](docs/GOVERNANCE.md)
- [Project boundary](docs/PROJECT_BOUNDARY.md)
- [Development workflow](docs/DEVELOPMENT_WORKFLOW.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Maintenance lifecycle](docs/MAINTENANCE_LIFECYCLE.md)
- [Failure model](docs/FAILURE_MODEL.md)
- [Docker transaction](docs/DOCKER_UPDATE_TRANSACTION.md)
- [Health and verification](docs/HEALTH_AND_VERIFICATION.md)
- [Doctor policy](docs/DOCTOR_REMEDIATION_POLICY.md)
- [Observability/evidence](docs/OBSERVABILITY_AND_EVIDENCE.md)
- [Migration plan](docs/MIGRATION_FROM_RPI5_MAIN.md)
- [Test strategy](docs/TEST_STRATEGY.md)
- [2026-09-06 incident](docs/INCIDENT_2026-09-06.md)
- [Latviešu kopsavilkums](docs/README-LV.md)

## Repository maturity

The first release line should preserve the extracted behavior and prove parity. Architectural improvements are separate, reviewable follow-up changes. This prevents a repository split from silently becoming an updater rewrite.
