# Health and verification

Health is layered because each layer detects different failure modes.

1. **Engine health:** Docker daemon/systemd/package manager can operate.
2. **Container/process state:** expected units/containers exist and are running.
3. **Declared healthchecks:** use Docker/systemd health semantics where available.
4. **Local application checks:** HTTP/API/TCP checks prove the app answers on the host.
5. **Public checks:** where required, prove Cloudflare/public routing still reaches the application.
6. **Dependency checks:** verify critical dependent services did not remain in restart loops or disconnected states.

A maintenance run must define which checks are required versus informational. A required check must have a timeout and a stable interpretation of success.

The verifier should be runnable separately from the updater so it can confirm state after natural recovery, reboot or bounded doctor actions.
