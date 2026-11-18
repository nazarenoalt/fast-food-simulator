"""Modelo: cajonera de 3 cajones (id `alacena_cajones`, bajo mesada, familia accesorios).

Genera:
    arte/fuentes/accesorios/alacena_cajones.blend
    godot/modelos/accesorios/alacena_cajones.glb
    docs/arte/revisiones/alacena_cajones.jpg

Uso:
    blender -b -P tools/blender/modelos/alacena_cajones.py
    python tools/blender/modelos/alacena_cajones.py

Tres cajones de acero con tirador corrido negro, numerados de arriba hacia abajo. 6 lugares:
2 en el piso de cada cajón (hijos del cajón, se mueven con él).

Medida única de todas las alacenas (entran en cualquier bahía de cualquier carrito), origen,
materiales, objetos y chequeos: ver _alacena.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _alacena  # noqa: E402

ID = "alacena_cajones"
VARIANTE = "cajones"
MEDIDAS = _alacena.medidas(VARIANTE)
PRESUPUESTO = _alacena.PRESUPUESTO


def main():
    _alacena.main(VARIANTE)


if __name__ == "__main__":
    main()
