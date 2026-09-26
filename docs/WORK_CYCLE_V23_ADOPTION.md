# FAST-LANE v2.3 work-cycle adoption

Tracking: `rozkalnsandris/ops-workflows#124` (roadmap `#119`).

Canonical shared revision: `274d58f2d9d3cb86feded2751b8f9009a4501f6b`.

## Classification

- Bootstrap manifest: adopted at `.github/agent-bootstrap.json`.
- Deployment profile: `custom` because repository-local maintenance/LIVE rules remain stricter than a generic deploy profile.
- START: existing `AGENTS.md` + `HANDOFF.md` FAST-LANE route remains authoritative and supplies minimum-sufficient bootstrap / compact terminal behavior.
- WRITE_PREFLIGHT_COMPACT: adopted through the existing `.github/github-api-access-v1.json` adapter; no duplicate mutation framework is added.
- AUTO-RUN FULL: `NOT_APPLICABLE`. This repository has no local AUTO-RUN FULL controller/schema, so rollout does not create one.

## Local rules preserved

This adoption does not change the repository's maintenance trust boundary. In particular:

- MERGE remains an explicit owner gate.
- Merge never grants LIVE authority.
- Production/RPi5 mutation requires separate exact LIVE authorization.
- Docker, systemd, APT, cleanup, reboot, permissions, credentials, networking and storage rules are unchanged.
- Existing reviewed scheduled maintenance policy remains the only exception for its already-defined installed mutation scope; this rollout does not alter that policy or install anything.
- Mutation ambiguity remains fail-closed with read-only reconciliation only.
- No Queue vNext activation, retry, rollback, cleanup, host mutation or deployment is introduced.

## Acceptance evidence

Acceptance requires one focused PR from an exact `main`, exact-head CI/review evidence, explicit merge authorization under local rules, and exact-main reconciliation after merge. Mutable SHA/PR/CI values are evidence only and must never be treated as durable bootstrap truth.
