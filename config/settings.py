"""
TRS Platform
Settings & Configuration
"""
import os
from pathlib import Path

BASE_DIR    = Path(__file__).resolve().parent.parent
DB_PATH     = Path(os.getenv("TRS_DB_PATH",   str(BASE_DIR / "trs_platform.db")))
UPLOADS_DIR = Path(os.getenv("TRS_UPLOADS",   str(BASE_DIR / "uploads")))
REPORTS_DIR = Path(os.getenv("TRS_REPORTS",   str(BASE_DIR / "reports")))

APP_NAME    = "TRS Platform — Job Files + Equipment + Torque Analysis"
APP_VERSION = "1.9.0-trs-final-mvp"

SECRET_KEY     = os.getenv("TRS_SECRET_KEY",   "trs-dev-secret-change-in-prod")
ADMIN_INIT_PASS= os.getenv("TRS_ADMIN_PASS",   "admin123")
SESSION_HOURS  = int(os.getenv("TRS_SESSION_HOURS", "12"))
MAX_UPLOAD_MB  = int(os.getenv("TRS_MAX_UPLOAD_MB",  "60"))

# Equipment categories for TRS devices
DEVICE_CATEGORIES = [
    "Torque Turn System",
    "Power Tongs",
    "Data Acquisition Unit",
    "Hydraulic Power Unit",
    "TRS Unit",
    "Other",
]

USER_ROLES  = ["Operator", "Supervisor", "Engineer", "Manager", "Admin"]
JOB_STATUSES = ["Planned", "Active", "Completed", "Cancelled", "On Hold"]
DEVICE_STATUSES = ["Available", "In Job", "Maintenance", "Out of Service", "Offline"]

PIPE_TYPES = [
    "Casing", "Tubing", "Drill Pipe", "OCTG", "Liner", "Other"
]
