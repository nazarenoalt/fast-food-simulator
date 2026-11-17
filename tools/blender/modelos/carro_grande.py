"""Modelo: carro grande (id `carro_grande`, godot/data/carritos/carro_grande.ron).

Genera:
    arte/fuentes/carritos/carro_grande.blend
    godot/modelos/carritos/carro_grande.glb
    docs/arte/revisiones/carro_grande.jpg

Uso:
    blender -b -P tools/blender/modelos/carro_grande.py
    python tools/blender/modelos/carro_grande.py

El carro más grande: 3,4 × 1,0 × 1,2 m. Mismo diseño que las barras pero más robusto: zócalo
más alto, manija más gruesa, 4 patas niveladoras con taco de goma y, del lado del vendedor,
abierto bajo la mesada con un estante bajo, un estante intermedio y el lugar para la garrafa
en la punta +X (con cincha y rejilla de ventilación en el costado). La construcción, qué se
mide y qué objetos lleva están explicados en _base_carrito.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _base_carrito as base  # noqa: E402

ID = "carro_grande"
DATOS = base.leer_ron(ID)
MEDIDAS = (DATOS["ancho"], DATOS["alto"], DATOS["profundidad"])  # cuerpo y mesada (ver base)
PRESUPUESTO = base.PRESUPUESTO


def main():
    base.main(ID, "carro grande (estante bajo y garrafa)", grande=True)


if __name__ == "__main__":
    main()
