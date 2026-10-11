# Project boundary

This repository owns the small RPi5 maintenance **source**:
the weekly updater, daily monitor, Telegram notifier, their systemd units,
the shared maintenance/backup lock implementation, tests and operator docs.

The backup runner and wrapper are retained here because they share the
maintenance lock. Backup schedules/data remain separately controlled.

This repository does not control application source or app-specific deploys
(CV, Weather, Coloring Pages, Hermes Deals, etc.), Cloudflare, secrets,
arbitrary host repair, or application data migrations.

Production RPi5 runtime state must be verified on the host. GitHub source
and merged PRs are not proof of deployment.
