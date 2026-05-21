# TRS Persistent Equipment + Simple Entry Update

## What changed

### 1) Persistence fix for Render / temporary hosting
The platform now supports automatic SQLite backup/restore using Cloudinary when Cloudinary environment variables are configured.

This fixes the issue where:
- Excel edits disappear after Render sleep/restart/redeploy
- Activity Log disappears the next day
- Equipment changes reset back to the bundled sample state

Required Render environment variables:

```env
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
TRS_CLOUD_DB_BACKUP=1
```

The database is restored on startup and backed up automatically after write operations.

### 2) Simple Maintenance Entry system
Each equipment detail page now has a new **Simple Maintenance Entry** section.

It automatically reads the Excel columns and creates:
- Add Entry form
- Edit Entry form
- Delete row action
- Clean table view for managers/operators

The original Excel Live Sync editor remains unchanged and still exists below.

### 3) Live Excel remains unchanged
The Excel editor is still available from **Live Sync** for full spreadsheet editing.

## Important note
For production company deployment, the strongest solution is still a dedicated server or persistent disk/PostgreSQL. This Cloudinary backup layer is designed to keep data safe during Render/free-hosting demos.
