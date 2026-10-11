# Development workflow

1. Read current `AGENTS.md`, `HANDOFF.md`, `main` and the relevant work item.
2. Change only needed source, docs or tests in a short-lived branch.
3. Run `make validate` without a production Docker socket or secrets.
4. Open a Draft PR; verify exact-head CI, diff, reviews and unresolved threads.
5. Mark Ready only after required checks pass.
6. Merge only after explicit owner authorization.
7. Install on RPi5 only with a **separate exact LIVE authorization**, pinned
   source identity, live preflight and verification.

Historical V21–V28 activation/extraction sources remain in Git history.
Do not revive them as a shortcut for host repair.
