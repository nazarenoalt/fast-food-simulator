"""Modelo: auto chico (id `auto_b`, familia `ciudad`). Diseño genérico, sin marca.

Genera:
    arte/fuentes/ciudad/auto_b.blend
    godot/modelos/ciudad/auto_b.glb
    docs/arte/revisiones/auto_b.jpg

Uso:
    python tools/blender/modelos/auto_b.py [--sin-hoja]

Hatchback chico de dos volúmenes: capó corto, techo largo y portón trasero casi vertical,
con el parante de atrás ancho. Ver _auto.py para la forma, los objetos y los materiales.

Medidas: 1,737 × 1,50 × 3,70 (con los espejos; la chapa mide 1,66) (lista ≈ 1,7 × 1,5 × 3,8). Ruedas de radio 0,30 y ejes a 2,36 m:
si el juego usa este modelo, tiene que girar las ruedas con radio 0,30 (hoy usa 0,33).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _auto as auto  # noqa: E402
import _ciudad as ciudad  # noqa: E402

L = 1.82   # medio largo de la chapa (con paragolpes: 1,85)
P = {
    "id": "auto_b",
    "medidas": (1.737, 1.50, 3.70),
    "largo": 2 * L,
    "radio": 0.30,
    "ejes": (1.18, -1.18),
    "trocha": 0.70,
    "piso_puntas": [(-L, 0.33), (-1.65, 0.25), (1.65, 0.25), (L, 0.33)],
    "techo": [(-L, 1.02), (-1.76, 1.06), (-1.50, 1.47), (-0.5, 1.492), (0.30, 1.47), (0.95, 0.99),
              (1.65, 0.88), (L, 0.78)],
    "cintura": [(-L, 0.90), (-1.76, 0.95), (0.95, 0.93), (1.65, 0.83), (L, 0.72)],
    "ancho": [(-L, 0.77), (-1.70, 0.82), (-1.3, 0.83), (1.3, 0.83), (1.7, 0.81), (L, 0.75)],
    "ancho_techo": [(-L, 0.68), (-1.76, 0.72), (-1.50, 0.64), (0.30, 0.64), (0.95, 0.73), (L, 0.68)],
    "parabrisas": (0.30, 0.95),
    "luneta": (-1.76, -1.50),
    "parante_b": (-0.22, -0.15),
    "ventanillas": [(-0.15, 0.95), (-1.15, -0.22)],
    "paragolpes": (0.35, 0.40),
}

if __name__ == "__main__":
    auto.main(P, ciudad.m("auto_b · 1.74 × 1.5 × 3.7 m · auto chico · vehículo (genérico, sin marca)"))
