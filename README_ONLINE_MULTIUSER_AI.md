# TRS Platform — Online + Multi-user Live Sync + AI Automation

## What was added

### Online deployment
- `/healthz` production health check.
- `Procfile` for Render/Railway style deployment.
- `railway.toml` and `fly.toml`.
- `deployment/docker-compose.production.yml` with persistent `/data` volume.
- Environment variables for DB, uploads, reports, secret key, and admin password.

### Multi-user live sync
- WebSocket presence per channel.
- `/api/realtime/status` for live connected clients/rooms.
- Broadcasts for Job Files, Equipment, Excel edits, and AI automation.
- Floating Live Sync status badge in the UI.

### AI automation
- `/ai-automation` page.
- `/api/ai-automation/run` endpoint.
- Detects and updates low-confidence Job File paths.
- Creates Equipment overdue/due-soon alerts.
- Detects missing Excel source files.
- Stores automation runs and notifications in database.

## Run locally
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
uvicorn app:app --reload
```

Open: http://127.0.0.1:8000

Login:
- username: `admin`
- password: `admin123`

## Deploy with Docker Compose
```bash
cd deployment
docker compose -f docker-compose.production.yml up -d --build
```

## Render/Railway
1. Push this folder to GitHub.
2. Create a Web Service from the repo.
3. Start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
4. Health check path: `/healthz`
5. Add environment variables:
   - `TRS_SECRET_KEY`
   - `TRS_ADMIN_PASS`
   - `TRS_DB_PATH=/data/trs_platform.db` if persistent disk is mounted
   - `TRS_UPLOADS=/data/uploads`
   - `TRS_REPORTS=/data/reports`

## Important production note
SQLite is okay for demo/internal MVP. For heavy multi-user production, move DB to PostgreSQL next.
