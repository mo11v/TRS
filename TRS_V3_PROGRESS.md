# TRS Platform v3 Progress

## Added in v3

### Job Files
- Added Job File Review page for each uploaded file.
- Upload now stores smart-detection confidence and the detected path.
- Added Confirm / Move workflow so the user can correct Company / Year / Rig / Connection after upload.
- Added per-file activity timeline.
- Job Files table now shows detection confidence and Review action.

### Equipment Maintenance
- Imported Excel files now keep the original source file path and original file name.
- Equipment detail can download the original Excel source file when available.
- Added professional Excel export `/equipment-maintenance/export.xlsx` plus existing CSV export.

### Platform / Admin
- Added full Activity Log page with filters.
- Added Activity Log to sidebar navigation.
- Added DB migrations for new columns, so older local databases can upgrade safely.

## Still pending
- True cloud storage integration for Job Files and Equipment Excel originals.
- Realtime collaborative cell-level editing for Excel-style maintenance logs.
- User/role restrictions per company/module.
- Better AI/PDF extraction once real PDF samples are provided.
