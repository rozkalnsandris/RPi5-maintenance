# Current handoff

## Current state

`rpi5-maintenance` is an independent source repository. The `0.1.0` extraction/parity milestone preserved the reviewed V27 updater lineage from `rozkalnsandris/RPi5_main`; production activation of the independent repository has not been performed.

The next source successor is **V28 — Docker evidence hardening**. V28 is derived from the extracted V27 updater and changes evidence/diagnostic behavior, not Docker remediation policy.

## P1 evidence contract

P1 now has an executable sanitized regression for the 2026-09-06 incident and source support for:

- run-scoped root-only Docker evidence;
- exact Docker command output and exit-code capture;
- structured `phases.jsonl` records;
- explicit pull / target-selection / reconcile / readiness / rollback phase evidence;
- explicit target-selection reason + affected service;
- immutable image/container state snapshots;
- independent final Compose health evidence;
- actionable failure detail in the final Docker summary.

The preserved host evidence shows that the 2026-09-06 APT transaction upgraded Docker components and restarted Docker, `mosquitto` remained stopped through the main Docker phase, candidate pulls completed, and V27 then emitted only a generic main failure. A stopped registry-backed service deterministically reproduces a V27 post-pull target-selection `rc=2` path. Because V27 did not retain a structured post-pull record, that reconstruction is evidence-backed but is not presented as proof of the exact historical return statement.

## Current gate

1. Prove V28 with `make validate` and exact-head CI.
2. Review the P1 diff and failure evidence contract; do not add automatic remediation in this gate.
3. Merge requires explicit owner authorization.
4. After merge, prepare immutable release/shadow-verification evidence before any production activation.
5. Production install/cutover remains a separate explicit LIVE authorization bound to an exact reviewed release/commit.

## Production boundary

No P1 source work authorizes package changes, Docker mutation, systemd changes, maintenance execution, deployment or reboot on the RPi5. Read-only host evidence may be gathered as needed. P2 transaction classification/continuation policy and P3 doctor/backoff remain later work.
