"""
TRS Platform — Cloudinary Service
===================================
Free PDF & file storage — 25GB free tier

Use Cases:
  - MTT PDF uploads → stored on Cloudinary
  - Generated reports → stored + URL returned
  - No need for local disk on Render

Free Tier:
  - 25 GB storage
  - 25 GB bandwidth/month
  - Transformations included
  - مجاني تماماً

Setup:
  1. cloudinary.com → Sign up free
  2. Dashboard → API Keys
  3. Set env vars:
     CLOUDINARY_CLOUD_NAME=your_cloud
     CLOUDINARY_API_KEY=your_key
     CLOUDINARY_API_SECRET=your_secret
"""

import os
import io
import logging
import base64
from typing import Optional

logger = logging.getLogger(__name__)

CLOUDINARY_ENABLED = False
_cloudinary = None


def _get_cloudinary():
    global _cloudinary, CLOUDINARY_ENABLED
    if _cloudinary is not None:
        return _cloudinary
    cloud = os.getenv("CLOUDINARY_CLOUD_NAME")
    key   = os.getenv("CLOUDINARY_API_KEY")
    secret= os.getenv("CLOUDINARY_API_SECRET")
    if not all([cloud, key, secret]):
        logger.info("Cloudinary not configured — using DB blob storage")
        return None
    try:
        import cloudinary
        import cloudinary.uploader
        import cloudinary.api
        cloudinary.config(
            cloud_name=cloud,
            api_key=key,
            api_secret=secret,
            secure=True,
        )
        _cloudinary = cloudinary
        CLOUDINARY_ENABLED = True
        logger.info(f"Cloudinary connected — cloud: {cloud}")
        return _cloudinary
    except ImportError:
        logger.warning("cloudinary package not installed — pip install cloudinary")
        return None
    except Exception as e:
        logger.error(f"Cloudinary init failed: {e}")
        return None


def cl_enabled() -> bool:
    return _get_cloudinary() is not None


# ════════════════════════════════════════════════════════
#  UPLOAD
# ════════════════════════════════════════════════════════

def upload_pdf(
    pdf_bytes: bytes,
    public_id: str,
    folder: str = "trs_mtt",
) -> Optional[str]:
    """
    Upload PDF to Cloudinary.
    Returns secure URL or None on failure.

    public_id example: "job_42_mtt_report"
    """
    cl = _get_cloudinary()
    if not cl:
        return None
    try:
        result = cl.uploader.upload(
            pdf_bytes,
            public_id=f"{folder}/{public_id}",
            resource_type="raw",
            format="pdf",
            overwrite=True,
            tags=["trs", "mtt", folder],
        )
        url = result.get("secure_url")
        logger.info(f"Cloudinary upload OK: {url}")
        return url
    except Exception as e:
        logger.error(f"Cloudinary upload failed: {e}")
        return None


def upload_report_pdf(
    pdf_bytes: bytes,
    job_number: str,
    mode: str = "flagged",
) -> Optional[str]:
    """Upload a generated TRS report PDF."""
    safe_job = job_number.replace("/", "_").replace(" ", "_")
    public_id = f"report_{safe_job}_{mode}"
    return upload_pdf(pdf_bytes, public_id, folder="trs_reports")


def upload_mtt_original(
    pdf_bytes: bytes,
    job_id: int,
    filename: str = "",
) -> Optional[str]:
    """Upload original MTT PDF (for graph extraction later)."""
    public_id = f"mtt_original_job{job_id}"
    return upload_pdf(pdf_bytes, public_id, folder="trs_mtt_originals")


# ════════════════════════════════════════════════════════
#  DOWNLOAD / FETCH
# ════════════════════════════════════════════════════════

def fetch_pdf(url: str) -> Optional[bytes]:
    """
    Download PDF bytes from Cloudinary URL.
    Used for graph extraction from stored MTT PDFs.
    """
    if not url:
        return None
    try:
        import httpx
        resp = httpx.get(url, timeout=15)
        if resp.status_code == 200:
            return resp.content
        logger.warning(f"Cloudinary fetch {resp.status_code}: {url}")
        return None
    except Exception as e:
        logger.error(f"Cloudinary fetch failed: {e}")
        return None


# ════════════════════════════════════════════════════════
#  DELETE
# ════════════════════════════════════════════════════════

def delete_file(public_id: str, resource_type: str = "raw") -> bool:
    cl = _get_cloudinary()
    if not cl:
        return False
    try:
        cl.uploader.destroy(public_id, resource_type=resource_type)
        return True
    except Exception as e:
        logger.warning(f"Cloudinary delete failed: {e}")
        return False


# ════════════════════════════════════════════════════════
#  LIST
# ════════════════════════════════════════════════════════

def list_job_files(job_id: int) -> list:
    """List all Cloudinary files for a job."""
    cl = _get_cloudinary()
    if not cl:
        return []
    try:
        result = cl.api.resources(
            type="upload",
            prefix=f"trs_mtt/job{job_id}",
            resource_type="raw",
        )
        return result.get("resources", [])
    except Exception as e:
        logger.warning(f"Cloudinary list failed: {e}")
        return []


# ════════════════════════════════════════════════════════
#  USAGE STATS
# ════════════════════════════════════════════════════════

def get_usage() -> dict:
    """Get Cloudinary storage usage."""
    cl = _get_cloudinary()
    if not cl:
        return {}
    try:
        result = cl.api.usage()
        return {
            "storage_gb": round(result.get("storage", {}).get("usage", 0) / 1e9, 3),
            "bandwidth_gb": round(result.get("bandwidth", {}).get("usage", 0) / 1e9, 3),
            "resources": result.get("resources", 0),
        }
    except Exception as e:
        logger.warning(f"Cloudinary usage failed: {e}")
        return {}
