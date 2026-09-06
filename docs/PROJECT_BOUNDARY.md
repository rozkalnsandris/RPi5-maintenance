# Project boundary

## This repository owns

- maintenance scheduling contracts and orchestration source;
- package-update policy integration;
- Docker Compose update transaction policy;
- verifier/health interpretation;
- bounded doctor playbooks;
- maintenance locks;
- reboot decision policy;
- evidence/reporting formats;
- systemd units directly belonging to maintenance;
- release, provenance, install and rollback contracts for the maintenance product.

## This repository does not own

- Home Assistant, Grafana, AdGuard, Prometheus, Hermes, Hermes Deals/Tech, CV application source;
- application-specific production Compose configuration except interfaces required by maintenance;
- Cloudflare configuration;
- host secrets or credentials;
- arbitrary host/network/storage administration;
- application data migrations.

`RPi5_main` remains the canonical host/application integration repository until the migration explicitly moves an interface to this repository.
