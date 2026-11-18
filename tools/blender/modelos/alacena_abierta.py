"""Modelo: alacena abierta (id `alacena_abierta`, bajo mesada, familia accesorios).

Genera:
    arte/fuentes/accesorios/alacena_abierta.blend
    godot/modelos/accesorios/alacena_abierta.glb
    docs/arte/revisiones/alacena_abierta.jpg

Uso:
    blender -b -P tools/blender/modelos/alacena_abierta.py
    python tools/blender/modelos/alacena_abierta.py

Sin puertas: 2 estantes de chapa con pestaña a la vista (piso + 2 estantes = 3 niveles).
6 lugares: 2 por nivel.

Medida única de todas las alacenas (entran en cualquier bahía de cualquier carrito), origen,
materiales, objetos y chequeos: ver _alacena.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _alacena  # noqa: E402

ID = "alacena_abierta"
VARIANTE = "abierta"
MEDIDAS = _alacena.medidas(VARIANTE)
PRESUPUESTO = _alacena.PRESUPUESTO


def main():
    _alacena.main(VARIANTE)


if __name__ == "__main__":
    main()
