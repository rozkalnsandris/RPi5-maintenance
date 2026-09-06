# Recommended GitHub repository settings

This file documents the intended repository-administration posture. It does not assert that the settings are currently enabled.

## Main branch / ruleset

Recommended rules for `main`:

- require changes through pull requests for normal development;
- require the permanent `validate` CI job before merge;
- require conversation resolution;
- require CODEOWNERS review for security-sensitive paths where practical;
- block force pushes and branch deletion;
- prefer linear history and squash merge for a compact operational audit trail;
- do not allow a failed/unknown CI state to be treated as deployment approval.

For a single-maintainer repository, emergency/break-glass bypass should remain explicit and auditable rather than disabling the normal rule set.

## Actions

Permanent workflows should default to minimum `GITHUB_TOKEN` permissions. The repository's permanent validation workflow uses `contents: read`. Any future workflow requiring write access must document why, scope permissions narrowly and avoid mixing source validation with production deployment authority.

Third-party actions should be pinned to immutable full commit SHAs. Dependabot may propose reviewed updates to GitHub Actions dependencies.

## Security

Recommended repository security features where available:

- Dependabot alerts/security updates;
- secret scanning;
- push protection for secrets;
- private vulnerability reporting where appropriate for a public operational repository;
- code scanning when it adds useful signal for the shell/Python codebase.

No production secrets belong in GitHub source, Actions variables, fixtures or issue reports unless an explicit secret-management design requires and protects them.

## Releases

Production must consume a pinned immutable release/commit. Creating or merging source is not itself production activation. Release artifacts should remain traceable to reviewed source and CI evidence.

## Repository metadata

Recommended description: `Safety-first maintenance control plane for a production Raspberry Pi 5.`

Recommended topics: `raspberry-pi`, `raspberry-pi-5`, `maintenance`, `docker-compose`, `systemd`, `debian`, `homelab`, `devops`, `sre`.
