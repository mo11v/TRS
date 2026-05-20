# ⚙️ JAM Platform — Complete Setup Guide
### من الصفر للـ production في 20 دقيقة — كل حاجة مجانية

---

## 📋 القائمة الكاملة

- [ ] GitHub repo
- [ ] Firebase project + Firestore
- [ ] Cloudinary account
- [ ] Render deployment
- [ ] ESP32 v11 flash
- [ ] Mobile bridge test
- [ ] أول login وتغيير password

---

## ① GitHub (3 دقايق)

### على الكمبيوتر:
```bash
# في فولدر jam_platform
git init
git add .
git commit -m "TRS Platform v1.0 — initial"
```

### على github.com:
1. **+** → **New repository**
2. Name: `jam-platform`
3. Visibility: **Private** ✅
4. **Create repository**
5. انسخ الأوامر اللي بتظهر وشغّلها:
```bash
git remote add origin https://github.com/YOUR_USER/jam-platform.git
git branch -M main
git push -u origin main
```

✅ **تأكيد:** شوف الملفات على GitHub

---

## ② Firebase + Firestore (5 دقايق)

### على console.firebase.google.com:

1. **Add project** → Name: `jam-platform`
2. **Disable** Google Analytics → **Create project**
3. انتظر (~30 ثانية)

### Firestore Database:
1. من القائمة الجانبية: **Build → Firestore Database**
2. **Create database**
3. **Start in production mode** → Next
4. Location: **europe-west3 (Frankfurt)** → **Enable**

### Service Account (للـ Render):
1. ⚙️ **Project Settings** (أعلى يسار)
2. تبويب **Service accounts**
3. **Generate new private key** → **Generate key**
4. هينزل ملف JSON — **احتفظ بيه**
5. افتح الـ JSON → انسخ **كل المحتوى** (Ctrl+A → Ctrl+C)

### Firestore Rules (مهم للأمان):
1. **Firestore → Rules**
2. استبدل الـ rules بالآتي:
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read, write: if false;
    }
  }
}
```
3. **Publish**

### Project ID:
- من **Project Settings → General**
- انسخ **Project ID** (مثلاً: `jam-platform-a1b2c`)

---

## ③ Cloudinary (3 دقايق)

1. **cloudinary.com** → **Sign up for free**
2. بعد التسجيل → **Dashboard**
3. انسخ:
   - **Cloud name** (مثلاً: `dxyz123abc`)
   - **API Key** (مثلاً: `123456789012345`)
   - **API Secret** (مثلاً: `AbCdEfGhIjKlMnOpQrSt`)

---

## ④ Render Deployment (5 دقايق)

1. **render.com** → **Sign up with GitHub**
2. **New +** → **Web Service**
3. **Connect a repository** → اختار `jam-platform`
4. Render هيقرأ `render.yaml` تلقائي ✅
5. اضغط **Create Web Service**

### Environment Variables — الأهم:
في Render Dashboard → **Environment**:

| Key | Value |
|-----|-------|
| `TRS_ADMIN_PASS` | `TRS@2024!` (غيّره!) |
| `TRS_ESP_KEY` | `esp-jam-key-2024` |
| `FIRESTORE_PROJECT_ID` | Project ID من Firebase |
| `FIRESTORE_CREDENTIALS` | محتوى الـ JSON كامل |
| `CLOUDINARY_CLOUD_NAME` | Cloud name |
| `CLOUDINARY_API_KEY` | API Key |
| `CLOUDINARY_API_SECRET` | API Secret |

> ⚠️ `FIRESTORE_CREDENTIALS` → انسخ الـ JSON كاملاً بما فيه الـ `{ }` والـ newlines

6. **Save Changes** → Render هيعيد الـ deploy تلقائي

### تأكيد الـ Deploy:
```
GET https://jam-platform.onrender.com/api/status
```
المفروض ترجع:
```json
{
  "status": "ok",
  "db": "ok",
  "version": "1.0.0"
}
```

---

## ⑤ أول Login

```
URL:      https://jam-platform.onrender.com
Username: admin
Password: (القيمة في TRS_ADMIN_PASS)
```

### بعد الدخول مباشرة:
1. **Settings** → تأكد إن Firestore وCloudinary متصلين
2. **Devices** → Add Device → Code: `TRS-001`
3. **Jobs** → New Job → Job Number: `TRS-2024-001`

---

## ⑥ ESP32 v11 Flash

### Libraries المطلوبة (Arduino Library Manager):
- `LiquidCrystal_I2C` by Frank de Brabander
- `WebSockets` by Markus Sattler ← **جديد في v11**

### Upload:
1. افتح `smart_torque_monitor_esp32_v11.ino`
2. Board: **ESP32 Dev Module**
3. Upload Speed: **115200**
4. **Upload** ✅

### تأكيد:
```
LCD Row 0: STA: 192.168.10.70
LCD Row 1: AP:  192.168.99.1
```

---

## ⑦ Mobile Bridge Test

### على الموبايل:
1. **WiFi Settings** → اتصل بـ `TRS-FIELD-001` (pass: `trs12345`)
2. افتح `trs_field_bridge_v2.html` في Chrome
3. اضغط **🔌 Connect WS**
4. ادخل TRS URL: `https://jam-platform.onrender.com`
5. اضغط **▶ Start**

### الـ 3 dots المفروض يبقوا كلهم خضر:
```
ESP: ● Connected   JAM: ● OK   FS: ● Ready
```

---

## ⑧ Test End-to-End

```
MTT Device → UDP →
ESP32 v11  → LCD يعرض التورك →
               AP WiFi →
Moبايل      → Bridge يبعت →
               4G →
TRS Server  → يحفظ في Firestore + SQLite →
               WebSocket →
Browser     → SCADA Live يعرض real-time ✅
```

---

## 🔧 Troubleshooting

### Render لا يشتغل:
```bash
# Check logs في Render Dashboard → Logs
# أو:
curl https://jam-platform.onrender.com/api/status
```

### Firestore connection error:
- تأكد إن الـ JSON في `FIRESTORE_CREDENTIALS` صح
- تأكد مش في الـ JSON أي line breaks في أول أو آخر القيمة
- Test: Firebase Console → Firestore → بشوف collections اتعملت؟

### ESP32 مش بيتصل بـ MTT:
```
Serial Monitor → بيعرض "Scanning MTT..."
```
- تأكد إن الـ MTT WiFi شغال
- تأكد إن الـ password في الكود صح: `"mttgowifi"`

### الموبايل مش بيوصل ESP32:
- تأكد اتصلت بـ `TRS-FIELD-001` لا MTT WiFi
- الـ ESP32 IP هو `192.168.99.1`
- Test: `http://192.168.99.1/data` في متصفح الموبايل

---

## 📊 Monitoring

| Service | Dashboard |
|---------|-----------|
| TRS Server | `https://jam-platform.onrender.com` |
| Health | `https://jam-platform.onrender.com/api/status` |
| Render Logs | render.com → Dashboard → Logs |
| Firestore | console.firebase.google.com |
| Cloudinary | cloudinary.com/console |
| GitHub CI | github.com/YOUR_USER/jam-platform/actions |

---

## 💰 التكلفة = $0/month

| Service | Free Limit | استخدامك المتوقع |
|---------|-----------|-----------------|
| Render | 750 hrs/month | ~720 hrs ✅ |
| Firestore | 50K reads + 20K writes/day | ~5K writes/day ✅ |
| Cloudinary | 25GB storage | <1GB/month ✅ |
| GitHub | Unlimited private repos | ✅ |
