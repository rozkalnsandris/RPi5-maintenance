# Extracted runtime source

Phase-1 extraction copies the canonical maintenance runtime files from `RPi5_main` into their existing `ops/...` paths. This placeholder intentionally does not contain a rewritten updater. Run `scripts/extract_from_rpi5_main.sh` against the exact baseline checkout, then verify with `scripts/verify_extraction.sh`.
