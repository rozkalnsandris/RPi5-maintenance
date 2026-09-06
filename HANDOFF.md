# Current handoff

## Current state

`rpi5-maintenance` is an independent source repository at the **0.1.0 extraction/parity milestone**.

The reviewed maintenance source was extracted from:

- source repository: `rozkalnsandris/RPi5_main`
- source branch: `main`
- source commit: `e949f7835898fc207aa137cb26ffb6dfc701a497`
- source tree: `bde4469517650594fbab6838f60af4c9ab472830`

The extraction preserves the existing maintenance behavior. The canonical updater remains the reviewed V27 source with Git blob `744192e2acb7105d90a93e1cf3426433c09cb26d` and executable mode `100755`.

The extraction/parity CI gate passed before the source import was published.

## Production state

**No production cutover has been performed.**

The production RPi5 continues to use its existing installed maintenance implementation. Source extraction, merge and release preparation do not authorize host mutation.

## Current work item

**P1 — evidence hardening for the 2026-09-06 Docker maintenance failure.**

Primary goal: a future Docker update failure must preserve enough structured evidence to identify the exact failing command/phase and distinguish:

- pull failure;
- Compose reconcile failure;
- timeout/readiness failure;
- mutation/no-mutation/unknown state;
- final service health.

The first P1 changes should focus on evidence capture and regression tests, not on broad doctor automation or production policy changes.

## Next source gate

1. Turn the 2026-09-06 scenario into executable regression fixtures.
2. Add lossless sanitized Docker command evidence and structured phase state.
3. Keep existing behavior unchanged except where the evidence contract requires it.
4. Run `make validate` and require CI PASS.
5. Review the resulting failure classification evidence before implementing automatic remediation changes.

## Owner gates

- merge/release operations follow repository governance;
- production activation requires separate explicit authorization bound to an exact reviewed release/commit;
- production configuration, systemd, Docker, APT, reboot and secret changes are not authorized by ordinary source work.
