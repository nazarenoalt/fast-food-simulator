"""Modelo: papel para envolver (id `papel_envoltorio`, etapa 2; no está en el juego).

Genera:
    arte/fuentes/comida/papel_envoltorio.blend
    godot/modelos/comida/papel_envoltorio.glb
    docs/arte/revisiones/papel_envoltorio.jpg

Uso:
    python tools/blender/modelos/papel_envoltorio.py [--sin-hoja]

Forma: hoja de papel de 0,20 × 0,003 × 0,20 (lista ≈ 0,20 × 0,005 × 0,20; 3 mm, el mínimo de
la guía 2.2, se ve más papel que 5 mm), M_BlancoCrema, sin bisel.

Las dos versiones son la MISMA malla, como la feta de queso (`feta_queso.py`):
- La base es el papel plano (el que mide 0,20 × 0,003 × 0,20, origen en el centro).
- Una forma clave (shape key → blend shape `envuelto` en Godot) lo dobla en U alrededor de un
  pancho: el papel se curva a lo largo de Z (a lo ancho del pan) y queda recto a lo largo de
  X (sale 1,5 cm por cada punta del pan, que mide 0,17). Abajo apoya plano a 1 mm del pan, los
  costados suben pegados al pan y terminan en dos solapas abiertas hacia afuera a 5 cm del
  centro, más arriba que el pan (se ve la salchicha desde arriba, no desde el costado).
  En la forma `envuelto` el origen del papel coincide con el centro del pancho (el de
  `pancho.glb`): el juego pone el papel en el mismo lugar que el pancho y sube la forma de 0
  a 1. Cada tramo del perfil mide lo mismo plano y doblado (el papel no se estira).
Perfil: 6 puntos a lo ancho (solapa, costado, esquina de abajo, x2) y 2 cortes a lo largo:
44 triángulos (presupuesto 50). Sombreado suave en los dobleces y canto marcado.

Objeto que se agarra: origen en el centro, sin colisión (guía 6.1).
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402,F401  (antes que bmesh)
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

import comun  # noqa: E402
import piezas  # noqa: E402
import _etapa2 as e2  # noqa: E402
import _comida4 as c4  # noqa: E402
from piezas import g2b  # noqa: E402

ID = "papel_envoltorio"
FAMILIA = "comida"
LADO, ESPESOR = 0.20, 0.003
MEDIDAS = (LADO, ESPESOR, LADO)
PRESUPUESTO = 50

# Perfil del papel envuelto: línea media (z, y), mitad −Z; se espeja. Medido contra el perfil
# del pan (pan_pancho.PERFIL_ABIERTO): abajo y = −0,0225, lo más ancho 0,0275 a y = 0,003.
MEDIO_ENVUELTO = [
    (-0.037, 0.0505),    # solapa (arriba, abierta hacia afuera)
    (-0.0325, 0.002),    # costado, a la altura de lo más ancho del pan
    (-0.023, -0.0245),   # esquina de abajo
]
PERFIL_ENVUELTO = MEDIO_ENVUELTO + [(-z, y) for z, y in reversed(MEDIO_ENVUELTO)]


def perfil_plano():
    """Mismos puntos, estirados sobre Z con el largo de cada tramo, centrados."""
    largos = [math.dist(a, b) for a, b in zip(PERFIL_ENVUELTO, PERFIL_ENVUELTO[1:])]
    total = sum(largos)
    zs = [0.0]
    for d in largos:
        zs.append(zs[-1] + d * LADO / total)
    return [(z - LADO / 2, 0.0) for z in zs]


def con_espesor(perfil):
    """Para cada punto de la línea media: (afuera, adentro) corridos medio espesor por la
    normal promedio (afuera = hacia abajo / hacia afuera de la U)."""
    out = []
    n = len(perfil)
    for i, (z, y) in enumerate(perfil):
        normales = []
        for a, b in ((i - 1, i), (i, i + 1)):
            if 0 <= a and b < n:
                dz, dy = perfil[b][0] - perfil[a][0], perfil[b][1] - perfil[a][1]
                normales.append(Vector((dy, -dz)).normalized())   # derecha del avance = afuera
        nm = sum(normales, Vector((0, 0))).normalized()
        k = ESPESOR / 2 / max(0.5, min(nm.dot(m) for m in normales))
        out.append(((z + nm.x * k, y + nm.y * k), (z - nm.x * k, y - nm.y * k)))
    return out


def puntos(perfil):
    """Vértices (Godot) en el orden de la malla: por cada x (−, +), anillo cerrado afuera
    0..5 y adentro 5..0."""
    pares = con_espesor(perfil)
    anillo = [p for p, _ in pares] + [q for _, q in reversed(pares)]
    return [(sx * LADO / 2, y, z) for sx in (-1, 1) for z, y in anillo]


def construir(nombre=ID, envuelto=0.0, forma_clave=True):
    (papel,) = comun.cargar_materiales("M_BlancoCrema")
    plano, doblado = puntos(perfil_plano()), puntos(PERFIL_ENVUELTO)
    base = [Vector(a).lerp(Vector(b), envuelto) for a, b in zip(plano, doblado)]
    bm = bmesh.new()
    vs = [bm.verts.new(g2b(p)) for p in base]
    m = len(vs) // 2           # 12 por punta
    izq, der = vs[:m], vs[m:]
    for k in range(m):         # alrededor (arriba, canto, abajo, canto)
        bm.faces.new((izq[k], izq[(k + 1) % m], der[(k + 1) % m], der[k]))
    h = m // 2
    for lado in (izq, der):    # puntas: tiras de quads entre afuera y adentro
        for i in range(h - 1):
            bm.faces.new((lado[i], lado[i + 1], lado[m - 2 - i], lado[m - 1 - i]))
    obj = e2.objeto_en(nombre, bm, [papel], (0, 0, 0), sombreado="duro")
    e2.suavizar_hasta(obj, 60)
    if forma_clave:
        obj.shape_key_add(name="Basis")
        clave = obj.shape_key_add(name="envuelto")
        # piezas.terminar no reordena vértices: el índice i es el punto i.
        for i, p in enumerate(doblado):
            clave.data[i].co = g2b(p)
        obj.data.shape_keys.use_relative = True
        clave.value = 0.0
        obj.active_shape_key_index = 0
    return obj


def chequeo_forma_clave(obj):
    claves = obj.data.shape_keys
    ok = claves is not None and "envuelto" in claves.key_blocks
    texto = "Forma clave `envuelto` (blend shape)"
    if ok:
        k = claves.key_blocks["envuelto"]
        base = claves.key_blocks["Basis"]
        # El papel no se estira: el largo del borde de afuera a lo ancho es el mismo.
        m = len(k.data) // 2       # vértices por punta: afuera 0..n-1, adentro n..m-1 (al revés)
        n = m // 2

        def medio(kb, i):          # punto de la línea media del papel
            return (kb.data[i].co + kb.data[m - 1 - i].co) / 2
        largo = [sum((medio(kb, i + 1) - medio(kb, i)).length for i in range(n - 1)) for kb in (base, k)]
        ys = [k.data[i].co.z for i in range(len(k.data))]
        ok = abs(largo[0] - largo[1]) < 0.002
        texto += ": dobla en U alrededor del pancho, de y = %.3f a %.3f; mismo largo de la línea media plano y doblado " \
                 "(%.3f / %.3f)" % (min(ys), max(ys), largo[0], largo[1])
    return ok, texto


def chequeo_pan(obj):
    """En la forma `envuelto`, ningún vértice de adentro del papel entra en el pan."""
    import pan_pancho
    perfil = pan_pancho.PERFIL_ABIERTO[:6]   # contorno de afuera (medio perfil: ancho, alto)
    adentro = []
    for z, y in [q for _, q in con_espesor(PERFIL_ENVUELTO)]:
        if y > perfil[-1][1] or y < perfil[0][1]:
            continue
        for (a0, y0), (a1, y1) in zip(perfil, perfil[1:]):
            if min(y0, y1) <= y <= max(y0, y1) and y1 != y0:
                ancho = a0 + (a1 - a0) * (y - y0) / (y1 - y0)
                if abs(z) < ancho:
                    adentro.append((round(z, 4), round(y, 4)))
                break
    return not adentro, "Envuelto: el papel no atraviesa el pan (perfil de pan_pancho)" + (
        f" — adentro: {adentro}" if adentro else "")


def hoja_revision(papel, revision):
    import pancho
    comun.preparar_revision()
    papel.location.z = ESPESOR / 2
    env = construir("ref_envuelto", envuelto=1.0, forma_clave=False)
    medio = construir("ref_medio", envuelto=0.5, forma_clave=False)
    raiz, pan, salchicha = pancho.construir()
    alto_pan = 0.0225 + 0.0245 + ESPESOR / 2
    for o, x in ((env, 0.0), (raiz, 0.0)):
        o.location = (x, 0.0, alto_pan)
    medio.location = (0.0, 0.0, 0.02)
    con_pancho = [env, pan, salchicha]
    solo = [papel]
    cuadros = e2.sacar_fotos([
        ("Plano (la base) · 3/4 · día", solo, "tres_cuartos", "dia", solo, 1.2),
        ("Plano · frente · día", solo, "frente", "dia", solo, 1.1),
        ("A mitad de camino (forma en 0,5) · día", [medio], "tres_cuartos", "dia"),
        ("Envuelto (forma en 1) con el pancho · día", con_pancho, "tres_cuartos", "dia"),
        ("Envuelto · de punta: el perfil en U · día", con_pancho, "costado", "dia", con_pancho, 1.3),
        ("Envuelto, como lo ve el jugador · atardecer", con_pancho, "vendedor_alto", "atardecer"),
    ])
    comun.componer_hoja(f"{ID} · 0,20 × 0,003 × 0,20 m · forma clave `envuelto` (pancho)", cuadros,
                        revision, comun.RAIZ / f"docs/arte/revisiones/{ID}.jpg")


def main():
    comun.escena_vacia()
    papel = construir()
    revision = comun.revisar(papel, PRESUPUESTO, MEDIDAS, origen="centro", tolerancia=1e-4)
    revision.insert(1, chequeo_forma_clave(papel))
    revision.insert(2, chequeo_pan(papel))
    ok = comun.imprimir_revision(ID, revision)
    c4.guardar_y_exportar(ID, [papel])
    if "--sin-hoja" not in sys.argv:
        hoja_revision(papel, revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
