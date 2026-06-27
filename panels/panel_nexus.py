# ============================================================
#  panels/panel_nexus.py  —  Nexus CDR API Panel
#  Sirf SECTION 2 ki values badlo, baaki kuch mat chhuo
# ============================================================

import requests
import html
from datetime import datetime, timedelta


# ============================================================
#  SECTION 1: PANEL IDENTITY
# ============================================================

PANEL_NAME    = "NexusPanel"
PANEL_COMMAND = "nexus"
POLL_INTERVAL = 5


# ============================================================
#  SECTION 2: CONFIG  ← SIRF YAHAN BADLO
# ============================================================

API_TOKEN = "AGT-LULK6PKC"
BASE_URL  = "http://15.235.207.137/api/messages/cdr"
LIMIT     = 200


# ============================================================
#  SECTION 3: fetch()
# ============================================================

def fetch() -> list:
    try:
        now  = datetime.now()
        past = now - timedelta(seconds=90)

        headers = {
            "X-API-Token": API_TOKEN,
            "User-Agent":  "Mozilla/5.0"
        }
        params = {
            "startDate": past.strftime("%Y-%m-%d"),
            "endDate":   now.strftime("%Y-%m-%d"),
            "limit":     LIMIT,
        }

        resp = requests.get(BASE_URL, headers=headers, params=params, timeout=15)

        if resp.status_code != 200:
            print(f"⚠️ {PANEL_NAME}: HTTP {resp.status_code}", flush=True)
            return []

        try:
            payload = resp.json()
        except ValueError:
            print(f"⚠️ {PANEL_NAME}: Non-JSON: {resp.text[:100]}", flush=True)
            return []

        if isinstance(payload, dict) and "data" in payload:
            rows = payload["data"]
            if not isinstance(rows, list):
                return []
            rows = [r for r in rows if str(r.get("cause", "")).lower() == "success"]
            print(f"✅ {PANEL_NAME}: {len(rows)} records", flush=True)
            return rows

        print(f"⚠️ {PANEL_NAME}: Unexpected format: {str(payload)[:100]}", flush=True)
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
#  Nexus format:
#  {
#    "time":    "2026-06-25T08:06:19.456Z",  ← dt
#    "number":  "2250789578813",              ← num
#    "cllr":    "FACEBOOK",                  ← cli
#    "content": "53027 is your code...",      ← message
#    "cause":   "Success"
#  }
# ============================================================

def parse_row(row) -> dict | None:
    try:
        if not isinstance(row, dict):
            return None

        dt      = str(row.get("time",    "") or "").strip()
        number  = str(row.get("number",  "") or "").strip().lstrip("+")
        sender  = str(row.get("cllr",    "") or "Unknown").strip()
        message = str(row.get("content", "") or "").strip()

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

    except Exception as e:
        print(f"⚠️ {PANEL_NAME}: parse_row error: {e}", flush=True)
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
