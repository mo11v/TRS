# 🚀 TRS Platform — Free Deployment Guide

## Free Stack (كل حاجة مجانية 100%)

| Service | Purpose | Free Limit |
|---------|---------|-----------|
| **GitHub** | Code + auto-deploy | Unlimited private repos |
| **Render** | Server hosting | 750 hrs/month |
| **Firestore** | Database (persistent) | 1GB + 50K reads/day |
| **Cloudinary** | PDF storage | 25GB storage |

---

## Architecture

```
GitHub ──auto-deploy──→ Render (TRS Server)
                              │
                    ┌─────────┴──────────┐
                    ▼                    ▼
              Firestore              Cloudinary
          (Jobs, Devices,          (MTT PDFs,
           SCADA, Summary)          Reports)
                    ▲
         Mobile Bridge (4G)
                    ▲
              ESP32 v11 (AP)
                    ▲
               MTT Device
```

---

## STEP 1 — GitHub (2 دقيقة)

```bash
cd trs_platform
git init
git add .
git commit -m "TRS Platform v1.0"

# على github.com: New Repository → trs-platform (Private)
git remote add origin https://github.com/YOUR_USER/trs-platform.git
git push -u origin main
```

---

## STEP 2 — Firebase / Firestore (5 دقائق)

1. روح **https://console.firebase.google.com**
2. **Add project** → اسم: `trs-platform` → Continue
3. Disable Google Analytics → **Create project**
4. **Firestore Database** → Create database → **Start in production mode**
5. Region: `europe-west3` (Frankfurt)

### Service Account (للـ Render):
1. Project Settings ⚙️ → **Service accounts**
2. **Generate new private key** → Download JSON
3. افتح الـ JSON → انسخ **كل المحتوى**
4. على Render: `FIRESTORE_CREDENTIALS` = paste المحتوى كامل
5. `FIRESTORE_PROJECT_ID` = الـ project ID من Firebase

### Firestore Rules (Security):
```javascript
// Firestore → Rules → Edit:
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read, write: if false;  // server-only access
    }
  }
}
```

---

## STEP 3 — Cloudinary (3 دقائق)

1. روح **https://cloudinary.com** → Sign up free
2. Dashboard → بتلاقي:
   - **Cloud name**
   - **API Key**
   - **API Secret**
3. حطهم في Render env vars

---

## STEP 4 — Render (5 دقائق)

1. روح **https://render.com** → Sign up بـ GitHub
2. **New** → **Web Service**
3. اختار repo `trs-platform`
4. Render يقرأ `render.yaml` تلقائي ✅
5. في **Environment** → ضيف المتغيرات:

```
TRS_ADMIN_PASS        = TRS@2024!           (غيّره!)
TRS_ESP_KEY           = trs-esp-key-2026
FIRESTORE_PROJECT_ID  = trs-platform-xxxxx
FIRESTORE_CREDENTIALS = { ... JSON كامل ... }
CLOUDINARY_CLOUD_NAME = your_cloud
CLOUDINARY_API_KEY    = 123456789
CLOUDINARY_API_SECRET = AbCdEfGhIjK
```

6. **Deploy** → انتظر 3-5 دقائق

---

## STEP 5 — أول Login

```
URL:      https://trs-platform.onrender.com
Username: admin
Password: TRS@2024!  (أو اللي حطيته في TRS_ADMIN_PASS)
```

⚠️ غيّر الـ password من Settings بعد أول login

---

## STEP 6 — Mobile Bridge

افتح `trs_field_bridge.html` في Chrome:
```
TRS URL: https://trs-platform.onrender.com
API Key: trs-esp-key-2026
Device:  TRS-001
Job ID:  1
```

---

## STEP 7 — ESP32 v11

```
AP SSID:     TRS-FIELD-001
AP Password: trs12345
AP IP:       192.168.99.1

موبايل يتصل بـ: TRS-FIELD-001
Bridge يبعت لـ: https://trs-platform.onrender.com
```

---

## ⚠️ Free Tier Notes

| Issue | Solution |
|-------|----------|
| Render sleeps after 15min | Mobile bridge push كل ثانية يخليه صاحي |
| SQLite resets on restart | Firestore restore تلقائي عند startup |
| PDF files lost on restart | Cloudinary يحفظهم permanently |
| 512MB RAM | كافي — لا ML لا heavy processing |

---

## Monitoring (مجاني)

- **Render Logs**: Dashboard → Logs
- **Firestore Usage**: Firebase Console → Usage
- **Cloudinary Usage**: Dashboard → Reports
- **Health Check**: `GET https://trs-platform.onrender.com/api/status`

---

## Custom Domain (اختياري - مجاني)

Render بيديك domain مجاني: `trs-platform.onrender.com`

لو عايز domain خاص:
1. Cloudflare (مجاني) → Add site
2. Render → Settings → Custom Domain
3. ضيف CNAME record على Cloudflare
