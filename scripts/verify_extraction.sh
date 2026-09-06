#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
missing=0
while IFS= read -r rel; do
  [[ -z "$rel" || "$rel" =~ ^[[:space:]]*# ]] && continue
  if [[ ! -f "$ROOT/$rel" ]]; then
    echo "MISSING $rel" >&2
    missing=1
  fi
done < "$ROOT/SOURCE_EXTRACTION_MANIFEST.txt"
if (( missing )); then
  exit 1
fi
echo "Extraction manifest complete"
