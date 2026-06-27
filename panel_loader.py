# ============================================================
#  panel_loader.py  —  Auto-loads all panel_*.py from panels/
# ============================================================

import importlib
import os
import sys


PANELS_DIR = "panels"   # Fixed — no config.py needed


def load_all_panels() -> list:
    panels      = []
    base_dir    = os.path.dirname(os.path.abspath(__file__))
    panels_path = os.path.join(base_dir, PANELS_DIR)

    if not os.path.exists(panels_path):
        print(f"⚠️  panels/ folder nahi mila: {panels_path}", flush=True)
        return panels

    if base_dir not in sys.path:
        sys.path.insert(0, base_dir)

    for filename in sorted(os.listdir(panels_path)):
        if not filename.startswith("panel_") or not filename.endswith(".py"):
            continue
        if filename == "panel_template.py":
            continue

        module_name = f"{PANELS_DIR}.{filename[:-3]}"
        try:
            mod = importlib.import_module(module_name)

            required = ["PANEL_NAME", "PANEL_COMMAND", "POLL_INTERVAL", "fetch", "parse_row"]
            missing  = [r for r in required if not hasattr(mod, r)]
            if missing:
                print(f"❌ Panel skip: {filename} — missing: {missing}", flush=True)
                continue

            panels.append(mod)
            print(f"✅ Panel loaded: {mod.PANEL_NAME} (/{mod.PANEL_COMMAND})", flush=True)

        except Exception as e:
            print(f"❌ Panel load error [{filename}]: {e}", flush=True)

    print(f"📦 Total panels loaded: {len(panels)}", flush=True)
    return panels
