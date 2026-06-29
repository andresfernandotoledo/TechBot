"""TechBot server launcher for Android (Chaquopy).
Starts the Flask app on localhost automatically when imported."""

import sys
import os
import threading
import time

# ─── Add our source directories to Python path ──────────────
SERVER_DIR = os.path.dirname(os.path.abspath(__file__))
if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)

# ─── Logging helper ─────────────────────────────────────────
_ANDROID = hasattr(sys, 'getandroidapilevel') or 'ANDROID_ROOT' in os.environ


def log(msg):
    if _ANDROID:
        try:
            from android import log as alog
            alog.v("TechBot", str(msg))
        except:
            print(f"[TechBot] {msg}")
    else:
        print(f"[TechBot] {msg}")


# ─── Import Flask app ──────────────────────────────────────
flask_app = None
import_error = None

try:
    from webapp.app import app as flask_app
    log("webapp.app importado OK")
except Exception as e:
    import_error = e
    log(f"Error importando webapp.app: {e}")
    from flask import Flask, jsonify
    flask_app = Flask(__name__)

    @flask_app.route('/')
    def home():
        return jsonify({
            "status": "error",
            "error": f"No se pudo cargar TechBot: {import_error}",
        })

    @flask_app.route('/api/status')
    def api_status():
        return jsonify({"status": "degraded" if import_error else "ok", "error": str(import_error) if import_error else None})


# ─── Start server automatically on import ──────────────────
def _run_server():
    try:
        flask_app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False, threaded=True)
    except Exception as e:
        log(f"Error en server.run(): {e}")


_server_thread = threading.Thread(target=_run_server, daemon=True, name="techbot-flask")
_server_thread.start()


def wait_ready(timeout=15):
    """Espera a que el server responda. Usado desde Java."""
    import urllib.request
    start = time.time()
    while time.time() - start < timeout:
        try:
            urllib.request.urlopen("http://127.0.0.1:5000/api/status", timeout=1)
            return True
        except:
            time.sleep(0.3)
    return False


def shutdown():
    log("Shutdown requested (not implemented for Flask dev server)")
