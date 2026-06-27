# HxOTP SMS API Server

Unified SMS API — saare panels ka data ek endpoint se.

---

## 📁 File Structure

```
hxotp_api/
├── api_server.py       ← Main Flask server
├── panel_loader.py     ← Auto panel loader
├── requirements.txt    ← Python dependencies
├── Procfile            ← Railway start command
└── panels/
    ├── panel_gaza.py
    ├── panel_green.py
    ├── panel_hadi.py
    ├── panel_konekta.py
    ├── panel_mbc.py
    ├── panel_nexus.py
    ├── panel_np.py
    ├── panel_ps.py
    └── panel_zone.py
```

---

## 🚂 Railway Deploy Steps

### Step 1 — GitHub repo banao
1. github.com pe new repo banao (private)
2. Is folder ki saari files upload karo

### Step 2 — Railway setup
1. railway.app pe jao → Login with GitHub
2. **New Project** → **Deploy from GitHub repo**
3. Apna repo select karo
4. Railway auto-detect karega `Procfile` aur deploy karega

### Step 3 — Environment Variables
Railway Dashboard → Variables tab → Add:
```
API_KEY = hxotp_secret_2025
```
(Ya jo bhi key rakhni ho)

### Step 4 — Domain milega
Railway ek URL dega:
```
https://yourapp.up.railway.app
```

---

## 🔌 API Endpoints

### All SMS (saare panels)
```
GET /api/sms?key=hxotp_secret_2025
```

### Ek panel ka SMS
```
GET /api/sms?key=hxotp_secret_2025&panel=gaza
GET /api/sms?key=hxotp_secret_2025&panel=nexus
GET /api/sms?key=hxotp_secret_2025&panel=green
```

### Number filter
```
GET /api/sms?key=hxotp_secret_2025&num=9199
```

### Limit
```
GET /api/sms?key=hxotp_secret_2025&limit=100
```

### Panel Status
```
GET /api/status?key=hxotp_secret_2025
```

### Health Check
```
GET /health
```

---

## 📦 Panels List

| Panel     | Command  | Poll |
|-----------|----------|------|
| Gaza/CR   | gaza     | 5s   |
| Hadi      | hadi     | 5s   |
| Konekta   | konekta  | 5s   |
| NP/ST     | np       | 5s   |
| PSCall    | ps       | 5s   |
| Zone      | zone     | 5s   |
| MBC       | mbc      | 5s   |
| Nexus CDR | nexus    | 5s   |
| Green SMS | green    | 30s  |

---

## ⚙️ Local Test (VPS/Termux)

```bash
pip install -r requirements.txt
python api_server.py
```

---

## 🐛 Bugs Fixed (from original)

1. `config.py` missing tha — `panel_loader.py` me hardcode kar diya
2. `HXOTP_DIR` wrong path tha — hata diya
3. `PORT` ab Railway env se aata hai
4. `API_KEY` ab env variable se aata hai
5. `/health` endpoint add kiya Railway ke liye
6. `gunicorn` add kiya production ke liye (Flask dev server nahi)
7. Error handlers (404, 500) add kiye
