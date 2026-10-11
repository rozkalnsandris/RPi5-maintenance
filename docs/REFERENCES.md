# Official references for the active maintenance

- [Docker Compose pull](https://docs.docker.com/reference/cli/docker/compose/pull/)
- [Docker Compose up and --wait](https://docs.docker.com/reference/cli/docker/compose/up/)
- [Docker Compose config](https://docs.docker.com/reference/cli/docker/compose/config/)
- [Docker image prune](https://docs.docker.com/reference/cli/docker/image/prune/)
- [Docker buildx prune](https://docs.docker.com/reference/cli/docker/buildx/prune/)
- [systemd service units](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html)
- [systemd timer units](https://www.freedesktop.org/software/systemd/man/latest/systemd.timer.html)
- [systemd unit dependencies and OnFailure](https://www.freedesktop.org/software/systemd/man/latest/systemd.unit.html)
- [Debian apt-get](https://manpages.debian.org/bookworm/apt/apt-get.8.en.html)
- [GitHub file removal and repository history](https://docs.github.com/en/repositories/working-with-files/managing-files/deleting-files-in-a-repository)

Keep the operational implementation small; do not add a duplicate Docker
health/rollback, APT orchestration, or public-URL monitoring framework.
