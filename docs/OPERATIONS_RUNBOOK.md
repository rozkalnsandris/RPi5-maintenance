# Operations runbook

## When a maintenance run reports failure

1. Read the final classification and mutation status; do not infer outage from exit code alone.
2. Check the run evidence for the first failing phase and exact stderr/timeout.
3. Verify current critical service health independently.
4. Determine whether the system is unchanged, converged to new state, rolled back, or unknown.
5. If current state is healthy and known, preserve evidence before retrying anything.
6. If state is unknown or critical, stop automatic actions and escalate to an explicit recovery plan.
7. Never use broad cleanup/restart/down/prune operations merely to make the alert disappear.

## When a dependent service loops during planned maintenance

Capture dependency availability and restart timestamps. Prefer fixing the client's reconnect behavior; add bounded systemd rate/backoff protection as a safety net.

## When no reboot is required

Do not reboot merely because the maintenance run produced a warning/error. Reboot is a separate policy decision.
