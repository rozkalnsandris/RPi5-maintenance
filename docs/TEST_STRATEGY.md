# Test strategy

## Layers

1. **Static:** shell syntax, Python compile, unit-file/config validation where feasible.
2. **Policy unit tests:** APT, cleanup, locks, origin/provenance, reboot, Compose decisions, health interpretation.
3. **Transaction/evidence tests:** fake Docker/Compose/systemctl/apt executables exercise exit codes, timeout classification and state transitions without a production socket.
4. **Regression fixtures:** incidents become deterministic, sanitized fixtures.
5. **Integration/shadow:** run verifier/check mode against the RPi5 with no production mutation.
6. **Release candidate:** controlled production activation only after source gates pass.

## Mandatory regression: 2026-09-06

The preserved host evidence shows Docker packages were upgraded, Docker restarted, `mosquitto` remained stopped during the main Docker phase, candidate pulls completed, and V27 then reported only a generic main failure. The exact historical post-pull return statement was not retained.

The P1 executable fixture reproduces the evidence-backed path: candidate pull complete -> registry-backed service has no running container -> target selection returns a stable `missing-running-container` reason before reconcile.

P1 also tests evidence primitives for:

- lossless command stdout/stderr capture with exact exit code;
- timeout/readiness reason classification;
- before/after mutation state;
- sanitized structured phase records;
- final Compose health capture.

P1 does not change CV failure-domain continuation, automatic remediation or systemd dependency backoff; those remain later milestones.

## Safety

CI tests must never assume access to a production Docker socket, production credentials or root privileges.
