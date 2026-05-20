# TRS UI Fixes

Applied changes:
- Replaced yellow primary theme with teal/cyan industrial theme.
- Dashboard sidebar cleaned: Dashboard is alone in Overview; Quick Start moved under Support.
- Fixed Activity Log crash caused by unsupported Jinja `contains` test.
- Equipment Maintenance detail page no longer stretches horizontally.
- Live Excel editor opens in a wide `Live Sync` modal instead of forcing the whole page to scroll.
- Restored latest `111470.xlsx` sample under `sample_data/equipment/HPU/` and `uploads/equipment/HPU/`.

Run as usual:
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
uvicorn app:app --reload
```
