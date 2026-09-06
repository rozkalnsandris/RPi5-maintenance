# Doctor remediation policy

The doctor is a deterministic policy executor, not an autonomous shell operator.

## Allowed classes of automatic action

- wait for bounded convergence;
- retry a health probe;
- restart one explicitly whitelisted service when its playbook permits it;
- perform a bounded Compose reconciliation for a known stack;
- restore a recorded known-good image/config identity when a rollback playbook is predeclared;
- re-run verification after any action.

Every playbook specifies prerequisites, maximum attempts, cooldown/backoff, success criteria, stop conditions and evidence to capture.

## Never automatic

- arbitrary shell generated from AI analysis;
- config edits;
- secret/permission/network changes;
- package downgrades outside a separately authorized recovery plan;
- deleting volumes or application data;
- `docker system prune`;
- `docker compose down -v`;
- changing systemd enablement/timers;
- rebooting merely to hide an unexplained failure.

AI/Hermes may analyze evidence and recommend a playbook, but execution must remain inside deterministic policy boundaries.
