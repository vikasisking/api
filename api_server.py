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
#  CONFIG — env variables se load hoga (Railway ke liye)
# ============================================================

API_KEY     = os.environ.get("API_KEY", "h2ihub")
HOST        = "0.0.0.0"
PORT        = int(os.environ.get("PORT", 5055))   # Railway dynamic port
CACHE_TTL   = 5      # seconds
MAX_RECORDS = 500

# ============================================================
#  PANEL LOADER
# ============================================================

try:
    from panel_loader import load_all_panels
    PANELS = load_all_panels()
except Exception as e:
    print(f"❌ Panel load failed: {e}", flush=True)
    PANELS = []

# ============================================================
#  CACHE
# ============================================================

_cache      = {}
_cache_lock = threading.Lock()

def _fetch_panel(panel):
    try:
        raw_rows = panel.fetch()
        parsed   = []
        seen     = set()
        for row in raw_rows:
            p = panel.parse_row(row)
            if not p:
                continue
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
    name = panel.PANEL_NAME
    now  = time.time()
    with _cache_lock:
        c = _cache.get(name)
        if c and (now - c["ts"]) < CACHE_TTL:
            return c["data"]
    data = _fetch_panel(panel)
    with _cache_lock:
        _cache[name] = {"data": data, "ts": time.time()}
    return data

# ============================================================
#  BACKGROUND POLLERS
# ============================================================

def _poller(panel):
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
    key = request.args.get("key", "")
    if key != API_KEY:
        return jsonify({"status": "error", "msg": "Invalid API key"}), 401
    return None

@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "status":   "running",
        "service":  "HxOTP SMS API",
        "version":  "2.0",
        "panels":   len(PANELS),
        "endpoints": [
            "/api/sms?key=YOUR_KEY",
            "/api/sms?key=YOUR_KEY&panel=gaza",
            "/api/sms?key=YOUR_KEY&num=91XXXXXX",
            "/api/sms?key=YOUR_KEY&limit=100",
            "/api/status?key=YOUR_KEY"
        ]
    })

@app.route("/api/sms", methods=["GET"])
def get_sms():
    """
    All panels ka merged SMS data.
    Params:
      key    — required
      panel  — optional (filter: gaza, hadi, green, ...)
      limit  — optional (default 500)
      num    — optional (filter by phone number, partial match)
    """
    err = auth_check()
    if err:
        return err

    panel_filter = request.args.get("panel", "").lower().strip()
    num_filter   = request.args.get("num", "").strip()
    limit        = min(int(request.args.get("limit", MAX_RECORDS)), MAX_RECORDS)

    all_sms = []

    for panel in PANELS:
        if panel_filter and panel.PANEL_COMMAND != panel_filter:
            continue
        if hasattr(panel, "is_enabled") and not panel.is_enabled():
            continue
        data = _get_cached(panel)
        all_sms.extend(data)

    if num_filter:
        all_sms = [s for s in all_sms if num_filter in s.get("num", "")]

    try:
        all_sms.sort(key=lambda x: x.get("dt", ""), reverse=True)
    except Exception:
        pass

    all_sms = all_sms[:limit]

    return jsonify({
        "status": "success",
        "count":  len(all_sms),
        "ts":     datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "data":   all_sms
    })


@app.route("/api/status", methods=["GET"])
def get_status():
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
            "name":       panel.PANEL_NAME,
            "command":    panel.PANEL_COMMAND,
            "enabled":    enabled,
            "last_fetch": last_ts,
            "records":    len(c.get("data", []))
        })

    return jsonify({
        "status": "ok",
        "panels": result,
        "total":  len(PANELS)
    })


@app.route("/health", methods=["GET"])
def health():
    """Railway health check endpoint"""
    return jsonify({"status": "ok", "ts": datetime.now().isoformat()}), 200


@app.errorhandler(404)
def not_found(e):
    return jsonify({"status": "error", "msg": "Endpoint not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"status": "error", "msg": "Internal server error"}), 500


# ============================================================
#  MAIN
# ============================================================

if __name__ == "__main__":
    print(f"🚀 HxOTP API Server starting on {HOST}:{PORT}", flush=True)
    print(f"🔑 API Key: {API_KEY}", flush=True)
    print(f"📦 Panels loaded: {len(PANELS)}", flush=True)
    start_pollers()
    app.run(host=HOST, port=PORT, debug=False, threaded=True)
