# Maintenance lifecycle

A maintenance run has a stable run ID and a durable evidence directory.

1. **Acquire shared maintenance lock.** Fail closed if another mutating maintenance operation owns it.
2. **Preflight.** Verify disk headroom, Docker daemon availability when Docker work is planned, configuration validity, required tools and baseline service health.
3. **Start evidence/reporting.** Record timestamp, source version, policy version and planned phases.
4. **Cleanup.** Only explicitly safe cleanup policies; no generic Docker prune.
5. **APT transaction.** One package mutation owner; capture exact result and reboot signals.
6. **Docker main transaction.** Validate, snapshot, pull, detect change, reconcile, verify and classify.
7. **Docker CV transaction.** Run independently only when shared infrastructure is healthy and policy permits continuation.
8. **Global verification.** Container, systemd, local HTTP/API and public endpoint checks.
9. **Doctor.** Only for eligible failure classes and only bounded playbooks.
10. **Verify again.** Never treat a remediation command's zero exit code as proof of recovery.
11. **Reboot decision.** Based on actual reboot requirement, final health and policy.
12. **Final report.** Include classification, mutations, recovery actions and evidence location.
13. **Release lock.** Always release through a trap/finalizer path.
