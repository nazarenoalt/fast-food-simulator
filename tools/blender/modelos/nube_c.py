"""Modelo: nube grande (id `nube_c`, familia `ciudad`): 5 bollos, 60 m de largo.

Genera arte/fuentes/ciudad/nube_c.blend, godot/modelos/ciudad/nube_c.glb y
docs/arte/revisiones/nube_c.jpg. Uso: python tools/blender/modelos/nube_c.py [--sin-hoja]
Ver _nube.py (forma, material pieza_nube, origen).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _nube as nube  # noqa: E402

P = {
    "id": "nube_c", "semilla": 59, "largo": 60.0, "alto_max": 16.0,
    "bollos": [
        ((-22.0, 1.5, 0.0), (7.0, 5.5, 6.0), 20),
        ((-12.0, 3.0, 1.5), (10.0, 9.0, 8.5), 28),
        ((0.0, 4.0, -1.0), (13.0, 12.0, 11.0), 34),
        ((12.0, 3.0, 1.0), (10.5, 9.0, 9.0), 28),
        ((22.0, 1.5, -1.5), (6.5, 5.0, 6.0), 20),
    ],
}

if __name__ == "__main__":
    nube.main(P, "nube_c · 60 m de largo · 5 bollos · cielo (el juego la pone a 90-140 m)")
