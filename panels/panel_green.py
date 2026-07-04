# ============================================================
#  panels/panel_green.py  —  Green SMS Panel (Session Login)
#  Sirf SECTION 2 ki values badlo, baaki kuch mat chhuo
# ============================================================

import requests
import html
import re
import time
import hashlib
from datetime import datetime
from bs4 import BeautifulSoup


# ============================================================
#  SECTION 1: PANEL IDENTITY
# ============================================================

PANEL_NAME    = "green"
PANEL_COMMAND = "green"        # Admin command: /panelgreen on|off
POLL_INTERVAL = 30             # seconds


# ============================================================
#  SECTION 2: CONFIG  ← SIRF YAHAN BADLO
# ============================================================

USERNAME   = "alexdevil899"
PASSWORD   = "alexdevil899"
BASE_URL   = "http://139.99.9.4/ints"


# ============================================================
#  SECTION 3: INTERNAL URLs  —  mat chhuo
# ============================================================

_LOGIN_PAGE  = f"{BASE_URL}/login"
_LOGIN_POST  = f"{BASE_URL}/signin"
_REPORTS_URL = f"{BASE_URL}/agent/SMSCDRReports"
_AJAX_URL    = f"{BASE_URL}/agent/res/data_smscdr.php"

_DATE_FROM  = "2026-01-01 00:00:00"
_DATE_TO    = "2099-12-31 23:59:59"
_BATCH_SIZE = 500

# Column indexes
_COL_DATE   = 0
_COL_NUMBER = 2
_COL_RANGE  = 1
_COL_CLI    = 3
_COL_SMS    = 5

_session   = requests.Session()
_logged_in = False
_sesskey   = None

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}


# ============================================================
#  SECTION 4: LOGIN HELPERS  —  mat chhuo
# ============================================================

def _solve_captcha(html_text: str) -> str:
    try:
        text = BeautifulSoup(html_text, "html.parser").get_text(" ")
    except Exception:
        text = html_text

    for pat in [
        r'[Ww]hat\s+is\s+(\d+)\s*([+\-*x×÷/])\s*(\d+)',
        r'(\d+)\s*([+\-*x×÷/])\s*(\d+)\s*=',
    ]:
        m = re.search(pat, text)
        if m:
            a, op, b = int(m.group(1)), m.group(2), int(m.group(3))
            if op == '+':                result = a + b
            elif op == '-':              result = a - b
            elif op in ('*', 'x', '×'): result = a * b
            elif op in ('/', '÷'):       result = a // b if b else 0
            else:                        result = a + b
            print(f"✅ {PANEL_NAME}: Captcha {a} {op} {b} = {result}", flush=True)
            return str(result)
    return "0"


def _refresh_sesskey():
    global _sesskey
    try:
        r = _session.get(_REPORTS_URL, timeout=20)
        for script in BeautifulSoup(r.text, "html.parser").find_all("script"):
            c = script.string or ""
            m = re.search(r'sesskey=([A-Za-z0-9+/=]+)', c)
            if m:
                _sesskey = m.group(1)
                print(f"✅ {PANEL_NAME}: sesskey refreshed", flush=True)
                return
    except Exception as e:
        print(f"⚠️ {PANEL_NAME}: sesskey refresh failed: {e}", flush=True)


def _login(retries=3, delay=3) -> bool:
    global _logged_in, _sesskey

    for attempt in range(1, retries + 1):
        try:
            _session.headers.update(_HEADERS)
            r = _session.get(_LOGIN_PAGE, timeout=20)
            r.raise_for_status()

            captcha = _solve_captcha(r.text)

            resp = _session.post(
                _LOGIN_POST,
                data={"username": USERNAME, "password": PASSWORD, "capt": captcha},
                timeout=20,
                allow_redirects=True
            )
            resp.raise_for_status()

            url_str = str(resp.url).lower()
            body    = resp.text.lower()

            if any(w in url_str for w in ("agent", "dashboard", "report")):
                print(f"✅ {PANEL_NAME}: Login SUCCESS", flush=True)
                _logged_in = True
                _refresh_sesskey()
                return True

            if any(w in body for w in ("invalid", "wrong", "incorrect")):
                print(f"⚠️ {PANEL_NAME}: Login rejected (try {attempt})", flush=True)
            elif any(w in url_str for w in ("signin", "login")):
                print(f"⚠️ {PANEL_NAME}: Still on login page (try {attempt})", flush=True)
            else:
                # assume OK
                print(f"✅ {PANEL_NAME}: Login assumed OK", flush=True)
                _logged_in = True
                _refresh_sesskey()
                return True

        except Exception as e:
            print(f"⚠️ {PANEL_NAME}: Login error (try {attempt}): {e}", flush=True)

        time.sleep(delay)

    print(f"❌ {PANEL_NAME}: All login attempts failed", flush=True)
    _logged_in = False
    return False


def _ajax_fetch(start=0, length=None) -> dict | None:
    length = length or _BATCH_SIZE
    params = {
        "fdate1": _DATE_FROM, "fdate2": _DATE_TO,
        "frange": "", "fclient": "", "fnum": "", "fcli": "",
        "fgdate": "", "fgmonth": "", "fgrange": "", "fgclient": "",
        "fgnumber": "", "fgcli": "", "fg": "0",
        "sesskey":        _sesskey or "",
        "iDisplayStart":  str(start),
        "iDisplayLength": str(length),
        "sEcho":          "1",
        "iSortCol_0":     "0",
        "sSortDir_0":     "desc",
    }
    try:
        r = _session.get(
            _AJAX_URL,
            params=params,
            headers={
                **_HEADERS,
                "Referer":           _REPORTS_URL,
                "X-Requested-With":  "XMLHttpRequest"
            },
            timeout=30
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"❌ {PANEL_NAME}: AJAX error: {e}", flush=True)
        return None


# ============================================================
#  SECTION 5: fetch()
# ============================================================

def fetch() -> list:
    global _logged_in

    if not _logged_in:
        if not _login():
            return []

    data = _ajax_fetch(start=0, length=_BATCH_SIZE)

    # session expire ho gayi
    if data is None:
        print(f"⚠️ {PANEL_NAME}: Session expired, re-login...", flush=True)
        _logged_in = False
        if not _login():
            return []
        data = _ajax_fetch(start=0, length=_BATCH_SIZE)
        if data is None:
            return []

    total = int(data.get("iTotalRecords", 0))
    rows  = data.get("aaData", [])
    offset = len(rows)

    # pagination — baaki records bhi fetch karo
    while offset < total:
        more = _ajax_fetch(start=offset, length=_BATCH_SIZE)
        if not more:
            break
        chunk = more.get("aaData", [])
        if not chunk:
            break
        rows.extend(chunk)
        offset += len(chunk)

    # sirf valid date wale rows
    DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}')
    valid = [r for r in rows if r and DATE_RE.match(str(r[_COL_DATE] or ""))]

    print(f"✅ {PANEL_NAME}: {len(valid)} records", flush=True)
    return valid


# ============================================================
#  SECTION 6: parse_row()
#  Green panel list format: [date, ?, number, ?, range, ?, cli, ?, ?, ?, sms, ...]
# ============================================================

def parse_row(row) -> dict | None:
    try:
        if not isinstance(row, list) or len(row) <= _COL_SMS:
            return None

        dt      = str(row[_COL_DATE]   or "").strip()
        number  = str(row[_COL_NUMBER] or "").strip().lstrip("+")
        range_  = str(row[_COL_RANGE]  or "").strip()
        sender  = str(row[_COL_CLI]    or "Unknown").strip()
        message = str(row[_COL_SMS]    or "").strip()

        message = message.replace("\\n", "\n").replace("\\\\n", "\n")
        message = html.unescape(message)

        # country extract from range
        m = re.match(r'^([A-Za-z ]+?)(?:\s+[A-Z]\s*\d|$)', range_.strip())
        country = m.group(1).strip() if m else (range_.split()[0] if range_ else "Unknown")

        if not number or number in ("0", ""):
            return None
        if not message:
            return None

        return {
            "dt":      dt,
            "num":     number,
            "cli":     sender,
            "country": country,
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
