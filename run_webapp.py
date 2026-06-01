#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from webapp.app import app
except ImportError as e:
    print(f"Error: {e}")
    print("\nInstalá Flask con:")
    print("  pip install -r requirements.txt")
    sys.exit(1)

if __name__ == "__main__":
    print("=" * 50)
    print("  TechBot Web App")
    print("=" * 50)
    print()
    print("  En PC:      http://localhost:5000")
    print("  En móvil:   http://<IP-DE-TU-PC>:5000")
    print()
    print("  Para acceder desde el móvil:")
    print("  1. Conectate a la misma red WiFi")
    print("  2. Buscá tu IP local (ip a / ipconfig)")
    print("  3. En el móvil abrí http://TU-IP:5000")
    print()
    print("  Ctrl+C para salir")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=False)
