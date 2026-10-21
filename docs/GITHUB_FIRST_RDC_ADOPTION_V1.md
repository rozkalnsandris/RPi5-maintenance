# GitHub-first / bounded RDC fallback — RPi5-maintenance

Tracking: #90. Source adoption of accepted `rozkalnsandris/ops-workflows@4e89b75d7f496dfb43fd9c1eb10a995fad53fdd8`, not a LIVE release. Machine contract: `.github/github-first-rdc-v1.json`.

## Mandatory per-step routing

1. For repository files, GitHub source changes, branches, commits, issues, PRs, checks, reviews, and canonical continuation, use the connected GitHub operations if capable.
2. For runnable safe source tests, prefer GitHub-hosted CI when equivalent; local RPi5 execution is not a convenience fallback.
3. For a host-local step that **cannot** be completed equivalently through those GitHub capabilities (systemd status, Docker/process/package/lock state, or an exact host mutation), verify applicable existing owner read/LIVE scope and document the precise missing capability, CI limitation and minimum RDC step.
4. Then use only that minimum authorized RDC operation; return to GitHub for durable source/PR evidence. Never turn an RDC exception into host-source-of-truth for repository files.
5. GitHub denial, 403/429, timeout, tool failure, ambiguous write, absent owner scope or unproven host need => **STOP**, no alternate host GitHub write, auto-retry or rollback.

Exception evidence: `STEP`, `REPOSITORY_AND_TARGET`, `GITHUB_CAPABILITY_CHECKED`, `PRECISE_CAPABILITY_GAP`, `GITHUB_CI_NOT_EQUIVALENT_REASON`, `MINIMAL_RDC_OPERATION`, `EXISTING_AUTHORIZATION`, `GITHUB_RETURN_EVIDENCE`. Keep records sanitized; no tokens, private paths, personal data or raw credentials.

## RPi5 maintenance rules remain authoritative

- `HANDOFF.md` remains the current-lane continuity source. This adoption does not alter the existing #23 app-owned failure-monitoring lane.
- MERGE requires its own exact owner approval and **never** grants RPi5 LIVE authority.
- Host `apt`, Docker, systemd, cleanup, packages, locks, permissions, credentials, networking, timers and reboot still require the repository's existing separate exact LIVE approval, except precisely scoped previously reviewed installed schedules.
- `AGENTS.md` local guards and fail-closed behavior win over generic shared policy. No new GITHUB-ONLY mode, autonomous FULL/Queue, privilege or host access is enabled.
- This PR changes only `AGENTS.md`, `.github/github-first-rdc-v1.json`, `docs/GITHUB_FIRST_RDC_ADOPTION_V1.md`, `tests/test-github-first-rdc-v1.py` and `Makefile`. All changes are governance/test wiring; no `ops/**`, systemd unit, maintenance schedule, deployment workflow, runtime or installed RPi5 file changes.
- Existing `make validate` / GitHub Actions `validate` covers the new contract test; this is source-only proof, not deployed behavior.

## Expected outcome

Following owner MERGE, GitHub-first becomes the mandatory step-level tool priority in this repository. Production remains unchanged until separately authorized exact LIVE work; regular scheduled operations continue under their already-reviewed host-local execution policy.
