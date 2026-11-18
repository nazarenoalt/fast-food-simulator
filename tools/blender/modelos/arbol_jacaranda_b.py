"""Modelo: jacarandá B (id `arbol_jacaranda_b`, rust/core/src/plaza.rs → TipoProp::Arbol).

Genera:
    arte/fuentes/plaza/arbol_jacaranda_b.blend
    godot/modelos/plaza/arbol_jacaranda_b.glb
    docs/arte/revisiones/arbol_jacaranda_b.jpg

Uso:
    python tools/blender/modelos/arbol_jacaranda_b.py [--sin-hoja]

Variante más chica y joven del jacarandá: tronco retorcido que se inclina 7° hacia −X, se
abre en tres ramas y una copa chata de 3 bollos, corrida hacia el lado de la inclinación.
Más verde mezclado que el A (todavía está floreciendo). Medidas decididas: 4,2 de ancho ×
5,0 de alto (lista ≈ 4 × 5). Como está inclinado, el origen va en la base del tronco y así
se chequea (ver _arbol.py). La hoja muestra las dos variantes juntas.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _arbol  # noqa: E402
import arbol_jacaranda_a  # noqa: E402

ID = "arbol_jacaranda_b"
PARAMETROS = {
    "semilla": 5129,
    "lista": "4 × 5",
    "ancho": 4.2, "alto": 5.0,
    "horqueta": 1.8, "radio_tronco": 0.18,
    "inclinacion": 7.0, "rumbo": -90.0,    # hacia −X
    "materiales": arbol_jacaranda_a.MATERIALES,
    "verdes": (2, 1, 2),
    "mezcla": 0.4,
    "tronco": [(0.0, 1.3), (0.25, 1.0), (0.7, 0.92), (1.2, 0.88), (None, 0.8)],
    "quiebre": 0.6,
    "ramas_abiertas": 0.15,
    "bollos": [
        {"centro": (-0.3, 2.0, 0.1), "radios": (1.45, 0.75, 1.35), "puntos": 36, "rama": 0.8},
        {"centro": (1.15, 1.55, -0.45), "radios": (1.05, 0.62, 1.0), "puntos": 28, "rama": 0.9},
        {"centro": (-1.25, 1.45, 0.6), "radios": (1.0, 0.6, 0.95), "puntos": 26, "rama": 0.9},
    ],
}


def main():
    _arbol.main(ID, PARAMETROS, "jacarandá más chico e inclinado, 3 bollos",
                juntos=[("arbol_jacaranda_a", arbol_jacaranda_a.PARAMETROS)])


if __name__ == "__main__":
    main()
