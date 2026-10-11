# Simple reboot policy

The weekly updater reboots only after APT, Docker pull, Compose
reconciliation, cleanup and monitor have all succeeded **and**
`/run/reboot-required` exists **and** `REBOOT_POLICY=if-needed`.

- `REBOOT_POLICY=never`: report reboot required, do not reboot.
- No `/run/reboot-required`: no reboot.
- Earlier command failure: updater exits before the reboot phase.
- `--check` mode never reboots.

There is no automatic rollback or doctor-based reboot decision.
Manual reboot or recovery requires separate LIVE authorization.
