# TRS Google Drive Automatic Backup

This backup system creates a daily ZIP containing:

- `trs_platform.db`
- `uploads/`
- `equipment_data/`
- `equipment_library/`
- `data/`
- `logs/`

and uploads it to Google Drive folder `TRS_BACKUP`.

## Important

Do **not** upload these files to GitHub:

- `google_drive_credentials.json`
- `google_drive_token.json`

They are ignored by `.gitignore`.

## 1) Put OAuth credentials file in the project

Rename your downloaded OAuth JSON file to:

```text
google_drive_credentials.json
```

Place it beside `app.py`.

## 2) Install requirements

```bash
pip install -r requirements.txt
```

## 3) First-time authorization

Run once on your computer/server:

```bash
python scripts/google_drive_backup.py --setup
```

A browser window will open. Login with your Google account and allow Drive access.
This creates `google_drive_token.json`.

## 4) Test backup manually

```bash
python scripts/google_drive_backup.py --once
```

Check Google Drive for folder:

```text
TRS_BACKUP
```

## 5) Automatic daily backup from inside app

Add this to `.env` or Render Environment:

```env
TRS_GOOGLE_DRIVE_BACKUP=1
TRS_BACKUP_HOUR=2
TRS_BACKUP_MINUTE=0
TRS_GOOGLE_DRIVE_FOLDER_NAME=TRS_BACKUP
```

The app will attempt a backup daily at 02:00 while the process is running.

## 6) Better for Windows server: Scheduled Task

Open PowerShell and run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
.\scripts\install_daily_google_drive_backup_task.ps1
```

This runs a backup every day at 02:00 AM even if the web app is not being used.
