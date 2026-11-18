"""Piezas y fotos compartidas por los accesorios de la etapa 5 (`accesorios/`).

Lo usan: banqueta, mesa_alta, maceta, cerco_metal, cartel_luminoso, guirnalda_luces y
pizarra_grande. Complementa a comun.py, piezas.py, _plaza.py y _etapa2.py (que no se tocan).

Todo en ejes de Godot (X derecha, Y arriba, Z hacia el cliente), como piezas.py.
"""
import math
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402  (antes que bmesh)
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

import _etapa2 as e2  # noqa: E402
import comun  # noqa: E402
import piezas  # noqa: E402
from piezas import g2b  # noqa: E402

FAMILIA = "accesorios"


# ── Piezas ─────────────────────────────────────────────────────────────

def anillo_h(c, radio, lados, giro=None):
    """Anillo horizontal (plano XZ de Godot) de `lados` puntos alrededor de c. radio =
    apotema (las caras planas miden el radio, guía 3.2); una cara plana mira a +Z."""
    giro = math.pi / lados - math.pi / 2 if giro is None else giro
    r = radio / math.cos(math.pi / lados)
    return [(c[0] + r * math.cos(giro + 2 * math.pi * k / lados), c[1],
             c[2] + r * math.sin(giro + 2 * math.pi * k / lados)) for k in range(lados)]


def poste(bm, puntos, radio, lados, mats=0, tapa_abajo=False, tapa_arriba=False):
    """Caño (recto o quebrado) que pasa por `puntos` (Godot) con los anillos HORIZONTALES:
    una pata inclinada apoya plana en el piso y arriba queda pareja contra lo que sostiene.
    mats = material de cada tramo (un número o una lista). Devuelve las caras."""
    mats = mats if isinstance(mats, (list, tuple)) else [mats] * (len(puntos) - 1)
    previas = set(bm.faces)
    anillos = [[bm.verts.new(g2b(p)) for p in anillo_h(c, radio, lados)] for c in puntos]
    for i, (a, b) in enumerate(zip(anillos, anillos[1:])):
        for k in range(lados):
            bm.faces.new((a[k], a[(k + 1) % lados], b[(k + 1) % lados], b[k])).material_index = mats[i]
    nuevas = [f for f in bm.faces if f not in previas]
    _hacia_afuera(nuevas, [g2b(c) for c in puntos])
    for hacer, anillo, afuera in ((tapa_abajo, anillos[0], g2b(puntos[0]) - g2b(puntos[1])),
                                  (tapa_arriba, anillos[-1], g2b(puntos[-1]) - g2b(puntos[-2]))):
        if hacer:
            f = bm.faces.new(anillo)
            f.material_index = mats[0] if anillo is anillos[0] else mats[-1]
            f.normal_update()
            if f.normal.dot(afuera) < 0:
                f.normal_flip()
            nuevas.append(f)
    return nuevas


def _hacia_afuera(caras, eje):
    """Da vuelta las caras que miran hacia el eje (polilínea, en Blender). recalc_face_normals
    no sirve en caños abiertos: puede dejarlos al revés."""
    def cercano(p):
        mejor = None
        for a, b in zip(eje, eje[1:]):
            d = b - a
            t = 0.0 if d.length_squared < 1e-12 else max(0.0, min(1.0, (p - a).dot(d) / d.length_squared))
            q = a + d * t
            if mejor is None or (p - q).length < (p - mejor).length:
                mejor = q
        return mejor
    for f in caras:
        f.normal_update()
        c = f.calc_center_median()
        if len(eje) > 1 and f.normal.dot(c - cercano(c)) < 0:
            f.normal_flip()


def tubo(bm, puntos, radio, lados, mat=0, cerrado=False):
    """Caño que sigue una línea (cable, aro): anillos perpendiculares a la dirección media
    en cada punto, así los quiebres no dejan huecos. Puntas abiertas (van tapadas) salvo
    cerrado=True (un aro: el último tramo vuelve al primero)."""
    previas = set(bm.faces)
    P = [Vector(p) for p in puntos]
    n = len(P)
    anillos = []
    ref = None
    for i, p in enumerate(P):
        if cerrado:
            t = (P[(i + 1) % n] - P[i - 1]).normalized()
        else:
            t = (P[min(i + 1, n - 1)] - P[max(i - 1, 0)]).normalized()
        if ref is None:
            ref = Vector((0, 0, 1)) if abs(t.z) < 0.9 else Vector((1, 0, 0))
        u = t.cross(ref).normalized()
        w = t.cross(u).normalized()
        # Inglete: en un quiebre el anillo se estira 1/cos(medio ángulo) en el plano del
        # quiebre, así el caño no se afina en la unión.
        estirar, m = 1.0, None
        if cerrado or 0 < i < n - 1:
            t_in = (P[i] - P[i - 1]).normalized()
            t_out = (P[(i + 1) % n] - P[i]).normalized()
            b = t_in.cross(t_out)
            if b.length > 1e-6:
                m = t.cross(b).normalized()
                estirar = 1 / max(0.5, math.cos(t_in.angle(t_out) / 2))

        def punto(k):
            d = (u * math.cos(2 * math.pi * k / lados) + w * math.sin(2 * math.pi * k / lados)) * radio
            if m is not None:
                d = d + m * (d.dot(m) * (estirar - 1))
            return p + d
        anillos.append([bm.verts.new(g2b(punto(k))) for k in range(lados)])
    pares = list(zip(anillos, anillos[1:])) + ([(anillos[-1], anillos[0])] if cerrado else [])
    for a, b in pares:
        for k in range(lados):
            bm.faces.new((a[k], a[(k + 1) % lados], b[(k + 1) % lados], b[k])).material_index = mat
    nuevas = [f for f in bm.faces if f not in previas]
    eje = [g2b(p) for p in P] + ([g2b(P[0])] if cerrado else [])
    _hacia_afuera(nuevas, eje)
    return nuevas


def marco(bm, ancho, alto, espesor, moldura, mat=0, bisel=0.003):
    """Marco rectangular de una sola malla (como el de pizarra_precios, con medidas):
    parado en el plano XY de Godot, base en y = 0, frente en z = 0 y espalda en z = −espesor."""
    previas = set(bm.faces)
    ax, ay, e = ancho / 2, alto, espesor
    bx, by0, by1 = ax - moldura, moldura, ay - moldura
    afuera = [(ax, 0), (ax, ay), (-ax, ay), (-ax, 0)]
    adentro = [(bx, by0), (bx, by1), (-bx, by1), (-bx, by0)]
    capas = {}
    for z, clave in ((0.0, "f"), (-e, "a")):
        capas[clave] = ([bm.verts.new(g2b((x, y, z))) for x, y in afuera],
                        [bm.verts.new(g2b((x, y, z))) for x, y in adentro])
    fo, fi = capas["f"]
    ao, ai = capas["a"]
    for k in range(4):
        j = (k + 1) % 4
        bm.faces.new((fo[k], fo[j], fi[j], fi[k]))
        bm.faces.new((ao[k], ai[k], ai[j], ao[j]))
        bm.faces.new((fo[k], ao[k], ao[j], fo[j]))
        bm.faces.new((fi[k], fi[j], ai[j], ai[k]))
    nuevas = [f for f in bm.faces if f not in previas]
    bmesh.ops.recalc_face_normals(bm, faces=nuevas)
    aristas = list({ed for f in nuevas for ed in f.edges})
    bmesh.ops.bevel(bm, geom=aristas, offset=bisel, segments=1, affect="EDGES", clamp_overlap=True)
    nuevas = [f for f in bm.faces if f not in previas]
    for f in nuevas:
        f.material_index = mat
    return nuevas


def colision_cilindro(nombre, radio, y0, y1, lados=12):
    """Cilindro `<nombre>-colonly` vertical, de y0 a y1, centrado en X y Z. radio = el de
    las caras planas (piezas.cilindro lo toma en las aristas)."""
    return piezas.colision_cilindro(nombre, radio / math.cos(math.pi / lados), y1 - y0,
                                    (0, (y0 + y1) / 2, 0), lados=lados)


# ── Chequeos ───────────────────────────────────────────────────────────

limites = e2.limites_godot


def reemplazar(res, prefijo, ok, texto):
    return [(ok, texto) if t.startswith(prefijo) else (o, t) for o, t in res]


def coma(texto):
    return texto.replace(".", ",")


def chequeo_cilindro_colision(col, radio, y0, y1):
    mn, mx = limites([col])
    ok = (abs(mn.y - y0) < 0.002 and abs(mx.y - y1) < 0.002 and abs(mx.x - radio) < 0.003
          and abs(mn.x + radio) < 0.003)
    return ok, "%s: cilindro de radio %.3f, de y %.2f a %.2f" % (col.name, mx.x, mn.y, mx.y)


# ── Escena de las fotos ────────────────────────────────────────────────

def leer_base(id_base="barra_chica"):
    import _techo
    return _techo.leer_base(id_base)


def carrito(id_base="barra_chica", x=0.0):
    """Una base terminada (con las tapas de las bahías) corrida x en Blender.
    Devuelve (visibles, datos de la base de _techo.leer_base)."""
    import _base_carrito
    b = leer_base(id_base)
    m = _base_carrito.construir(id_base, grande=b.grande)
    m["raiz"].location.x = x
    vis = [m["pintura"], m["estructura"]] + list(m["tapas"])
    return vis, b


def poner(raiz, pos_godot, x=0.0, rot_y=0.0):
    """Ubica un modelo armado (su Empty raíz) en una posición de Godot del carrito."""
    raiz.location = Vector((x, 0, 0)) + g2b(pos_godot)
    raiz.rotation_euler.z = math.radians(rot_y)
    bpy.context.view_layer.update()


def persona():
    return bpy.data.objects["ref_persona_1,75m"]


def mover_persona(pos_godot, x=0.0):
    def mover():
        persona().location = Vector((x, 0, 0)) + g2b(pos_godot)
    return mover


def sacar_fotos(pedidos):
    """pedidos = [(etiqueta, visibles, vista, luz, encuadre=None, antes=None, margen=1.2)].
    Vistas de _etapa2 (frente, costado, arriba, tres_cuartos, vendedor, vendedor_alto, bajo).
    encuadre = objetos a encuadrar (por defecto los visibles); antes() se llama antes."""
    tmp = Path(tempfile.mkdtemp())
    todos = {o for p in pedidos for o in p[1]}
    cuadros = []
    for p in pedidos:
        etiqueta, objs, vista, luz = p[:4]
        encuadre = (p[4] if len(p) > 4 else None) or objs
        antes = p[5] if len(p) > 5 else None
        margen = p[6] if len(p) > 6 else 1.2
        if antes:
            antes()
        bpy.context.view_layer.update()
        comun.poner_luz(luz)
        for o in todos:
            o.hide_render = o not in objs
        e2.encuadrar(encuadre, vista, margen=margen)
        cuadros.append((etiqueta, comun.render(tmp / f"{len(cuadros)}.png")))
    return cuadros


def hoja(id_, titulo, pedidos, revision):
    """La hoja de revisión: comun.preparar_revision() ya tiene que estar hecho."""
    cuadros = sacar_fotos(pedidos)
    comun.componer_hoja(titulo, cuadros, revision, comun.RAIZ / f"docs/arte/revisiones/{id_}.jpg")


def guardar_y_exportar(id_, exportar, uvs=False):
    comun.guardar_blend(comun.RAIZ / f"arte/fuentes/{FAMILIA}/{id_}.blend")
    comun.exportar_glb(exportar, comun.RAIZ / f"godot/modelos/{FAMILIA}/{id_}.glb", uvs=uvs)


def volumen_cerrado(obj):
    """Volumen con signo de la malla cerrando sus huecos con abanicos virtuales (> 0 si las
    normales miran hacia afuera). comun.revisar() suma solo las caras que hay: en una malla
    con caras borradas (lo apoyado, lo pegado a otra pieza, las puntas de un caño tapadas)
    el resultado depende de dónde está el origen y puede dar negativo estando bien."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    vol = 0.0
    for f in bm.faces:
        v = [l.vert.co for l in f.loops]
        for i in range(1, len(v) - 1):
            vol += v[0].dot(v[i].cross(v[i + 1])) / 6
    borde = [e for e in bm.edges if len(e.link_faces) == 1]
    # Agrupa las aristas de borde en huecos (componentes conexas) para el centro de cada uno.
    grupo = {}
    for e in borde:
        a, b = e.verts
        ga, gb = grupo.get(a), grupo.get(b)
        if ga is None and gb is None:
            g = {a, b}
        elif ga is None or gb is None or ga is gb:
            g = ga or gb
            g.update((a, b))
        else:
            ga.update(gb)
            g = ga
        for v in g:
            grupo[v] = g
    for e in borde:
        f = e.link_faces[0]
        bucle = next(l for l in f.loops if l.edge == e)
        a, b = bucle.vert.co, bucle.link_loop_next.vert.co
        g = grupo[bucle.vert]
        c = sum((v.co for v in g), Vector()) / len(g)
        vol += b.dot(a.cross(c)) / 6       # el abanico recorre la arista al revés
    bm.free()
    return vol


def chequeo_normales(res, objetos):
    """Cambia la línea de normales de comun.revisar() por volumen_cerrado()."""
    vols = [volumen_cerrado(o) for o in objetos]
    return reemplazar(res, "Normales", all(v > 0 for v in vols),
                      "Normales hacia afuera (volumen con signo cerrando los huecos de las caras "
                      "borradas: %s)" % ", ".join("%s %+.4f" % (o.name, v) for o, v in zip(objetos, vols)))
