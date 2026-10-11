# Current handoff

## Canonical state

GitHub is canonical for repository source/policy/tests; the RPi5 is canonical
for installed files, systemd/Docker and observed health. Refresh mutable SHA,
CI and host evidence rather than treating these notes as current proof.

## Active maintenance model

- Weekly `rpi5-update.timer` (Sunday 02:20): conservative APT,
  bounded post-APT Docker/DNS readiness, main Compose pull/up, narrow cleanup,
  read-only monitor and conditional reboot.
- Daily `rpi5-monitor.timer` (09:00): Docker/SSH/Cloudflared, 12 main
  Compose services, unhealthy/restarting state and root disk threshold.
- OnSuccess/OnFailure: systemd Telegram notifier.
- Backup wrapper/core share the maintenance lock; other applications,
  Uptime Kuma and Hermes remain separate owners.

## Last verified incident and installation evidence (2026-10-11)

PR #76 was squash-merged into source commit
`fc39ebae77a9b305dee6d86f31cb6531cc87e587` (validate passed).
The authorized single-file LIVE installation of `/usr/local/sbin/rpi5-update`
was verified with blob `c4054933c4990a34dd1ff5ca90e1588d69b2fefa`.
A later read-only host check returned `rpi5-update --check: PASS`,
`rpi5-monitor: PASS`, 12 main services and reboot not required.
The 2026-10-11 02:21 failed systemd state remained historical, from a
Docker Hub DNS timeout after Docker package upgrades.

Do not infer current production status from these dated observations.

## Repository cleanup continuation

The simplified scheduled runtime is deliberately limited to five bin
entrypoints, two library files and five systemd unit files, including the
retained backup/lock path. Old V21–V28 activation/doctor/evidence engines,
historical tests and documents are removed from the working tree only;
they remain available from historical Git commits.

This repository cleanup is source-only and does not install, restart,
clean or delete anything on RPi5. Merge needs explicit owner approval.
No LIVE action is necessary solely for repository decluttering.
