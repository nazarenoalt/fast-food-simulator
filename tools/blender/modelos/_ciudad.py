"""Piezas y ayudas comunes de los modelos de la ciudad (familia `ciudad`, etapa 6).

Complementa a piezas.py y a _plaza.py (que no se tocan). Como en piezas.py, todo se da en
**ejes de Godot** (X derecha, Y arriba, Z hacia el frente = hacia la calle) y se pasa a
Blender con piezas.g2b.

- caja_frente(): caja sin la cara de atrás (y, si se pide, sin la de abajo): molduras,
  alféizares y zócalos pegados a una pared (guía 3.6: la cara contra la pared no se ve).
- barra(): prisma de 4 caras laterales, sin tapas (barrotes de rejas, parantes).
- muro_con_vanos(): paño de pared plano (en z = cte) con agujeros rectangulares (vanos de
  ventanas y puertas) y su jamba hacia adentro. Arma una grilla con los cortes de los vanos,
  así no quedan vértices sueltos ni caras ocultas. Devuelve el rectángulo del fondo de cada
  vano, para poner ahí el vidrio, la puerta o la vidriera.
- rectangulo(): un rectángulo plano (vidrio de una ventana), mirando a +Z.
- perfil_segmentado(): perfil cerrado (z, y) estirado sobre X en tramos, con material por
  tramo (toldo rayado, cortina metálica).
- guardar_y_exportar(), hoja(): como en _plaza.py, pero en la familia `ciudad`.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402  (antes que bmesh)
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

import _plaza as plaza  # noqa: E402
import comun  # noqa: E402
import piezas  # noqa: E402
from piezas import g2b  # noqa: E402

FAMILIA = "ciudad"
BISEL = 0.02        # edificios y mobiliario urbano (guía 3.3: 2-3 cm)


# ── Piezas ─────────────────────────────────────────────────────────────

def _borrar(bm, caras, cond):
    malas = [f for f in caras if f.is_valid and cond(f)]
    bmesh.ops.delete(bm, geom=malas, context="FACES_ONLY")
    return [f for f in caras if f.is_valid]


def caja_frente(bm, medidas, centro, mat=0, bisel=0.0, sin_abajo=False, sin_arriba=False):
    """Caja (medidas y centro en Godot) sin la cara de atrás (−Z de Godot = +Y de Blender)."""
    caras = piezas.caja(bm, medidas, centro, mat=mat, bisel=bisel)
    atras = g2b(centro).y + medidas[2] / 2
    abajo = g2b(centro).z - medidas[1] / 2
    arriba = g2b(centro).z + medidas[1] / 2

    def sobra(f):
        f.normal_update()
        if f.normal.y > 0.999 and all(abs(v.co.y - atras) < 1e-5 for v in f.verts):
            return True
        if sin_abajo and f.normal.z < -0.999 and all(abs(v.co.z - abajo) < 1e-5 for v in f.verts):
            return True
        if sin_arriba and f.normal.z > 0.999 and all(abs(v.co.z - arriba) < 1e-5 for v in f.verts):
            return True
        return False
    return _borrar(bm, caras, sobra)


def barra(bm, a, b, grosor, mat=0):
    """Prisma cuadrado de `a` a `b` (puntos de Godot, sobre un eje), sin tapas: barrotes que
    nacen y mueren dentro de otra pieza."""
    a, b = Vector(a), Vector(b)
    d = b - a
    eje = max(range(3), key=lambda i: abs(d[i]))
    med = [grosor, grosor, grosor]
    med[eje] = abs(d[eje])
    caras = piezas.caja(bm, tuple(med), tuple((a + b) / 2), mat=mat)
    nb = g2b(tuple(1.0 if i == eje else 0.0 for i in range(3)))
    nb = Vector((abs(nb.x), abs(nb.y), abs(nb.z)))

    def tapa(f):
        f.normal_update()
        return abs(f.normal.dot(nb)) > 0.999
    return _borrar(bm, caras, tapa)


def muro_con_vanos(bm, x0, x1, y0, y1, vanos, prof, mat=0, mat_jamba=None, z=0.0,
                   espesor=0.0, costados=(True, True)):
    """Paño de pared en el plano z (Godot), de x0 a x1 y de y0 a y1, mirando a +Z.

    vanos = [(xa, xb, ya, yb)]: agujeros. Cada vano lleva su jamba (4 caras hacia adentro, de
    `prof` de hondo); si el vano toca y0 (puerta), no lleva jamba abajo (es el piso).
    espesor > 0: agrega los costados (retornos) del paño en x0 y x1, hacia atrás.
    Las caras de arriba y abajo del paño no se crean: los módulos se apilan (guía 3.6).
    Devuelve [(xa, xb, ya, yb, z_fondo)] de cada vano, para el vidrio o la puerta.
    """
    mat_jamba = mat if mat_jamba is None else mat_jamba
    xs = sorted({x0, x1} | {v[0] for v in vanos} | {v[1] for v in vanos})
    ys = sorted({y0, y1} | {v[2] for v in vanos} | {v[3] for v in vanos})
    xs = [x for x in xs if x0 - 1e-9 <= x <= x1 + 1e-9]
    ys = [y for y in ys if y0 - 1e-9 <= y <= y1 + 1e-9]
    vs = {(i, j): bm.verts.new(g2b((x, y, z))) for i, x in enumerate(xs) for j, y in enumerate(ys)}

    def en_vano(x, y):
        return any(v[0] < x < v[1] and v[2] < y < v[3] for v in vanos)

    def cara(verts, m, normal):
        f = bm.faces.new(verts)
        f.normal_update()
        if f.normal.dot(normal) < 0:
            f.normal_flip()
        f.material_index = m
        return f

    frente = g2b((0, 0, 1))
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1):
            if en_vano((xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2):
                continue
            cara((vs[i, j], vs[i + 1, j], vs[i + 1, j + 1], vs[i, j + 1]), mat, frente)
    fondos = []
    for xa, xb, ya, yb in vanos:
        zf = z - prof
        atras = {}

        def va(i, j):
            if (i, j) not in atras:
                atras[i, j] = bm.verts.new(g2b((xs[i], ys[j], zf)))
            return atras[i, j]
        ia, ib = xs.index(xa), xs.index(xb)
        ja, jb = ys.index(ya), ys.index(yb)
        centro = Vector(g2b(((xa + xb) / 2, (ya + yb) / 2, zf)))
        bordes = []
        for i in range(ia, ib):                    # abajo y arriba
            if ja > 0 or ya > y0 + 1e-9:
                bordes.append(((i, ja), (i + 1, ja)))
            bordes.append(((i, jb), (i + 1, jb)))
        for j in range(ja, jb):                    # costados
            bordes.append(((ia, j), (ia, j + 1)))
            bordes.append(((ib, j), (ib, j + 1)))
        for p, q in bordes:
            f = bm.faces.new((vs[p], vs[q], va(*q), va(*p)))
            f.normal_update()
            medio = f.calc_center_median()
            hacia = centro - medio
            hacia.y = 0  # solo en el plano de la pared
            if f.normal.dot(hacia) < 0:
                f.normal_flip()
            f.material_index = mat_jamba
        fondos.append((xa, xb, ya, yb, zf))
    if espesor > 0:
        for lado, (i, signo) in zip(costados, ((0, -1), (len(xs) - 1, 1))):
            if not lado:
                continue
            for j in range(len(ys) - 1):
                a, b = vs[i, j], vs[i, j + 1]
                atras_a = bm.verts.new(g2b((xs[i], ys[j], z - espesor)))
                atras_b = bm.verts.new(g2b((xs[i], ys[j + 1], z - espesor)))
                cara((a, b, atras_b, atras_a), mat, g2b((signo, 0, 0)))
    return fondos


def rectangulo(bm, xa, xb, ya, yb, z, mat=0):
    """Rectángulo plano mirando a +Z (vidrio de una ventana, fondo de un vano)."""
    f = bm.faces.new([bm.verts.new(g2b(p)) for p in ((xa, ya, z), (xb, ya, z), (xb, yb, z), (xa, yb, z))])
    f.normal_update()
    if f.normal.dot(g2b((0, 0, 1))) < 0:
        f.normal_flip()
    f.material_index = mat
    return f


def perfil_segmentado(bm, perfil, xs, mats, tapas=True):
    """Perfil cerrado [(z, y)] estirado sobre X por los cortes xs (de izquierda a derecha).
    mats[k] = material del tramo entre xs[k] y xs[k+1]; las tapas usan el del tramo vecino."""
    previas = set(bm.faces)
    anillos = [[bm.verts.new(g2b((x, y, z))) for z, y in perfil] for x in xs]
    n = len(perfil)
    for k, (a, b) in enumerate(zip(anillos, anillos[1:])):
        for i in range(n):
            i2 = (i + 1) % n
            f = bm.faces.new((a[i], a[i2], b[i2], b[i]))
            f.material_index = mats[k]
    if tapas:
        bm.faces.new(list(reversed(anillos[0]))).material_index = mats[0]
        bm.faces.new(anillos[-1]).material_index = mats[-1]
    nuevas = [f for f in bm.faces if f not in previas]
    bmesh.ops.recalc_face_normals(bm, faces=nuevas)
    return nuevas


def terminar_en(nombre, bm, materiales, origen=(0.0, 0.0, 0.0), sombreado="duro"):
    """piezas.terminar, con el origen del objeto en `origen` (Godot): la malla se corre para
    que quede en el mismo lugar del mundo. Para módulos que se apilan y piezas que giran."""
    bmesh.ops.translate(bm, vec=-g2b(origen), verts=bm.verts)
    obj = piezas.terminar(nombre, bm, materiales, sombreado=sombreado)
    obj.location = g2b(origen)
    return obj


def materiales_usados(bm, todos):
    """Deja en el bmesh solo los materiales que usa, en el orden de `todos`, y los renumera.
    Devuelve la lista para piezas.terminar()."""
    usados = sorted({f.material_index for f in bm.faces})
    nuevo = {m: i for i, m in enumerate(usados)}
    for f in bm.faces:
        f.material_index = nuevo[f.material_index]
    return [todos[m] for m in usados]


# ── Chequeos ───────────────────────────────────────────────────────────

def chequeo_materiales(objetos, max_total, max_objeto=4, por_que=""):
    """Reemplazo del chequeo de 4 materiales para modelos grandes armados de varias piezas."""
    nombres = list(dict.fromkeys(m.name for o in objetos for m in o.data.materials if m))
    peor = max(len(o.data.materials) for o in objetos)
    ok = len(nombres) <= max_total and peor <= max_objeto
    return ok, "Materiales: %d en el modelo (máx. %d%s), hasta %d por objeto (máx. %d)" % (
        len(nombres), max_total, por_que, peor, max_objeto)


# ── Archivos y hoja ────────────────────────────────────────────────────

def guardar_y_exportar(id_, exportar):
    comun.guardar_blend(comun.RAIZ / f"arte/fuentes/{FAMILIA}/{id_}.blend")
    comun.exportar_glb(exportar, comun.RAIZ / f"godot/modelos/{FAMILIA}/{id_}.glb")


def hoja(id_, titulo, cuadros, revision, persona_en=None, sin_piso=False):
    """Como _plaza.hoja. sin_piso=True esconde el piso de referencia (nubes)."""
    if sin_piso:
        viejo = comun.preparar_revision

        def preparar():
            viejo()
            bpy.data.objects["ref_piso"].hide_render = True
        comun.preparar_revision = preparar
        try:
            plaza.hoja(id_, titulo, cuadros, revision, persona_en=persona_en)
        finally:
            comun.preparar_revision = viejo
    else:
        plaza.hoja(id_, titulo, cuadros, revision, persona_en=persona_en)


m = plaza.m
reemplazar = plaza.reemplazar
limites = plaza.limites
