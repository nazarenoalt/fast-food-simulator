"""Modelo: freidora doble (id `freidora_doble`, accesorios.ron, SPEC-026).

Genera:
    arte/fuentes/cocina/freidora_doble.blend
    godot/modelos/cocina/freidora_doble.glb
    docs/arte/revisiones/freidora_doble.jpg

Uso:
    blender -b -P tools/blender/modelos/freidora_doble.py
    python tools/blender/modelos/freidora_doble.py

Dos freidoras como `freidora` (ver _freidora.py) en un solo mueble, con un cabezal corrido y
una perilla y un piloto por cuba: 0,521 × 0,328 × 0,474. Ocupa un solo anclaje de mostrador y
entra en la porción más chica (0,57 m entre anclajes del carro kiosco).

Objetos (hijos del Empty `freidora_doble`): `freidora_doble_cuerpo`, `pieza_piloto_1/2`,
`pieza_aceite_1/2`, `punto_colador_1/2` (centro de cada canasto apoyado) y
`freidora_doble-colonly` (las dos cubas huecas y el cabezal).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _equipos as eq  # noqa: E402
import _freidora as fr  # noqa: E402

ID = "freidora_doble"
CXS = [-0.1305, 0.1305]
MEDIDAS = (CXS[1] - CXS[0] + fr.ANCHO, fr.ALTO, fr.PROFUNDIDAD)


def construir():
    return fr.construir(ID, CXS)


def revisar(m):
    return fr.revisar(m, MEDIDAS)


def hoja(m, revision):
    fr.hoja(ID, "freidora_doble · 0,521 × 0,328 × 0,474 m · equipo de cocina (dos cubas, un anclaje)",
            m["raiz"], fr.visibles(m), fr.coladores(m), revision)


def main():
    eq.main_modelo(ID, fr.FAMILIA, construir, revisar, hoja, fr.exportar)


if __name__ == "__main__":
    main()
