# Observability classifier

Issue #40 introduces a deterministic classifier for sanitized evidence that is
not covered by simple process-running or `systemctl --failed` checks.

## Safety boundary

`ops/lib/rpi5-observability-classifier.py` is a pure classifier. It does not
invoke systemd, journalctl, Docker, Hermes, networking, or remediation commands.
It accepts a JSON evidence snapshot through stdin or a file and emits only JSON.
Invalid or ambiguous input exits with code `2`.

Runtime evidence collection remains a separate read-only concern. Any collector
feeding this classifier must use fixed, timeout-bounded probes and must sanitize
logs before persistence. This classifier does not authorize deployment or any
runtime mutation.

## Input contract

Schema: `rpi5-observability-evidence.v1`.

The payload may contain:

- `services`: system and user-manager unit observations, restart/activation
  counts, failure timestamps, optional timer relationship, and sanitized
  readiness/auth evidence;
- `memory`: kernel OOM messages, cgroup `memory.events` counters/results, and
  explicit user-space fatal-memory evidence;
- `hermes`: `cron doctor` health, execution/delivery states, and `next_run_at`.

Thresholds are explicit in the payload so fixture results remain deterministic.

## Stable classifications

Service root-cause keys include:

- `service.authorization-required`
- `service.persistent-failure`
- `service.failure-loop`
- `service.inactive`
- `service.active-not-ready`
- `service.recovered-transient`
- `service.historical-stale-failure`
- `service.intentional-fail-closed`

Memory classes remain distinct:

- `memory.kernel-oom`
- `memory.cgroup-oom`
- `memory.user-space-v8-oom`
- `memory.user-space-runtime-oom`

Hermes execution failure, delivery failure, unknown attempts, missed/late/catch-up
dispatches, doctor failure, and a parked `next_run_at` use separate root-cause
keys.

Explicit pending-auth/pairing evidence takes precedence over an
`active/running` process state. Fresh readiness evidence is required before a
historical failure is downgraded to `recovered-transient`.

## Example

```bash
python3 ops/lib/rpi5-observability-classifier.py \
  tests/fixtures/observability/rdc-pending-auth.json
```

The fixtures use synthetic/redacted data only.
