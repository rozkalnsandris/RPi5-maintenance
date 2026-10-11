# Exact source and production installation

1. Review source in a PR and pass required checks.
2. Merge only with explicit owner authorization.
3. Bind a proposed installation to an **immutable full Git commit** and
   verify the expected source blob/SHA-256 and current installed file.
4. Apply only the separately LIVE-authorized target mutation and verify
   installed identity/permissions/health without broad maintenance reruns.

GitHub `main` does not automatically deploy to RPi5.
The repository intentionally has no active V21–V28 activation framework.
Old release/provenance procedures remain available in Git history.
A recovery/rollback must be independently authorized and scope-checked.
