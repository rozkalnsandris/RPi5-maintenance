# Contributing

Prefer one behavioral concern per pull request. Every behavioral change must state: problem, evidence, invariant, change, tests, operational impact, rollback and whether production activation is required.

Extraction/parity PRs must not mix source movement with behavioral changes. A failing production incident should first become a reproducible test or fixture before changing policy where feasible.
