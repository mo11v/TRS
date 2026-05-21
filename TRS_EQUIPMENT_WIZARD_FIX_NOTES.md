# TRS Equipment Wizard Fix

This build fixes the Equipment Maintenance simple entry flow:

- Preventive / Corrective are both detected, including the template typo `Perventive`.
- Local / Std / Etc and Preventive / Corrective columns are inferred from the Excel layout when merged headers hide some sub-columns.
- Empty template header/sub-header rows are no longer shown as editable saved entries.
- Add Maintenance now writes to the first real empty maintenance row in the Excel sheet instead of jumping to the end.
- Add / Edit / Delete actions update both the database and the original Excel workbook where possible.
- Live Excel editor was left unchanged.
