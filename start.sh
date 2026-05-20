#!/bin/bash
## TRS Platform — Production Start Script
## Used by Render / Docker

set -e

echo "═══════════════════════════════════════════"
echo "  TRS Platform — Starting..."
echo "═══════════════════════════════════════════"

## ── Create required directories ─────────────
mkdir -p "${TRS_UPLOADS:-/tmp/trs_uploads}"
mkdir -p "${TRS_REPORTS:-/tmp/trs_reports}"
mkdir -p "$(dirname "${TRS_DB_PATH:-/tmp/trs_platform.db}")"

echo "✅ Directories ready"
echo "   DB:      ${TRS_DB_PATH:-/tmp/trs_platform.db}"
echo "   Uploads: ${TRS_UPLOADS:-/tmp/trs_uploads}"

## ── Start server ─────────────────────────────
echo ""
echo "🚀 Starting uvicorn..."
echo ""

exec uvicorn app:app \
  --host 0.0.0.0 \
  --port "${PORT:-10000}" \
  --workers 1 \
  --loop uvloop \
  --log-level info \
  --access-log
