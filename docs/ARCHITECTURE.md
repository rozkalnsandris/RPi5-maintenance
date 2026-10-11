# Simple maintenance architecture

Two scheduled entrypoints; no legacy activation or doctor framework:

```text
Sunday 02:20
rpi5-update.timer -> rpi5-update.service -> rpi5-update
  preflight -> shared backup lock -> conservative APT -> Docker/DNS ready
  -> main Compose pull -> main Compose up --wait -> bounded cleanup
  -> rpi5-monitor -> reboot only if required and earlier phases succeeded

Daily 09:00
rpi5-monitor.timer -> rpi5-monitor.service -> rpi5-monitor
  Docker/SSH/Cloudflared -> main Compose running/health -> disk threshold

Service OnSuccess/OnFailure -> isolated Telegram notifier
```

The main Compose update scope is `/home/andris/docker`. App-specific
deployment and public endpoints belong to application deployers and Uptime
Kuma; Hermes is separate/manual. APT owns APT-installed software.

The updater never prunes volumes, runs broad `docker system prune`, or
auto-retries/rolls back a failed Compose operation. A command failure
short-circuits later phases, including reboot.

The backup wrapper and updater share the same exclusive lock. Backup code
is retained even though backups are not launched by these two timers.

See [lifecycle](MAINTENANCE_LIFECYCLE.md),
[configuration](CONFIGURATION.md) and [official references](REFERENCES.md).
