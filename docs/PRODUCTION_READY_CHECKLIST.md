# TRS Platform — Production Checklist

## جاهز داخل الباكدج
- Login + roles foundation.
- Job Files: companies/year/rig/connection, upload, preview, search, folder/ZIP import.
- Equipment Maintenance: equipment list, Excel import from folder ZIP, web spreadsheet editor, export Excel.
- WebSocket real-time notifications for uploads, moves, equipment edits, and sheet saves.
- Activity log foundation.
- Dockerfile, Render config, docker-compose, health endpoint.
- Backup script.
- Smoke test script.

## مطلوب منك قبل الرفع النهائي
1. املأ `.env` من `.env.example`.
2. حط Cloudinary keys لو عايز تخزين PDFs خارج السيرفر.
3. حط Firebase service account لو عايز restore/sync إضافي.
4. ارفع فولدر HPU الحقيقي ZIP لاختبار importer.
5. ارفع PDF reports حقيقية لتحسين Auto Detect.

## تشغيل محلي سريع
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
```

## Docker
```bash
cp .env.example .env
cd deployment
docker compose up --build
```

## Smoke Test
```bash
python scripts/smoke_test.py
```

## Deploy على Render
- ادفع المشروع إلى GitHub.
- اعمل New Blueprint على Render واختر `render.yaml`.
- راجع Environment Variables.
- افتح `/api/status` بعد الرفع.
