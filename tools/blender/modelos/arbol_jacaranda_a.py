"""Modelo: jacarandá A (id `arbol_jacaranda_a`, rust/core/src/plaza.rs → TipoProp::Arbol).

Genera:
    arte/fuentes/plaza/arbol_jacaranda_a.blend
    godot/modelos/plaza/arbol_jacaranda_a.glb
    docs/arte/revisiones/arbol_jacaranda_a.jpg

Uso:
    python tools/blender/modelos/arbol_jacaranda_a.py [--sin-hoja]

El jacarandá en flor, el toque de color de la plaza (guía 5.4). Distinto del plátano en la
silueta, no solo en el color: tronco más corto y retorcido (anillos corridos al azar), que se
abre en ramas largas casi horizontales que después suben, y copa ancha y aplanada de 4
bollos bajos. Copa lila (M_FlorLila1/2, apagados: es fondo, guía 4.2 regla 2) con algo de
verde (M_Hojas2) mezclado, como un jacarandá de noviembre que todavía tiene hojas.
Medidas decididas: 5,4 de ancho × 6,0 de alto (lista ≈ 5 × 6). La construcción, qué se
mide, el origen y los objetos están explicados en _arbol.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _arbol  # noqa: E402

ID = "arbol_jacaranda_a"
MATERIALES = ("M_Tronco", "M_FlorLila1", "M_FlorLila2", "M_Hojas2")
PARAMETROS = {
    "semilla": 4411,
    "lista": "5 × 6",
    "ancho": 5.4, "alto": 6.0,
    "horqueta": 1.9, "radio_tronco": 0.22,
    "inclinacion": 4.0, "rumbo": -50.0,
    "materiales": MATERIALES,
    "verdes": (1, 2, 1, 2),   # FlorLila1, 2, 1, 2 (uno por bollo); Hojas2 entra por la mezcla
    "mezcla": 0.35,
    "tronco": [(0.0, 1.3), (0.2, 1.0), (0.6, 0.95), (1.05, 0.9), (1.5, 0.85), (None, 0.8)],
    "quiebre": 0.7,
    "ramas_abiertas": 0.12,
    "bollos": [
        {"centro": (0.0, 2.35, 0.0), "radios": (1.7, 0.85, 1.6), "puntos": 40, "rama": 0.8},
        {"centro": (-1.65, 1.75, 0.55), "radios": (1.25, 0.7, 1.15), "puntos": 32, "rama": 0.9},
        {"centro": (1.6, 1.9, -0.5), "radios": (1.3, 0.72, 1.2), "puntos": 32, "rama": 0.9},
        {"centro": (0.35, 2.05, 1.35), "radios": (1.05, 0.6, 0.95), "puntos": 26, "rama": 0.9},
    ],
}


def main():
    _arbol.main(ID, PARAMETROS, "jacarandá en flor, copa ancha y chata de 4 bollos")


if __name__ == "__main__":
    main()
