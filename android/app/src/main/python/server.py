"""TechBot server launcher for Android (Chaquopy).
Starts the Flask app on localhost and notifies the Java layer when ready."""

import sys
import os
import threading
import json
import time

# ─── Add our source directories to Python path ──────────────
# Chaquopy extracts these to the filesystem, so we find them
# relative to this file's directory.
SERVER_DIR = os.path.dirname(os.path.abspath(__file__))
if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)

# ─── Logging helper (goes to Android logcat) ────────────────
_ANDROID = hasattr(sys, 'getandroidapilevel') or 'ANDROID_ROOT' in os.environ


def log(msg):
    if _ANDROID:
        from android import log
        log.v("TechBot", str(msg))
    else:
        print(f"[TechBot] {msg}")


# ─── Import and configure Flask app ─────────────────────────
try:
    from webapp.app import app as flask_app
    log("Módulo webapp.app importado correctamente")
except Exception as e:
    log(f"Error importando webapp.app: {e}")
    # Fallback: create minimal app for debugging
    from flask import Flask, jsonify
    flask_app = Flask(__name__)

    @flask_app.route('/')
    def home():
        return jsonify({
            "status": "error",
            "error": f"No se pudo cargar TechBot: {e}",
            "hint": "Verificá que los módulos techbot/ y webapp/ estén en app/src/main/python/"
        })

    @flask_app.route('/api/status')
    def api_status():
        return jsonify({"status": "degraded", "error": str(e)})


# ─── Shutdown handler ───────────────────────────────────────
def shutdown():
    """Graceful shutdown: call from Java when activity destroys."""
    log("Servidor TechBot deteniéndose...")
    func = flask_app.request_context.__globals__.get('shutdown')
    if func:
        func()


def wait_for_server(timeout_sec=10):
    """Bloquea hasta que el servidor esté listo. Retorna True si OK."""
    import urllib.request
    start = time.time()
    while time.time() - start < timeout_sec:
        try:
            urllib.request.urlopen("http://127.0.0.1:5000/api/status", timeout=1)
            return True
        except:
            time.sleep(0.2)
    return False


def start(port=5000):
    """Inicia el servidor Flask en background (llamado desde Java)."""
    log(f"Iniciando TechBot en 127.0.0.1:{port}...")
    try:
        flask_app.run(
            host="127.0.0.1",
            port=port,
            debug=False,
            use_reloader=False,
            threaded=True
        )
    except Exception as e:
        log(f"Error iniciando servidor: {e}")


if __name__ == "__main__":
    start()
