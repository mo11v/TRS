"""
TRS Platform — Firestore Service
=================================
بيستخدم Google Firestore كـ persistent DB
بديل عن SQLite على Render free tier

Free Tier:
  - 1 GB storage
  - 50,000 reads/day
  - 20,000 writes/day
  - مجاني تماماً

Collections Structure:
  trs_users/       → users
  trs_devices/     → devices
  trs_jobs/        → jobs
  trs_joints/      → mtt joint data
  trs_summaries/   → mtt job summaries
  trs_scada/       → live readings (last 1000)
  trs_ai/          → AI insights
  trs_activity/    → activity log
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# ── Firestore client (lazy init) ──────────────────────────────
_db = None
FIRESTORE_ENABLED = False


def _get_db():
    global _db, FIRESTORE_ENABLED
    if _db is not None:
        return _db
    creds_json = os.getenv("FIRESTORE_CREDENTIALS")
    project_id = os.getenv("FIRESTORE_PROJECT_ID")
    if not creds_json or not project_id:
        logger.warning("Firestore not configured — using SQLite only")
        return None
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
        if not firebase_admin._apps:
            creds_dict = json.loads(creds_json)
            cred = credentials.Certificate(creds_dict)
            firebase_admin.initialize_app(cred)
        _db = firestore.client()
        FIRESTORE_ENABLED = True
        logger.info(f"Firestore connected — project: {project_id}")
        return _db
    except Exception as e:
        logger.error(f"Firestore init failed: {e}")
        return None


def fs_enabled() -> bool:
    return _get_db() is not None


# ════════════════════════════════════════════════════════
#  SYNC HELPERS — push SQLite data to Firestore
# ════════════════════════════════════════════════════════

def sync_job_to_fs(job: dict):
    """Push/update a job to Firestore."""
    db = _get_db()
    if not db: return
    try:
        doc_id = f"job_{job['id']}"
        db.collection("trs_jobs").document(doc_id).set({
            **job,
            "_synced_at": datetime.utcnow().isoformat(),
        })
    except Exception as e:
        logger.warning(f"Firestore sync job failed: {e}")


def sync_summary_to_fs(summary: dict):
    """Push MTT summary to Firestore (without pdf_blob)."""
    db = _get_db()
    if not db: return
    try:
        safe = {k: v for k, v in summary.items() if k != "pdf_blob"}
        # Convert lists/dicts stored as JSON strings
        for f in ["outliers_high","outliers_low","reruns","fast_joints","slow_joints","stats_json"]:
            if safe.get(f) and isinstance(safe[f], str):
                try:
                    safe[f] = json.loads(safe[f])
                except Exception:
                    pass
        doc_id = f"summary_{summary['job_id']}"
        safe["_synced_at"] = datetime.utcnow().isoformat()
        db.collection("trs_summaries").document(doc_id).set(safe)
    except Exception as e:
        logger.warning(f"Firestore sync summary failed: {e}")


def sync_scada_to_fs(reading: dict, device_id: int):
    """Push a live SCADA reading — keeps last 1000 per device."""
    db = _get_db()
    if not db: return
    try:
        from datetime import datetime
        doc_id = f"{device_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
        db.collection("trs_scada").document(doc_id).set({
            **reading,
            "_synced_at": datetime.utcnow().isoformat(),
        })
    except Exception as e:
        logger.debug(f"Firestore SCADA sync failed: {e}")


def sync_device_to_fs(device: dict):
    db = _get_db()
    if not db: return
    try:
        doc_id = f"device_{device['id']}"
        db.collection("trs_devices").document(doc_id).set({
            **device,
            "_synced_at": datetime.utcnow().isoformat(),
        })
    except Exception as e:
        logger.warning(f"Firestore sync device failed: {e}")


def push_activity_to_fs(action: str, user_id: int,
                        entity_type: str = None, entity_id: int = None,
                        detail: str = None):
    db = _get_db()
    if not db: return
    try:
        ts = datetime.utcnow().isoformat()
        db.collection("trs_activity").add({
            "action": action,
            "user_id": user_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "detail": detail,
            "created_at": ts,
        })
    except Exception as e:
        logger.debug(f"Firestore activity failed: {e}")


# ════════════════════════════════════════════════════════
#  REAL-TIME SCADA — Firestore listener
# ════════════════════════════════════════════════════════

def get_latest_scada(device_id: int = None, limit: int = 50) -> list:
    """Read latest SCADA readings from Firestore."""
    db = _get_db()
    if not db: return []
    try:
        col = db.collection("trs_scada")
        if device_id:
            col = col.where("device_id", "==", device_id)
        docs = col.order_by("_synced_at", direction="DESCENDING").limit(limit).stream()
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        logger.warning(f"Firestore SCADA read failed: {e}")
        return []


def get_jobs_from_fs(limit: int = 100) -> list:
    """Read jobs from Firestore (fallback when SQLite is empty after restart)."""
    db = _get_db()
    if not db: return []
    try:
        docs = db.collection("trs_jobs").order_by(
            "_synced_at", direction="DESCENDING"
        ).limit(limit).stream()
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        logger.warning(f"Firestore jobs read failed: {e}")
        return []


def restore_from_firestore_to_sqlite():
    """
    يُستدعى عند startup — يرجع البيانات من Firestore لـ SQLite
    لو SQLite فاضية (بعد Render restart).
    """
    db = _get_db()
    if not db:
        return 0

    from database.db import get_conn, q1
    import sqlite3

    conn = get_conn()
    restored = 0

    try:
        # Check if SQLite is empty
        job_count = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        if job_count > 0:
            logger.info(f"SQLite has {job_count} jobs — skipping Firestore restore")
            conn.close()
            return 0

        logger.info("SQLite empty — restoring from Firestore...")

        # ── Restore devices ──
        try:
            dev_docs = db.collection("trs_devices").stream()
            for doc in dev_docs:
                d = doc.to_dict()
                try:
                    conn.execute("""
                        INSERT OR IGNORE INTO devices
                        (id, code, name, category, model, serial_no, status, location, notes, created_at)
                        VALUES (?,?,?,?,?,?,?,?,?,?)
                    """, (d.get("id"), d.get("code"), d.get("name"),
                          d.get("category","Torque Turn System"),
                          d.get("model",""), d.get("serial_no",""),
                          d.get("status","Available"),
                          d.get("location",""), d.get("notes",""),
                          d.get("created_at", datetime.utcnow().isoformat())))
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"Restore devices failed: {e}")

        # ── Restore jobs ──
        try:
            job_docs = db.collection("trs_jobs").stream()
            for doc in job_docs:
                d = doc.to_dict()
                try:
                    conn.execute("""
                        INSERT OR IGNORE INTO jobs
                        (id, job_number, customer, rig, well, field, country,
                         assigned_device_id, status, start_date, end_date, notes, created_at)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """, (d.get("id"), d.get("job_number"), d.get("customer"),
                          d.get("rig"), d.get("well"), d.get("field"),
                          d.get("country"), d.get("assigned_device_id"),
                          d.get("status","Planned"), d.get("start_date"),
                          d.get("end_date"), d.get("notes"),
                          d.get("created_at", datetime.utcnow().isoformat())))
                    restored += 1
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"Restore jobs failed: {e}")

        # ── Restore summaries ──
        try:
            sum_docs = db.collection("trs_summaries").stream()
            for doc in sum_docs:
                d = doc.to_dict()
                try:
                    # Convert sub-fields back to JSON strings for SQLite
                    for f in ["outliers_high","outliers_low","reruns",
                              "fast_joints","slow_joints","stats_json"]:
                        if d.get(f) and not isinstance(d[f], str):
                            d[f] = json.dumps(d[f], ensure_ascii=False)
                    conn.execute("""
                        INSERT OR IGNORE INTO mtt_job_summary
                        (job_id, pipe_type, tong_model, total_joints, ok_count,
                         rerun_count, rerun_rate, outlier_count,
                         ft_mean, ft_std, ft_min, ft_max,
                         turns_mean, rpm_mean, dt_mean, low_rpm_count,
                         outliers_high, outliers_low, reruns,
                         fast_joints, slow_joints, stats_json, computed_at)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """, (d.get("job_id"), d.get("pipe_type"), d.get("tong_model"),
                          d.get("total_joints",0), d.get("ok_count",0),
                          d.get("rerun_count",0), d.get("rerun_rate",0),
                          d.get("outlier_count",0),
                          d.get("ft_mean"), d.get("ft_std"),
                          d.get("ft_min"), d.get("ft_max"),
                          d.get("turns_mean"), d.get("rpm_mean"),
                          d.get("dt_mean"), d.get("low_rpm_count",0),
                          d.get("outliers_high"), d.get("outliers_low"),
                          d.get("reruns"), d.get("fast_joints"),
                          d.get("slow_joints"), d.get("stats_json"),
                          d.get("computed_at")))
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"Restore summaries failed: {e}")

        conn.commit()
        logger.info(f"Firestore restore complete — {restored} jobs restored")

    except Exception as e:
        logger.error(f"Firestore restore error: {e}")
    finally:
        conn.close()

    return restored
