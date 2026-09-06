# ADR-0001: Separate maintenance repository

Status: Accepted for bootstrap.

Decision: extract RPi5 maintenance orchestration from `RPi5_main` into `rpi5-maintenance` with independent CI/releases. `RPi5_main` remains host/application source; production consumes a pinned maintenance release after a separately authorized migration.
