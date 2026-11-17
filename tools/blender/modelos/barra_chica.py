"""Modelo: barra chica (id `barra_chica`, godot/data/carritos/barra_chica.ron).

Genera:
    arte/fuentes/carritos/barra_chica.blend
    godot/modelos/carritos/barra_chica.glb
    docs/arte/revisiones/barra_chica.jpg

Uso:
    blender -b -P tools/blender/modelos/barra_chica.py
    python tools/blender/modelos/barra_chica.py

El carrito con el que arranca el jugador: 1,6 × 0,95 × 0,7 m, con 2 puertitas del lado del
vendedor. La construcción (compartida con barra_mediana y carro_grande), qué se mide y qué
objetos lleva están explicados en _base_carrito.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _base_carrito as base  # noqa: E402

ID = "barra_chica"
DATOS = base.leer_ron(ID)
MEDIDAS = (DATOS["ancho"], DATOS["alto"], DATOS["profundidad"])  # cuerpo y mesada (ver base)
PRESUPUESTO = base.PRESUPUESTO
PUERTAS = 2


def main():
    base.main(ID, "barra chica (2 puertitas)", puertas=PUERTAS)


if __name__ == "__main__":
    main()
