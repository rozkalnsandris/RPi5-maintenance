# Observability and evidence

The most important lesson from the 2026-09-06 incident is that a Docker failure without the concrete stderr is not diagnosable enough.

## Per-run evidence

Recommended logical layout:

```text
/var/log/rpi5-maintenance/<run-id>/
  summary.json
  phases.jsonl
  apt.log
  docker-main-pull.log
  docker-main-up.log
  docker-main-state-before.json
  docker-main-state-after.json
  docker-main-health.json
  docker-cv-*.log/json
  global-health.json
  doctor-actions.jsonl
```

This path is a design target; production paths are not changed until authorized.

## Each mutating command records

- run ID, stack and phase;
- exact program/operation identity (with secrets redacted);
- start/end time and duration;
- exit code/signal/timeout;
- stdout and stderr or a lossless sanitized equivalent;
- state before and after;
- whether a mutation actually occurred;
- health after the command;
- retry/remediation attempt number.

## Reporting

Telegram/operator summaries should distinguish:

```text
Docker main: UPDATE FAILED / SYSTEM HEALTHY
reason: <specific sanitized error>
mutation: none | changed | rolled back | unknown
final health: healthy | unhealthy | unknown
evidence: <run-id/path>
```

A red `X` without failure phase/reason/mutation status is insufficient.
