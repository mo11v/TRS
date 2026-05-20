# Login Fix Notes

Fixed login rate limiter bug in `app.py`.

Default accounts:

- Admin: `admin` / `admin123`
- Field Operator: `operator` / `operator123`

Run:

```cmd
.venv\Scripts\activate.bat
pip install -r requirements.txt
uvicorn app:app --reload
```

Then open:

```text
http://127.0.0.1:8000
```
