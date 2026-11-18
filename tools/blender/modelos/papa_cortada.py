"""Modelo: papas cortadas en bastones, crudas (id `papa_cortada`, productos.ron, SPEC-026).

Genera:
    arte/fuentes/comida/papa_cortada.blend
    godot/modelos/comida/papa_cortada.glb
    docs/arte/revisiones/papa_cortada.jpg

Uso:
    blender -b -P tools/blender/modelos/papa_cortada.py
    python tools/blender/modelos/papa_cortada.py

Forma: una papa cortada en bastones de 1 cm (como para freír), apilados en tres capas (4, 3 y
2), casi paralelos: cortes rectos de aristas vivas (sección cuadrada, 4 puntos, sombreado
duro: así se distinguen de las fritas, que son doradas, ochavadas y torcidas). Cada bastón
tiene su largo (de 6,4 a 8,4 cm, como salen de una papa) y una punta más finita (el borde
redondeado de la papa). Pulpa `M_PapaPulpa`. Porción completa: 0,084 × 0,031 × 0,045,
centrada (la caja de la colisión del dato).

Objeto único `papa_cortada`, origen en el centro (guía 2.4). Sin colisión (la define el dato).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402,F401  (antes que bmesh)
import bmesh  # noqa: E402

import comun  # noqa: E402
import _etapa2 as e2  # noqa: E402
import _papas as pp  # noqa: E402

ID = "papa_cortada"
MEDIDAS = pp.MEDIDAS[ID]
LADO = 0.0098
# (largo, x, capa, z, giro en Y, afinar −X, afinar +X)
BASTONES = [
    (0.084, 0.000, 0, -0.0165, 2, 0.8, 1.0),
    (0.078, 0.002, 0, -0.0055, -1, 1.0, 0.85),
    (0.081, -0.001, 0, 0.0055, 1.5, 0.9, 1.0),
    (0.072, 0.003, 0, 0.0165, -2, 1.0, 0.8),
    (0.080, -0.002, 1, -0.011, -3, 1.0, 0.85),
    (0.075, 0.002, 1, 0.000, 2.5, 0.85, 1.0),
    (0.069, -0.003, 1, 0.011, -1, 1.0, 0.9),
    (0.070, 0.001, 2, -0.0055, 4, 0.9, 1.0),
    (0.064, -0.002, 2, 0.0055, -3, 1.0, 0.8),
]


def construir(nombre=ID):
    pulpa, = comun.cargar_materiales("M_PapaPulpa")
    bm = bmesh.new()
    for largo, x, capa, z, giro, a0, a1 in BASTONES:
        pp.baston(bm, largo, LADO, (x, capa * (LADO + 0.0005), z), rot=(0, giro, 0),
                  afinar=(a0, a1), cuadrado=True)
    pp.ajustar_caja(bm, MEDIDAS)
    return e2.objeto_en(nombre, bm, [pulpa], (0, 0, 0), sombreado="duro")


def revisar(obj):
    return comun.revisar(obj, pp.PRESUPUESTO_CHICA, MEDIDAS, origen="centro")


def main():
    pp.main_comida(ID, construir, revisar, "papa_cortada · 0,084 × 0,031 × 0,045 m · bastones crudos (comida)")


if __name__ == "__main__":
    main()
