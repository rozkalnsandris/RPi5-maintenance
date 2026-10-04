# Simple maintenance architecture

## Active runtime

There are only two scheduled maintenance entrypoints.

```text
Sunday 02:20
systemd timer -> rpi5-update (oneshot)
                  |-- APT
                  |-- main Docker Compose
                  |-- bounded cleanup
                  |-- rpi5-monitor
                  `-- reboot if required

Daily 09:00
systemd timer -> rpi5-monitor (oneshot)
                  |-- docker/ssh/cloudflared active
                  |-- all main Compose services running
                  |-- no unhealthy/restarting containers
                  `-- root filesystem below threshold
```

`systemd` owns scheduling, missed-run catch-up for the weekly job and failure notification triggering. There is no separate activation framework in the scheduled path.

## Ownership boundaries

- `/home/andris/docker`: generic weekly Compose update scope.
- App-specific/simple-deployer projects: owned by their application/deployer workflow, not rediscovered by maintenance.
- Public endpoint availability: owned by Uptime Kuma; maintenance does not maintain a second URL matrix.
- Hermes: manual/separate maintenance class.
- rclone: when installed from APT, normal APT upgrade owns its version.

## Docker cleanup

The weekly job uses only narrow Docker primitives:

- `docker image prune -f --filter until=<age>`: dangling images only;
- `docker buildx prune -f --filter until=<age> --max-used-space <limit>`: bounded build cache.

It never runs `docker system prune`, never prunes volumes, and never uses `docker image prune -a`.

## Failure model

A command failure exits the oneshot service non-zero. `systemd` records the result in the journal and activates the notification unit through `OnFailure=`. There is no runtime classifier, doctor or automatic repair layer.

The scheduled updater does not implement rollback. Docker Compose only recreates a service when its configuration or image changed; persistent volumes remain attached by Compose. Recovery after a failed mutation is an explicit operator action.

## References

- systemd oneshot services: https://manpages.debian.org/bookworm/systemd/systemd.service.5.en.html
- systemd timers/Persistent: https://manpages.debian.org/bookworm/systemd/systemd.timer.5.en.html
- systemd OnFailure: https://manpages.debian.org/bookworm/systemd/systemd.unit.5.en.html
- Debian apt-get: https://manpages.debian.org/bookworm/apt/apt-get.8.en.html
- Docker Compose pull: https://docs.docker.com/reference/cli/docker/compose/pull/
- Docker Compose up: https://docs.docker.com/reference/cli/docker/compose/up/
- Docker image prune: https://docs.docker.com/reference/cli/docker/image/prune/
- Docker buildx prune: https://docs.docker.com/reference/cli/docker/buildx/prune/
