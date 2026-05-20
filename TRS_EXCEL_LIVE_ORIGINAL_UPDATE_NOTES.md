# TRS Excel Live Sync Update

This build updates the Equipment Live Sync workflow:

- Live Sync cell edits now write back to the original `.xlsx` workbook when possible.
- Workbook formatting, logos, colors, merged cells and formulas outside the edited cell are preserved because the source workbook is updated in-place with openpyxl.
- Checkbox-like cells are rendered as clickable web checkboxes and saved back as TRUE/FALSE or matching checkbox-style values where possible.
- Added `Download Updated Excel` to download the original workbook after Live Sync edits.
- `Export Data XLSX` still exists as a simple database/data export.

Notes:
- True Excel form-control checkboxes are not fully editable by openpyxl; the web editor supports checkbox-like cell values such as TRUE/FALSE, YES/NO, ☑/☐, ✓/blank.
- Editing a formula cell will replace that formula with the typed value. Other formulas remain preserved.
