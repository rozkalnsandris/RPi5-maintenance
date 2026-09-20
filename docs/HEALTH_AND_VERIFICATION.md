# Health and verification

Health is layered because each layer detects different failure modes.

1. **Engine health:** Docker daemon/systemd/package manager can operate.
2. **Container/process state:** expected units/containers exist and are running.
3. **Declared healthchecks:** use Docker/systemd health semantics where available.
4. **Local application checks:** HTTP/API/TCP checks prove the app answers on the host.
5. **Public checks:** where required, prove Cloudflare/public routing still reaches the application.
6. **Dependency checks:** verify critical dependent services did not remain in restart loops or disconnected states.

A maintenance run must define which checks are required versus informational. A required check must have a timeout and a stable interpretation of success.

`ops/config/service-health.tsv` is the canonical service-health ownership policy; see `docs/SERVICE_HEALTH_MATRIX.md`. A Docker container that is merely `running` without a meaningful `HEALTHCHECK` is not application-health proof. Such a service requires an explicit application/protocol probe or a documented visible exception.

Startup state must be bounded by service-specific grace and retry policy. `starting` may be classified as transient only inside that budget; exhausted startup budget, `unhealthy`, exited/missing state, probe failure/timeout, or unavailable required evidence must fail closed rather than being hidden as healthy.

External-owner and preview services may be observed without granting `RPi5-maintenance` authority to mutate them. Maintenance convergence must consume the same ownership policy instead of maintaining a conflicting implicit definition of health.

The verifier should be runnable separately from the updater so it can confirm state after natural recovery, reboot or bounded doctor actions.
