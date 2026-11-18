"""Modelo: papa cruda sin pelar (id `papa_cruda`, godot/data/productos.ron, SPEC-026).

Genera:
    arte/fuentes/comida/papa_cruda.blend
    godot/modelos/comida/papa_cruda.glb
    docs/arte/revisiones/papa_cruda.jpg

Uso:
    blender -b -P tools/blender/modelos/papa_cruda.py
    python tools/blender/modelos/papa_cruda.py

Forma: papa mediana (~200 g) de 0,095 × 0,058 × 0,068, nada de esfera perfecta: elipsoide
acostado sobre X con lomas suaves fijas al azar, un poco arriñonado y con la panza de abajo
más chata (así apoya). Esfera UV de 14 lados × 8 anillos con los polos en las puntas
(_papas.papa). Cinco ojos repartidos (cada uno lejos de los otros): caras chicas hundidas 0,8 mm en `M_Tronco`. Cáscara
`M_PapaCascara`. Sombreado suave (guía 3.4), sin bisel (comida).

Objeto único `papa_cruda`, origen en el centro (= centro de la colisión del dato, guía 2.4).
Sin colisión: la define el dato (guía 6.1).
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

ID = "papa_cruda"
MEDIDAS = pp.MEDIDAS[ID]
SEMILLA = 7


def construir(nombre=ID):
    cascara, ojo = pp.material_ojo_y_cascara()
    bm = bmesh.new()
    pp.papa(bm, MEDIDAS, SEMILLA, lados=14, anillos=8, ojos=5, mat_ojo=1, lomas=0.045)
    return c4.terminar(nombre, bm, [cascara, ojo])


def revisar(obj):
    return comun.revisar(obj, pp.PRESUPUESTO_CHICA, MEDIDAS, origen="centro")


def main():
    pp.main_comida(ID, construir, revisar, "papa_cruda · 0,095 × 0,058 × 0,068 m · papa sin pelar (comida)")


if __name__ == "__main__":
    main()
