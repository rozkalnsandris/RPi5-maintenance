# Security and trust boundaries

## Source plane

GitHub stores reviewed source, tests, docs and immutable release metadata. It does not store production credentials.

## Release plane

A release binds reviewed source to a version/commit. Production installation uses a pinned identity and verifies provenance according to the installation contract.

## Production plane

The RPi5 owns runtime configuration, credentials, service data and actual health. Source approval never implies permission to mutate this plane.

## AI boundary

AI may reason over sanitized evidence and propose source changes. It must not be a free-form privileged remediation executor. Runtime doctor actions are deterministic playbooks with bounded parameters.
