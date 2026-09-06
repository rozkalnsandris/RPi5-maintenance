# systemd policy

systemd is the scheduler/supervisor, not the source of application readiness truth.

## Updater

The updater is a bounded oneshot unit with a timer and explicit failure reporting. `OnFailure=` may activate a notification/diagnostic unit, but the failure handler must not create an unbounded mutation loop.

## Long-running dependents

Services such as MQTT consumers should preferably reconnect internally when a dependency is temporarily unavailable. systemd restart is a safety net, not the primary connection-management mechanism.

Use bounded restart behavior and rate limiting. On systemd versions that support it, `RestartSteps=` and `RestartMaxDelaySec=` can provide increasing restart delay. The exact production settings must be tested before activation.

The 2026-09-06 `balkons-log.service` ~230 restart loop is a regression target: planned Mosquitto downtime must not create a restart storm.
