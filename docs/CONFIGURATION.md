# Runtime configuration

The active updater reads an optional root-owned **Bash** file:
`/etc/rpi-update.conf`. It refuses symlinks and files writable by group or
others. Do not copy configuration from untrusted sources: this file is sourced
by a root process. Never commit production credentials.

See [the example](../config/rpi-update.conf.example). Supported updater values:

- `MAIN_COMPOSE_DIR` (default `/home/andris/docker`)
- `CLEANUP_RETENTION_DAYS` (default `14`, allowed 1–3650)
- `BUILD_CACHE_MAX` (default `8gb`)
- `REBOOT_POLICY` (`if-needed` or `never`)
- `MONITOR_BIN` (default `/usr/local/sbin/rpi5-monitor`)

The standalone daily monitor reads `MAIN_COMPOSE_DIR` and
`DISK_FAIL_PERCENT` (default 90) from its environment; it does not source
the updater configuration file.

Telegram credentials belong to the isolated
`rpi5-maintenance-notify@.service` using systemd `LoadCredential=`;
do not place them in updater configuration.
