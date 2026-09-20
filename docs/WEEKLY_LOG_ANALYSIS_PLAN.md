# Weekly log analysis and Hermes integrity plan

Tracking: #37, #38, #39, #40, #41

## Status and ownership

This document defines the planned P3 observability workstream for `RPi5-maintenance`.

The current repository continuation remains Phase 9 issue #24. This plan is intentionally queued as a separate workstream and does not change `HANDOFF.md` or make #37 the active lane.

Existing ownership boundaries remain unchanged:

- #12 owns per-service health-gate coverage;
- #13 owns container/resource budgets and host headroom policy;
- #15 owns Docker stack ownership/freshness/convergence policy;
- #23 owns failed-unit lifecycle and any `journald` retention/configuration mutation;
- #24 owns the current duplicated-source cleanup lane.

## Problem statement

A weekly report is only trustworthy when the evidence window itself is trustworthy. The 2026-09-20 run exposed several blind spots that are not equivalent to a simple failed process:

- a reboot can remove earlier volatile journal history;
- a service can be `active` while functionally blocked on authorization/pairing;
- Hermes can update code while leaving local customization restoration unresolved;
- Hermes can fall back to stale web assets after a failed UI build;
- configuration migration/checks can fail after the code update reports completion;
- a user-space Node/V8 heap OOM can terminate a build without a kernel OOM event;
- timer/one-shot failures can repeat frequently and flood logs while remaining fail-closed;
- Hermes cron execution, delivery and scheduling health are separate states;
- Docker reclaimable storage is useful trend evidence but is not cleanup authority.

The weekly pipeline therefore needs durable bounded snapshots, deterministic classification and explicit evidence-coverage semantics before any LLM narrative layer.

## Target architecture

### Stage A — daily deterministic collector (#38)

Run a source-controlled read-only collector once per day. Produce one small normalized snapshot containing:

- schema version, timestamp, boot ID, uptime and reboot-required state;
- root filesystem/inode use;
- RAM/swap/pressure summary;
- failed system and user units plus bounded status metadata;
- critical timer last/next result metadata;
- Docker container/health summary and `docker system df` counters;
- maintenance evidence/source identity needed to correlate the snapshot;
- evidence-coverage flags for optional/unavailable sources.

Snapshots must be atomic, secret-safe and retained for at least the weekly analysis horizon plus a bounded safety margin. Missing snapshots remain explicit coverage gaps.

The collector must remain useful even while `journald` is volatile. Any future persistent-journal configuration change stays in #23.

### Stage B — Hermes post-update integrity verifier (#39)

Run read-only integrity checks that separate four dimensions:

1. `process_active`;
2. `configuration_valid`;
3. `artifact_current`;
4. `functional_ready`.

Checks should cover Hermes version/checkout identity, dirty/unmerged state, autostash/update residue, `hermes doctor`, `hermes config check`, supported read-only update check/plan commands, recent update-log result classification, web UI build identity/stale-dist fallback, gateway state and bounded connected-platform/function signals.

No verifier path may apply a stash, resolve conflicts, migrate config, rebuild assets, restart services, refresh credentials, update Hermes, roll back, or clean files.

### Stage C — deterministic anomaly classifier (#40)

Classify and deduplicate:

- current persistent systemd failures;
- user-service failures;
- stale historical failed state;
- recovered transient boot/update failures;
- repeated one-shot/timer/restart loops;
- kernel OOM;
- cgroup/systemd OOM;
- user-space fatal heap OOM such as Node/V8 exit 134/SIGABRT;
- Hermes cron failed, unknown, late/catch-up, delivery-failed and parked-next-run states.

Every finding receives a stable root-cause key so repeated identical events collapse into a count and time range rather than flooding the report.

### Stage D — weekly synthesis (#41)

Generate one concise weekly report from bounded normalized evidence.

Top-level severities are limited to:

- `ACTION_REQUIRED` — current/persistent failure, integrity mismatch, progressive risk or a coverage gap that invalidates a required conclusion;
- `WATCH` — bounded degradation/drift/trend that is not currently service-breaking;
- `EXPECTED_SELF_HEALED` — transient noise with fresh success/recovery evidence.

Each finding includes:

- stable root-cause key;
- first/last seen;
- recurrence count;
- current state;
- affected scope;
- evidence source and coverage;
- owning issue/playbook when known;
- a non-executing next-step recommendation.

Trend inputs include disk/inodes, RAM/swap/pressure, Docker images/build-cache/volumes reclaimable usage, failed/recovered service counts, loop counts, cron failed/unknown/delivery-failed counts and Hermes integrity/version drift.

## Scheduling model

Prefer two stages in Hermes:

1. daily no-agent/script-only collection for deterministic low-cost evidence;
2. weekly synthesis over the bounded seven-day snapshot set.

Hermes cron health is part of the monitored system. `hermes cron doctor`, the execution ledger and delivery state must be checked so a missing or failed analyzer run cannot fail silently.

Cron job definitions/install instructions should be source-controlled. Actual installation or modification of Hermes jobs on the production RPi5 remains a separate LIVE mutation.

## Data and secret policy

Do not store or report:

- API tokens, bearer credentials, cookies or passwords;
- environment-secret values;
- private authorization/device codes;
- unbounded raw logs;
- sensitive query-string values when they may contain credentials.

Prefer normalized counters, statuses, timestamps, identities and bounded excerpts. Evidence must remain sufficient to explain classifications without becoming a second general-purpose log archive.

## Implementation order

1. #38 — define snapshot schema, collector and fixtures/tests.
2. #39 — define Hermes integrity schema/verifier and fixtures/tests.
3. #40 — implement classifier/root-cause keys over synthetic and collected evidence.
4. #41 — implement trends, deduplication, report schema and operator scheduling documentation.
5. Review source/tests to Ready.
6. Merge only with explicit owner authorization.
7. Perform fresh production preflight and prepare exact installation/scheduling plan.
8. Install/schedule only with separate explicit LIVE authorization.
9. Verify first daily snapshots and first natural weekly report; do not manufacture a reboot or maintenance event merely to create evidence.

## Test strategy

Repository tests should cover at least:

- clean week;
- reboot boundary with volatile journal;
- one missing daily snapshot;
- Docker unavailable/read failure;
- stale systemd failed state versus current repeated failure;
- user service `active` but functional authorization pending;
- fail-closed timer loop;
- kernel OOM versus cgroup OOM versus Node/V8 heap OOM;
- Hermes clean update;
- Hermes autostash conflict;
- stale UI asset fallback;
- config-check/migration-required state;
- cron failed execution;
- cron successful execution with delivery failure;
- cron abandoned/unknown attempt after restart;
- trend increase/decrease and root-cause deduplication;
- secret-shaped fixture values proving redaction/exclusion.

## Upstream references

- Hermes cron/no-agent, execution history and `hermes cron doctor`: https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/cron.md
- Hermes updating/config checks: https://github.com/NousResearch/hermes-agent/blob/main/website/docs/getting-started/updating.md
- Node diagnostic reports and fatal-OOM reporting: https://nodejs.org/api/report.html
- Docker disk usage: https://docs.docker.com/reference/cli/docker/system/df/

## Safety boundary

This plan does not authorize runtime installation, Hermes cron mutation, `journald` changes, service restart/enable/disable, configuration migration, credential refresh, Docker prune, package mutation, cleanup, reboot, rollback or any other production mutation. Source-level implementation may proceed through normal FAST-LANE review; MERGE and LIVE remain separate owner gates.
