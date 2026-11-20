#!/usr/bin/env bash
# Medición de rendimiento (SPEC-032, TASK-0255): abre res://scenes/rendimiento.tscn con ventana
# (sin --headless ni --fixed-fps) y sin vsync; a los ~75 s imprime la línea RENDIMIENTO: y se
# cierra (REQ-REN-01..04). Necesita placa de video: no entra en tools/verificar.sh (REQ-REN-06).
# Uso: GODOT=/ruta/a/godot tools/rendimiento.sh [opciones extra de Godot]
# Para probar la escena rápido: RENDIMIENTO_ESPERA=2 RENDIMIENTO_MEDICION=5 (segundos).
set -euo pipefail
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
: "${GODOT:?Falta GODOT=/ruta/a/godot (Godot 4.7, ver CLAUDE.md)}"

(cd "$RAIZ/rust" && cargo build)
# La primera vez Godot tiene que "importar" el proyecto (registra la extensión de Rust).
"$GODOT" --headless --path "$RAIZ/godot" --import >/dev/null 2>&1 || true
# REQ-REN-06: la meta es a 1080p.
"$GODOT" --path "$RAIZ/godot" --disable-vsync --max-fps 0 --resolution 1920x1080 "$@" \
  res://scenes/rendimiento.tscn 2>&1 | grep -a "RENDIMIENTO"
