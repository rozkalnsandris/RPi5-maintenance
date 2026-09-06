# Test strategy

## Layers

1. **Static:** shell syntax, Python compile, unit-file/config validation where feasible.
2. **Policy unit tests:** APT, cleanup, locks, origin/provenance, reboot, Compose decisions, health interpretation.
3. **Transaction tests:** fake Docker/Compose/systemctl/apt executables exercise exit codes, timeouts and state transitions without touching a real host.
4. **Regression fixtures:** incidents become deterministic fixtures.
5. **Integration/shadow:** run verifier/check mode against the RPi5 with no mutation.
6. **Release candidate:** controlled production activation only after source gates pass.

## Mandatory regression: 2026-09-06

Simulate a large candidate image, `compose up` non-zero, no retained unhealthy mutation, eventual 20/20 healthy, transient dependent service reconnects, no reboot required.

Expected behavior after redesign:

- exact Compose error retained;
- final classification is evidence-based (`RECOVERED` or `DEGRADED` depending mutation/convergence evidence), not blindly `CRITICAL`;
- CV continuation decision uses shared-infrastructure gate;
- no restart storm;
- report distinguishes update failure from healthy final system;
- reboot remains unnecessary when host does not require one.

## Safety

CI tests must never assume access to a production Docker socket, production credentials or root privileges.
