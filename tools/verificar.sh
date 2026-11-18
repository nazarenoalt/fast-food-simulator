#!/usr/bin/env bash
# Verificación completa (SPEC-000): lo que antes corría la CI. La corre el dueño de la
# feature antes de abrir o actualizar el PR, y pega la última línea en la descripción.
# Uso: GODOT=/ruta/a/godot tools/verificar.sh
set -euo pipefail
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
: "${GODOT:?Falta GODOT=/ruta/a/godot (Godot 4.7, ver CLAUDE.md)}"

# Sin los .glb reales (quedan los punteros de LFS) fallan los tests de modelos.
f=$(cd "$RAIZ" && git lfs ls-files -n -I 'godot/**' | sed -n 1p)
if [ -n "$f" ] && [ "$(head -c 4 "$RAIZ/$f")" != "glTF" ]; then
  echo "Faltan los modelos: corré git lfs pull --include=\"godot/**\"" >&2
  exit 1
fi

cd "$RAIZ/rust"
echo "== Formato";  cargo fmt --check
# Con pipefail, cualquier advertencia de clippy corta acá (TASK-0002).
echo "== Lints";    cargo clippy --all-targets -q -- -D warnings
echo "== Tests (reglas, trazabilidad, docs y audio)"; cargo test -q
echo "== Prueba de humo"; GODOT="$GODOT" "$RAIZ/tools/prueba_humo.sh" | grep -E "FALLA|PRUEBA DE HUMO"

cd "$RAIZ"
echo "VERIFICACIÓN: todo OK en $(git rev-parse --short HEAD)$(git diff --quiet HEAD || echo ' (con cambios sin commitear)')"
