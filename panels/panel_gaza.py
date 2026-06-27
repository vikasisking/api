# ============================================================
#  panels/panel_gaza.py  —  Gaza / CR API Panel
#  Sirf is file ki values badlo, baaki kuch mat chhuo
# ============================================================

import requests
import html
import time
from urllib.parse import urlencode


# ============================================================
#  SECTION 1: PANEL IDENTITY
# ============================================================

PANEL_NAME    = "GazaPanel"
PANEL_COMMAND = "gaza"        # Admin command banega: /panelgaza on|off
POLL_INTERVAL = 5             # seconds


# ============================================================
#  SECTION 2: API SETTINGS
# ============================================================

API_BASE_URL = "http://51.77.216.195/crapi/gaza/viewstats"
API_TOKEN    = "RVdUNEVBgXuLU5BSfZaBQneLjlmLb2lzZFWGVGWGjmFmdVJGfmA="
API_RECORDS  = 200


# ============================================================
#  SECTION 3: fetch()
# ============================================================

def _build_url(searchnumber=""):
    params = {
        "token":   API_TOKEN,
        "records": str(API_RECORDS),
    }
    if searchnumber:
        params["filternum"] = searchnumber
    return API_BASE_URL + "?" + urlencode(params)


def fetch() -> list:
    url = _build_url()
    for attempt in range(1, 4):
        try:
            resp    = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
            payload = resp.json()
            if payload.get("status") == "success":
                records = payload.get("data", [])
                print(f"✅ {PANEL_NAME}: {len(records)} records", flush=True)
                return records
            else:
                return []
        except (requests.exceptions.ConnectionError,
                requests.exceptions.ChunkedEncodingError):
            time.sleep(attempt * 3)
        except Exception:
            return []
    return []


# ============================================================
#  SECTION 4: parse_row()
# ============================================================

def parse_row(row: dict):
    try:
        number  = str(row.get("num",     "") or "").strip().lstrip("+").lstrip("0")
        sender  = str(row.get("cli",     "") or "").strip()
        message = str(row.get("message", "") or "").replace("\\n", "\n").replace("\\\\n", "\n")
        message = html.unescape(message).strip()
        dt      = str(row.get("dt",      "") or "").strip()
        if not number or not message:
            return None
        return {"dt": dt, "num": number, "cli": sender, "message": message}
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