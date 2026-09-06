# Roadmap

## P0 — extraction and parity

- create repository and import baseline source;
- independent CI for existing maintenance tests;
- source provenance and release skeleton;
- no behavior changes.

## P1 — evidence first

- lossless sanitized stdout/stderr capture;
- run IDs and structured phase records;
- immutable before/after image/container identity;
- actionable Telegram summary.

## P2 — transaction model

- `compose config -q` preflight;
- configurable `up -d --wait` policy;
- explicit change detection;
- per-stack failure-domain gates;
- `SUCCESS/RECOVERED/DEGRADED/CRITICAL`.

## P3 — resilience

- reconnect/backoff for Mosquitto-dependent services;
- systemd restart-rate/backoff hardening;
- bounded doctor playbooks;
- deterministic rollback prerequisites.

## P4 — release/cutover

- immutable release artifact/provenance;
- shadow verification;
- separately authorized RPi5 cutover;
- rollback drill;
- remove duplicated maintenance source from `RPi5_main` only after stable production proof.
