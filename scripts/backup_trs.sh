#!/usr/bin/env bash
set -euo pipefail
STAMP=$(date +%Y%m%d_%H%M%S)
ROOT=${TRS_BACKUP_ROOT:-./backups}
DB=${TRS_DB_PATH:-./jam.db}
UPLOADS=${TRS_UPLOADS:-./uploads}
REPORTS=${TRS_REPORTS:-./reports}
mkdir -p "$ROOT"
OUT="$ROOT/trs_backup_$STAMP.tar.gz"
tar -czf "$OUT" "$DB" "$UPLOADS" "$REPORTS" 2>/dev/null || true
echo "Backup created: $OUT"
