"""Modelo: montón de carbón encendido (id `carbon_brasa`, etapa 4; va adentro de la batea
de `parrilla_carbon`, en su `punto_carbon`).

Genera:
    arte/fuentes/cocina/carbon_brasa.blend
    godot/modelos/cocina/carbon_brasa.glb
    docs/arte/revisiones/carbon_brasa.jpg

Uso:
    blender -b -P tools/blender/modelos/carbon_brasa.py
    python tools/blender/modelos/carbon_brasa.py

Forma: una cama de brasas baja y abombada, de planta redondeada (`pieza_brasa`, M_Brasa con
emisión) y encima
unos 28 trozos de carbón (M_Carbon) de formas irregulares, que la tapan a medias: entre los
trozos se ve el naranja. Tres trozos más son brasa pura (también en `pieza_brasa`). Sombreado
facetado (guía 3.4: piedras y terreno), sin bisel. Los trozos salen de un sorteo con semilla
fija: el modelo sale siempre igual.

Medidas (lista de modelos: ≈ 0,5 × 0,08 × 0,35): 0,50 × 0,08 × 0,35 justos. Entra en la
batea de la parrilla (adentro 0,60 × 0,406).

Objetos (hijos del Empty `carbon_brasa`, origen = centro de la base, apoyado en y = 0: el
código lo pone en el `punto_carbon` de la parrilla):
- `carbon_brasa_trozos` (M_Carbon): los trozos apagados.
- `pieza_brasa` (M_Brasa): la cama y los trozos encendidos. **El juego cambia la intensidad
  de la emisión según el fuego** (guía 4.4): apagada cuando el carbón se gastó. Si el código
  quiere que el montón "baje" al gastarse, puede achicar en Y la raíz.

Sin colisión: no se agarra ni choca (es parte de la parrilla, que tiene su `-colonly`).
"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402,F401  (antes que bmesh)
import bmesh  # noqa: E402
from mathutils import Euler, Vector  # noqa: E402

import comun  # noqa: E402
import piezas  # noqa: E402
import _equipos as eq  # noqa: E402
from piezas import g2b  # noqa: E402

ID = "carbon_brasa"
FAMILIA = "cocina"
PRESUPUESTO = 500  # lista de modelos
MEDIDAS = (0.50, 0.08, 0.35)
HX, HZ, ALTO = MEDIDAS[0] / 2, MEDIDAS[2] / 2, MEDIDAS[1]
ALTO_CAMA = 0.035
GRILLA_CAMA = (8, 6)
TROZOS, TROZOS_BRASA = 28, 3
SEMILLA = 7


def alto_cama(x, z):
    """Loma baja: 0,035 en el medio, casi nada en los bordes."""
    u, w = min(1.0, abs(x) / HX), min(1.0, abs(z) / HZ)
    return ALTO_CAMA * (1 - u ** 2.5) * (1 - w ** 2.5) + 0.002


def cama(bm, azar):
    """Grilla abombada sin cara de abajo (apoya en la batea)."""
    nx, nz = GRILLA_CAMA
    vs = []
    for i in range(nx + 1):
        fila = []
        for k in range(nz + 1):
            x = -HX + 2 * HX * i / nx
            z = -HZ + 2 * HZ * k / nz
            borde = i in (0, nx) or k in (0, nz)
            # (adentro, nunca a ras del apoyo: se pelearía con el piso de la batea)
            y = 0.0 if borde else max(0.004, alto_cama(x, z) + azar.uniform(-0.004, 0.004))
            if not borde:  # un poco de desorden en planta, sin salirse
                x += azar.uniform(-0.01, 0.01)
                z += azar.uniform(-0.01, 0.01)
            # Planta redondeada (superelipse): las esquinas se meten, el medio de cada lado
            # queda en el borde (así la caja sigue midiendo 0,50 × 0,35).
            u, w = x / HX, z / HZ
            r = (abs(u) ** 4 + abs(w) ** 4) ** 0.25
            if r > 1e-6:
                f = max(abs(u), abs(w)) / r
                x, z = x * f, z * f
            fila.append(bm.verts.new(g2b((x, y, z))))
        vs.append(fila)
    for i in range(nx):
        for k in range(nz):
            bm.faces.new((vs[i][k], vs[i + 1][k], vs[i + 1][k + 1], vs[i][k + 1]))


def trozo(bm, azar, centro, tam):
    """Cubo deformado: un trozo de carbón (12 triángulos)."""
    res = bmesh.ops.create_cube(bm, size=1.0)
    v = res["verts"]
    escala = Vector((azar.uniform(0.8, 1.4), azar.uniform(0.6, 1.0), azar.uniform(0.7, 1.2))) * tam
    for p in v:
        p.co = Vector((p.co.x * escala.x, p.co.y * escala.y, p.co.z * escala.z))
        p.co += Vector([azar.uniform(-0.18, 0.18) * tam for _ in range(3)])
    giro = Euler((azar.uniform(-0.5, 0.5), azar.uniform(-0.5, 0.5), azar.uniform(0, math.tau))).to_matrix()
    bmesh.ops.rotate(bm, verts=v, matrix=giro)
    bmesh.ops.translate(bm, vec=g2b(centro), verts=v)
    # Que no se salga de la planta del montón ni se meta debajo del apoyo.
    corr = Vector((0, 0, 0))
    for eje, lim in ((0, HX), (1, HZ)):
        mn, mx = min(p.co[eje] for p in v), max(p.co[eje] for p in v)
        corr[eje] = min(0.0, lim - 0.002 - mx) + max(0.0, -lim + 0.002 - mn)
    corr.z = max(0.0, 0.001 - min(p.co.z for p in v))
    bmesh.ops.translate(bm, vec=corr, verts=v)


def cama_hacia_arriba(obj):
    """La cama es una superficie abierta: recalc_face_normals puede dejarla mirando para
    abajo. Sus caras son las primeras (se crearon antes que los trozos)."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    for f in bm.faces[:GRILLA_CAMA[0] * GRILLA_CAMA[1]]:
        f.normal_update()
        if f.normal.z < 0:
            f.normal_flip()
    bm.to_mesh(obj.data)
    bm.free()


def construir():
    m_carbon, m_brasa = comun.cargar_materiales("M_Carbon", "M_Brasa")
    azar = random.Random(SEMILLA)
    bm_b, bm_c = bmesh.new(), bmesh.new()
    cama(bm_b, azar)
    lugares = []
    intentos = 0
    while len(lugares) < TROZOS + TROZOS_BRASA and intentos < 5000:
        intentos += 1
        tam = azar.uniform(0.034, 0.05)
        x = azar.uniform(-HX + 0.045, HX - 0.045)
        z = azar.uniform(-HZ + 0.04, HZ - 0.04)
        if all((x - a) ** 2 + (z - b) ** 2 > (0.75 * (tam + t)) ** 2 / 4 for a, b, t in lugares):
            lugares.append((x, z, tam))
    for n, (x, z, tam) in enumerate(lugares):
        y = alto_cama(x, z) + tam * 0.15
        trozo(bm_b if n < TROZOS_BRASA else bm_c, azar, (x, y, z), tam)
    # Ajuste final: alto justo (los trozos no pasan de los bordes de la cama en planta).
    alto = max(v.co.z for bm in (bm_b, bm_c) for v in bm.verts)
    for bm in (bm_b, bm_c):
        for v in bm.verts:
            v.co.z *= ALTO / alto
    trozos = piezas.terminar(f"{ID}_trozos", bm_c, [m_carbon], sombreado="plano")
    brasa = piezas.terminar("pieza_brasa", bm_b, [m_brasa], sombreado="plano")
    cama_hacia_arriba(brasa)
    raiz = piezas.raiz(ID, [trozos, brasa])
    return {"raiz": raiz, "trozos": trozos, "brasa": brasa}


def revisar(m):
    return comun.revisar([m["trozos"], m["brasa"]], PRESUPUESTO, MEDIDAS, origen="base")


def hoja(m, revision):
    import parrilla_carbon
    comun.preparar_revision()
    vis = [m["trozos"], m["brasa"]]
    cuadros = eq.e2.sacar_fotos([
        ("Frente · día", vis, "frente", "dia"),
        ("3/4 · día", vis, "tres_cuartos", "dia"),
        ("Arriba · día", vis, "arriba", "dia"),
        ("3/4 · atardecer", vis, "tres_cuartos", "atardecer"),
    ])
    # En la parrilla, en su punto_carbon.
    p = parrilla_carbon.construir()
    m["raiz"].location = p["carbon"].location.copy()
    con = vis + [p["cuerpo"]]
    cuadros += eq.e2.sacar_fotos([
        ("En la parrilla (punto_carbon), desde el vendedor · día", con, "vendedor_alto", "dia"),
        ("En la parrilla · atardecer", con, "tres_cuartos", "atardecer"),
    ])
    comun.componer_hoja(f"{ID} · 0,50 × 0,08 × 0,35 m · brasas (pieza_brasa con emisión)",
                        cuadros, revision, comun.RAIZ / f"docs/arte/revisiones/{ID}.jpg")


def main():
    eq.main_modelo(ID, FAMILIA, construir, revisar, hoja,
                   lambda m: [m["raiz"], m["trozos"], m["brasa"]])


if __name__ == "__main__":
    main()
