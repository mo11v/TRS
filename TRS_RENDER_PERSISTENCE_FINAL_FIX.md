# TRS Render Persistence Final Fix

This build fixes the Render data-loss issue caused by startup overwriting the cloud DB backup.

## What changed
- Startup restore still happens before `init_db()`.
- If Cloudinary backup is missing, the app no longer uploads a freshly seeded/empty database at startup.
- Cloud backup now runs only after real write operations:
  - Excel cell edit
  - Maintenance add/edit/delete
  - PDF upload/import
  - Equipment import/delete
- Logs now show:
  - `Cloud DB persistence active - restored backup is in use`
  - `TRS persistent backup completed - equipment_cell_update`

## Required Render ENV
- CLOUDINARY_CLOUD_NAME
- CLOUDINARY_API_KEY
- CLOUDINARY_API_SECRET
- TRS_CLOUD_DB_BACKUP=1

## Important
After deploying this build, make one real edit and check logs for:
`TRS persistent backup completed`
