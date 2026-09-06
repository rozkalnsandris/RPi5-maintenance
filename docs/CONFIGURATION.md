# Configuration model

Repository defaults describe policy but production-specific secrets/paths/endpoints remain external.

Configuration should separate:

- stack inventory and project identity;
- per-stack wait/readiness timeout;
- optional pull parallelism;
- required local/public health checks;
- criticality/dependency relationships;
- reboot policy;
- allowed doctor playbooks;
- evidence retention/redaction;
- notification routing identifiers (not credentials).

Prefer a checked-in example/schema plus host-owned production configuration. Validate configuration before any mutation.
