#!/usr/bin/env bash
# Prueba de rendimiento (TASK-0255): plaza en su hora más poblada y fila llena.
# Mide el tiempo de cada cuadro a las 13:00 y a las 20:30 y lo imprime.
# Uso:
#   GODOT=/ruta/a/godot tools/prueba_rendimiento.sh            # con ventana: FPS reales
#   GODOT=/ruta/a/godot tools/prueba_rendimiento.sh --headless # sin pantalla: solo procesador
set -euo pipefail
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
GODOT="${GODOT:-godot}"

(cd "$RAIZ/rust" && cargo build)
"$GODOT" --headless --path "$RAIZ/godot" --import >/dev/null 2>&1 || true
"$GODOT" "$@" --path "$RAIZ/godot" res://scenes/prueba_rendimiento.tscn
