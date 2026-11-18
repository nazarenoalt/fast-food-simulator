"""Modelo: nube chica (id `nube_a`, familia `ciudad`): 3 bollos, 30 m de largo.

Genera arte/fuentes/ciudad/nube_a.blend, godot/modelos/ciudad/nube_a.glb y
docs/arte/revisiones/nube_a.jpg. Uso: python tools/blender/modelos/nube_a.py [--sin-hoja]
Ver _nube.py (forma, material pieza_nube, origen).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _nube as nube  # noqa: E402

P = {
    "id": "nube_a", "semilla": 31, "largo": 30.0, "alto_max": 12.0,
    "bollos": [
        ((-8.0, 2.0, 0.5), (7.5, 6.0, 6.5), 22),
        ((1.5, 3.0, -0.5), (10.0, 9.0, 8.5), 28),
        ((10.0, 1.5, 1.0), (6.5, 5.0, 6.0), 20),
    ],
}

if __name__ == "__main__":
    nube.main(P, "nube_a · 30 m de largo · 3 bollos · cielo (el juego la pone a 90-140 m)")
