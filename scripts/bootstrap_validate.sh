#!/usr/bin/env bash
set -euo pipefail
root="${1:-.}"
required=(
  README.md AGENTS.md LICENSE VERSION CHANGELOG.md
  SOURCE_BASELINE.md SOURCE_EXTRACTION_MANIFEST.txt
  docs/ARCHITECTURE.md docs/FAILURE_MODEL.md docs/MIGRATION_FROM_RPI5_MAIN.md
  docs/INCIDENT_2026-09-06.md docs/REFERENCES.md
)
for f in "${required[@]}"; do
  [[ -f "$root/$f" ]] || { echo "missing required bootstrap file: $f" >&2; exit 1; }
done
bash -n "$root/scripts/extract_from_rpi5_main.sh"
bash -n "$root/scripts/verify_extraction.sh"
echo "bootstrap validation PASS"
