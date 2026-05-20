# TRS Platform — Cleanup + HPU 111470

## What was fixed
- Cleaned remaining old branding from the main UI and docs so the platform presents as **TRS Platform**.
- Changed default database name to `trs_platform.db`.
- Changed session cookie to `trs_session` while keeping backward compatibility with the older cookie.
- Updated default ESP bridge key to `trs-esp-key-2026`.
- Added the test equipment Excel file `111470.xlsx` under HPU.

## HPU sample included
The file is available in both locations:

```text
sample_data/equipment/HPU/111470.xlsx
uploads/equipment/HPU/111470.xlsx
```

On first run, the database seeds:

```text
Equipment Category: HPU
Equipment ID: 111470
Name: HPU 111470
```

The Excel file is imported into the Web Excel Editor automatically if the equipment cells are still empty.

## Login
```text
Username: admin
Password: admin123
```

## Run locally
```bash
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
uvicorn app:app --reload
```

Open:

```text
http://127.0.0.1:8000
```
