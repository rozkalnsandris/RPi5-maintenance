# Current handoff

## Canonical ownership

`rozkalnsandris/RPi5-maintenance` is canonical for maintenance source, policy, tests and review. The live RPi5 remains canonical for installed/runtime state.

## Current production state

The simplified maintenance runtime from PR #73 is deployed on the RPi5.

Production source identity:

- reviewed/merged source: `60a1d6ebfcc819978073d39066c22f4cf0ce33a9`;
- issue #11 is closed;
- PR #73 is merged;
- push `validate` for the merged source passed.

Installed active runtime:

- `/usr/local/sbin/rpi5-update` matches the simplified source;
- `/usr/local/sbin/rpi5-monitor` matches the simplified source;
- `rpi5-update.service/timer` and `rpi5-monitor.service/timer` match the simplified source;
- `rpi5-maintenance-notify@.service` matches the simplified source;
- `rpi5-update.timer` and `rpi5-monitor.timer` are enabled and active;
- the corresponding services are inactive between scheduled runs, not failed.

The simple monitor and updater check both pass on the live host:

- main Compose services checked: 12;
- root filesystem usage observed during cutover/SYNC verification: 56%;
- `rpi5-monitor`: PASS;
- `rpi5-update --check`: PASS;
- `REBOOT_REQUIRED=no`.

## Retired legacy runtime

The following old scheduled-runtime artifacts were removed during the authorized SIMPLE-CUTOVER:

- `rpi5-post-reboot.service`;
- `/usr/local/sbin/rpi5-post-reboot`;
- `/etc/rpi5-maintenance/docker-retention.conf`;
- `/etc/rpi5-maintenance/required-containers`;
- `/usr/local/lib/rpi5-maintenance/docker-retention`.

The custom retention planner/report/executor path, `docker system df` dependency and service-health TSV/classifier are no longer part of the scheduled runtime.

The cutover preserved the notifier helper/credentials, shared maintenance lock semantics, backup runtime and unrelated maintenance support files.

Rollback evidence from the cutover is preserved under:

`/var/lib/rpi5-maintenance/simple-cutover/20261004T084845Z-60a1d6ebfcc8`

No rollback was executed.

## Active maintenance model

Weekly:

1. conservative APT update/upgrade;
2. generic Compose update only for `/home/andris/docker`;
3. narrow cleanup;
4. run the simple monitor;
5. reboot only when required by `/run/reboot-required` and policy allows it.

Daily:

- verify `docker.service`, `ssh.service`, and `cloudflared.service`;
- verify all services declared by the main Compose project are running;
- fail on unhealthy/restarting containers;
- check root filesystem usage.

Public endpoint monitoring remains owned by Uptime Kuma. App-specific/simple-deployer projects remain owned by their application/deployer workflows. Hermes remains separate/manual, and APT owns APT-managed rclone.

## Continuation

There is no remaining issue #11 retention rollout work.

Normal continuation is observation of the next scheduled monitor/update runs. Any future source/runtime change remains subject to the normal MERGE/LIVE gates.
