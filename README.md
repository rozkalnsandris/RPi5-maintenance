# rpi5-maintenance

Small, predictable maintenance for one private Raspberry Pi 5.

The active runtime is intentionally boring:

```text
rpi5-update.timer  -> rpi5-update.service  -> /usr/local/sbin/rpi5-update
rpi5-monitor.timer -> rpi5-monitor.service -> /usr/local/sbin/rpi5-monitor
                                      \-> OnFailure Telegram notification
```

## What the weekly update does

1. validates Docker and the main Compose project;
2. runs conservative APT update/upgrade (`--with-new-pkgs --no-remove`);
3. pulls and reconciles only `/home/andris/docker`;
4. cleans APT cache, old journal data, dangling Docker images and bounded BuildKit cache;
5. runs the same small monitor used by the daily timer;
6. reboots only when `/run/reboot-required` exists and policy is `if-needed`.

## What it deliberately does not do

- no custom Docker retention inventory/planner/executor;
- no `docker system df` dependency;
- no `docker system prune`, volume prune or `docker image prune -a`;
- no service-health TSV matrix or classifier framework;
- no public endpoint duplication (Uptime Kuma owns that job);
- no app-specific deployment discovery (simple-deployer/app repos own those deployments);
- no Hermes self-update or special rclone updater;
- no automatic package removal or `autoremove`.

## Source of truth and LIVE boundary

GitHub is canonical for source, tests and review. The RPi5 is canonical for installed/runtime state. Merge never implies deployment. Any LIVE installation, systemd change, package/Docker mutation, cleanup or reboot still requires the repository's explicit LIVE authorization model.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and [docs/README-LV.md](docs/README-LV.md).
