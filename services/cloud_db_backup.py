"""
Cloud DB Backup for TRS Platform
--------------------------------
Keeps SQLite data persistent on ephemeral hosts like Render Free.
If Cloudinary env vars are configured, the local SQLite DB is restored
on startup and backed up automatically after write operations.
"""
import os
import time
import logging
import threading
from pathlib import Path

logger = logging.getLogger(__name__)

BACKUP_PUBLIC_ID = os.getenv("TRS_DB_BACKUP_PUBLIC_ID", "trs_persistence/trs_platform_db")
BACKUP_MIN_INTERVAL = int(os.getenv("TRS_DB_BACKUP_MIN_INTERVAL", "15"))
_enabled_cache = None
_timer = None
_lock = threading.Lock()
_last_backup = 0.0


def _cloudinary():
    cloud = os.getenv("CLOUDINARY_CLOUD_NAME")
    key = os.getenv("CLOUDINARY_API_KEY")
    secret = os.getenv("CLOUDINARY_API_SECRET")
    if not all([cloud, key, secret]):
        return None
    try:
        import cloudinary
        import cloudinary.uploader
        import cloudinary.api
        cloudinary.config(cloud_name=cloud, api_key=key, api_secret=secret, secure=True)
        return cloudinary
    except Exception as e:
        logger.warning("Cloud DB backup disabled: %s", e)
        return None


def enabled() -> bool:
    global _enabled_cache
    if _enabled_cache is None:
        _enabled_cache = _cloudinary() is not None and os.getenv("TRS_CLOUD_DB_BACKUP", "1") != "0"
    return bool(_enabled_cache)


def restore_db_from_cloud(db_path) -> bool:
    """Restore DB before init_db() if a cloud backup exists."""
    if not enabled():
        return False
    db_path = Path(db_path)
    cl = _cloudinary()
    if not cl:
        return False
    try:
        result = cl.api.resource(BACKUP_PUBLIC_ID, resource_type="raw")
        url = result.get("secure_url")
        if not url:
            return False
        import requests
        r = requests.get(url, timeout=30)
        if r.status_code != 200 or not r.content:
            logger.warning("Cloud DB restore failed: HTTP %s", r.status_code)
            return False
        db_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = db_path.with_suffix(".restore.tmp")
        tmp.write_bytes(r.content)
        # Basic SQLite signature check
        if not tmp.read_bytes()[:16].startswith(b"SQLite format 3"):
            tmp.unlink(missing_ok=True)
            logger.warning("Cloud DB restore skipped: invalid SQLite backup")
            return False
        tmp.replace(db_path)
        logger.info("Cloud DB restored from Cloudinary backup")
        return True
    except Exception as e:
        # Not found is fine on first run.
        logger.info("No cloud DB backup restored: %s", e)
        return False


def _backup_now(db_path):
    global _last_backup
    if not enabled():
        return False
    db_path = Path(db_path)
    if not db_path.exists() or db_path.stat().st_size == 0:
        return False
    cl = _cloudinary()
    if not cl:
        return False
    try:
        # Make SQLite checkpoint so WAL writes are included in main DB file.
        try:
            import sqlite3
            conn = sqlite3.connect(str(db_path))
            conn.execute("PRAGMA wal_checkpoint(FULL)")
            conn.close()
        except Exception:
            pass
        cl.uploader.upload(
            str(db_path),
            public_id=BACKUP_PUBLIC_ID,
            resource_type="raw",
            overwrite=True,
            invalidate=True,
            tags=["trs", "sqlite", "backup"],
        )
        _last_backup = time.time()
        logger.info("Cloud DB backup updated")
        return True
    except Exception as e:
        logger.warning("Cloud DB backup failed: %s", e)
        return False


def request_db_backup(db_path, delay: int = 3):
    """Debounced background backup after DB write operations."""
    global _timer
    if not enabled():
        return
    with _lock:
        if time.time() - _last_backup < BACKUP_MIN_INTERVAL:
            return
        if _timer and _timer.is_alive():
            _timer.cancel()
        _timer = threading.Timer(delay, _backup_now, args=(db_path,))
        _timer.daemon = True
        _timer.start()


def backup_now(db_path):
    return _backup_now(db_path)
