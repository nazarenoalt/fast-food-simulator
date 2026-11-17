#!/usr/bin/env bash
# Prueba de humo (SPEC-000): compila, abre el juego sin pantalla y verifica los criterios
# de aceptación de integración. Sale con código 0 si todo pasa.
# Uso: GODOT=/ruta/a/godot tools/prueba_humo.sh
set -euo pipefail
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
GODOT="${GODOT:-godot}"

(cd "$RAIZ/rust" && cargo build)
# La primera vez Godot tiene que "importar" el proyecto (registra la extensión de Rust).
"$GODOT" --headless --path "$RAIZ/godot" --import >/dev/null 2>&1 || true
# --fixed-fps corre la simulación lo más rápido posible con pasos de 1/60 s.
"$GODOT" --headless --path "$RAIZ/godot" --fixed-fps 60 res://scenes/prueba_humo.tscn
