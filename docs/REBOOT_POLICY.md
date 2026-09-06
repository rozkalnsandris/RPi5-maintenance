# Reboot policy

A reboot is a separate controlled action at the end of maintenance.

## Inputs

- whether the host actually requires a reboot;
- final maintenance classification;
- critical service health;
- whether a rollback/recovery is incomplete;
- lock/transaction state.

## Default decisions

- `SUCCESS` + reboot required + final health green: eligible.
- `RECOVERED` + reboot required: policy decision; require complete evidence and green final verification.
- `DEGRADED`: normally do not reboot automatically unless a future explicit policy proves the degraded condition cannot make reboot riskier.
- `CRITICAL`: never automatic reboot as a generic repair.
- no reboot requirement: do not reboot solely because maintenance ran.

Any change from the current production reboot policy must be a separately reviewed behavioral change.
