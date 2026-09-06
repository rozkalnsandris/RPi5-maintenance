# Rollback

Compose rollback is an application-level maintenance transaction because ordinary Docker Compose does not provide the Swarm `docker service rollback` mechanism.

## Before mutation

Record enough immutable state to reconstruct the previous deployment: service -> image ID/digest/reference, relevant Compose/config identity, container state and required runtime metadata without secrets.

## Rollback eligibility

Automatic rollback is allowed only when a predeclared playbook can restore a known-good state without destructive data operations. If previous identity is unknown or data migration compatibility is uncertain, stop and escalate rather than guessing.

## Verification

Rollback command success is not recovery. Run the full required health set afterward and record `RECOVERED` only when the old state is verified.
