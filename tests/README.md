# Tests

The existing maintenance test suite is imported from the exact `RPi5_main` baseline during phase 1. New tests should be separated into policy/unit, transaction/fake-runtime and incident regression fixtures. CI must not require a production Docker socket or production credentials.
