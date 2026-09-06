# V28 release and shadow-verification gate

## Purpose

V28 is the `0.2.0` evidence-hardening milestone. Production must not consume moving `main`; the deployable candidate must be bound to one immutable Git commit/tag with reproducible release metadata.

## Release manifest

`scripts/build-release-manifest.py` builds deterministic JSON from an exact Git ref and verifies that the tracked updater bytes, Git blob, size and `updater-source-provenance.json` candidate agree before emitting metadata.

Example after the release commit is merged:

```bash
python3 scripts/build-release-manifest.py --ref <exact-commit> --version 0.2.0
```

The manifest explicitly records `production_activation_authorized=false`. Publishing a tag/release does not authorize installation.

## Read-only shadow verification

`scripts/rpi5-maintenance-shadow-verify.py` is a host preflight tool. It performs only read operations: candidate/provenance hashing, installed updater identity when readable, `docker info`, Compose `config/ps`, container `inspect`, `systemctl is-active` and `/run/reboot-required` inspection.

It does not run APT, Compose mutation, Docker pull/build/up/down/restart/prune, systemd mutation, cleanup, filesystem mutation or reboot.

A sticky failed state for the prior one-shot `rpi5-update.service` is reported as a warning; shadow verification must not clear it. Current Docker/Compose health is evaluated independently from the historical maintenance exit status.

## Gate sequence

1. Merge this release/shadow tooling with exact-head CI green.
2. Generate release metadata from the exact merged commit.
3. Owner explicitly authorizes creation of the immutable `0.2.0` tag/GitHub release.
4. Re-run read-only shadow verification against the exact release source and preserve the output as release evidence.
5. Only then request separate LIVE authorization for production installation/cutover.

No step in this document authorizes production mutation.
