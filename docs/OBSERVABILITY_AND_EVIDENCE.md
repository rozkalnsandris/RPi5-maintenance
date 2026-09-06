# Observability and evidence

The most important lesson from the 2026-09-06 incident is that a Docker failure without the concrete phase, command result and state evidence is not diagnosable enough.

## Per-run evidence

P1 source uses a run-scoped evidence directory:

```text
/var/log/rpi5-maintenance/<run-id>/
  phases.jsonl
  docker-main-pull.log
  docker-main-up.log
  docker-main-rollback.log
  docker-main-images-before.tsv
  docker-main-images-after-pull.tsv
  docker-main-state-before.tsv
  docker-main-state-after.tsv
  docker-main-state-final.tsv
  docker-cv-*.log/tsv
```

Production does not consume this source until a separately authorized release/cutover. Runtime evidence files are root-only and are never committed to GitHub.

## Structured Docker phase record

Each Docker phase record identifies:

- run ID, stack and phase;
- stable command/operation identity;
- start/end epoch;
- exact command exit code;
- outcome;
- mutation state (`none`, `changed`, `rolled-back` or `unknown` where applicable);
- sanitized reason and service tokens.

Command logs retain the command output needed for diagnosis. Operator/Telegram summaries expose only bounded structured tokens plus the evidence ID/path; credentials and environment data are never copied into repository fixtures.

## Required phase distinction

Docker evidence distinguishes at least:

- `pull`;
- `post-pull-snapshot`;
- `target-selection`;
- `reconcile`;
- `readiness`;
- `rollback`/`rollback-readiness`;
- `final-health`.

A command timeout/readiness timeout must not collapse into the same opaque result as an ordinary non-zero command. A green endpoint check also does not erase a known Docker transaction failure.

## Reporting

A failed Docker summary should provide actionable evidence such as:

```text
Docker main: FAILED
phase: target-selection
reason: missing-running-container
mutation: changed
final-health: unhealthy
Evidence: <run-id/path>
```

A red `X` without failure phase/reason/mutation/final-health evidence is insufficient.
