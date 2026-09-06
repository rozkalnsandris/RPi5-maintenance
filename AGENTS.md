# Repository operating rules

## Canonical state

GitHub is the canonical source of truth for repository state, reviews, checks, release metadata and source provenance. Chat history is not canonical state.

## Work model

- Read current repository instructions and current work-item state before changing source.
- Keep changes narrowly scoped and reviewable.
- Source changes may be prepared without production activation.
- Merge requires explicit authorization where the operator workflow requires it.
- Merge authorization is not deployment authorization.

## Production trust boundary

No repository workflow, agent or doctor may autonomously:

- use root/sudo on the production RPi5;
- edit production Compose files, systemd units, networking, firewall, storage, permissions or secrets;
- install/remove packages outside an explicitly authorized maintenance transaction;
- delete Docker volumes, run `docker system prune`, or use `docker compose down -v` as recovery;
- deploy a new maintenance release to production;
- change timers, services or reboot policy in production.

A production mutation requires a separately authorized operation bound to an exact source/release identity with preflight, verification and rollback.

## Extraction rule

Phase 1 is **extract, don't rewrite**. Preserve source semantics, names and paths wherever practical. Behavioral refactors belong in later PRs after parity is established.

## Evidence rule

Any mutating phase must record command identity, phase, exit code, duration, stdout/stderr (sanitized), before/after state and health results. Do not suppress the error stream needed for root-cause analysis.

## Doctor rule

The doctor is deterministic and playbook-driven. It may select only predeclared, bounded remediation actions. It must never generate arbitrary shell from free-form AI reasoning.

## Secrets

Never commit credentials, tokens, private URLs, raw customer/user data or environment files. Tests must use fixtures or redacted synthetic values.
