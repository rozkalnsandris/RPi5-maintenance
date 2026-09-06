# Failure model

The engine separates **command failure**, **mutation outcome**, and **system health**.

## SUCCESS

All required phases succeeded, final health is green, and no recovery was required.

## RECOVERED

A phase failed or a transient outage occurred, but bounded recovery or natural convergence restored the intended state and all required final verification passed. The report must still expose the original error.

## DEGRADED

A maintenance goal was not completed, but the system remains safely on a known/verified state. Examples: an image pull failed before mutation while the old containers remain healthy; an optional update check is unavailable; a non-critical stack update is skipped after a policy gate.

## CRITICAL

The system is not in a verified safe state after mutation, shared infrastructure is unhealthy, package state is inconsistent, rollback/recovery failed, or a required critical service remains down.

## Invariants

- A non-zero command is evidence, not the entire classification.
- A green health check cannot erase an unknown partial mutation; mutation state must also be known.
- A zero command exit is not sufficient for `SUCCESS`; required health verification must pass.
- `RECOVERED` remains visible so recurring transient failures are not hidden.
- Reboot policy consumes the final classification plus actual reboot requirement.
