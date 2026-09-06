# Repository operating rules

## Canonical state

GitHub is the canonical source of truth for repository source, policy, tests, reviews, checks, release metadata and continuity. Chat history and Memory are not canonical state.

The live RPi5 host is canonical only for actual runtime state: installed files and packages, Docker containers/images/networks/volumes, systemd units/timers, processes, disk/RAM/load, endpoints, locks, logs, deployment identity and reboot-required state.

Repository source does not prove that the same state is deployed or active in production.

Never reuse old SHA, PR/CI state, runtime output, package/image version, reboot state or authorization as current evidence.

## START / SYNC / AUDIT-HANDOFF

Normal `START` is lightweight:

1. Read this file and only path-specific rules relevant to the current work.
2. Read `HANDOFF.md`.
3. Read current `main` SHA.
4. Select exactly one current work item/lane/gate from the handoff.
5. Read only that issue/PR state.
6. If a PR exists, inspect only its current exact-head required checks, reviews and unresolved threads.
7. Obtain live-host evidence only when the current work item requires it, and only the minimum read-only evidence needed.

Do not enumerate unrelated issues/PRs, historical CI, complete logs/comments/review history, repo-wide roadmap state or broad host inventory during normal START.

Additional evidence is demand-driven:

- failed check -> concrete failing job/step;
- blocking review -> concrete review/thread;
- Docker failure -> affected Compose project/service/phase;
- APT failure -> affected package/dpkg/APT state;
- systemd failure -> affected unit/timer;
- health failure -> affected service/endpoint;
- conflicting continuation -> expand retrieval only enough to resolve the conflict.

`SYNC` is an incremental refresh of current main, current work item, current PR/head/checks/reviews and only relevant live evidence. Re-read the handoff only when continuation may have changed or is unclear.

`AUDIT-HANDOFF` is the explicit heavy continuity/audit mode. Repo-wide inventory is reserved for that command or explicit audit requests.

## Work model / FAST-LANE v2.2

Bare START and `turpini` use FAST-LANE v2.2 unless a different mode is explicitly requested.

Safe source-level work may proceed through:

- GitHub reads;
- branch creation;
- source/docs/tests changes;
- maintenance/systemd/Compose configuration changes in the repository only;
- commit/push;
- Draft PR;
- CI polling and analysis;
- review/comment analysis;
- scope-preserving corrections;
- read-only host preflight;
- diff/head/mergeability checks;
- Ready for review.

Do not STOP for ordinary technical intermediate steps, CI polling, diff/head validation, read-only preflight or safe source correction.

MERGE always requires separate explicit owner authorization.

Merge authorization is never production authorization.

## Production trust boundary / LIVE gate

No repository workflow, agent or doctor may autonomously mutate the production RPi5.

Interactive live mutation requires separate explicit LIVE authorization. This includes, non-exhaustively:

- deploying maintenance scripts or configuration;
- writes under `/etc`, `/usr/local`, `/opt` or another live runtime/configuration path;
- `apt-get update`, package install/upgrade/remove;
- Docker pull/build/up/down/recreate/restart/prune;
- systemd start/stop/restart/enable/disable/daemon-reload;
- timer/cron changes;
- filesystem cleanup/delete;
- Hermes update;
- rclone ownership/update changes;
- permissions/ownership changes;
- secrets/tokens/credentials;
- networking/firewall/DNS changes;
- production storage/DB mutation;
- reboot, rollback or cutover.

Before any live mutation identify:

- exact host;
- exact reviewed source/release identity when relevant;
- exact current deployed/live state when relevant;
- exact mutation;
- affected services/resources;
- rollback semantics if part of the reviewed plan;
- whether reboot is included in authorization scope.

A one-time LIVE authorization is consumed when the first authorized mutation begins. Read-only preflight does not consume it.

If mutation has started and any tool error, timeout, uncertainty, unexpected state, source/head drift, live-state drift, lock conflict, health regression or authorization ambiguity appears: collect only necessary read-only evidence and STOP. Do not automatically retry, rollback, clean up, reboot or choose an alternate mutation path without new explicit authorization.

After three failed attempts at the same action, STOP and summarize the attempts and most likely failure layer.

## Read-only host preflight

Allowed read-only evidence includes:

- systemd unit/timer status and configuration;
- journal/log inspection;
- Docker `ps`, `inspect`, Compose config/status;
- disk/RAM/load;
- package state and simulation;
- filesystem metadata;
- endpoint GET/HEAD health checks;
- installed version inspection;
- lock inspection;
- `/run/reboot-required` state.

Read-only mode must not run mutating commands such as:

- `apt-get update` or any package mutation;
- Docker pull/build/up/down/restart/recreate;
- systemctl start/stop/restart/enable/disable/daemon-reload;
- filesystem writes/deletes/cleanup;
- live `git pull` deployment;
- permission/ownership changes;
- reboot.

## Extraction and parity

Until the extraction/parity phase is explicitly closed for an area, prefer **extract, don't rewrite**. Preserve source semantics, names and paths wherever practical. Behavioral refactors belong in later scoped PRs after parity is established.

## Maintenance safety invariants

### Cleanup

- Cleanup is allowlist-based only.
- Default retention is 14 days unless repository policy intentionally changes it.
- Never use broad filesystem cleanup equivalent to `find / -mtime ...`.
- Never automatically delete Docker volumes, persistent application data, databases, secrets, configuration or backups outside explicit cleanup scope.
- `docker system prune`, volume prune, `--remove-orphans`, destructive cache cleanup and equivalent broad cleanup are not default maintenance actions.

### APT

- Dry-run/check paths must remain non-mutating.
- Prefer conservative upgrade semantics equivalent to `apt-get upgrade --with-new-pkgs --no-remove` unless a reviewed policy intentionally changes this.
- Package removals and `autoremove` are not automatic maintenance steps.
- Do not ignore package holds.
- Unexpected package-removal proposals are a STOP condition before mutation.
- Preserve package-manager ownership. APT-managed software must not silently switch to an upstream/standalone installer.

### Docker

- Treat distinct Compose projects/scopes separately when topology requires it.
- Before mutation identify exact Compose project/files, service classification and expected running/stopped state.
- Distinguish registry-managed services from local-build/local-only services.
- Do not automatically pull/rebuild/recreate local-build services merely because they exist in a Compose project.
- Intentionally stopped services remain stopped unless explicitly in scope.
- Treat `docker compose pull` and `docker compose up` as separate mutation phases.
- Preserve persistent volumes.
- After mutation verify only the affected scope with repository-defined container, health, local endpoint and public endpoint gates.
- `running` alone is not sufficient application-health evidence.

### Hermes

- Hermes is a separate maintenance class.
- Upstream commit-behind count is informational, not authorization.
- If current policy marks Hermes as manual, generic automated maintenance must not update it.
- Interactive Hermes update requires LIVE authorization.

### Locking / concurrency

- Maintenance must respect repository-defined shared locking/concurrency with backup, deploy and other operations touching the same mutable resources.
- Interpret lock state according to actual lock semantics, not merely file existence.
- Do not bypass an active lock through an alternate mutation path without explicit authorization.

## Health and reboot

Health gates are service-specific and repository-defined. Evaluate only affected scope: relevant systemd units/logs, Docker state/health, local/public endpoints, disk/RAM/load, residual APT state and reboot-required state.

An HTTP status code is PASS only when it matches the endpoint's documented expectation.

Default reboot policy is `if-needed`.

Automatic reboot is allowed only when it is inside an already reviewed scheduled maintenance policy or explicit LIVE scope, all pre-reboot mutation phases completed without error, no conflicting operation exists and required pre-reboot gates pass.

Any maintenance mutation/update failure blocks automatic reboot. Collect minimum read-only evidence and fail closed.

Post-reboot verification must be fresh; pre-reboot health is not proof of post-reboot health.

## Scheduled automation

A previously reviewed and explicitly installed scheduled maintenance policy may execute its exact defined mutation scope without new ChatGPT authorization for every timer run.

Changing the scheduled policy, timer/unit, deployed maintenance script, mutation scope, cleanup class, automatic reboot behavior, package ownership or Docker/Hermes handling is a new live mutation and requires LIVE authorization.

A manual maintenance run is a live-host mutation and requires LIVE authorization.

## Evidence and doctor rules

Any mutating maintenance phase must record enough sanitized evidence to reconstruct what happened, including command identity, phase, exit code, duration, stdout/stderr as appropriate, before/after state and health results. Do not suppress the error stream needed for root-cause analysis.

The doctor is deterministic and playbook-driven. It may select only predeclared bounded remediation actions. It must never generate arbitrary shell from free-form AI reasoning.

## Secrets

Never commit credentials, tokens, private URLs, raw customer/user data or environment files. Tests must use fixtures or redacted synthetic values.

## GitHub write safety

Before GitHub write identify exact repository, target, current base/head, intended mutation and scope. Do not create placeholder/test issues, PRs, branches or commits merely to test tooling.

If branch/head drifts after preparation, refresh before writing.

## STOP report

At STOP report, when applicable, include:

- what is ready and what remains undone;
- exact current main SHA and branch/head SHA;
- current issue/PR;
- exact-head required checks;
- reviews/unresolved threads;
- relevant read-only host preflight state;
- affected APT/Docker/systemd/Hermes/health state;
- reboot-required state;
- whether mutation began and what changed;
- whether LIVE authorization was consumed;
- exact next owner authorization gate.
