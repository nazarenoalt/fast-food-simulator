"""Modelo: hoja de lechuga (id `hoja_lechuga`, etapa 4; solo si hay ingredientes extra).

Genera:
    arte/fuentes/comida/hoja_lechuga.blend
    godot/modelos/comida/hoja_lechuga.glb
    docs/arte/revisiones/hoja_lechuga.jpg

Uso:
    blender -b -P tools/blender/modelos/hoja_lechuga.py
    python tools/blender/modelos/hoja_lechuga.py

Forma: hoja de lechuga de ≈ 0,10 × 0,01 × 0,10 (lista de modelos), M_Lechuga. Contorno con
lóbulos irregulares, apenas ahuecada en el centro y con el borde ondulado (5 olas suaves
alrededor). Es una lente cerrada: la cara de arriba y la de abajo se juntan en el borde
(24 puntos, 8 olas de 3 puntos) y en el medio tiene 3 mm de espesor (guía 2.2). Por dentro,
un anillo de 8 puntos y el centro. El borde va marcado (arista dura) para que la luz no
mezcle la cara de arriba con la de abajo; el resto, suave. 80 triángulos (presupuesto 100). Se centra y se mide justo después del ruido.
"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402, F401
import bmesh  # noqa: E402

import comun  # noqa: E402
import _comida4 as c4  # noqa: E402
import _etapa2 as e2  # noqa: E402
from piezas import g2b  # noqa: E402

ID = "hoja_lechuga"
MEDIDAS = (0.10, 0.01, 0.10)
PRESUPUESTO = 100
LADOS_BORDE, LADOS_MEDIO = 24, 8
R, R_MEDIO, ESPESOR = 0.05, 0.03, 0.003
OLAS, OLA = 8, 0.0034   # olas del borde: 3 puntos por ola


def construir(nombre=ID):
    (material,) = comun.cargar_materiales("M_Lechuga")
    contorno = c4.ruido_angular(9, [(2, 0.06), (3, 0.05), (5, 0.03)])
    rnd = random.Random(9)
    hueco = lambda r: 0.0025 * (r / R) ** 2  # noqa: E731  sube hacia el borde
    n, m = LADOS_BORDE, LADOS_MEDIO

    bm = bmesh.new()
    afuera = []
    for j in range(n):
        a = 2 * math.pi * j / n
        r = R * contorno(a) * (1 + 0.035 * math.cos(2 * math.pi * j / 3)) * rnd.uniform(0.98, 1.02)
        ola = OLA * math.sin(2 * math.pi * j * OLAS / n + 0.4) * rnd.uniform(0.7, 1.0)
        afuera.append(bm.verts.new(g2b((r * math.cos(a), hueco(r) + ola, r * math.sin(a)))))
    medio_a, medio_b = [], []
    for i in range(m):
        a = 2 * math.pi * i / m
        rm = R_MEDIO * contorno(a)
        for lista, dy in ((medio_a, ESPESOR / 2), (medio_b, -ESPESOR / 2)):
            lista.append(bm.verts.new(g2b((rm * math.cos(a), hueco(rm) + dy, rm * math.sin(a)))))
    centro_a = bm.verts.new(g2b((0, ESPESOR / 2, 0)))
    centro_b = bm.verts.new(g2b((0, -ESPESOR / 2, 0)))
    paso = n // m
    for medio, centro in ((medio_a, centro_a), (medio_b, centro_b)):
        for i in range(m):
            i2 = (i + 1) % m
            bm.faces.new((centro, medio[i], medio[i2]))
            for t in range(paso):
                bm.faces.new((medio[i], afuera[paso * i + t], afuera[(paso * i + t + 1) % n]))
            bm.faces.new((medio[i], afuera[(paso * i2) % n], medio[i2]))
    c4.ajustar_caja(bm, MEDIDAS)
    obj = c4.terminar(nombre, bm, [material])
    # Arista dura en el borde: ahí la hoja se dobla 180° de la cara de arriba a la de abajo.
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    borde = set(range(n))  # los primeros vértices creados son los del borde
    for e in bm.edges:
        if all(v.index in borde for v in e.verts):
            e.smooth = False
    bm.to_mesh(obj.data)
    bm.free()
    return obj


def hoja_revision(hoja_obj, revision):
    comun.preparar_revision()
    hoja_obj.location.z = MEDIDAS[1] / 2
    ref = c4.pan_de_escala(0.0, -0.1)
    solo = [hoja_obj]
    import hamburguesa
    raiz, piezas = hamburguesa.construir()
    piezas[1].data.materials[0] = c4.material_ref("carne_cocida", c4.COCCION_CARNE[1][1])
    raiz.location = (0.4, 0, c4.ALTO_HAMBURGUESA / 2)
    lech = e2.copiar(hoja_obj, "ref_lechuga")
    lech.location = (0.4, 0, c4.ALTO_HAMBURGUESA / 2 + c4.Y_QUESO_ARRIBA + 0.004)
    piezas[3].location.z += 0.008
    cuadros = e2.sacar_fotos([
        ("Frente · día", solo, "frente", "dia", solo, 1.1),
        ("Arriba · día", solo, "arriba", "dia"),
        ("3/4 · día", solo, "tres_cuartos", "dia"),
        ("3/4 · atardecer", solo, "tres_cuartos", "atardecer"),
        ("En la hamburguesa (prueba, tapa +8 mm) · día", piezas + [lech], "tres_cuartos", "dia"),
        ("Al lado de un pan de pancho · día", [hoja_obj, ref], "tres_cuartos", "dia"),
    ])
    c4.hoja(ID, f"{ID} · ≈ 0,10 × 0,01 × 0,10 m · ingrediente extra", cuadros, revision)


def main():
    comun.escena_vacia()
    hoja_obj = construir()
    revision = comun.revisar(hoja_obj, PRESUPUESTO, MEDIDAS, origen="centro")
    ok = comun.imprimir_revision(ID, revision)
    c4.guardar_y_exportar(ID, [hoja_obj])
    if "--sin-hoja" not in sys.argv:
        hoja_revision(hoja_obj, revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
