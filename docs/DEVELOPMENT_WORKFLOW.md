# Development workflow

1. Start from current `main` and current repository instructions.
2. Select one issue/work item and define evidence plus invariant.
3. Create a short-lived branch.
4. Add or update a deterministic test/fixture before changing operational policy where feasible.
5. Keep extraction/path-only changes separate from behavioral changes.
6. Run local validation.
7. Open a PR with problem, change, tests, operational impact and rollback.
8. Merge only after required CI/review gates are satisfied.
9. Create a release separately when the change is intended for consumption.
10. Production activation remains a distinct authorized operation against an exact release.

Do not debug by repeatedly mutating the production RPi5. Capture evidence, reproduce with fakes/fixtures, fix in source, then prove the release candidate before activation.
