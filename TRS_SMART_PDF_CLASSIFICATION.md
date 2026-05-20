# TRS Smart PDF Classification Update

This build updates Job Files auto-detection to use the final field structure:

Company → Year → Rig → Connection Type → Well → Files

Example from the provided PDF:

AGIBA → 2026 → EDC 47 → VAM TOP → LOTUS.W.3

Detected values from `Job# 4-AGIBA _ EDC 47- LOTUS.W.3_Report.PDF`:
- Company: AGIBA
- Year: 2026
- Rig: EDC 47
- Connection Type: VAM TOP
- Well: LOTUS.W.3
- Job Name: JOB# 4-AGIBA _ EDC 47- LOTUS.W.3
- Report Date: 21/04/2026
- Confidence: 100%

Changes included:
- Added `well_name`, `job_name`, and `report_date` columns to job files.
- Added `well_name` to job folders.
- Updated upload and ZIP import to store files under the 5-level path.
- Updated Job Files UI to show Company / Year / Rig / Connection Type / Well.
- Updated Review page to confirm or move files using the new structure.
- Improved PDF parser rules for MTT reports, VAM TOP, PH, BTC/LTC/STC/NUE/EUE, etc.
