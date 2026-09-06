#!/usr/bin/env bash
set -euo pipefail

SOURCE_ROOT="${1:-../RPi5_main}"
DEST_ROOT="${2:-.}"
EXPECTED_COMMIT="${EXPECTED_SOURCE_COMMIT:-e949f7835898fc207aa137cb26ffb6dfc701a497}"

if [[ ! -d "$SOURCE_ROOT/.git" ]]; then
  echo "ERROR: source root is not a Git checkout: $SOURCE_ROOT" >&2
  exit 2
fi

actual_commit="$(git -C "$SOURCE_ROOT" rev-parse HEAD)"
if [[ "$actual_commit" != "$EXPECTED_COMMIT" ]]; then
  echo "ERROR: source commit mismatch" >&2
  echo "expected: $EXPECTED_COMMIT" >&2
  echo "actual:   $actual_commit" >&2
  exit 3
fi

mapfile -t paths < <(grep -Ev '^[[:space:]]*(#|$)' "$DEST_ROOT/SOURCE_EXTRACTION_MANIFEST.txt")
for rel in "${paths[@]}"; do
  src="$SOURCE_ROOT/$rel"
  dst="$DEST_ROOT/$rel"
  if [[ ! -f "$src" ]]; then
    echo "ERROR: manifest source missing: $rel" >&2
    exit 4
  fi
  mkdir -p "$(dirname "$dst")"
  cp -p "$src" "$dst"
done

mkdir -p "$DEST_ROOT/provenance"
python3 - "$DEST_ROOT/provenance/extraction.json" "$actual_commit" <<'PY'
import json, sys
from datetime import datetime, timezone
path, commit = sys.argv[1:]
obj = {
  "source_repository": "rozkalnsandris/RPi5_main",
  "source_commit": commit,
  "extracted_at_utc": datetime.now(timezone.utc).isoformat(),
  "method": "scripts/extract_from_rpi5_main.sh"
}
with open(path, "w", encoding="utf-8") as f:
    json.dump(obj, f, indent=2)
    f.write("\n")
PY

echo "Extracted ${#paths[@]} canonical files from $actual_commit"
