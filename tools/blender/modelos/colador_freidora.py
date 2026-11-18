"""Modelo: colador (canasto) de la freidora (id `colador_freidora`, productos.ron, SPEC-026).

Genera:
    arte/fuentes/cocina/colador_freidora.blend
    godot/modelos/cocina/colador_freidora.glb
    docs/arte/revisiones/colador_freidora.jpg

Uso:
    blender -b -P tools/blender/modelos/colador_freidora.py
    python tools/blender/modelos/colador_freidora.py

Forma: canasto de alambre de freidora de 0,19 × 0,095 × 0,27, planta redondeada y fondo con
el canto redondeado. La malla no se ve a 2 m (guía 3.5): las paredes son `M_MetalOscuro` y la
leen como malla los alambres de acero de afuera (4 verticales en cada lado largo, 2 en los
cortos y un cinturón a media altura) y el aro de acero de la boca. Pared de 3 mm.
Del lado del vendedor (−Z) sale el mango: una varilla que sube derecho 5 cm (para pasar el
borde de la cuba) y después se va hacia el vendedor subiendo 25°, con el puño negro. Del lado
del cliente (+Z), el gancho para colgarlo.

Origen = centro del **canasto** (= centro de la colisión del dato, que es solo el canasto:
así entra en la cuba de la freidora, `_freidora.CANASTO`). El mango y el gancho sobresalen:
el chequeo de origen y de medidas se reemplaza por uno propio que mide el canasto (las caras
de M_MetalOscuro). Sin colisión en el modelo (la define el dato, guía 6.1).
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
import _etapa2 as e2  # noqa: E402
import _freidora as fr  # noqa: E402

ID = "colador_freidora"
FAMILIA = "cocina"
PRESUPUESTO = 500  # utensilios (guía 3.1)
ACERO, OSCURO, NEGRO = range(3)
CX, CY, CZ = fr.CANASTO
HX, HY, HZ = CX / 2, CY / 2, CZ / 2
A = 0.003  # alambres y pared


def construir():
    mats = fr.materiales()
    bm = bmesh.new()
    perfil = [(0.006, 0.0), (0.0, 0.006), (0.0, CY - 0.008), (0.0, CY), (A, CY), (A, A)]
    e2.torno_rr(bm, perfil, HX, HZ, 0.012, segs=1, centro=(0, -HY, 0),
                mats=[OSCURO, OSCURO, ACERO, ACERO, OSCURO], tapa_ini=True, tapa_fin=True)
    # Alambres de afuera (sin bisel: son alambres de 3 mm).
    alto = CY - 0.014
    for z in (-0.09, -0.03, 0.03, 0.09):
        for lado in (-1, 1):
            piezas.caja(bm, (A, alto, A), (lado * (HX + A / 2), -HY + 0.006 + alto / 2, z), mat=ACERO)
    for x in (-0.045, 0.045):
        for lado in (-1, 1):
            piezas.caja(bm, (A, alto, A), (x, -HY + 0.006 + alto / 2, lado * (HZ + A / 2)), mat=ACERO)
    for lado in (-1, 1):
        piezas.caja(bm, (A, A, CZ - 0.02), (lado * (HX + A), 0.0, 0.0), mat=ACERO)
        piezas.caja(bm, (CX - 0.02, A, A), (0.0, 0.0, lado * (HZ + A)), mat=ACERO)
    # Mango: sube derecho y sale hacia el vendedor a 25°, con el puño negro.
    z_m = -HZ + 0.004
    piezas.cilindro(bm, 0.004, 0.058, (0, HY + 0.02, z_m), lados=8, mat=ACERO)
    import math
    d = (0.0, math.sin(math.radians(25)), -math.cos(math.radians(25)))
    p0 = (0.0, HY + 0.047, z_m)
    def punto(t):
        return tuple(p0[i] + d[i] * t for i in range(3))
    piezas.cilindro(bm, 0.004, 0.075, punto(0.0375), eje="z", lados=8, mat=ACERO, rot=(25, 0, 0))
    piezas.cilindro(bm, 0.011, 0.10, punto(0.075 + 0.05), eje="z", lados=8, mat=NEGRO, rot=(25, 0, 0))
    # Gancho del lado del cliente.
    piezas.caja(bm, (0.03, 0.034, A), (0, HY + 0.012, HZ + A / 2), mat=ACERO, bisel=0.0008)
    piezas.caja(bm, (0.03, A, 0.012), (0, HY + 0.0275, HZ + 0.006), mat=ACERO, bisel=0.0008)
    return {"obj": piezas.terminar(ID, bm, mats)}


def chequeo_canasto(obj):
    vs = eq.caras_material(obj, OSCURO)
    mn = [min(v[i] for v in vs) for i in range(3)]
    mx = [max(v[i] for v in vs) for i in range(3)]
    tam = [mx[i] - mn[i] for i in range(3)]
    centro = [(mx[i] + mn[i]) / 2 for i in range(3)]
    ok = all(abs(tam[i] - fr.CANASTO[i]) < 0.001 for i in range(3)) and all(abs(c) < 0.001 for c in centro)
    return ok, ("Canasto %.3f × %.3f × %.3f m (dato: %.3f × %.3f × %.3f), centrado en el origen "
                "(%.3f, %.3f, %.3f); el mango y el gancho sobresalen" % (*tam, *fr.CANASTO, *centro))


def revisar(m):
    obj = m["obj"]
    mn, mx = e2.limites_godot([obj])
    t = mx - mn
    res = comun.revisar(obj, PRESUPUESTO, (t.x, t.y, t.z), origen="centro")
    res = comun.reemplazar_linea(res, "Medidas", True, "Medidas totales %.3f × %.3f × %.3f m "
                                 "(con el mango)" % (t.x, t.y, t.z))
    return comun.reemplazar_linea(res, "Origen", *chequeo_canasto(obj))


def hoja(m, revision):
    eq.hoja_mano(ID, "colador_freidora · canasto 0,19 × 0,095 × 0,27 m · utensilio (origen en el canasto)",
                 m["obj"], revision)


def main():
    eq.main_modelo(ID, FAMILIA, construir, revisar, hoja, lambda m: [m["obj"]])


if __name__ == "__main__":
    main()
