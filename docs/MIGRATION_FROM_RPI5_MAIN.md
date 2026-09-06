# Migration from RPi5_main

## Non-goal

Repository extraction is not an opportunity to rewrite the updater.

## Phase 0 — bootstrap

- create `rozkalnsandris/rpi5-maintenance`;
- add governance, architecture and extraction manifest;
- bind the source baseline to `e949f7835898fc207aa137cb26ffb6dfc701a497`;
- no production mutation.

## Phase 1 — source extraction/parity

Copy the exact manifest paths from the baseline commit. Preserve executable bits and behavior. Adjust only repository-local references required to make tests run independently. Record every unavoidable path/dependency change.

Acceptance: extracted maintenance tests pass and a source/provenance comparison proves the intended files match the baseline except documented repository-boundary edits.

## Phase 2 — CI/release foundation

Add independent CI, release metadata, changelog/versioning, secret scanning and artifact/provenance verification. Still no production cutover.

## Phase 3 — evidence hardening

Capture Docker/apt stdout+stderr, command exit/timeout, before/after immutable state and per-run artifacts. Convert the 2026-09-06 incident into a regression test.

## Phase 4 — transaction/failure model

Implement `SUCCESS/RECOVERED/DEGRADED/CRITICAL`, per-stack transactions, failure-domain continuation gates, configurable `--wait` timeouts and deterministic rollback prerequisites.

## Phase 5 — dependency/backoff hardening

Prevent maintenance-triggered restart storms; add application reconnect/backoff where possible and systemd rate/backoff safety nets.

## Phase 6 — doctor hardening

Move from post-hoc free-form repair toward explicit playbooks, budgets, stop conditions and verify-again semantics.

## Phase 7 — production candidate

Prove shadow/check mode against real host behavior without changing production. Create an exact release candidate with install and rollback plans.

## Phase 8 — separately authorized cutover

Only an explicit LIVE/production authorization may change the RPi5 to consume the new repository/release. Preserve the old installed version as rollback target and verify all critical services.

## Phase 9 — cleanup

Only after stable operation: remove duplicated maintenance source from `RPi5_main`, replacing it with the pinned dependency/integration contract and links to this repository.
