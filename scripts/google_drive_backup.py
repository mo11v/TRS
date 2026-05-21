import argparse
import logging
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.google_drive_backup import setup_auth, backup_once

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

parser = argparse.ArgumentParser(description="TRS Google Drive Backup")
parser.add_argument("--setup", action="store_true", help="First-time OAuth browser login")
parser.add_argument("--once", action="store_true", help="Create and upload one backup now")
parser.add_argument("--db", default=str(ROOT / "trs_platform.db"), help="SQLite DB path")
args = parser.parse_args()

if args.setup:
    setup_auth()
elif args.once:
    link = backup_once(base_dir=ROOT, db_path=Path(args.db), interactive=False)
    print("Backup uploaded:", link)
else:
    parser.print_help()
