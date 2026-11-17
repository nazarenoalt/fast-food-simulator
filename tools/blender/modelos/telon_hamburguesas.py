"""Modelo: telón "Hamburguesas" (id `telon_hamburguesas`, lista de modelos, etapa 5).

Genera:
    godot/modelos/accesorios/texturas/telon_hamburguesas.png   ← franjas y letras (guía 4.5)
    arte/fuentes/accesorios/telon_hamburguesas.blend
    godot/modelos/accesorios/telon_hamburguesas.glb
    docs/arte/revisiones/telon_hamburguesas.jpg

Uso:
    python tools/blender/modelos/telon_hamburguesas.py [--sin-hoja]

Es el MISMO modelo que telon_panchos (lona de 1,3 × 0,42 × 0,01 m en el anclaje `frente`,
de y = 0,31 a 0,73), con otra imagen: la palabra "HAMBURGUESAS" con las letras de carrito. Todo el
código está en telon_panchos.py (main(id_, texto)); acá solo cambia la palabra.
Sin colisión, como el de panchos.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import telon_panchos  # noqa: E402

ID = "telon_hamburguesas"
TEXTO = "HAMBURGUESAS"

if __name__ == "__main__":
    telon_panchos.main(ID, TEXTO)
