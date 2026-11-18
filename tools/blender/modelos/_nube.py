"""Construcción común de las nubes (`nube_a`, `nube_b`, `nube_c`, familia `ciudad`).

Qué dibuja hoy el juego (rust/core/src/ciudad.rs y rust/game/src/transito.rs, REQ-AMB-11):
16 nubes de 4 a 7 esferas lisas en fila (radio 6 a 17 m, más chicas en las puntas,
aplastadas a 0,55 en Y), de 30 a 60 m de largo, a 90-140 m de altura, que el viento mueve.
Material propio sin niebla y sin sombra; el código le cambia el color con la hora (blanco
de día, anaranjado al atardecer, oscuro de noche: nocturno::set_color_nubes).

Acá, como las copas de los árboles (guía 3.2 y 5.4, _arbol.py): de 3 a 5 "bollos"
facetados (envolvente convexa de puntos sobre un elipsoide con ruido, sombreado plano),
más grandes en el medio, con la panza aplastada (la mitad de abajo de cada bollo se
achata a 0,3: un cúmulo tiene la base pareja). No se aplasta del todo contra un plano: los
puntos coplanares de la envolvente dejaban triángulos degenerados (se veían negros). Con la misma semilla sale siempre la misma nube.

Objetos (hijos del Empty `<id>`): pieza_nube, un solo material M_Lona (el blanco más claro
de la paleta; el del código, #F7F7FA, se pasa del límite de la guía 4.2): el juego le cambia
el color como hoy. Sin colisión y sin sombra (lo decide el juego).

Origen = centro de la base (la panza), a la altura donde la pone el juego.
Presupuesto: no hay fila para el cielo en la guía 3.1; se usa 400 (las 16 nubes juntas
quedan en unos 5.000 triángulos, menos que las esferas lisas de hoy).
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402, F401  (antes que bmesh)
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

import _arbol as arbol  # noqa: E402
import _ciudad as ciudad  # noqa: E402
import _plaza as plaza  # noqa: E402
import comun  # noqa: E402
import piezas  # noqa: E402
from piezas import g2b  # noqa: E402

PRESUPUESTO = 400


def construir(p):
    rng = random.Random(p["semilla"])
    (lona,) = comun.cargar_materiales("M_Lona")
    bm = bmesh.new()
    for centro, radios, puntos in p["bollos"]:
        arbol.bollo(bm, rng, centro, radios, puntos, 0, [0], aplastar=0.3, mezcla=0.0)
    # Centrar la caja envolvente en X y Z (la panza ya está en y = 0) y llevar el largo justo
    # (escala pareja en X y Z, como el ajuste de los árboles).
    xs = [v.co.x for v in bm.verts]
    ys = [v.co.y for v in bm.verts]
    zs = [v.co.z for v in bm.verts]
    bmesh.ops.translate(bm, vec=Vector((-(max(xs) + min(xs)) / 2, -(max(ys) + min(ys)) / 2, -min(zs))),
                        verts=bm.verts)
    k = p["largo"] / (max(xs) - min(xs))
    bmesh.ops.scale(bm, vec=Vector((k, k, 1.0)), verts=bm.verts)
    obj = piezas.terminar("pieza_nube", bm, [lona], sombreado="plano")   # cerrada: recálculo seguro
    raiz = piezas.raiz(p["id"], [obj])
    return {"raiz": raiz, "nube": obj}


def revisar(p, m):
    o = m["nube"]
    mn, mx = ciudad.limites([o])
    d = mx - mn
    res = comun.revisar(o, PRESUPUESTO, tuple(d), origen="base")
    res = ciudad.reemplazar(res, "Medidas", abs(d.x - p["largo"]) < 1e-3 and d.y <= p["alto_max"],
                            "Medidas %.1f × %.1f × %.1f m (largo pedido ≈ %.0f, alto ≤ %.0f; el juego hace "
                            "nubes de 30 a 60 m de largo)" % (d.x, d.y, d.z, p["largo"], p["alto_max"]))
    res = ciudad.reemplazar(res, "Triángulos", res[1][0],
                            res[1][1].replace(")", ": cielo, sin fila en la guía 3.1)"))
    caras = [len(c) for c in arbol._componentes(o)]
    res.append((min(caras) >= 30 and max(caras) <= 80 or len(caras) == 1,
                "Bollos facetados: %d de %d caras en total (como las copas: 30 a 80 por bollo)" % (
                    len(p["bollos"]), sum(caras))))
    return res


def main(p, titulo):
    comun.escena_vacia()
    m = construir(p)
    revision = revisar(p, m)
    ok = comun.imprimir_revision(p["id"], revision)
    ciudad.guardar_y_exportar(p["id"], [m["raiz"], m["nube"]])
    if "--sin-hoja" not in sys.argv:
        plaza.PERSPECTIVAS["desde_abajo"] = Vector((0.35, -1.0, -0.45))
        c = [m["nube"]]
        ciudad.hoja(p["id"], titulo, [
            ("Frente · día", c, "frente", "dia", True),
            ("Costado · día", c, "costado", "dia", True),
            ("Arriba · día", c, "arriba", "dia", True),
            ("3/4 · día", c, "tres_cuartos", "dia", False),
            ("3/4 · atardecer", c, "tres_cuartos", "atardecer", False),
            ("Desde abajo (como se ve desde la plaza) · día", c, "desde_abajo", "dia", False),
        ], revision, sin_piso=True)
    if not ok:
        sys.exit(1)
