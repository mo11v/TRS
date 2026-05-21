"""
Google Drive ZIP Backup for TRS Platform
---------------------------------------
Creates a ZIP backup of the SQLite DB, uploads, equipment data and logs,
then uploads it to Google Drive using OAuth Desktop credentials.

Required first-time setup:
    python scripts/google_drive_backup.py --setup

Manual backup:
    python scripts/google_drive_backup.py --once

Automatic inside app:
    Set TRS_GOOGLE_DRIVE_BACKUP=1
"""
from __future__ import annotations

import os
import json
import shutil
import zipfile
import logging
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Iterable, Optional

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
DEFAULT_FOLDER_NAME = os.getenv("TRS_GOOGLE_DRIVE_FOLDER_NAME", "TRS_BACKUP")
CREDENTIALS_PATH = Path(os.getenv("GOOGLE_DRIVE_CREDENTIALS", "google_drive_credentials.json"))
TOKEN_PATH = Path(os.getenv("GOOGLE_DRIVE_TOKEN", "google_drive_token.json"))
BACKUP_DIR = Path(os.getenv("TRS_LOCAL_BACKUP_DIR", "local_backups"))
MAX_LOCAL_BACKUPS = int(os.getenv("TRS_MAX_LOCAL_BACKUPS", "7"))
DRIVE_KEEP_DAYS = int(os.getenv("TRS_DRIVE_KEEP_DAYS", "60"))

_scheduler_started = False
_scheduler_lock = threading.Lock()


def enabled() -> bool:
    return os.getenv("TRS_GOOGLE_DRIVE_BACKUP", "0") == "1"


def _get_credentials(interactive: bool = False):
    """Load/refresh OAuth credentials. If interactive=True, open browser for first auth."""
    if not CREDENTIALS_PATH.exists():
        raise FileNotFoundError(
            f"Google Drive credentials file not found: {CREDENTIALS_PATH}. "
            "Rename your OAuth Desktop JSON to google_drive_credentials.json or set GOOGLE_DRIVE_CREDENTIALS."
        )

    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow

    creds = None
    if TOKEN_PATH.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        except Exception as e:
            logger.warning("Could not read Google Drive token, will re-auth: %s", e)
            creds = None

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")

    if not creds or not creds.valid:
        if not interactive:
            raise RuntimeError(
                "Google Drive token is missing/invalid. Run: python scripts/google_drive_backup.py --setup"
            )
        flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
        creds = flow.run_local_server(port=0)
        TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")

    return creds


def _service(interactive: bool = False):
    from googleapiclient.discovery import build
    creds = _get_credentials(interactive=interactive)
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def _find_or_create_folder(service, folder_name: str = DEFAULT_FOLDER_NAME) -> str:
    folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
    if folder_id:
        return folder_id

    safe_name = folder_name.replace("'", "\\'")
    query = (
        "mimeType='application/vnd.google-apps.folder' "
        f"and name='{safe_name}' and trashed=false"
    )
    res = service.files().list(q=query, fields="files(id,name)", pageSize=10).execute()
    files = res.get("files", [])
    if files:
        return files[0]["id"]

    metadata = {"name": folder_name, "mimeType": "application/vnd.google-apps.folder"}
    folder = service.files().create(body=metadata, fields="id").execute()
    return folder["id"]


def _iter_existing_paths(paths: Iterable[Path]) -> Iterable[Path]:
    for p in paths:
        try:
            if p and p.exists():
                yield p
        except Exception:
            continue


def _sqlite_checkpoint(db_path: Path) -> None:
    try:
        if db_path.exists():
            import sqlite3
            conn = sqlite3.connect(str(db_path))
            conn.execute("PRAGMA wal_checkpoint(FULL)")
            conn.close()
    except Exception as e:
        logger.warning("SQLite checkpoint skipped: %s", e)


def create_backup_zip(base_dir: Optional[Path] = None, db_path: Optional[Path] = None) -> Path:
    base_dir = Path(base_dir or os.getcwd()).resolve()
    db_path = Path(db_path) if db_path else base_dir / "trs_platform.db"
    if not db_path.is_absolute():
        db_path = base_dir / db_path

    _sqlite_checkpoint(db_path)

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    zip_path = BACKUP_DIR / f"trs_backup_{stamp}.zip"

    include_paths = list(_iter_existing_paths([
        db_path,
        base_dir / "uploads",
        base_dir / "equipment_data",
        base_dir / "equipment_library",
        base_dir / "data",
        base_dir / "logs",
    ]))

    # Include small operational config files when present, but never include OAuth secrets/tokens.
    optional_files = [base_dir / ".env", base_dir / "README.md", base_dir / "TRS_READY_START_HERE.txt"]
    include_paths.extend(list(_iter_existing_paths(optional_files)))

    exclude_names = {
        "google_drive_credentials.json",
        "google_drive_token.json",
        "client_secret.json",
    }

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        manifest = {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "source": str(base_dir),
            "included": [],
        }
        for p in include_paths:
            if p.is_file():
                if p.name in exclude_names or p.suffix.lower() == ".pyc":
                    continue
                arc = p.relative_to(base_dir) if p.is_relative_to(base_dir) else Path(p.name)
                z.write(p, arc.as_posix())
                manifest["included"].append(arc.as_posix())
            elif p.is_dir():
                for f in p.rglob("*"):
                    if not f.is_file():
                        continue
                    if f.name in exclude_names or f.suffix.lower() == ".pyc" or "__pycache__" in f.parts:
                        continue
                    try:
                        arc = f.relative_to(base_dir)
                    except ValueError:
                        arc = Path(p.name) / f.relative_to(p)
                    z.write(f, arc.as_posix())
                    manifest["included"].append(arc.as_posix())
        z.writestr("backup_manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))

    _cleanup_local_backups()
    return zip_path


def upload_backup_zip(zip_path: Path, interactive: bool = False) -> str:
    from googleapiclient.http import MediaFileUpload

    service = _service(interactive=interactive)
    folder_id = _find_or_create_folder(service)
    metadata = {"name": zip_path.name, "parents": [folder_id]}
    media = MediaFileUpload(str(zip_path), mimetype="application/zip", resumable=True)
    uploaded = service.files().create(body=metadata, media_body=media, fields="id,webViewLink,name").execute()
    logger.info("Google Drive backup uploaded: %s", uploaded.get("name"))
    _cleanup_drive_backups(service, folder_id)
    return uploaded.get("webViewLink") or uploaded.get("id")


def backup_once(base_dir: Optional[Path] = None, db_path: Optional[Path] = None, interactive: bool = False) -> str:
    zip_path = create_backup_zip(base_dir=base_dir, db_path=db_path)
    return upload_backup_zip(zip_path, interactive=interactive)


def setup_auth() -> None:
    service = _service(interactive=True)
    folder_id = _find_or_create_folder(service)
    logger.info("Google Drive OAuth setup complete. Backup folder id: %s", folder_id)


def _cleanup_local_backups() -> None:
    try:
        backups = sorted(BACKUP_DIR.glob("trs_backup_*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)
        for old in backups[MAX_LOCAL_BACKUPS:]:
            old.unlink(missing_ok=True)
    except Exception:
        pass


def _cleanup_drive_backups(service, folder_id: str) -> None:
    if DRIVE_KEEP_DAYS <= 0:
        return
    try:
        cutoff = (datetime.utcnow() - timedelta(days=DRIVE_KEEP_DAYS)).isoformat("T") + "Z"
        query = (
            f"'{folder_id}' in parents and name contains 'trs_backup_' "
            f"and mimeType='application/zip' and createdTime < '{cutoff}' and trashed=false"
        )
        res = service.files().list(q=query, fields="files(id,name,createdTime)", pageSize=1000).execute()
        for f in res.get("files", []):
            service.files().delete(fileId=f["id"]).execute()
    except Exception as e:
        logger.warning("Google Drive cleanup skipped: %s", e)


def start_daily_scheduler(base_dir: Optional[Path] = None, db_path: Optional[Path] = None) -> None:
    """Start lightweight background scheduler while the app process is running."""
    global _scheduler_started
    if not enabled():
        return
    with _scheduler_lock:
        if _scheduler_started:
            return
        _scheduler_started = True

    hour = int(os.getenv("TRS_BACKUP_HOUR", "2"))
    minute = int(os.getenv("TRS_BACKUP_MINUTE", "0"))
    base_dir = Path(base_dir or os.getcwd()).resolve()

    def loop():
        import time
        last_date = None
        logger.info("Google Drive daily backup scheduler active at %02d:%02d", hour, minute)
        while True:
            now = datetime.now()
            if now.hour == hour and now.minute == minute and last_date != now.date():
                try:
                    backup_once(base_dir=base_dir, db_path=db_path, interactive=False)
                    last_date = now.date()
                except Exception as e:
                    logger.warning("Google Drive scheduled backup failed: %s", e)
            time.sleep(30)

    t = threading.Thread(target=loop, daemon=True)
    t.start()
