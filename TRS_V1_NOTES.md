# TRS Platform v1 progress

Built on the existing JAM FastAPI project.

## Added in this version

1. Platform identity updated to `TRS Platform — JAM + Files + Maintenance`.
2. New database tables:
   - `trs_job_files`
   - `trs_equipment`
   - `trs_equipment_logs`
3. New Job Files module:
   - `/job-files`
   - company/year/rig/connection file tree
   - upload files
   - download files
   - PDF preview endpoint
   - WebSocket reload broadcast on upload/delete
4. New Equipment Maintenance module:
   - `/equipment-maintenance`
   - equipment register
   - due/overdue alerts
   - detail page per equipment
   - maintenance log rows
   - CSV export
   - WebSocket reload broadcast on asset/log updates
5. Sidebar navigation and dashboard quick links updated.

## Next development step

- Add real user permissions per module.
- Replace local file storage with Cloudinary/S3 for production.
- Add Firestore/Supabase real-time database sync.
- Add Excel `.xlsx` export instead of CSV.
- Add Smart Torque desktop uploader API to push job results into the web app.
