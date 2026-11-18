"""Modelo: charco (id `charco`, familia `ciudad`).

Genera:
    arte/fuentes/ciudad/charco.blend
    godot/modelos/ciudad/charco.glb
    docs/arte/revisiones/charco.jpg

Uso:
    python tools/blender/modelos/charco.py [--sin-hoja]

Charco de agua quieta para cuando llueva (hoy el juego no tiene lluvia: SPEC-013 la deja
afuera). Es una lámina con contorno irregular de 10 puntos (sin simetría), con el borde
apenas biselado hacia el piso (un anillo de 3 cm que baja 5 mm) para que no tenga un canto
vivo, y sin cara de abajo (apoya en el piso, guía 3.6). Es una pieza de agua quieta, así que
va como malla `pieza_agua` (guía 5.4), con M_Agua (transparente, alfa 0,7).

Origen = centro de la base, a nivel del piso. Ojo al ponerla: la vereda del juego es una caja
de 1 cm (su cara de arriba está a 0,011 m) y la calle es el terreno: el charco va apoyado
sobre esa cara, no en y = 0, o queda tapado.

Medidas: 1,00 × 0,005 × 0,70 (las de la lista). Sin colisión.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402, F401  (antes que bmesh)
import bmesh  # noqa: E402

import _ciudad as ciudad  # noqa: E402
import comun  # noqa: E402
import piezas  # noqa: E402
from piezas import g2b  # noqa: E402

ID = "charco"
PRESUPUESTO = 30       # lista de modelos
MEDIDAS = (1.0, 0.005, 0.7)
ALTO, BORDE = 0.005, 0.03
# Contorno: radio relativo en cada uno de 10 ángulos (irregular, a mano).
CONTORNO = [1.0, 0.7, 0.62, 0.95, 1.08, 0.8, 0.58, 0.72, 0.98, 0.85]


def construir():
    (agua,) = comun.cargar_materiales("M_Agua")
    n = len(CONTORNO)
    pts = [(r * math.cos(2 * math.pi * k / n + 0.2), r * math.sin(2 * math.pi * k / n + 0.2))
           for k, r in enumerate(CONTORNO)]
    # Escala y centrado: la caja envolvente justa de 1,0 × 0,7, centrada en el origen.
    xs, zs = [p[0] for p in pts], [p[1] for p in pts]
    cx, cz = (max(xs) + min(xs)) / 2, (max(zs) + min(zs)) / 2
    sx, sz = MEDIDAS[0] / (max(xs) - min(xs)), MEDIDAS[2] / (max(zs) - min(zs))
    afuera = [((x - cx) * sx, (z - cz) * sz) for x, z in pts]
    # Anillo de adentro: cada punto se corre BORDE hacia el centro.
    adentro = []
    for x, z in afuera:
        d = math.hypot(x, z)
        adentro.append((x * (d - BORDE) / d, z * (d - BORDE) / d))
    bm = bmesh.new()
    va = [bm.verts.new(g2b((x, 0.0, z))) for x, z in afuera]
    vi = [bm.verts.new(g2b((x, ALTO, z))) for x, z in adentro]
    arriba = bm.faces.new(vi)
    arriba.normal_update()
    if arriba.normal.z < 0:
        arriba.normal_flip()
    for k in range(n):
        k2 = (k + 1) % n
        f = bm.faces.new((va[k], va[k2], vi[k2], vi[k]))
        f.normal_update()
        medio = f.calc_center_median()
        if f.normal.x * medio.x + f.normal.y * medio.y < 0:
            f.normal_flip()
    obj = ciudad.terminar("pieza_agua", bm, [agua], sombreado="plano")
    raiz = piezas.raiz(ID, [obj])
    return {"raiz": raiz, "agua": obj}


def main():
    comun.escena_vacia()
    m = construir()
    revision = comun.revisar(m["agua"], PRESUPUESTO, MEDIDAS, origen="base")
    ok, texto = ciudad.chequeo_normales([m["agua"]], frente=False)
    revision = ciudad.reemplazar(revision, "Normales", ok, texto + " (lámina abierta: sin cara de abajo)")
    ok = comun.imprimir_revision(ID, revision)
    ciudad.guardar_y_exportar(ID, [m["raiz"], m["agua"]])
    if "--sin-hoja" not in sys.argv:
        c = [m["agua"]]
        ciudad.hoja(ID, "charco · 1,0 × 0,005 × 0,7 m · agua quieta (pieza_agua)", [
            ("Arriba · día", c, "arriba", "dia", True),
            ("Frente · día", c, "frente", "dia", True),
            ("3/4 · día", c, "tres_cuartos", "dia", False),
            ("3/4 · atardecer", c, "tres_cuartos", "atardecer", False),
            ("Con la persona de 1,75 m · día", c + ["persona"], "tres_cuartos", "dia", False),
        ], revision, persona_en=(0.9, 0, -0.3))
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
