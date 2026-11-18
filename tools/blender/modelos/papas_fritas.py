"""Modelo: porción de papas fritas (id `papas_fritas`, productos.ron, SPEC-026).

Genera:
    arte/fuentes/comida/papas_fritas.blend
    godot/modelos/comida/papas_fritas.glb
    docs/arte/revisiones/papas_fritas.jpg

Uso:
    blender -b -P tools/blender/modelos/papas_fritas.py
    python tools/blender/modelos/papas_fritas.py

Forma: un puñado de 8 bastones fritos amontonados sin orden (dos capas que se cruzan, de 5,6 a
8,6 cm): sección cuadrada con las esquinas ochavadas (8 puntos, sombreado suave: se ven
redondeados y blandos), arqueados, con una punta más finita y algo torcidos, como salen de la
freidora. Dorado `M_PapaFrita`. Porción completa: 0,09 × 0,034 × 0,05, centrada (la caja de la
colisión del dato). Tope de comida armada (600 tris): es una porción de varias piezas.

Objeto único `papas_fritas`, origen en el centro (guía 2.4). Sin colisión (la define el dato).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402,F401  (antes que bmesh)
import bmesh  # noqa: E402

import comun  # noqa: E402
import _comida4 as c4  # noqa: E402
import _papas as pp  # noqa: E402

ID = "papas_fritas"
MEDIDAS = pp.MEDIDAS[ID]
LADO = 0.0095
# (largo, x, y, z, giro Y, inclinación Z, arco Y, arco Z, afinar −X, afinar +X, torsión)
BASTONES = [
    (0.086, 0.000, 0.000, -0.018, 6, 0, 0.002, -0.002, 0.8, 1.0, 10),
    (0.080, 0.004, 0.000, -0.006, -4, 0, -0.0015, 0.002, 1.0, 0.75, -8),
    (0.075, -0.003, 0.000, 0.006, 9, 0, 0.002, 0.0015, 0.85, 1.0, 12),
    (0.070, 0.002, 0.000, 0.018, -7, 0, 0.0015, -0.002, 1.0, 0.8, -6),
    (0.082, -0.002, 0.0095, -0.010, -22, 4, 0.003, 0.0, 0.9, 1.0, 15),
    (0.072, 0.004, 0.0095, 0.004, 28, -5, 0.0025, -0.002, 1.0, 0.8, -12),
    (0.064, -0.006, 0.0105, 0.014, -38, 6, -0.002, 0.002, 0.8, 1.0, 8),
    (0.056, 0.010, 0.019, -0.002, 55, 8, 0.002, 0.0, 1.0, 0.75, -10),
]


def construir(nombre=ID):
    frita, = comun.cargar_materiales("M_PapaFrita")
    bm = bmesh.new()
    for largo, x, y, z, giro, incl, ay, az, a0, a1, tor in BASTONES:
        pp.baston(bm, largo, LADO, (x, y, z), rot=(0, giro, incl), curva=(ay, az),
                  afinar=(a0, a1), torsion=tor, ochave=0.0028)
    pp.ajustar_caja(bm, MEDIDAS)
    return c4.terminar(nombre, bm, [frita])


def revisar(obj):
    return comun.revisar(obj, pp.PRESUPUESTO_PORCION, MEDIDAS, origen="centro")


def main():
    pp.main_comida(ID, construir, revisar, "papas_fritas · 0,09 × 0,034 × 0,05 m · porción de papas fritas (comida)")


if __name__ == "__main__":
    main()
