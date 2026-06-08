#!/bin/bash
# Build TechBot APK
# Requisitos: Android SDK + Gradle
# Configurar ANDROID_HOME en ~/.bashrc o exportar antes de ejecutar

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [ -z "$ANDROID_HOME" ]; then
    echo "ERROR: ANDROID_HOME no está configurado"
    echo "Agregalo a ~/.bashrc:"
    echo '  export ANDROID_HOME=$HOME/Android/Sdk'
    echo '  export PATH=$PATH:$ANDROID_HOME/tools:$ANDROID_HOME/platform-tools'
    exit 1
fi

echo "📦 Compilando TechBot APK..."
./gradlew assembleDebug

echo ""
echo "✅ APK generado:"
echo "  $SCRIPT_DIR/app/build/outputs/apk/debug/app-debug.apk"
echo ""
echo "Instalalo con:"
echo "  adb install $SCRIPT_DIR/app/build/outputs/apk/debug/app-debug.apk"
