"""Modelo: plátano B (id `arbol_platano_b`, rust/core/src/plaza.rs → TipoProp::Arbol).

Genera:
    arte/fuentes/plaza/arbol_platano_b.blend
    godot/modelos/plaza/arbol_platano_b.glb
    docs/arte/revisiones/arbol_platano_b.jpg

Uso:
    python tools/blender/modelos/arbol_platano_b.py [--sin-hoja]

Variante más chica e inclinada: el tronco se inclina 9° hacia +X y la copa (3 bollos) queda
corrida para ese lado. Medidas decididas: 4,0 de ancho × 6,0 de alto (lista ≈ 4 × 6). Como
está inclinado, la caja envolvente no queda centrada en el origen: el origen va en la base
del tronco y así se chequea (ver _arbol.py).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _arbol  # noqa: E402

ID = "arbol_platano_b"
PARAMETROS = {
    "semilla": 2318,
    "lista": "4 × 6",
    "ancho": 4.0, "alto": 6.0,
    "horqueta": 2.4, "radio_tronco": 0.21,
    "inclinacion": 9.0, "rumbo": 90.0,     # hacia +X
    "verdes": (3, 2, 1),
    "bollos": [
        {"centro": (0.35, 1.7, 0.1), "radios": (1.5, 1.25, 1.45), "puntos": 38},
        {"centro": (-0.9, 0.95, -0.9), "radios": (1.05, 0.9, 1.05), "puntos": 26},
        {"centro": (0.9, 2.4, 0.75), "radios": (1.0, 0.85, 0.95), "puntos": 24, "rama": 0.55},
    ],
}


def main():
    _arbol.main(ID, PARAMETROS, "más chico e inclinado, 3 bollos")


if __name__ == "__main__":
    main()
