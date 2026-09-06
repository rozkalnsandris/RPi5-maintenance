# Release and versioning

## Principle

Production never tracks the moving `main` branch.

## Release flow

1. source PR reviewed and CI green;
2. merge to `main`;
3. create immutable version/tag and release metadata;
4. verify release artifact/provenance;
5. separately authorize production activation of that exact version;
6. preflight current production state;
7. install/activate transactionally;
8. verify and retain rollback target.

## Versioning

Use semantic versioning after parity release. Before the first stable production release, `0.x` versions may evolve contracts, but every production candidate is still immutable and reviewable.

Recommended milestones:

- `0.1.0`: extraction/parity source only;
- `0.2.0`: evidence/error-capture redesign;
- `0.3.0`: transaction classification + bounded doctor;
- `0.4.0`: dependency/backoff hardening;
- `1.0.0`: proven stable release contract and production cutover complete.
