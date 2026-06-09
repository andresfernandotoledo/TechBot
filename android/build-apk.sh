#!/bin/bash
# Build TechBot APK with embedded Python (Chaquopy)
# Requisitos: Android SDK + Gradle + Python 3.11 en PATH
# Configurar ANDROID_HOME en ~/.bashrc o exportar antes de ejecutar

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$SCRIPT_DIR"

if [ -z "$ANDROID_HOME" ]; then
    echo "ERROR: ANDROID_HOME no está configurado"
    echo "Agregalo a ~/.bashrc:"
    echo '  export ANDROID_HOME=$HOME/Android/Sdk'
    echo '  export PATH=$PATH:$ANDROID_HOME/tools:$ANDROID_HOME/platform-tools'
    exit 1
fi

PYTHON_DIR="$SCRIPT_DIR/app/src/main/python"

echo "📦 Preparando TechBot APK con Python embebido..."

# 1. Copiar módulos Python al proyecto Android
echo "   Copiando techbot/ → python/techbot/"
rm -rf "$PYTHON_DIR/techbot"
cp -r "$PROJECT_DIR/techbot" "$PYTHON_DIR/techbot"

echo "   Copiando webapp/ → python/webapp/"
rm -rf "$PYTHON_DIR/webapp"
cp -r "$PROJECT_DIR/webapp" "$PYTHON_DIR/webapp"

# 2. Crear __init__.py si no existe
touch "$PYTHON_DIR/techbot/__init__.py"

# 3. Verificar que server.py existe
if [ ! -f "$PYTHON_DIR/server.py" ]; then
    echo "ERROR: server.py no encontrado en $PYTHON_DIR"
    exit 1
fi

# 4. Compilar APK
echo ""
echo "🔨 Compilando APK (Chaquopy + Flask embebido)..."
echo "    Esto puede tomar varios minutos la primera vez (descarga pip deps)"
echo ""
./gradlew assembleDebug

echo ""
echo "✅ APK generado:"
APK="$SCRIPT_DIR/app/build/outputs/apk/debug/app-debug.apk"
if [ -f "$APK" ]; then
    SIZE=$(du -h "$APK" | cut -f1)
    echo "  $APK ($SIZE)"
else
    APK=$(find "$SCRIPT_DIR/app/build/outputs" -name "*.apk" 2>/dev/null | head -1)
    if [ -n "$APK" ]; then
        echo "  $APK"
    else
        echo "  (buscar en app/build/outputs/)"
    fi
fi
echo ""
echo "Instalalo con:"
echo "  adb install $SCRIPT_DIR/app/build/outputs/apk/debug/app-debug.apk"
echo ""
echo "🧪 El APK incluye:"
echo "   • Servidor Flask embebido (Chaquopy Python 3.11)"
echo "   • 92 API endpoints"
echo "   • Scanner TCP/UDP, DNS, SSL, SNMP, WiFi, DHCP"
echo "   • Speedtest, Topología interactiva, IPAM"
echo "   • SIN dependencia de Termux ni servidor externo"
echo ""
echo "📱 Al abrir la app, el servidor inicia automáticamente"
echo "    en http://127.0.0.1:5000"
