"""Modelo: plátano C (id `arbol_platano_c`, rust/core/src/plaza.rs → TipoProp::Arbol).

Genera:
    arte/fuentes/plaza/arbol_platano_c.blend
    godot/modelos/plaza/arbol_platano_c.glb
    docs/arte/revisiones/arbol_platano_c.jpg

Uso:
    python tools/blender/modelos/arbol_platano_c.py [--sin-hoja]

Variante más grande: tronco más grueso, copa de 4 bollos más baja y extendida, con un bollo
colgando de un costado (la copa no es redonda). Medidas decididas: 6,0 de ancho × 8,0 de
alto (lista ≈ 6 × 8). La hoja de revisión trae además las tres variantes juntas (A, B y C,
armadas con los PARAMETROS de sus scripts, solo para la foto).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _arbol  # noqa: E402
import arbol_platano_a  # noqa: E402
import arbol_platano_b  # noqa: E402

ID = "arbol_platano_c"
PARAMETROS = {
    "semilla": 3907,
    "lista": "6 × 8",
    "ancho": 6.0, "alto": 8.0,
    "horqueta": 2.7, "radio_tronco": 0.3,
    "inclinacion": 3.0, "rumbo": -120.0,
    "verdes": (1, 3, 2, 2),
    "bollos": [
        {"centro": (0.0, 2.6, 0.1), "radios": (2.1, 1.7, 2.2), "puntos": 40},
        {"centro": (-1.4, 1.35, -1.0), "radios": (1.55, 1.2, 1.45), "puntos": 32},
        {"centro": (1.35, 1.25, 1.1), "radios": (1.55, 1.15, 1.45), "puntos": 32},
        {"centro": (-0.5, 3.7, -0.5), "radios": (1.3, 1.0, 1.25), "puntos": 28, "rama": 0.5},
    ],
}


def main():
    _arbol.main(ID, PARAMETROS, "el más grande, 4 bollos",
                juntos=[("arbol_platano_a", arbol_platano_a.PARAMETROS),
                        ("arbol_platano_b", arbol_platano_b.PARAMETROS)])


if __name__ == "__main__":
    main()
