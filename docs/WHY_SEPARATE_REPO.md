# Why a separate repository

## Problem

The maintenance subsystem has outgrown the role of a few host helper scripts. It has an updater, policy libraries, health checks, locks, systemd integration, Telegram reporting, activation/cutover transactions, provenance enforcement and a large test surface. Keeping it embedded in the host monorepo makes its ownership, release cadence and trust boundary harder to reason about.

## Decision

Maintain it as `rozkalnsandris/rpi5-maintenance`.

## Benefits

1. **Independent release unit.** Production can pin `rpi5-maintenance` vX.Y.Z without pinning the whole host repository.
2. **Independent CI.** Maintenance regression tests are not diluted by unrelated application checks.
3. **Explicit trust boundary.** The repository documents exactly which host mutations the maintenance engine may perform and under which authorization.
4. **Cleaner incident history.** Operational failures and regressions live with the software that caused or classified them.
5. **Safer evolution.** Verifier and doctor logic can mature without coupling unrelated RPi5 application source.
6. **Reusable architecture.** The design becomes a coherent maintenance product rather than host-specific glue.

## Costs

- one more repository and release stream;
- cross-repository dependency management;
- migration/provenance work;
- need to avoid configuration duplication between `RPi5_main` and this repository.

These costs are managed with pinned releases, a narrow installation contract and explicit ownership: `RPi5_main` describes the host/app environment; `rpi5-maintenance` owns maintenance orchestration.
