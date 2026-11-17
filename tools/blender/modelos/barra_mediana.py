"""Modelo: barra mediana (id `barra_mediana`, godot/data/carritos/barra_mediana.ron).

Genera:
    arte/fuentes/carritos/barra_mediana.blend
    godot/modelos/carritos/barra_mediana.glb
    docs/arte/revisiones/barra_mediana.jpg

Uso:
    blender -b -P tools/blender/modelos/barra_mediana.py
    python tools/blender/modelos/barra_mediana.py

La barra larga: 2,4 × 0,95 × 0,8 m (3 puestos de mostrador), con 3 puertitas del lado del
vendedor. La construcción (compartida con barra_mediana y carro_grande), qué se mide y qué
objetos lleva están explicados en _base_carrito.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _base_carrito as base  # noqa: E402

ID = "barra_mediana"
DATOS = base.leer_ron(ID)
MEDIDAS = (DATOS["ancho"], DATOS["alto"], DATOS["profundidad"])  # cuerpo y mesada (ver base)
PRESUPUESTO = base.PRESUPUESTO
PUERTAS = 3


def main():
    base.main(ID, "barra mediana (3 puertitas)", puertas=PUERTAS)


if __name__ == "__main__":
    main()
