# TRS Dynamic PDF Connection Fix

Implemented fixes:

- Connection is now extracted from the PDF field text itself, not from a fixed known list.
- Priority fields:
  1. `Connection Used:`
  2. `Lot(s) Used`
  3. `Lots Used`
  4. Manufacturer + Type table fallback
- Removes specs from the connection folder name:
  - size, grade, weight, torque specs
  - examples: `3.5`, `L80`, `9.2`, `3500`
- Supports multiple connections in the same PDF:
  - example: `TENARIS BLUE / VAM TOP`
- Fixes common OCR/report spelling:
  - `TENARS` → `TENARIS`
  - `VAMTOP` → `VAM TOP`
  - `EDC82` → `EDC 82`
- Upload route no longer fails with `422 company field required`; it falls back to auto-detected metadata.

Validated examples:

- `Job#13-KHALDA EDC-82 NORTH HARON-01X_Report_073612.PDF`
  - `KHALDA / 2026 / EDC 82 / TENARIS BLUE`

- `Job# 4-AGIBA _ EDC 47- LOTUS.W.3_Report.PDF`
  - `AGIBA / 2026 / EDC 47 / VAM TOP`
