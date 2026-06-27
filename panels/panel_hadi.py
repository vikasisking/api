# ============================================================
#  panels/panel_hadi.py  —  Hadi Panel (API Token Based)
#  Sirf SECTION 2 ki values badlo, baaki kuch mat chhuo
# ============================================================

import requests
import html
import time


# ============================================================
#  SECTION 1: PANEL IDENTITY
# ============================================================

PANEL_NAME    = "HadiPanel"
PANEL_COMMAND = "hadi"        # Admin command: /panelhadi on|off
POLL_INTERVAL = 5             # seconds


# ============================================================
#  SECTION 2: CONFIG  ← SIRF YAHAN BADLO
# ============================================================

API_TOKEN  = "RlVQQjRSQkJoVHdpaX-VeURWg3xzkphXRpNRV4aYU2peZo2Ii5dY"
BASE_URL   = "http://147.135.212.197/crapi/had/viewstats"

API_PARAMS = {
    "token":   API_TOKEN,
    "dt1":     "2026-01-01 00:00:00",
    "dt2":     "2099-12-31 23:59:59",
    "records": 200
}


# ============================================================
#  SECTION 3: fetch()
# ============================================================

def fetch() -> list:
    try:
        res = requests.get(BASE_URL, params=API_PARAMS, timeout=10)

        if not res.text.strip():
            print(f"⚠️ {PANEL_NAME}: Empty response — token invalid or server down", flush=True)
            return []

        try:
            data = res.json()
        except ValueError:
            print(f"⚠️ {PANEL_NAME}: Non-JSON response: {res.text[:100]}", flush=True)
            return []

        if data.get("status") == "error":
            print(f"⚠️ {PANEL_NAME}: API error: {data.get('msg', 'Unknown')}", flush=True)
            return []

        if data.get("status") == "success":
            rows = data.get("data", [])
            print(f"✅ {PANEL_NAME}: {len(rows)} records", flush=True)
            return rows

        print(f"⚠️ {PANEL_NAME}: Unexpected response status: {data.get('status')}", flush=True)
        return []

    except requests.exceptions.Timeout:
        print(f"⚠️ {PANEL_NAME}: Timeout", flush=True)
        return []
    except requests.exceptions.ConnectionError:
        print(f"⚠️ {PANEL_NAME}: Connection error", flush=True)
        return []
    except Exception as e:
        print(f"❌ {PANEL_NAME}: fetch error: {e}", flush=True)
        return []


# ============================================================
#  SECTION 4: parse_row()
#  Hadi API dict format: {num, cli, message, dt}
# ============================================================

def parse_row(row) -> dict | None:
    try:
        if not isinstance(row, dict):
            return None

        dt      = str(row.get("dt", "")).strip()
        number  = str(row.get("num", "")).strip().lstrip("+").lstrip("0")
        sender  = str(row.get("cli") or "Unknown").strip()
        message = str(row.get("message") or "").strip()

        message = message.replace("\\n", "\n").replace("\\\\n", "\n")
        message = html.unescape(message)

        if not number or number in ("0", ""):
            return None
        if not message:
            return None

        return {
            "dt":      dt,
            "num":     number,
            "cli":     sender,
            "message": message,
        }
    except Exception:
        return None


# ============================================================
#  INTERNAL — mat chhuo
# ============================================================

_enabled = True

def is_enabled() -> bool:
    return _enabled

def set_enabled(state: bool):
    global _enabled
    _enabled = state
