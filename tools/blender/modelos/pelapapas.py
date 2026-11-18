"""Modelo: pelapapas (id `pelapapas`, godot/data/productos.ron, SPEC-026).

Genera:
    arte/fuentes/cocina/pelapapas.blend
    godot/modelos/cocina/pelapapas.glb
    docs/arte/revisiones/pelapapas.jpg

Uso:
    blender -b -P tools/blender/modelos/pelapapas.py
    python tools/blender/modelos/pelapapas.py

Forma: pelapapas de hoja giratoria, acostado. Mango negro de sección redondeada que se afina
hacia el cuello, con el agujero para colgarlo marcado como un aro de acero en la punta.
Cuello de acero y cabeza en U (dos varillas de 4 mm que se juntan en la punta), con la hoja
de 13 mm en el medio (la ranura del filo, una línea negra) y, de un costado, la uña
para sacar los ojos de la papa (una punta de acero). Todo de 3 mm o más (guía 2.2).

Medidas: 0,18 × 0,014 × 0,034. Objeto único `pelapapas`, origen en el centro de la caja (=
centro de la colisión del dato, guía 2.4). Sin colisión: la define el dato (guía 6.1).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402,F401  (antes que bmesh)
import bmesh  # noqa: E402

import comun  # noqa: E402
import piezas  # noqa: E402
import _equipos as eq  # noqa: E402
import _papas as pp  # noqa: E402

ID = "pelapapas"
FAMILIA = "cocina"
PRESUPUESTO = 500  # utensilios (guía 3.1)
MEDIDAS = (0.18, 0.014, 0.034)
ACERO, NEGRO = range(2)
V = 0.004   # varillas de la cabeza


def construir():
    acero, negro = comun.cargar_materiales("M_Acero", "M_PlasticoNegro")
    bm = bmesh.new()
    # Mango (−X), del extremo al cuello.
    pp.mango(bm, [(-0.114, 0.0055, 0.0095, 0.004), (-0.104, 0.007, 0.0118, 0.005),
                  (-0.04, 0.0068, 0.0105, 0.0045), (-0.012, 0.0052, 0.0075, 0.003)], mat=NEGRO, segs=1)
    piezas.cilindro(bm, 0.0065, 0.004, (-0.106, 0.0, 0.0), lados=8, mat=ACERO)   # aro de colgar
    # Cuello y cabeza en U.
    piezas.caja(bm, (0.026, 0.005, 0.009), (-0.004, 0.0, 0.0), mat=ACERO, bisel=0.0012)
    for lado in (-1, 1):
        piezas.caja(bm, (0.062, V, V), (0.035, 0.0, lado * 0.0115), mat=ACERO, bisel=0.001)
        piezas.caja(bm, (0.012, V, V), (0.006, 0.0, lado * 0.0078), rot=(0, lado * 30, 0),
                    mat=ACERO, bisel=0.001)
    piezas.caja(bm, (V, V, 0.027), (0.064, 0.0, 0.0), mat=ACERO, bisel=0.001)
    # Hoja de 13 mm entre las varillas, con la ranura del filo marcada en negro.
    piezas.caja(bm, (0.054, 0.003, 0.013), (0.035, 0.0, 0.0), rot=(6, 0, 0), mat=ACERO,
                bisel=0.0008)
    piezas.caja(bm, (0.042, 0.0034, 0.0018), (0.035, 0.0, 0.0), rot=(6, 0, 0), mat=NEGRO)
    # Uña para los ojos de la papa.
    piezas.cilindro(bm, 0.003, 0.009, (0.012, 0.0, 0.0155), eje="z", lados=8, mat=ACERO,
                    radio_arriba=0.0008)
    eq.centrar(bm)
    return {"obj": piezas.terminar(ID, bm, [acero, negro])}


def revisar(m):
    return comun.revisar(m["obj"], PRESUPUESTO, MEDIDAS, origen="centro")


def hoja(m, revision):
    eq.hoja_mano(ID, "pelapapas · 0,18 × 0,014 × 0,034 m · utensilio (origen en el centro)", m["obj"], revision)


def main():
    eq.main_modelo(ID, FAMILIA, construir, revisar, hoja, lambda m: [m["obj"]])


if __name__ == "__main__":
    main()
