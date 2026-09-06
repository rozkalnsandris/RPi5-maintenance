# ADR-0002: Extract, don't rewrite

Status: Accepted.

Decision: the first migration preserves behavior and source structure as much as practical. Refactoring and policy changes occur only after parity, in separate PRs with tests. This reduces simultaneous variables during a trust-boundary migration.
