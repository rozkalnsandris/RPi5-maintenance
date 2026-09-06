# Security

This repository controls software that can mutate a production host, so source compromise has operational impact.

- Never commit secrets or production environment dumps.
- Release artifacts must be traceable to reviewed Git commits.
- Production installation must pin an immutable release/commit identity.
- Runtime credentials are supplied out-of-repository and with minimum privileges.
- Logs/evidence must redact tokens, credentials, private headers and sensitive environment values.
- Report security problems privately to the repository owner rather than posting credentials or exploit details in public issues.
