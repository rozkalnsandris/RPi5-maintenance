# Active runtime source

The scheduled maintenance runtime is intentionally small:

- `bin/rpi5-update`
- `bin/rpi5-monitor`
- `bin/rpi5-maintenance-notify`
- `lib/rpi5-maintenance-telegram.py`
- matching `systemd` service/timer units

Application deployers, Uptime Kuma, Hermes maintenance and backup logic are separate concerns. Legacy activation/retention/health-classifier tooling is not part of the active scheduled path.
