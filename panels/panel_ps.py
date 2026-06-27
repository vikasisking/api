# ============================================================
#  panels/panel_ps.py  —  PSCall Panel (pscall.net)
#  Sirf is file ki values badlo, baaki kuch mat chhuo
# ============================================================

import requests
import html
import time
from urllib.parse import urlencode


# ============================================================
#  SECTION 1: PANEL IDENTITY
# ============================================================

PANEL_NAME    = "PSCall"
PANEL_COMMAND = "ps"          # Admin command banega: /panelps on|off
POLL_INTERVAL = 5             # seconds


# ============================================================
#  SECTION 2: API SETTINGS
# ============================================================

API_BASE_URL = "http://pscall.net/restapi/smsreport"
API_TOKEN    = "SFRRRz1SS3V2lIR9gI6Eg0NT"
API_RECORDS  = 200


# ============================================================
#  SECTION 3: fetch()
# ============================================================

def _build_url(searchnumber=""):
    params = {
        "key":     API_TOKEN,
        "start":   "0",
        "length":  str(API_RECORDS),
        "sortby":  "a.dateadded",
        "ascdesc": "desc",
    }
    if searchnumber:
        params["searchnumber"] = searchnumber
    return API_BASE_URL + "?" + urlencode(params)


def fetch() -> list:
    url = _build_url()
    for attempt in range(1, 4):
        try:
            resp    = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
            payload = resp.json()
            if payload.get("result") == "success":
                return payload.get("data", [])
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
        number  = str(row.get("num",      "") or "").strip().lstrip("+").lstrip("0")
        sender  = str(row.get("cli",      "") or "").strip()
        message = str(row.get("sms",      "") or "").replace("\\n", "\n").replace("\\\\n", "\n")
        message = html.unescape(message).strip()
        dt      = str(row.get("dateadded","") or "").strip()
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