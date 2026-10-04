# Maintenance lifecycle

## Weekly update

1. Read-only preflight: Docker daemon and `/home/andris/docker` Compose config.
2. Acquire the shared maintenance lock.
3. `apt-get update`.
4. `apt-get upgrade -y --with-new-pkgs --no-remove` and `apt-get check`.
5. `docker compose pull --ignore-buildable` in `/home/andris/docker`.
6. `docker compose up -d --no-build --wait --wait-timeout 180`.
7. Bounded cleanup: APT autoclean, journal vacuum, tmpfiles clean, dangling-image prune and BuildKit cache cap.
8. Run `rpi5-monitor`.
9. If `/run/reboot-required` exists and policy is `if-needed`, reboot.

Any non-zero command stops the oneshot service. There is no automatic retry or rollback.

## Daily monitor

The monitor is read-only. It checks only host/runtime basics that maintenance owns:

- `docker.service`, `ssh.service`, `cloudflared.service` are active;
- Docker responds;
- all services declared by the main Compose project are running;
- no running container reports `unhealthy` or `restarting`;
- `/` usage remains below the configured threshold.

Public URL checks belong to Uptime Kuma and are intentionally not duplicated here.
