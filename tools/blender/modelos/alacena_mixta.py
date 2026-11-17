"""Modelo: alacena de puerta y cajones (id `alacena_mixta`, bajo mesada, familia accesorios).

Genera:
    arte/fuentes/accesorios/alacena_mixta.blend
    godot/modelos/accesorios/alacena_mixta.glb
    docs/arte/revisiones/alacena_mixta.jpg

Uso:
    blender -b -P tools/blender/modelos/alacena_mixta.py
    python tools/blender/modelos/alacena_mixta.py

Una puerta (bisagra en −X) con estante adentro y, del lado +X, una columna de 3 cajones,
separadas por un montante en el marco y un tabique. 5 lugares: piso y estante del lado de la
puerta, y uno por cajón.

Medida única de todas las alacenas (entran en cualquier bahía de cualquier carrito), origen,
materiales, objetos y chequeos: ver _alacena.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _alacena  # noqa: E402

ID = "alacena_mixta"
VARIANTE = "mixta"
MEDIDAS = _alacena.medidas(VARIANTE)
PRESUPUESTO = _alacena.PRESUPUESTO


def main():
    _alacena.main(VARIANTE)


if __name__ == "__main__":
    main()
