# Simple operations runbook

## When `rpi5-update.service` fails

1. Read `journalctl -u rpi5-update.service` around the failed invocation.
   Record the first `FAIL phase=...` and its stderr.
2. Check Docker, the affected Compose services and dependent DNS, as needed.
   A failed update does not by itself prove a current service outage.
3. Confirm APT/package consistency, current state, shared lock and
   `/run/reboot-required` only when the failing phase warrants it.
4. If the system is healthy but the update is incomplete, preserve the
   evidence and wait for reviewed remediation. Do not rerun mutation merely
   to clear the red systemd state.
5. Manual update runs, Docker recovery, service restarts, cleanup or reboot
   require separate explicit LIVE authorization.

`systemctl reset-failed` only clears historical unit failure state; it
does not resolve its cause and is not part of the automatic update.

## Normal ownership

- Main Compose: `/home/andris/docker`.
- Other applications and public endpoints: respective deployers/Uptime Kuma.
- Backup: separate runner protected by the shared maintenance lock.
- Hermes: independent/manual maintenance.
- Pinned GitHub source and installed RPi5 files have distinct identities.
