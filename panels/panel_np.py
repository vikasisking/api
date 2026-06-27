# ============================================================
#  panels/panel_np.py  —  NP Panel (147.135.212.197/crapi/st)
#  Sirf is file ki values badlo, baaki kuch mat chhuo
# ============================================================

import requests
import html
import time
from urllib.parse import urlencode


# ============================================================
#  SECTION 1: PANEL IDENTITY
# ============================================================

PANEL_NAME    = "NPPanel"
PANEL_COMMAND = "np"          # Admin command banega: /panelnp on|off
POLL_INTERVAL = 5             # seconds


# ============================================================
#  SECTION 2: API SETTINGS
# ============================================================

API_BASE_URL = "http://147.135.212.197/crapi/st/viewstats"
API_TOKEN    = "RldXRUhBUzRJk3ZkQ3CGQopfeHtGh3JZXmqVhlaJmUqKjIxoaYx1hQ=="
API_RECORDS  = 200


# ============================================================
#  SECTION 3: fetch()
#  Response format: list of arrays — [cli, num, message, dt]
# ============================================================

def _build_url():
    params = {
        "token":   API_TOKEN,
        "records": str(API_RECORDS),
    }
    return API_BASE_URL + "?" + urlencode(params)


def fetch() -> list:
    url = _build_url()
    for attempt in range(1, 4):
        try:
            resp    = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
            payload = resp.json()

            # Response seedha list of arrays hai (no wrapper object)
            if isinstance(payload, list):
                print(f"✅ {PANEL_NAME}: {len(payload)} records", flush=True)
                return payload
            else:
                print(f"⚠️ {PANEL_NAME}: Unexpected response format", flush=True)
                return []

        except (requests.exceptions.ConnectionError,
                requests.exceptions.ChunkedEncodingError):
            time.sleep(attempt * 3)
        except Exception as e:
            print(f"❌ {PANEL_NAME} fetch error: {e}", flush=True)
            return []
    return []


# ============================================================
#  SECTION 4: parse_row()
#  Array format: [cli, num, message, dt]
#  Index:         [0]   [1]   [2]     [3]
# ============================================================

def parse_row(row):
    try:
        # Row ek list hai: [cli, num, message, dt]
        if not isinstance(row, (list, tuple)) or len(row) < 4:
            return None

        sender  = str(row[0] or "").strip()
        number  = str(row[1] or "").strip().lstrip("+").lstrip("0")
        message = str(row[2] or "").replace("\\n", "\n").replace("\\\\n", "\n")
        message = html.unescape(message).strip()
        dt      = str(row[3] or "").strip()

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
