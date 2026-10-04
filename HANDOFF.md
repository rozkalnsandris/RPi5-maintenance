# Current handoff

## Canonical ownership

`rozkalnsandris/RPi5-maintenance` is canonical for maintenance source, policy, tests and review. The live RPi5 remains canonical for installed/runtime state.

## Current work item

Issue #11 is being superseded by a simpler maintenance model. The custom Docker retention inventory/planner/report/executor and service-health classifier/matrix are no longer intended to be part of the scheduled runtime.

The target scheduled runtime is:

- one weekly `rpi5-update` oneshot;
- one daily read-only `rpi5-monitor` oneshot;
- native systemd timers and OnFailure/OnSuccess notification;
- generic Compose ownership limited to `/home/andris/docker`;
- app-specific/simple-deployer projects remain owned by their app/deployer workflows;
- Uptime Kuma owns public endpoint monitoring;
- Hermes remains separate/manual and APT owns APT-managed rclone.

## LIVE state boundary

The source simplification does not imply deployment.

Production currently still has the partially deployed PR #72 retention wrapper/config from the 2026-10-04 incident recovery attempt and the older monitor baseline. A read-only retention verification then failed because `docker system df` exceeded the configured 15-second timeout. No health-gates activation followed that failure.

Do not manually retry the old retention report or activate the old health-gates path. After the simplification PR is reviewed and merged, prepare a separate exact LIVE cutover from the installed complex runtime to the small runtime. That cutover must define the exact installed files/units to replace or retire, preserve the existing notification credentials and shared lock semantics, and decide post-reboot unit retirement explicitly.

No reboot is part of source-only work.
