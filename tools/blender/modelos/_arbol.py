"""Construcción común de los árboles de la plaza (`arbol_platano_a`, `_b`, `_c`).

Cada script de modelo (`<id>.py`) define sus PARAMETROS y llama a main(). Con la misma
semilla, el script da siempre el mismo árbol (random.Random(semilla), nada de azar global).

Forma (guía 5.4 y 3.4), en ejes de Godot:
    - Tronco de 6 caras, con anillos horizontales y un ensanche en la base, que sube (con la
      inclinación del parámetro) hasta la horqueta. Los centros de los anillos se corren
      apenas al azar para que no sea un caño.
    - Ramas: de la horqueta sale una rama de 5 caras hacia cada bollo de la copa, con un
      quiebre en el medio, que termina adentro del bollo. Se ven entre los bollos y debajo
      de la copa (así no parece un brócoli ni una pelota en un palo).
    - Copa: de 3 a 4 "bollos", cada uno la envolvente convexa (convex hull) de 18 a 40 puntos
      sobre un elipsoide con ruido: formas irregulares facetadas de 32 a 76 caras (guía 3.2:
      30 a 80), con la panza de abajo más chata. Cada bollo usa uno de los tres verdes
      (M_Hojas1/2/3) y un 15 % de sus caras, otro: los tres verdes quedan mezclados en el árbol.
    - Sombreado plano (facetado).
    - Los bollos se pisan entre sí (como en todo árbol low poly): las caras que quedan
      adentro de otro bollo no se ven.

Ajuste de medidas: después de armar la copa, se escala (horizontal alrededor del eje del
tronco y vertical desde la horqueta) para que el ancho en X y el alto total den justo los del
parámetro. Así las medidas "≈" de la lista quedan decididas en cada script.

Qué se mide y origen (los árboles no son simétricos, y el B está inclinado):
    - ancho = caja envolvente en X; alto = del piso a la punta de la copa; la profundidad en Z
      se informa (sale de la forma, ≤ ancho).
    - Origen = centro de la base del tronco, a nivel del piso (no el centro de la caja
      envolvente, que en un árbol inclinado o asimétrico queda corrido): se chequea con los
      vértices de la base del tronco. Ese chequeo reemplaza al de comun.revisar().

Objetos que se exportan (bajo un Empty raíz `<id>`):
    <id>_tronco (tronco y ramas, M_Tronco), <id>_copa (bollos, M_Hojas1/2/3),
    <id>-colonly (cilindro de 8 lados del tronco, del piso a la horqueta, con su inclinación;
    la copa no choca).
"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402  (antes que bmesh)
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

import _plaza as plaza  # noqa: E402
import comun  # noqa: E402
import piezas  # noqa: E402
from piezas import g2b  # noqa: E402

PRESUPUESTO = 1200  # árbol (guía 3.1)
LADOS_TRONCO, LADOS_RAMA = 6, 5
COPA_MINIMA = 2.2   # se tiene que poder pasar caminando por abajo de la copa


def V(x, y, z):
    return Vector((x, y, z))


# ── Piezas ─────────────────────────────────────────────────────────────

def _base_perpendicular(d):
    """Dos vectores perpendiculares a d (Godot), para los anillos de las ramas."""
    a = V(0, 0, 1) if abs(d.z) < 0.9 else V(1, 0, 0)
    u = d.cross(a).normalized()
    return u, d.cross(u).normalized()


def tubo(bm, puntos, radios, lados, mat=0, horizontal=False, tapa_inicio=True, rng=None):
    """Tubo facetado por una lista de puntos (Godot). horizontal=True: anillos horizontales
    (tronco); si no, perpendiculares al recorrido (ramas)."""
    previas = set(bm.faces)
    giro = rng.uniform(0, 2 * math.pi) if rng else 0.0
    anillos = []
    for i, (p, r) in enumerate(zip(puntos, radios)):
        if horizontal:
            u, w = V(1, 0, 0), V(0, 0, 1)
        else:
            a = puntos[max(i - 1, 0)]
            b = puntos[min(i + 1, len(puntos) - 1)]
            u, w = _base_perpendicular((b - a).normalized())
        anillo = []
        for k in range(lados):
            t = giro + 2 * math.pi * k / lados
            anillo.append(bm.verts.new(g2b(p + (u * math.cos(t) + w * math.sin(t)) * r)))
        anillos.append(anillo)
    for a, b in zip(anillos, anillos[1:]):
        for k in range(lados):
            bm.faces.new((a[k], a[(k + 1) % lados], b[(k + 1) % lados], b[k]))
    if tapa_inicio:
        bm.faces.new(anillos[0])
    bm.faces.new(anillos[-1])
    nuevas = [f for f in bm.faces if f not in previas]
    for f in nuevas:
        f.material_index = mat
    return nuevas


def bollo(bm, rng, centro, radios, puntos, mat, otros, aplastar=0.65, piso=None):
    """Bollo irregular: envolvente convexa de `puntos` puntos sobre un elipsoide con ruido.
    piso = altura (Godot) debajo de la cual se aplastan los puntos (arbustos en el suelo)."""
    oro = math.pi * (3 - math.sqrt(5))
    giro = rng.uniform(0, 2 * math.pi)
    vs = []
    for i in range(puntos):
        y = 1 - 2 * (i + 0.5) / puntos
        r = math.sqrt(max(0.0, 1 - y * y))
        t = giro + oro * i
        d = V(r * math.cos(t), y, r * math.sin(t))
        d += V(rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1)) * 0.13
        d = d.normalized() * rng.uniform(0.88, 1.08)
        if d.y < 0:
            d.y *= aplastar
        p = V(centro[0] + d.x * radios[0], centro[1] + d.y * radios[1], centro[2] + d.z * radios[2])
        if piso is not None:
            p.y = max(p.y, piso)
        vs.append(bm.verts.new(g2b(p)))
    res = bmesh.ops.convex_hull(bm, input=vs, use_existing_faces=False)
    sobran = list({v for v in res["geom_interior"] + res["geom_unused"]
                   if isinstance(v, bmesh.types.BMVert) and not v.link_faces})
    bmesh.ops.delete(bm, geom=sobran, context="VERTS")
    caras = [g for g in res["geom"] if isinstance(g, bmesh.types.BMFace) and g.is_valid]
    for f in caras:
        f.material_index = mat if rng.random() > 0.15 else rng.choice(otros)
    return caras


# ── Modelo ─────────────────────────────────────────────────────────────

def construir(p, nombre, desplazamiento=(0.0, 0.0, 0.0), colision=True):
    """Arma un árbol con los PARAMETROS p. Devuelve un dict con los objetos."""
    rng = random.Random(p["semilla"])
    mats = comun.cargar_materiales("M_Tronco", "M_Hojas1", "M_Hojas2", "M_Hojas3")
    off = V(*desplazamiento)

    # ── Tronco ──
    a, phi = math.radians(p["inclinacion"]), math.radians(p["rumbo"])
    eje = V(math.sin(a) * math.sin(phi), math.cos(a), math.sin(a) * math.cos(phi))
    largo = p["horqueta"] / eje.y
    horqueta = eje * largo
    r0 = p["radio_tronco"]
    alturas = [0.0, 0.22, 0.9, 1.7, p["horqueta"]]
    radios = [r0 * 1.25, r0, r0 * 0.93, r0 * 0.86, r0 * 0.78]
    puntos = []
    for y, r in zip(alturas, radios):
        c = eje * (y / eje.y)
        if 0 < y < p["horqueta"]:
            c += V(rng.uniform(-1, 1), 0, rng.uniform(-1, 1)) * r0 * 0.25
        puntos.append(c)
    bt = bmesh.new()
    tubo(bt, puntos, radios, LADOS_TRONCO, horizontal=True, tapa_inicio=False, rng=rng)

    # ── Copa ──
    bc = bmesh.new()
    centros = []
    for i, b in enumerate(p["bollos"]):
        c = horqueta + V(*b["centro"])
        centros.append(c)
        mat = p["verdes"][i % len(p["verdes"])] - 1   # índice en [Hojas1, Hojas2, Hojas3]
        bollo(bc, rng, c, b["radios"], b["puntos"], mat, [m for m in (0, 1, 2) if m != mat])
    # Ajuste de medidas: ancho en X y alto total justos.
    xs = [v.co.x for v in bc.verts]
    ys = [v.co.z for v in bc.verts]  # Y de Godot = Z de Blender
    ancho_x = max(xs) - min(xs)
    sx = p["ancho"] / ancho_x
    sy = (p["alto"] - horqueta.y) / (max(ys) - horqueta.y)
    cx = (max(xs) + min(xs)) / 2
    for v in bc.verts:
        v.co.x = cx + (v.co.x - cx) * sx
        v.co.y = -horqueta.z + (v.co.y + horqueta.z) * sx  # Blender Y = −Z de Godot
        v.co.z = horqueta.y + (v.co.z - horqueta.y) * sy
    # Los centros de los bollos se mueven igual (para las ramas).
    centros = [V(cx + (c.x - cx) * sx, horqueta.y + (c.y - horqueta.y) * sy,
                 horqueta.z + (c.z - horqueta.z) * sx) for c in centros]

    # ── Ramas: de la horqueta a cada bollo, terminan adentro ──
    rr = r0 * 0.78
    for i, (c, b) in enumerate(zip(centros, p["bollos"])):
        ini = horqueta - eje * 0.25
        fin = ini + (c - ini) * b.get("rama", 0.6)
        medio = (ini + fin) / 2 + V(rng.uniform(-1, 1), 0.3, rng.uniform(-1, 1)) * 0.12
        grosor = rr * (0.9 if i == 0 else 0.75)
        tubo(bt, [ini, medio, fin], [grosor, grosor * 0.75, grosor * 0.5], LADOS_RAMA, rng=rng)

    for bm in (bt, bc):
        bmesh.ops.translate(bm, vec=g2b(off), verts=bm.verts)
    tronco = piezas.terminar(f"{nombre}_tronco", bt, mats[:1], sombreado="plano")
    copa = piezas.terminar(f"{nombre}_copa", bc, mats[1:], sombreado="plano")
    objetos = {"tronco": tronco, "copa": copa, "horqueta": horqueta, "colisiones": []}
    hijos = [tronco, copa]
    if colision:
        centro_col = eje * (largo / 2) + off
        col = plaza.colision_cilindro(nombre, r0 * 1.05, largo, tuple(centro_col), lados=8,
                                      rot=(p["inclinacion"], p["rumbo"], 0))
        objetos["colisiones"].append(col)
        hijos.append(col)
    objetos["raiz"] = piezas.raiz(nombre, hijos)
    return objetos


# ── Revisión ───────────────────────────────────────────────────────────

def revisar(id_, p, m, tol=0.002):
    visibles = [m["tronco"], m["copa"]]
    res = comun.revisar(visibles, PRESUPUESTO, (p["ancho"], p["alto"], p["ancho"]), origen="base")
    mn, mx = plaza.limites(visibles)
    medidas_ok = abs(mx.x - mn.x - p["ancho"]) <= tol and abs(mx.y - p["alto"]) <= tol and \
        abs(mn.y) <= tol and mx.z - mn.z <= p["ancho"] + tol
    res = plaza.reemplazar(res, "Medidas", medidas_ok,
                           "Medidas: ancho X %.2f, alto %.2f, profundidad Z %.2f m "
                           "(decididas: %.2f × %.2f; lista ≈ %s)" % (
                               mx.x - mn.x, mx.y - mn.y, mx.z - mn.z, p["ancho"], p["alto"],
                               p["lista"]))
    base = [v for v in plaza.verts_mundo([m["tronco"]]) if v.z < 1e-4]
    cx = sum(v.x for v in base) / len(base)
    cz = sum(-v.y for v in base) / len(base)
    origen_ok = math.hypot(cx, cz) <= 0.01 and abs(mn.y) <= tol
    res = plaza.reemplazar(res, "Origen", origen_ok,
                           "Origen en el centro de la base del tronco (%.3f, %.3f), a nivel del "
                           "piso (la caja envolvente no sirve: árbol asimétrico)" % (cx, cz))
    mn_c, _ = plaza.limites([m["copa"]])
    res.append((mn_c.y >= COPA_MINIMA,
                "Copa desde %.2f m (se pasa caminando por abajo: mín. %.1f)" % (mn_c.y, COPA_MINIMA)))
    caras = [len(c) for c in _componentes(m["copa"])]
    res.append((all(30 <= n <= 80 for n in caras) and 2 <= len(caras) <= 4,
                "Copa de %d bollos de %s caras (guía: 2 a 4 bollos de 30 a 80)" % (
                    len(caras), ", ".join(map(str, caras)))))
    return res


def _componentes(obj):
    """Caras de cada parte suelta de la malla."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    vistas, partes = set(), []
    for f in bm.faces:
        if f.index in vistas:
            continue
        pila, parte = [f], []
        vistas.add(f.index)
        while pila:
            g = pila.pop()
            parte.append(g.index)
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in vistas:
                        vistas.add(h.index)
                        pila.append(h)
        partes.append(parte)
    bm.free()
    return partes


# ── Hoja y main ────────────────────────────────────────────────────────

def main(id_, p, descripcion, juntos=None):
    """juntos = [(id, PARAMETROS)] de otras variantes para una foto de todas juntas."""
    comun.escena_vacia()
    m = construir(p, id_)
    revision = revisar(id_, p, m)
    ok = comun.imprimir_revision(id_, revision)
    plaza.guardar_y_exportar(id_, [m["raiz"], m["tronco"], m["copa"]] + m["colisiones"])
    if "--sin-hoja" not in sys.argv:
        c = [m["tronco"], m["copa"]]
        pedidos = [
            ("Frente · día", c, "frente", "dia", True),
            ("Costado · día", c, "costado", "dia", True),
            ("3/4 · día", c, "tres_cuartos_bajo", "dia", False),
            ("3/4 · atardecer", c, "tres_cuartos_bajo", "atardecer", False),
            ("Con la persona de 1,75 m · día", c + ["persona"], "tres_cuartos_bajo", "dia", False),
        ]
        if juntos:
            todos = list(c)
            x = p["ancho"] / 2
            for otro_id, q in juntos:
                x += q["ancho"] / 2 + 0.8
                o = construir(q, f"foto_{otro_id}", (x, 0, 0), colision=False)
                todos += [o["tronco"], o["copa"]]
                x += q["ancho"] / 2
            pedidos.append(("Las tres variantes juntas · día", todos, "frente", "dia", True))
        else:
            pedidos.append(("Arriba · día", c, "arriba", "dia", True))
        plaza.hoja(id_, plaza.m("%s · ancho %.1f × alto %.1f m · árbol · %s" % (
            id_, p["ancho"], p["alto"], descripcion)), pedidos, revision,
            persona_en=(0.9, 0, 0.9))
    if not ok:
        sys.exit(1)
