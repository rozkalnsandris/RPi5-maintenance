# RPi5-maintenance

Small, auditable updater and monitor for one Raspberry Pi 5.

```text
Sun 02:20  rpi5-update.timer  -> APT -> Docker/DNS ready -> main Compose
                              -> bounded cleanup -> monitor -> reboot if needed
Daily 09:00 rpi5-monitor.timer -> host/main Compose checks
OnSuccess/OnFailure -> isolated Telegram notification
```

Active runtime: `ops/bin/rpi5-update`, `rpi5-monitor`,
`rpi5-maintenance-notify`, Telegram helper and five systemd unit files.
Backup wrapper/core and lock helper are retained to prevent concurrent
backup/update mutations.

Only `/home/andris/docker` is in the weekly generic Compose scope.
CV, Weather, Coloring Pages and other application deployments are separate.
Public endpoints belong to Uptime Kuma; Hermes is separate/manual.
No automatic rollback, arbitrary doctor, broad Docker/volume prune or
autoremove.

Run `make validate` against source. `rpi5-update --check` is the
read-only host check; an actual maintenance run is a LIVE mutation.
GitHub is canonical for source/review and RPi5 for actual runtime state.
**Merge never means deploy.**

See [architecture](docs/ARCHITECTURE.md),
[configuration](docs/CONFIGURATION.md),
[Latvian overview](docs/README-LV.md) and
[operations runbook](docs/OPERATIONS_RUNBOOK.md).
