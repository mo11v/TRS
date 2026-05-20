# TRS Platform v6 + v7 + v8 Progress

## v6 — Professional Web App UI
- Kept the unified TRS sidebar/dashboard structure.
- Added live-ready front-end helper `/static/trs_realtime.js`.
- Updated project version to `1.8.0-trs-mvp`.

## v7 — Web Excel Editor
- Added database-backed editable spreadsheet tables.
- Imported Excel/CSV equipment source files into live editable cells.
- Added instant cell save endpoint.
- Added add-row endpoint.
- Added export of the live sheet back to `.xlsx`.
- Added re-import from original source Excel.

## v8 — Real-time Collaboration Foundation
- Added equipment sheet WebSocket updates.
- Added live cell broadcasting between users.
- Added auto reconnect WebSocket helper.
- Kept Render/Docker deployment files already present.

## Important Notes
- This is a strong MVP build, not yet final production.
- For production, move from SQLite to PostgreSQL and move files to S3/Cloudinary.
- For heavy Excel sheets, the editor currently limits import to 200 rows × 30 columns by default to stay fast.
