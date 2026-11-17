"""Modelo: alacena de 2 puertas (id `alacena_puertas`, bajo mesada, familia accesorios).

Genera:
    arte/fuentes/accesorios/alacena_puertas.blend
    godot/modelos/accesorios/alacena_puertas.glb
    docs/arte/revisiones/alacena_puertas.jpg

Uso:
    blender -b -P tools/blender/modelos/alacena_puertas.py
    python tools/blender/modelos/alacena_puertas.py

Dos puertas batientes de acero con tirador vertical negro y, adentro, un estante de chapa
con pestaña. 4 lugares: 2 en el piso y 2 en el estante.

Medida única de todas las alacenas (entran en cualquier bahía de cualquier carrito), origen,
materiales, objetos y chequeos: ver _alacena.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _alacena  # noqa: E402

ID = "alacena_puertas"
VARIANTE = "puertas"
MEDIDAS = _alacena.medidas(VARIANTE)
PRESUPUESTO = _alacena.PRESUPUESTO


def main():
    _alacena.main(VARIANTE)


if __name__ == "__main__":
    main()
