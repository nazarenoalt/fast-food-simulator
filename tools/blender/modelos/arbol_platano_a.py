"""Modelo: plátano A (id `arbol_platano_a`, rust/core/src/plaza.rs → TipoProp::Arbol).

Genera:
    arte/fuentes/plaza/arbol_platano_a.blend
    godot/modelos/plaza/arbol_platano_a.glb
    docs/arte/revisiones/arbol_platano_a.jpg

Uso:
    python tools/blender/modelos/arbol_platano_a.py [--sin-hoja]

El plátano "de siempre" de la plaza: tronco derecho hasta 2,5 m y copa ancha y redondeada
de 4 bollos. Medidas decididas: 5,0 de ancho × 7,0 de alto (lista ≈ 5 × 7). La construcción,
qué se mide, el origen y los objetos están explicados en _arbol.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _arbol  # noqa: E402

ID = "arbol_platano_a"
PARAMETROS = {
    "semilla": 1701,
    "lista": "5 × 7",
    "ancho": 5.0, "alto": 7.0,
    "horqueta": 2.5, "radio_tronco": 0.26,
    "inclinacion": 2.0, "rumbo": 30.0,
    "verdes": (2, 1, 3, 1),  # M_Hojas2, 1, 3, 1 (uno por bollo)
    # centro relativo a la horqueta (Godot), radios (x, y, z), puntos del bollo.
    "bollos": [
        {"centro": (0.1, 2.1, 0.0), "radios": (1.75, 1.45, 1.7), "puntos": 40},
        {"centro": (-1.2, 1.05, 0.85), "radios": (1.25, 1.05, 1.2), "puntos": 30},
        {"centro": (1.2, 1.2, -0.85), "radios": (1.3, 1.1, 1.2), "puntos": 32},
        {"centro": (0.6, 2.8, 0.3), "radios": (1.25, 0.95, 1.15), "puntos": 26, "rama": 0.5},
    ],
}


def main():
    _arbol.main(ID, PARAMETROS, "copa ancha de 4 bollos")


if __name__ == "__main__":
    main()
