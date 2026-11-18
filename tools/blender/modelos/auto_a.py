"""Modelo: auto sedán (id `auto_a`, familia `ciudad`). Diseño genérico, sin marca.

Genera:
    arte/fuentes/ciudad/auto_a.blend
    godot/modelos/ciudad/auto_a.glb
    docs/arte/revisiones/auto_a.jpg

Uso:
    python tools/blender/modelos/auto_a.py [--sin-hoja]

Sedán de tres volúmenes: capó largo, cabina con parante del medio y baúl. Ver _auto.py para
la forma, los objetos y los materiales.

Medidas: 1,815 × 1,45 × 4,30 (con los espejos; la chapa mide 1,74) (lista ≈ 1,8 × 1,45 × 4,5). Se acerca al auto que dibuja hoy
el juego (4,1 de largo, 1,48 de alto, 1,86 con las ruedas) y a su colisión de 4,1 m: un
sedán de 4,5 m pisaría 20 cm afuera de esa caja de cada lado. Ruedas de radio 0,33 (las del
código, que las gira con ese radio) y ejes a 2,6 m (los del código).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _auto as auto  # noqa: E402
import _ciudad as ciudad  # noqa: E402

L = 2.12   # medio largo de la chapa (con paragolpes: 2,15)
P = {
    "id": "auto_a",
    "medidas": (1.815, 1.45, 4.30),
    "largo": 2 * L,
    "radio": 0.33,
    "ejes": (1.30, -1.30),
    "trocha": 0.74,
    "piso_puntas": [(-L, 0.34), (-1.95, 0.27), (1.95, 0.27), (L, 0.34)],
    "techo": [(-L, 0.90), (-2.02, 0.99), (-1.55, 1.03), (-0.95, 1.41), (-0.35, 1.442), (0.25, 1.42),
              (0.92, 0.99), (1.95, 0.88), (L, 0.78)],
    "cintura": [(-L, 0.84), (-2.02, 0.92), (-1.55, 0.95), (0.92, 0.93), (1.95, 0.83), (L, 0.72)],
    "ancho": [(-L, 0.80), (-1.98, 0.86), (-1.5, 0.87), (1.5, 0.87), (1.98, 0.85), (L, 0.79)],
    "ancho_techo": [(-L, 0.70), (-1.55, 0.76), (-0.95, 0.66), (0.25, 0.66), (0.92, 0.76), (L, 0.70)],
    "parabrisas": (0.25, 0.92),
    "luneta": (-1.55, -0.95),
    "parante_b": (-0.38, -0.30),
    "ventanillas": [(-0.30, 0.92), (-0.88, -0.38)],
    "paragolpes": (0.36, 0.40),
}

if __name__ == "__main__":
    auto.main(P, ciudad.m("auto_a · 1.82 × 1.45 × 4.3 m · sedán · vehículo (genérico, sin marca)"))
