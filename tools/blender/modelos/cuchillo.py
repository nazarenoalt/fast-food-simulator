"""Modelo: cuchillo de cocina (id `cuchillo`, godot/data/productos.ron, SPEC-026).

Genera:
    arte/fuentes/cocina/cuchillo.blend
    godot/modelos/cocina/cuchillo.glb
    docs/arte/revisiones/cuchillo.jpg

Uso:
    blender -b -P tools/blender/modelos/cuchillo.py
    python tools/blender/modelos/cuchillo.py

Forma: cuchillo de cocinero de 27 cm, acostado (como queda sobre la mesada): la hoja en el
plano XZ, el filo hacia −Z. Hoja de acero de 16 cm y 3 mm (guía 2.2) con silueta de cuchillo
de verdad: lomo recto que cae hacia la punta y filo con panza que sube a la punta (nada de
rectángulo). Virola de acero biselada y mango negro de sección redondeada que se ensancha hacia
atrás y termina un poco caído, con tres remaches de acero de los dos lados.

Medidas: 0,27 × 0,017 × 0,034 (largo × grueso del mango con remaches × alto de la hoja en el
talón). Objeto único `cuchillo`, origen en el centro de la caja (= centro de la colisión del
dato, guía 2.4). Sin colisión: la define el dato (guía 6.1).
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

ID = "cuchillo"
FAMILIA = "cocina"
PRESUPUESTO = 500  # utensilios (guía 3.1)
MEDIDAS = (0.27, 0.017, 0.034)
ACERO, NEGRO = range(2)
ESP = 0.003
# Silueta de la hoja en planta (x, z), del talón del filo a la punta y de vuelta por el lomo.
HOJA = [(-0.02, -0.0175), (0.05, -0.0175), (0.095, -0.014), (0.125, -0.008), (0.145, -0.001),
        (0.155, 0.006), (0.13, 0.0115), (0.07, 0.0155), (-0.02, 0.0165)]
X_VIROLA = -0.02


def construir():
    acero, negro = comun.cargar_materiales("M_Acero", "M_PlasticoNegro")
    bm = bmesh.new()
    eq.prisma(bm, HOJA, -ESP / 2, ESP / 2, mat=ACERO)
    piezas.caja(bm, (0.012, 0.014, 0.03), (X_VIROLA - 0.006, 0, -0.001), mat=ACERO, bisel=0.002)
    # Mango: de la virola hacia atrás, se ensancha y cae apenas en la punta.
    pp.mango(bm, [(X_VIROLA - 0.011, 0.0065, 0.0095, 0.004), (-0.07, 0.0075, 0.0105, 0.0045),
                  (-0.105, 0.0078, 0.0112, 0.0045), (-0.115, 0.007, 0.0102, 0.004)], mat=NEGRO)
    for x in (-0.045, -0.07, -0.095):
        for lado in (-1, 1):
            piezas.cilindro(bm, 0.0028, 0.0018, (x, lado * 0.0077, -0.001), lados=8, mat=ACERO,
                            tapas=(lado < 0, lado > 0))
    eq.centrar(bm)
    obj = piezas.terminar(ID, bm, [acero, negro])
    return {"obj": obj}


def revisar(m):
    return comun.revisar(m["obj"], PRESUPUESTO, MEDIDAS, origen="centro")


def hoja(m, revision):
    eq.hoja_mano(ID, "cuchillo · 0,27 × 0,017 × 0,034 m · utensilio (origen en el centro)", m["obj"], revision)


def main():
    eq.main_modelo(ID, FAMILIA, construir, revisar, hoja, lambda m: [m["obj"]])


if __name__ == "__main__":
    main()
