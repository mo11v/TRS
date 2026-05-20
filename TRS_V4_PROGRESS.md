# TRS Platform v4 Progress

## Added in v4

### Job Files
- Added a real folder-path registry table: `trs_job_folders`.
- Added **Create Folder Path** action for paths like `Khalda/2026/EDC-9/PH-6` before any files are uploaded.
- Updated the Job Files tree to show both empty folders and folders that already contain files.
- Added **Batch Import ZIP** for job files.
- ZIP import reads each PDF/Excel/CSV/image, runs smart path detection, stores it under the detected Company / Year / Rig / Connection, and logs files that need review.
- Auto-created folders during ZIP import.

### Database
- Added `trs_job_folders` table and index.

### UX
- Job Files topbar now has: New Folder, Import ZIP, Upload File.
- Folder tree can be planned in advance before job documents arrive.

## Still Missing / Next
- Production cloud storage integration for every upload, not just local filesystem fallback.
- Final permission matrix for Admin / Manager / Engineer / Viewer per module.
- More advanced PDF extraction rules based on actual customer report samples.
- Excel in-browser editor for maintenance files.
- Full audit trail comparing old vs new values.
- Notification center and email/WhatsApp alerts.
- Deployment hardening: HTTPS, backups, PostgreSQL, object storage, environment secrets.
