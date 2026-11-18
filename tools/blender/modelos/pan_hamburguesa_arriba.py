"""Modelo: pan de hamburguesa, la tapa (id `pan_hamburguesa_arriba`, etapa 4; sin dato todavía).

Genera:
    arte/fuentes/comida/pan_hamburguesa_arriba.blend
    godot/modelos/comida/pan_hamburguesa_arriba.glb
    docs/arte/revisiones/pan_hamburguesa_arriba.jpg

Uso:
    blender -b -P tools/blender/modelos/pan_hamburguesa_arriba.py
    python tools/blender/modelos/pan_hamburguesa_arriba.py

Forma: la tapa del pan de hamburguesa, Ø 0,11 × 0,045 (lista de modelos), 16 lados (guía
3.2): un domo inflado de corteza (M_PanCorteza) con el corte de miga (M_PanMiga) abajo,
plano, para que apoye derecho sobre el queso o el medallón. Radio con una ondulación muy
chica, para que no parezca torneado.

Semillas de sésamo pintadas (lista de modelos: "color, no geometría"): no son piezas sueltas
ni caritas flotando, sino caras de la misma superficie del domo con color de miga. En 6
caras del domo se mete una cara chiquita (≈ 5,5 × 2,7 mm, girada al azar) unida a las esquinas
de la cara original: el domo sigue siendo una sola cáscara cerrada. Cuesta 8 triángulos
por semilla.

Sombreado suave (comida), con borde marcado solo donde cambia el material.
"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402, F401
import bmesh  # noqa: E402
from mathutils import Matrix  # noqa: E402

import comun  # noqa: E402
import _comida4 as c4  # noqa: E402
import _etapa2 as e2  # noqa: E402

ID = "pan_hamburguesa_arriba"
R, ALTO = c4.R_PAN, c4.ALTO_TAPA
MEDIDAS = (2 * R, ALTO, 2 * R)
PRESUPUESTO = 250
LADOS = 16
H = ALTO / 2

# (radio, y) de abajo hacia arriba: miga plana abajo, después el domo de corteza.
PERFIL = [
    (0.0, -H),
    (0.0488, -H),         # borde del corte (miga → corteza)
    (0.0538, -0.0172),
    (R, -0.0075),         # lo más ancho
    (0.0518, 0.0048),
    (0.0425, 0.0142),
    (0.0262, 0.0204),
    (0.0, H),             # arriba del domo
]
MATS = [1, 0, 0, 0, 0, 0, 0]
# Semillas: (banda del perfil, índice alrededor). Bandas 3–5 son quads (en los triángulos
# de arriba del todo la semilla quedaba con una arruga de sombreado).
SEMILLAS = [(5, 1), (5, 7), (5, 12), (4, 4), (4, 10), (3, 14)]
LARGO_SEMILLA, ANCHO_SEMILLA = 0.0055, 0.0027


def poner_semilla(bm, cara, rnd, mat):
    """Reemplaza `cara` por una semilla chiquita en el medio, unida a sus esquinas."""
    cara.normal_update()
    n = cara.normal.copy()
    c = cara.calc_center_median()
    vs = list(cara.verts)
    u = (vs[1].co - vs[0].co)
    u = (u - n * u.dot(n)).normalized()
    w = n.cross(u)
    eu = max((v.co - c).dot(u) for v in vs) - min((v.co - c).dot(u) for v in vs)
    ew = max((v.co - c).dot(w) for v in vs) - min((v.co - c).dot(w) for v in vs)
    largo, ancho = (LARGO_SEMILLA, ANCHO_SEMILLA) if rnd.random() < 0.5 else (ANCHO_SEMILLA, LARGO_SEMILLA)
    giro = Matrix.Rotation(rnd.uniform(-0.6, 0.6), 3, n)
    semilla = []
    for v in vs:
        d = v.co - c
        off = u * (d.dot(u) * largo / eu) + w * (d.dot(w) * ancho / ew)
        semilla.append(bm.verts.new(c + giro @ off + n * 0.0003))
    bmesh.ops.delete(bm, geom=[cara], context="FACES_ONLY")
    m = len(vs)
    nuevas = [bm.faces.new(semilla)]
    nuevas[0].material_index = mat
    for j in range(m):
        f = bm.faces.new((vs[j], vs[(j + 1) % m], semilla[(j + 1) % m], semilla[j]))
        f.material_index = 0
        nuevas.append(f)


def construir(nombre=ID):
    materiales = comun.cargar_materiales("M_PanCorteza", "M_PanMiga")
    ond = c4.ruido_angular(5, [(3, 0.008), (4, 0.006)])
    bm = bmesh.new()
    caras = c4.torno(bm, PERFIL, LADOS, mats=MATS, radio=lambda k, i: ond(2 * math.pi * k / LADOS))
    c4.ajustar_caja(bm, MEDIDAS)
    rnd = random.Random(21)
    elegidas = [caras[banda * LADOS + k] for banda, k in SEMILLAS]  # e2._unir: LADOS caras por banda
    for cara in elegidas:
        poner_semilla(bm, cara, rnd, 1)
    return c4.terminar(nombre, bm, materiales)


def hoja_revision(pan, revision):
    comun.preparar_revision()
    pan.location.z = H
    da_vuelta = e2.copiar(pan, "ref_tapa_al_reves")
    da_vuelta.rotation_euler = (math.pi, 0, 0)
    da_vuelta.location = (0.3, 0, H)
    ref = c4.pan_de_escala(0.0, -0.11)
    solo = [pan]
    cuadros = e2.sacar_fotos([
        ("Frente · día", solo, "frente", "dia"),
        ("Arriba: semillas pintadas · día", solo, "arriba", "dia"),
        ("3/4 · día", solo, "tres_cuartos", "dia"),
        ("3/4 · atardecer", solo, "tres_cuartos", "atardecer"),
        ("Dada vuelta: el corte de miga · día", [da_vuelta], "tres_cuartos", "dia"),
        ("Al lado de un pan de pancho · día", [pan, ref], "tres_cuartos", "dia"),
    ])
    c4.hoja(ID, f"{ID} · Ø 0,11 × 0,045 m · comida chica", cuadros, revision)


def main():
    comun.escena_vacia()
    pan = construir()
    revision = comun.revisar(pan, PRESUPUESTO, MEDIDAS, origen="centro")
    ok = comun.imprimir_revision(ID, revision)
    c4.guardar_y_exportar(ID, [pan])
    if "--sin-hoja" not in sys.argv:
        hoja_revision(pan, revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
