# TRS Platform
### Job Files · Equipment · Torque Analysis

---

## 🚀 Quick Start

```bash
cd trs_platform
pip install -r requirements.txt
python app.py
# Open: http://localhost:8000
# Login: admin / admin123
```

---

## 🏗️ Project Structure

```
trs_platform/
├── app.py                    ← Main FastAPI app (all routes)
├── requirements.txt
├── config/
│   └── settings.py           ← Environment config
├── database/
│   └── db.py                 ← SQLite schema + helpers
├── services/
│   ├── auth_service.py       ← bcrypt + session + rate limiting
│   ├── rbac.py               ← Role Based Access Control ✨
│   ├── mtt_parser.py         ← MTT PDF parser
│   ├── mtt_csv_parser.py     ← MTT CSV parser
│   ├── graph_extractor.py    ← Graph extraction from PDF
│   ├── job_analysis_pdf.py   ← Report PDF generation
│   └── ai_insights_service.py← AI analysis engine
└── templates/
    ├── base.html             ← Sidebar + layout (RBAC-aware nav)
    ├── login.html
    ├── dashboard.html        ← Role-aware dashboard ✨
    ├── jobs.html
    ├── job_detail.html       ← MTT upload + charts
    ├── analysis.html         ← Full joint analysis
    ├── fleet.html            ← Fleet comparison
    ├── ai.html               ← AI insights
    ├── scada.html            ← Live SCADA monitoring
    ├── devices.html
    ├── device_detail.html
    ├── users.html            ← User management
    └── settings.html
```

---

## 🔐 Role System

| Role       | Access |
|------------|--------|
| **Admin**      | Full — users, settings, all data |
| **Manager**    | Operations — no user management |
| **Engineer**   | Analysis + AI + Reports + Upload |
| **Supervisor** | View + Upload + Limited analysis |
| **Operator**   | Upload MTT + SCADA + Own jobs |

### Default Login
- **Username:** `admin`
- **Password:** `admin123`

---

## 📡 API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| POST | `/api/upload-mtt/{job_id}` | Upload MTT PDF/CSV |
| POST | `/api/ai/analyze/{job_id}` | Run AI analysis |
| POST | `/api/scada/push` | Push live reading |
| GET  | `/api/scada/latest` | Get live readings |
| GET  | `/api/jobs/{id}/report` | Download PDF report |
| GET  | `/api/status` | Platform health check |

---

## ⚙️ Environment Variables

```env
TRS_DB_PATH=trs_platform.db
TRS_UPLOADS=uploads/
TRS_REPORTS=reports/
TRS_SECRET_KEY=your-secret-key-here
TRS_ADMIN_PASS=admin123
TRS_SESSION_HOURS=12
TRS_MAX_UPLOAD_MB=60
```

---

## 🔧 Production Deployment

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 2
```

Or with `systemd` / `supervisor` on Windows Server.
