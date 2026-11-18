"""Modelo: papa pelada (id `papa_pelada`, godot/data/productos.ron, SPEC-026).

Genera:
    arte/fuentes/comida/papa_pelada.blend
    godot/modelos/comida/papa_pelada.glb
    docs/arte/revisiones/papa_pelada.jpg

Uso:
    blender -b -P tools/blender/modelos/papa_pelada.py
    python tools/blender/modelos/papa_pelada.py

Forma: la misma papa que `papa_cruda` (misma semilla de lomas) pero sin la cáscara: un poco
más chica (0,086 × 0,052 × 0,062) y con menos caras (10 lados × 6 anillos) en sombreado
**facetado**, a propósito: son los cortes planos del pelapapas, y así se distingue de la
cruda aun de lejos o de noche (excepción a la guía 3.4, que pide comida suave). Pulpa
`M_PapaPulpa`, con dos ojos que quedaron (caras hundidas en `M_PapaCascara`).

Objeto único `papa_pelada`, origen en el centro (guía 2.4). Sin colisión (la define el dato).
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

ID = "papa_pelada"
MEDIDAS = pp.MEDIDAS[ID]
SEMILLA = 7  # la misma papa que papa_cruda


def construir(nombre=ID):
    pulpa, cascara = comun.cargar_materiales("M_PapaPulpa", "M_PapaCascara")
    bm = bmesh.new()
    pp.papa(bm, MEDIDAS, SEMILLA, lados=10, anillos=6, ojos=2, mat_ojo=1, lomas=0.04)
    return e2.objeto_en(nombre, bm, [pulpa, cascara], (0, 0, 0), sombreado="plano")


def revisar(obj):
    return comun.revisar(obj, pp.PRESUPUESTO_CHICA, MEDIDAS, origen="centro")


def main():
    pp.main_comida(ID, construir, revisar, "papa_pelada · 0,086 × 0,052 × 0,062 m · papa pelada, facetada (comida)")


if __name__ == "__main__":
    main()
