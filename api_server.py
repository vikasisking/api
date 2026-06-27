# ============================================================
#  api_server.py  —  Unified SMS API Server
#  Saare panels ka SMS ek hi endpoint se milega
#  Usage: python api_server.py
#  Endpoint: GET /api/sms?key=YOUR_API_KEY
#            GET /api/sms?key=YOUR_API_KEY&panel=gaza
#            GET /api/status?key=YOUR_API_KEY
# ============================================================

import sys
import os
import time
import threading
import json
from datetime import datetime
from flask import Flask, request, jsonify

# ============================================================
#  CONFIG — yahan apni values set karo
# ============================================================

API_KEY        = "hxotp_secret_2025"   # Client is API key use karega
HOST           = "0.0.0.0"
PORT           = 5055
CACHE_TTL      = 5      # seconds — kitni baar panel fetch ho (per panel ka POLL_INTERVAL override)
MAX_RECORDS    = 500    # ek response me max kitne SMS

# ============================================================
#  PANEL LOADER SETUP
# ============================================================

# hxotp folder same directory me hona chahiye ya sys.path me add karo
HXOTP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hxotp")
if HXOTP_DIR not in sys.path:
    sys.path.insert(0, HXOTP_DIR)

try:
    from panel_loader import load_all_panels
    PANELS = load_all_panels()
except Exception as e:
    print(f"❌ Panel load failed: {e}", flush=True)
    PANELS = []

# ============================================================
#  CACHE — har panel ka data alag cache hoga
# ============================================================

_cache = {}         # { panel_name: {"data": [...], "ts": float} }
_cache_lock = threading.Lock()

def _fetch_panel(panel):
    """Panel ka data fetch karo aur parse karo."""
    try:
        raw_rows = panel.fetch()
        parsed = []
        seen = set()
        for row in raw_rows:
            p = panel.parse_row(row)
            if not p:
                continue
            # Dedup key: num + message
            key = f"{p.get('num','')}__{p.get('message','')}"
            if key in seen:
                continue
            seen.add(key)
            parsed.append(p)
        return parsed
    except Exception as e:
        print(f"❌ {panel.PANEL_NAME} fetch error: {e}", flush=True)
        return []

def _get_cached(panel):
    """Cache se data lo, agar stale ho toh refresh karo."""
    name = panel.PANEL_NAME
    now = time.time()

    with _cache_lock:
        c = _cache.get(name)
        if c and (now - c["ts"]) < CACHE_TTL:
            return c["data"]

    # Cache miss / stale — bahar fetch karo (lock ke bahar)
    data = _fetch_panel(panel)

    with _cache_lock:
        _cache[name] = {"data": data, "ts": time.time()}

    return data

# ============================================================
#  BACKGROUND POLLER — har panel khud apne interval pe fetch
# ============================================================

def _poller(panel):
    """Per-panel background thread — cache warm rakhta hai."""
    interval = getattr(panel, "POLL_INTERVAL", 10)
    print(f"🔄 Poller started: {panel.PANEL_NAME} (every {interval}s)", flush=True)
    while True:
        try:
            if getattr(panel, "is_enabled", lambda: True)():
                data = _fetch_panel(panel)
                with _cache_lock:
                    _cache[panel.PANEL_NAME] = {"data": data, "ts": time.time()}
        except Exception as e:
            print(f"⚠️ Poller error [{panel.PANEL_NAME}]: {e}", flush=True)
        time.sleep(interval)

def start_pollers():
    for p in PANELS:
        t = threading.Thread(target=_poller, args=(p,), daemon=True, name=f"poller_{p.PANEL_NAME}")
        t.start()

# ============================================================
#  FLASK APP
# ============================================================

app = Flask(__name__)

def auth_check():
    """API key verify karo."""
    key = request.args.get("key", "")
    if key != API_KEY:
        return jsonify({"status": "error", "msg": "Invalid API key"}), 401
    return None

@app.route("/api/sms", methods=["GET"])
def get_sms():
    """
    All panels ka merged SMS data.
    Params:
      key    — required (API key)
      panel  — optional (filter: gaza, hadi, green, ...)
      limit  — optional (default 500)
      num    — optional (filter by phone number, partial match)
    """
    err = auth_check()
    if err:
        return err

    panel_filter = request.args.get("panel", "").lower().strip()
    num_filter   = request.args.get("num", "").strip()
    limit        = int(request.args.get("limit", MAX_RECORDS))

    all_sms = []

    for panel in PANELS:
        # panel filter
        if panel_filter and panel.PANEL_COMMAND != panel_filter:
            continue

        # disabled panels skip
        if hasattr(panel, "is_enabled") and not panel.is_enabled():
            continue

        data = _get_cached(panel)
        all_sms.extend(data)

    # number filter
    if num_filter:
        all_sms = [s for s in all_sms if num_filter in s.get("num", "")]

    # sort by dt (latest first), limit
    try:
        all_sms.sort(key=lambda x: x.get("dt", ""), reverse=True)
    except Exception:
        pass

    all_sms = all_sms[:limit]

    return jsonify({
        "status":  "success",
        "count":   len(all_sms),
        "ts":      datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "data":    all_sms
    })


@app.route("/api/status", methods=["GET"])
def get_status():
    """
    Panels ka status — enabled/disabled, last fetch time, record count.
    """
    err = auth_check()
    if err:
        return err

    result = []
    for panel in PANELS:
        with _cache_lock:
            c = _cache.get(panel.PANEL_NAME, {})
        enabled = getattr(panel, "is_enabled", lambda: True)()
        last_ts  = datetime.fromtimestamp(c["ts"]).strftime("%H:%M:%S") if c.get("ts") else "N/A"
        result.append({
            "name":      panel.PANEL_NAME,
            "command":   panel.PANEL_COMMAND,
            "enabled":   enabled,
            "last_fetch": last_ts,
            "records":   len(c.get("data", []))
        })

    return jsonify({
        "status":  "ok",
        "panels":  result,
        "total":   len(PANELS)
    })


@app.route("/api/panels", methods=["GET"])
def list_panels():
    return jsonify({"status": "error", "msg": "Ladle Jada Hosiyari Na Kar Baap Baap Hota 😂"}), 403
@app.errorhandler(404)
def not_found(e):
    return jsonify({"status": "error", "msg": "Endpoint not found"}), 404


# ============================================================
#  MAIN
# ============================================================

if __name__ == "__main__":
    print(f"🚀 API Server starting on {HOST}:{PORT}", flush=True)
    print(f"🔑 API Key: {API_KEY}", flush=True)
    print(f"📦 Panels loaded: {len(PANELS)}", flush=True)

    start_pollers()

    app.run(host=HOST, port=PORT, debug=False, threaded=True)
