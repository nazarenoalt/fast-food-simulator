"""Modelo: nube mediana (id `nube_b`, familia `ciudad`): 4 bollos, 45 m de largo.

Genera arte/fuentes/ciudad/nube_b.blend, godot/modelos/ciudad/nube_b.glb y
docs/arte/revisiones/nube_b.jpg. Uso: python tools/blender/modelos/nube_b.py [--sin-hoja]
Ver _nube.py (forma, material pieza_nube, origen).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _nube as nube  # noqa: E402

P = {
    "id": "nube_b", "semilla": 47, "largo": 45.0, "alto_max": 15.0,
    "bollos": [
        ((-15.0, 1.5, 1.0), (7.0, 5.5, 6.5), 20),
        ((-5.0, 3.0, -1.0), (11.0, 10.0, 9.0), 30),
        ((6.0, 3.5, 1.5), (12.0, 11.0, 10.0), 32),
        ((16.0, 1.5, -0.5), (7.5, 6.0, 7.0), 22),
    ],
}

if __name__ == "__main__":
    nube.main(P, "nube_b · 45 m de largo · 4 bollos · cielo (el juego la pone a 90-140 m)")
