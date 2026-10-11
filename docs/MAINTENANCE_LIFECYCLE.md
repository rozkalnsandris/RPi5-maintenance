# Maintenance lifecycle

## Weekly update — Sunday 02:20

1. Read-only check of Docker and the main Compose configuration.
2. Acquire the shared exclusive maintenance/backup lock.
3. Conservative `apt-get update`, `upgrade --with-new-pkgs --no-remove`,
   then `apt-get check`.
4. After APT may have restarted Docker/AdGuard, wait for **two consecutive**
   successful Docker daemon and Docker Hub DNS checks, with a finite budget
   of 12 checks. Fail before pulling if readiness does not recover.
5. `docker compose pull --ignore-buildable` for `/home/andris/docker`.
6. `docker compose up -d --no-build --wait --wait-timeout 180`.
7. Bounded APT/journal/tmpfiles/dangling-image/BuildKit cleanup.
8. Run the daily monitor checks.
9. Reboot only if `/run/reboot-required` exists and policy allows it.

A failure stops the sequence: no retry of a failed Compose pull, no automatic
rollback, no cleanup or reboot after an update failure.

## Daily monitor — 09:00

Verify `docker.service`, `ssh.service` and `cloudflared.service`;
the 12 declared main Compose services are running; no container is
`unhealthy` or `restarting`; root filesystem usage is below threshold.
This is **not** full application-health verification: Uptime Kuma owns public
endpoint monitoring and application deployers own app-specific checks.

The updater and daily monitor share no automatic repair framework.
