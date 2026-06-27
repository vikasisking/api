# ============================================================
#  panels/panel_zone.py  —  Zone CR Panel (137.74.1.203)
#  Sirf SECTION 2 ki values badlo, baaki kuch mat chhuo
# ============================================================

import requests
import html
import time
from datetime import datetime, timedelta


# ============================================================
#  SECTION 1: PANEL IDENTITY
# ============================================================

PANEL_NAME    = "ZonePanel"
PANEL_COMMAND = "zone"        # Admin command: /panelzone on|off
POLL_INTERVAL = 5             # seconds


# ============================================================
#  SECTION 2: CONFIG  ← SIRF YAHAN BADLO
# ============================================================

API_TOKEN  = "Qk9TQkJVfkRGUA=="
BASE_URL   = "http://137.74.1.203/zonecr/reseller/mdr.php"
API_RECORDS = 20


# ============================================================
#  SECTION 3: fetch()
#  Zone API params: token, fromdate, todate, searchnumber,
#                   searchcli, records
# ============================================================

def fetch() -> list:
    try:
        now       = datetime.now()
        from_date = (now - timedelta(minutes=6000)).strftime("%Y-%m-%d %H:%M:%S")
        to_date   = now.strftime("%Y-%m-%d %H:%M:%S")

        params = {
            "token":        API_TOKEN,
            "fromdate":     from_date,
            "todate":       to_date,
            "searchnumber": "",
            "searchcli":    "",
            "records":      API_RECORDS,
        }

        res = requests.get(
            BASE_URL,
            params=params,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10
        )

        if not res.text.strip():
            print(f"⚠️ {PANEL_NAME}: Empty response", flush=True)
            return []

        try:
            data = res.json()
        except ValueError:
            print(f"⚠️ {PANEL_NAME}: Non-JSON response: {res.text[:100]}", flush=True)
            return []

        if data.get("status") != "Success":
            print(f"⚠️ {PANEL_NAME}: API status: {data.get('status')} | {data}", flush=True)
            return []

        rows = data.get("data", [])
        print(f"✅ {PANEL_NAME}: {len(rows)} records", flush=True)
        return rows

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
#  Zone API row format:
#    row["datetime"] = timestamp
#    row["number"]   = phone number
#    row["cli"]      = sender / service name
#    row["message"]  = SMS body
# ============================================================

def parse_row(row) -> dict | None:
    try:
        if not isinstance(row, dict):
            return None

        dt      = str(row.get("datetime", "") or "").strip()
        number  = str(row.get("number",   "") or "").strip().lstrip("+").lstrip("0")
        sender  = str(row.get("cli",      "") or "Unknown").strip()
        message = str(row.get("message",  "") or "").strip()

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
