# Governance

## Source of truth

GitHub is canonical for source, reviews, checks, issues, releases and provenance. Runtime state is observed on the RPi5; chat history is not canonical project state.

## Change classes

1. **Documentation / tests only** — no runtime behavior change.
2. **Source behavior change** — requires tests and review; still does not mutate production.
3. **Release creation** — creates an immutable candidate identity; still does not activate production.
4. **Production activation** — separate, explicit authorization bound to an exact release/commit, with preflight, verification and rollback.
5. **Emergency recovery** — separately scoped production action with preserved evidence; never inferred from ordinary source authorization.

## Main branch

Normal development should use short-lived branches and pull requests. Required CI should gate merges. Workflow, governance and production-control paths are code-owned by `@rozkalnsandris`.

## Decision records

Architecturally significant decisions are recorded in `docs/decisions/ADR-*.md`. Incidents that reveal a design defect should create a regression specification before or alongside the fix.
