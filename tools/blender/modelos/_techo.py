"""Funciones comunes de los techos y toldos de los carritos (etapa 5, `accesorios/`).

Cada tipo (`techo_plano.py`, `toldo_rayado.py`, ...) es un script parametrizado que arma los
TRES tamaños con el mismo código, uno por base de carrito:
    _chico   → barra_chica   (ancho 1,6)
    _mediano → barra_mediana (ancho 2,4)
    _grande  → carro_grande  (ancho 3,4)
Las medidas salen del .ron de cada base (godot/data/carritos/<id>.ron): ancho, profundidad,
alto_mostrador y los anclajes `techo`, `frente` y `luz_N`.

Tamaño dinámico (a futuro): cada .glb viene partido en tres objetos a lo largo de X,
    pieza_punta_izq · pieza_tramo · pieza_punta_der
Se arma el modelo entero en un bmesh y se corta con dos planos x = ±corte (partir()). Todo lo
que tiene forma propia (caños, frontones, brazos, manivela, tapas) queda en las puntas, y el
tramo del medio queda de dos maneras, según el tipo:
    - estirable: el tramo no tiene ni un vértice adentro, solo en los dos planos de corte
      (chapa, vigas, caja del toldo): se puede escalar en X sin deformar nada;
    - repetible: el tramo es un número entero de módulos de dos rayas (cada raya con su festón):
      se puede repetir corriéndolo su ancho, o de a un módulo.
Las dos cosas las comprueba la revisión automática (chequeo_tramo).
Los objetos que no se estiran (tubo de luz, colgadores, cartel, lamparitas) van aparte.

Superficies (guía 4.2, regla 5): en las tres piezas, la superficie 0 y la 1 son siempre las
mismas (lona: raya A y raya B; chapa: chapa y borde pintado), así el juego cambia el color
igual en las tres. Las que siguen (acero, plástico negro) pueden faltar en el tramo.

Posiciones en ejes de Godot (como piezas.py), relativas al anclaje del accesorio.
"""
import math
import re
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402  (antes que bmesh)
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

import comun  # noqa: E402
import piezas  # noqa: E402
from piezas import g2b  # noqa: E402

FAMILIA = "accesorios"
TAMANOS = (("chico", "barra_chica"), ("mediano", "barra_mediana"), ("grande", "carro_grande"))
BASE_DE = dict(TAMANOS)

# ── Medidas comunes (Godot, metros) ────────────────────────────────────
ALERO_MIN = 2.10          # borde más bajo de un techo: vendedor de 1,75 m + margen
CANO_R = 0.02             # caños de los techos (12 lados, guía 3.2)
BRIDA = (0.08, 0.012, 0.08)
VIGA = 0.03               # caño cuadrado bajo la chapa
BISEL = 0.008             # accesorios (guía 3.3, chapa de 3-4 cm)
LONA = 0.012              # espesor de lona (guía 2.2, sin bisel)
RAYA = 0.15               # ancho aproximado de una raya
FESTON_PASOS = 4          # cortes por festón (uno por raya)
LUZ_ALTA = 2.05           # referencia: luz_1 de las barras (foco_calido cuelga 0,38)


# ── Datos de las bases ─────────────────────────────────────────────────

def leer_base(id_base):
    """Lo que hace falta del .ron de la base (mismo criterio que _base_carrito.leer_ron)."""
    texto = re.sub(r"//[^\n]*", "", (comun.RAIZ / f"godot/data/carritos/{id_base}.ron").read_text())

    def num(campo):
        return float(re.search(rf"\b{campo}:\s*([-\d.]+)", texto).group(1))

    anc = {m.group(1): tuple(float(x) for x in m.group(2).split(","))
           for m in re.finditer(r'\(\s*id:\s*"(\w+)",\s*pos:\s*\(([^)]*)\)', texto)}
    w, p, a = num("ancho"), num("profundidad"), num("alto_mostrador")
    grande = id_base == "carro_grande"
    return SimpleNamespace(
        id=id_base, w=w, p=p, a=a, anclajes=anc, grande=grande,
        luces=[anc[k] for k in sorted(anc) if k.startswith("luz_")],
        # Lo que hay alrededor (carrito.rs / _base_carrito.py), en coordenadas del carrito:
        mesada_x=w / 2 + 0.02, mesada_z=(-p / 2 - 0.01, p / 2 + 0.05),
        ruedas_x=w / 2 - 0.3, rueda_r=0.15,
        ruedas_z=p / 2 + 0.01 + (0.08 if grande else 0.06) + 0.016,   # hasta la taza
        manija_x=-w / 2 - 0.15 - (0.02 if grande else 0.015), manija_y=a - 0.1,
    )


def base(tam):
    return leer_base(BASE_DE[tam])


def rel(b, anclaje, pos):
    """Posición del carrito → relativa al anclaje (origen del accesorio)."""
    o = b.anclajes[anclaje]
    return (pos[0] - o[0], pos[1] - o[1], pos[2] - o[2])


def presupuesto(lista, b, tope=2000):
    """La lista da el presupuesto del chico. Si los tris crecen con el ancho (rayas), el
    mediano y el grande tienen el proporcional al ancho, con el tope de la guía (3.1)."""
    return min(tope, int(round(lista * b.w / 1.6, -1)))


# ── Geometría ──────────────────────────────────────────────────────────

def varilla(bm, p0, p1, radio, lados=8, mat=0, tapas=(True, True)):
    """Cilindro entre dos puntos de Godot (como en carpa_2x2)."""
    a, b = g2b(p0), g2b(p1)
    eje = (b - a).normalized()
    u = eje.orthogonal().normalized()
    v = eje.cross(u)
    anillos = [[bm.verts.new(c + radio * (math.cos(t) * u + math.sin(t) * v))
                for t in (2 * math.pi * (k + 0.5) / lados for k in range(lados))] for c in (a, b)]
    caras = [bm.faces.new((anillos[0][k], anillos[0][(k + 1) % lados], anillos[1][(k + 1) % lados],
                           anillos[1][k])) for k in range(lados)]
    if tapas[0]:
        caras.append(bm.faces.new(list(reversed(anillos[0]))))
    if tapas[1]:
        caras.append(bm.faces.new(anillos[1]))
    for f in caras:
        f.material_index = mat
    return caras


def biselar(bm, caras, ancho, angulo=30):
    """Bisel de 1 segmento solo en las aristas duras (más de `angulo` grados)."""
    lim = math.radians(angulo)
    aristas = list({e for f in caras for e in f.edges if len(e.link_faces) == 2 and
                    e.link_faces[0].normal.angle(e.link_faces[1].normal, 0.0) > lim})
    if aristas:
        bmesh.ops.bevel(bm, geom=aristas, offset=ancho, segments=1, affect="EDGES",
                        profile=0.5, clamp_overlap=True)


def prisma_x(bm, perfil, x0, x1, bisel=0.0, mat=0):
    """Perfil [(y, z)] de Godot extruido a lo largo de X, de x0 a x1, con tapas."""
    previas = set(bm.faces)
    a = [bm.verts.new(g2b((x0, y, z))) for y, z in perfil]
    b = [bm.verts.new(g2b((x1, y, z))) for y, z in perfil]
    n = len(perfil)
    for k in range(n):
        bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]))
    bm.faces.new(a)
    bm.faces.new(list(reversed(b)))
    nuevas = [f for f in bm.faces if f not in previas]
    bmesh.ops.recalc_face_normals(bm, faces=nuevas)
    if bisel:
        biselar(bm, nuevas, bisel)
        nuevas = [f for f in bm.faces if f not in previas]
    for f in nuevas:
        f.material_index = mat
    return nuevas


def prisma_z(bm, perfil, z0, z1, mat=0):
    """Perfil [(x, y)] de Godot extruido a lo largo de Z (frontones, chapitas)."""
    previas = set(bm.faces)
    a = [bm.verts.new(g2b((x, y, z0))) for x, y in perfil]
    b = [bm.verts.new(g2b((x, y, z1))) for x, y in perfil]
    n = len(perfil)
    for k in range(n):
        bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]))
    bm.faces.new(a)
    bm.faces.new(list(reversed(b)))
    nuevas = [f for f in bm.faces if f not in previas]
    bmesh.ops.recalc_face_normals(bm, faces=nuevas)
    for f in nuevas:
        f.material_index = mat
    return nuevas


def normal_g(f):
    n = f.normal
    return Vector((n.x, n.z, -n.y))


def centro_g(f):
    c = f.calc_center_median()
    return Vector((c.x, c.z, -c.y))


def pintar(caras, fn):
    """material_index = fn(normal Godot, centro Godot) para cada cara."""
    for f in caras:
        f.material_index = fn(normal_g(f), centro_g(f))


def partir(bm, corte):
    """Corta el bmesh con los planos x = ±corte y devuelve [izq, tramo, der] (bmesh)."""
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for x in (-corte, corte):
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-6, plane_co=(x, 0, 0), plane_no=(1, 0, 0))
    partes = []
    for lo, hi in ((-1e9, -corte), (-corte, corte), (corte, 1e9)):
        b = bm.copy()
        fuera = [f for f in b.faces if not lo < f.calc_center_median().x < hi]
        bmesh.ops.delete(b, geom=fuera, context="FACES")
        partes.append(b)
    bm.free()
    return partes


def objeto(nombre, bm, materiales, sombreado="duro", recalcular=False):
    """Como piezas.terminar, pero sin recalcular normales (las piezas partidas son abiertas:
    se recalculan antes de partir) y sacando los materiales del final que esa pieza no usa
    (ej. el plástico negro de las puntas, que el tramo no tiene)."""
    if recalcular:
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    usados = {f.material_index for f in bm.faces}
    n = max(usados) + 1
    faltan = set(range(n)) - usados
    if faltan:
        raise SystemExit(f"{nombre}: no usa las superficies {sorted(faltan)}")
    materiales = materiales[:n]
    for f in bm.faces:
        f.smooth = sombreado != "plano"
    if sombreado != "plano":
        for e in bm.edges:
            caras = e.link_faces
            if len(caras) != 2:
                e.smooth = sombreado == "suave"
                continue
            distinto = caras[0].material_index != caras[1].material_index
            angulo = caras[0].normal.angle(caras[1].normal, 0.0)
            e.smooth = not (distinto or (sombreado == "duro" and angulo > piezas.ANGULO_DURO))
    return comun.objeto_desde_bmesh(nombre, bm, materiales)


def tres_piezas(bm, corte, materiales, sombreado="duro"):
    izq, tramo, der = partir(bm, corte)
    return [objeto("pieza_punta_izq", izq, materiales, sombreado),
            objeto("pieza_tramo", tramo, materiales, sombreado),
            objeto("pieza_punta_der", der, materiales, sombreado)]


def colision(nombre, cilindros=(), cajas=()):
    """Un objeto `<nombre>-colonly` con varios cilindros [(p0, p1, r)] y cajas
    [(medidas, centro)] (guía 6.1)."""
    bm = bmesh.new()
    for p0, p1, r in cilindros:
        varilla(bm, p0, p1, r, lados=8)
    for med, c in cajas:
        piezas.caja(bm, med, c)
    malla = bpy.data.meshes.new(f"{nombre}-colonly")
    bm.to_mesh(malla)
    bm.free()
    obj = bpy.data.objects.new(f"{nombre}-colonly", malla)
    bpy.context.scene.collection.objects.link(obj)
    obj.display_type = "WIRE"
    obj.hide_render = True
    return obj


# ── Techos (anclaje `techo`) ───────────────────────────────────────────

def geometria_techo(b, extra=0.34, punta=0.30):
    """Medidas de un techo sobre la base b, relativas al anclaje `techo`.

    Ancho = ancho de la base + 0,10 (5 cm de alero a cada lado de la mesada, que ya sale 2).
    Fondo = profundidad + extra, centrado sobre la mesada (que está corrida 2 cm al cliente).
    Caños: 4, parados sobre la mesada, 5 cm adentro de sus bordes (x = ±(ancho/2 − 0,03),
    z = adelante p/2, atrás −p/2 + 0,04). Así no tocan ruedas, manija ni al vendedor.
    """
    az = b.anclajes["techo"][2]
    W = b.w + 0.10
    zc = 0.02 - az
    D = b.p + extra
    return SimpleNamespace(
        W=W, D=D, zc=zc, zb=zc - D / 2, zf=zc + D / 2, corte=W / 2 - punta,
        xp=b.w / 2 - 0.03, zpf=b.p / 2 - az, zpb=-b.p / 2 + 0.04 - az, a=b.a,
        mesada_x=b.mesada_x, mesada_z=(b.mesada_z[0] - az, b.mesada_z[1] - az),
        luces=[rel(b, "techo", l) for l in b.luces], az=az,
    )


def canos(bm, g, y_arriba, mat):
    """Los 4 caños con su brida sobre la mesada. y_arriba(z) = hasta dónde sube cada uno.
    Devuelve los cilindros para la colisión."""
    col = []
    for sx in (-1, 1):
        for z in (g.zpb, g.zpf):
            x = sx * g.xp
            piezas.caja(bm, BRIDA, (x, g.a + BRIDA[1] / 2, z), mat=mat, bisel=0.003, sin_abajo=True)
            y1 = y_arriba(z)
            varilla(bm, (x, g.a + BRIDA[1], z), (x, y1, z), CANO_R, lados=12, mat=mat,
                    tapas=(False, False))
            col.append(((x, g.a, z), (x, y1, z), CANO_R))
    return col


def vigas_x(bm, g, y_arriba, mat, zs=None):
    """Vigas de caño cuadrado a lo largo de X sobre los caños (de punta a punta de caños)."""
    for z in zs or (g.zpb, g.zpf):
        y = y_arriba(z)
        piezas.caja(bm, (2 * g.xp + VIGA, VIGA, VIGA), (0, y - VIGA / 2, z), mat=mat, bisel=0.005)


def colgadores(g, y_desde, mat_acero):
    """Un colgador por cada luz_N de la base: varilla de la chapa hasta la altura de luz_N
    con un ojal abajo. El foco_calido, puesto en luz_N como hoy, queda colgado de él.
    Devuelve (objeto `pieza_colgadores`, [Empties `punto_foco_N`])."""
    bm = bmesh.new()
    puntos = []
    for i, (x, y, z) in enumerate(g.luces, 1):
        yd = y_desde(z)
        varilla(bm, (x, yd - 0.006, z), (x, y + 0.012, z), 0.005, lados=6)
        piezas.cilindro(bm, 0.016, 0.012, (x, y + 0.006, z), lados=8)
        piezas.cilindro(bm, 0.022, 0.008, (x, yd - 0.002, z), lados=8)
        puntos.append(piezas.punto(f"punto_foco_{i}", (x, y, z)))
    return objeto("pieza_colgadores", bm, [mat_acero], recalcular=True), puntos


# ── Toldos (anclaje `frente`) ──────────────────────────────────────────

def rayas(b):
    """Rayas de la lona de un toldo del ancho de la base: un número par, de ≈ 0,15 m.
    Cada punta lleva 2 rayas (un módulo) y el tramo el resto (módulos enteros)."""
    n = 2 * max(3, round(b.w / (2 * RAYA)))
    s = b.w / n
    return SimpleNamespace(n=n, s=s, modulo=2 * s, corte=b.w / 2 - 2 * s, ancho=b.w)


def lona_rayada(bm, r, atras, adelante, faldon, feston, mat0=0, canto_atras=True):
    """Lona plana con faldón festoneado al frente, de x = −ancho/2 a +ancho/2.

    atras = (y, z) del borde de atrás (cara de abajo); adelante = (y, z) de la esquina de
    adelante (cara de abajo, cara de adentro del faldón). faldon = caída en las uniones de
    los festones; feston = cuánto más baja en el medio de cada raya. Espesor LONA, dos caras
    (se ve de abajo). Superficie mat0 = rayas pares (la primera desde −X), mat0+1 = impares.
    Topología mínima: arriba y abajo, una cara por raya; el festón solo en el faldón.
    canto_atras=False no hace el canto de atrás (cuando queda adentro de la caja del toldo).
    """
    yb, zb = atras
    yf, zf = adelante
    e = LONA

    def seccion(x):  # P0..P5 en la unión de dos rayas (fase 0)
        return [bm.verts.new(g2b(p)) for p in (
            (x, yb, zb), (x, yb + e, zb), (x, yf + e, zf + e),
            (x, yf + e - faldon, zf + e), (x, yf + e - faldon, zf), (x, yf, zf))]

    x0 = -r.ancho / 2
    cortes = [seccion(x0 + i * r.s) for i in range(r.n + 1)]
    for i in range(r.n):
        a, b = cortes[i], cortes[i + 1]
        mat = mat0 + i % 2
        afuera, adentro = [], []
        for k in range(1, FESTON_PASOS):
            x = x0 + (i + k / FESTON_PASOS) * r.s
            y = yf + e - faldon - feston * math.sin(math.pi * k / FESTON_PASOS)
            afuera.append(bm.verts.new(g2b((x, y, zf + e))))
            adentro.append(bm.verts.new(g2b((x, y, zf))))
        caras = [
            bm.faces.new((a[1], b[1], b[2], a[2])),                       # arriba
            bm.faces.new((a[0], a[5], b[5], b[0])),                       # abajo
            bm.faces.new([a[2], b[2], b[3]] + afuera[::-1] + [a[3]]),     # faldón, afuera
            bm.faces.new([a[5], a[4]] + adentro + [b[4], b[5]]),          # faldón, adentro
        ]
        if canto_atras:
            caras.append(bm.faces.new((a[0], b[0], b[1], a[1])))          # canto de atrás
        fila_a = [a[3]] + afuera + [b[3]]
        fila_i = [a[4]] + adentro + [b[4]]
        for k in range(FESTON_PASOS):                                     # canto del festón
            caras.append(bm.faces.new((fila_a[k], fila_i[k], fila_i[k + 1], fila_a[k + 1])))
        for f in caras:
            f.material_index = mat
    for sec, mat in ((cortes[0], mat0), (cortes[-1], mat0 + (r.n - 1) % 2)):
        bm.faces.new(sec).material_index = mat                            # tapas de los costados
    if not canto_atras:
        bmesh.ops.recalc_face_normals(bm, faces=[f for f in bm.faces if f.material_index in (mat0, mat0 + 1)])


def mastiles(bm, b, xm, zm, y_arriba, mat, mat_negro):
    """Dos mástiles de caño (r 0,018) agarrados con dos grapas a la cara del frente del
    carrito, por debajo de la mesada y afuera del telón; arrancan arriba de las ruedas.
    Devuelve los cilindros para la colisión."""
    col = []
    y0 = 0.40
    for sx in (-1, 1):
        x = sx * xm
        varilla(bm, (x, y0, zm), (x, y_arriba, zm), 0.018, lados=12, mat=mat, tapas=(True, False))
        for y in (0.47, b.a - 0.09):
            # Grapa de 4,5 cm: sin bisel (no se distingue a 2 m, guía 3.5).
            piezas.caja(bm, (0.045, 0.035, zm + 0.01), (x, y, (zm - 0.01) / 2), mat=mat_negro)
        col.append(((x, y0, zm), (x, y_arriba, zm), 0.018))
    return col


def brazo(bm, p0, p1, baja, mat, mat_negro):
    """Brazo articulado desplegado: dos tramos con un codo negro que baja `baja` m."""
    p0, p1 = Vector(p0), Vector(p1)
    codo = (p0 + p1) / 2 - Vector((0, baja, 0))
    varilla(bm, p0, codo, 0.012, lados=8, mat=mat, tapas=(True, False))
    varilla(bm, codo, p1, 0.012, lados=8, mat=mat, tapas=(False, True))
    piezas.cilindro(bm, 0.02, 0.04, tuple(codo), eje="x", lados=8, mat=mat_negro)


# ── Revisión ───────────────────────────────────────────────────────────

def verts_g(objetos):
    out = []
    for o in objetos:
        m = o.matrix_world
        for v in o.data.vertices:
            w = m @ v.co
            out.append(Vector((w.x, w.z, -w.y)))
    return out


def verts_mat(objetos, indices):
    """Vértices (Godot) de las caras con esas superficies."""
    out = []
    for o in objetos:
        m = o.matrix_world
        for p in o.data.polygons:
            if p.material_index in indices:
                for i in p.vertices:
                    w = m @ o.data.vertices[i].co
                    out.append(Vector((w.x, w.z, -w.y)))
    return out


def caja_g(vs):
    lo = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
    hi = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    return lo, hi


def chequeo_medidas(visibles, esperado, descripcion, tol=0.003):
    """Caja total (Godot) contra lo esperado: esperado = ((x0, x1), (y0, y1), (z0, z1))."""
    lo, hi = caja_g(verts_g(visibles))
    ok = all(abs(lo[i] - esperado[i][0]) <= tol and abs(hi[i] - esperado[i][1]) <= tol for i in range(3))
    texto = "Medidas %.2f × %.2f × %.2f m (x %.2f a %.2f, y %.2f a %.2f, z %.2f a %.2f) · %s" % (
        hi.x - lo.x, hi.y - lo.y, hi.z - lo.z, lo.x, hi.x, lo.y, hi.y, lo.z, hi.z, descripcion)
    return ok, coma(texto)


def chequeo_tramo(tramo, corte, modulo=None, tol=1e-4):
    """Estirable: el tramo solo tiene vértices en x = ±corte. Repetible: el tramo mide un
    número entero de módulos y cada vértice tiene su gemelo corrido un módulo."""
    vs = verts_g([tramo])
    if modulo is None:
        adentro = [v for v in vs if abs(abs(v.x) - corte) > tol]
        ok = not adentro
        return ok, ("Tramo estirable en X: %d vértices, todos en los cortes x = ±%.3f%s" %
                    (len(vs), corte, "" if ok else f" ({len(adentro)} adentro)"))
    n = 2 * corte / modulo
    entero = abs(n - round(n)) < 1e-4

    def clave(v, dx=0.0):
        return (round(v.x + dx, 4), round(v.y, 4), round(v.z, 4))
    todas = {clave(v) for v in vs}
    izq = {clave(v, 2 * corte) for v in vs if abs(v.x + corte) < tol}
    der = {clave(v) for v in vs if abs(v.x - corte) < tol}
    calzan = izq == der
    adentro = [v for v in vs if abs(abs(v.x) - corte) > tol]
    periodico = all(clave(v, modulo) in todas for v in adentro if v.x + modulo <= corte + tol)
    ok = entero and calzan and periodico
    return ok, ("Tramo repetible en X: %d módulos de %.3f m (2 rayas con su festón); la lona es "
                "periódica y los dos bordes del tramo calzan%s" % (
                    round(n), modulo, "" if periodico and calzan else " (NO)"))


def coma(texto):
    """Coma decimal en los números del texto (no toca los puntos de las frases)."""
    return re.sub(r"(?<=\d)\.(?=\d)", ",", texto)


def reemplazar(res, inicio, nuevo):
    return [nuevo if t.startswith(inicio) else (ok, t) for ok, t in res]


def revisar_basico(visibles, presup):
    """comun.revisar() sin las medidas ni el origen (los cambia cada tipo: el accesorio no
    está centrado en su anclaje ni apoya en el piso)."""
    res = comun.revisar(visibles, presup, (1, 1, 1), origen="base")
    return [(ok, t) for ok, t in res if not t.startswith(("Medidas", "Origen"))]


# ── Hoja de revisión ───────────────────────────────────────────────────

DIRECCIONES = {  # en Blender (frente = −Y)
    "frente": (Vector((0, -1, 0)), True),
    "costado": (Vector((-1, 0, 0)), True),           # del lado de la manija (−X)
    "tres_cuartos": (Vector((1, -1.3, 0.75)), False),
    "vendedor": (Vector((-1, 1.25, 0.7)), False),     # 3/4 desde atrás, lado de la manija
    "bajo": (Vector((0.9, -1.4, 0.18)), False),       # 3/4 bajo, a la altura de los ojos
}


def encuadrar(objetos, vista, margen=1.1):
    esquinas = [o.matrix_world @ Vector(c) for o in objetos for c in o.bound_box]
    minimo = Vector(map(min, *esquinas))
    maximo = Vector(map(max, *esquinas))
    centro = (minimo + maximo) / 2
    tam = maximo - minimo
    d, orto = DIRECCIONES[vista]
    d = d.normalized()
    cam = comun._camara()
    escena = bpy.context.scene
    aspecto = escena.render.resolution_x / escena.render.resolution_y
    radio = tam.length / 2
    if orto:
        cam.data.type = "ORTHO"
        ancho_vis = abs(d.y) * tam.x + abs(d.x) * tam.y
        cam.data.ortho_scale = max(ancho_vis, tam.z * aspecto) * margen
        cam.location = centro + d * (radio * 4 + 1)
    else:
        cam.data.type = "PERSP"
        cam.data.lens = 50
        medio = math.atan(cam.data.sensor_width / aspecto / 2 / cam.data.lens)
        cam.location = centro + d * (radio * 0.82 / math.sin(medio))
    cam.data.clip_start = 0.05
    cam.data.clip_end = radio * 100 + 10
    cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()


def sacar_fotos(pedidos):
    """pedidos = [(etiqueta, objetos, vista, luz, antes)]; antes() se llama antes del render
    (para mover la persona, cambiar colores...)."""
    tmp = Path(tempfile.mkdtemp())
    todos = {o for _, objs, *_ in pedidos for o in objs}
    cuadros = []
    for etiqueta, objs, vista, luz, antes in pedidos:
        if antes:
            antes()
        bpy.context.view_layer.update()
        comun.poner_luz(luz)
        for o in todos:
            o.hide_render = o not in objs
        encuadrar(objs, vista)
        cuadros.append((etiqueta, comun.render(tmp / f"{len(cuadros)}.png")))
    return cuadros


def armar_escena(construir, anclaje):
    """Para la hoja: las tres bases en fila (en X de Blender) con su tamaño puesto en el
    anclaje. Devuelve {tam: dict(carro=[mallas], modelo=dict de construir, x=desplazamiento)}."""
    import _base_carrito as base_carrito
    escena = {}
    x = 0.0
    for tam, id_base in TAMANOS:
        b = leer_base(id_base)
        m_carro = base_carrito.construir(id_base, grande=b.grande)
        raiz_carro = m_carro["raiz"]
        x += b.w / 2 + 0.25
        raiz_carro.location.x = x
        carro = [o for o in raiz_carro.children_recursive
                 if o.type == "MESH" and not o.name.endswith("-colonly")]
        m = construir(tam)
        m["raiz"].location = Vector((x, 0, 0)) + g2b(b.anclajes[anclaje])
        escena[tam] = {"carro": carro, "modelo": m, "x": x, "base": b}
        x += b.w / 2 + 0.6
    bpy.context.view_layer.update()
    return escena


def colgar_foco(m, x):
    """Un foco_calido en cada punto_foco_N (para ver que cuelga del colgador)."""
    import foco_calido
    out = []
    for p in m.get("puntos_foco", []):
        raiz, cuerpo, lampara, _ = foco_calido.construir()
        bpy.context.view_layer.update()
        raiz.location = p.matrix_world.translation.copy()
        out += [cuerpo, lampara]
    return out


def persona_en(b, x, pos):
    """Ubica la persona de 1,75 m en pos (Godot, relativa al centro del carrito)."""
    persona = bpy.data.objects["ref_persona_1,75m"]

    def mover():
        persona.location = Vector((x, 0, 0)) + g2b(pos)
    return mover


def juntar_revisiones(por_tamano):
    """Une las revisiones de los tres tamaños: si un chequeo dice lo mismo en los tres, va
    una sola vez con [los 3]; si no, una línea por tamaño."""
    out = []
    largo = max(len(r) for _, r in por_tamano)
    for i in range(largo):
        filas = [(tam, r[i]) for tam, r in por_tamano if i < len(r)]
        textos = {t for _, (ok, t) in filas}
        if len(textos) == 1 and len(filas) == len(por_tamano):
            ok = all(o for _, (o, _t) in filas)
            out.append((ok, "[los 3] " + filas[0][1][1]))
        else:
            out += [(ok, f"[{tam}] {t}") for tam, (ok, t) in filas]
    return out


def main(ID, construir, revisar, hoja, uvs=False):
    """Arma, revisa, guarda y exporta los tres tamaños; después la hoja (si no --sin-hoja)."""
    por_tamano = []
    ok = True
    for tam, _ in TAMANOS:
        comun.escena_vacia()
        m = construir(tam)
        bpy.context.view_layer.update()
        res = [(ok, coma(t)) for ok, t in revisar(m)]
        nombre = f"{ID}_{tam}"
        ok &= comun.imprimir_revision(nombre, res)
        comun.guardar_blend(comun.RAIZ / f"arte/fuentes/{FAMILIA}/{nombre}.blend")
        comun.exportar_glb(m["exportar"], comun.RAIZ / f"godot/modelos/{FAMILIA}/{nombre}.glb", uvs=uvs)
        por_tamano.append((tam, res))
    if "--sin-hoja" not in sys.argv:
        comun.escena_vacia()
        comun.preparar_revision()
        hoja(juntar_revisiones(por_tamano))
    if not ok:
        sys.exit(1)


def raiz_modelo(ID, tam, hijos):
    return piezas.raiz(f"{ID}_{tam}", hijos)


def componer(ID, titulo, cuadros, revision):
    comun.componer_hoja(titulo, cuadros, revision, comun.RAIZ / f"docs/arte/revisiones/{ID}.jpg")


def hoja_techo(ID, construir, titulo, revision, extra=None):
    """Hoja estándar de un techo: los tres tamaños, el chico sobre la barra chica (frente,
    costado, 3/4, lado del vendedor, atardecer, con focos colgados) y el grande sobre el carro
    grande. extra(escena) puede devolver fotos para agregar al final."""
    esc = armar_escena(construir, "techo")
    persona = bpy.data.objects["ref_persona_1,75m"]
    persona.hide_render = False
    ch, me, gr = esc["chico"], esc["mediano"], esc["grande"]
    focos_ch = colgar_foco(ch["modelo"], ch["x"])
    focos_gr = colgar_foco(gr["modelo"], gr["x"])
    todo_ch = ch["carro"] + ch["modelo"]["visibles"] + focos_ch
    todo_me = me["carro"] + me["modelo"]["visibles"] + colgar_foco(me["modelo"], me["x"])
    todo_gr = gr["carro"] + gr["modelo"]["visibles"] + focos_gr
    b = ch["base"]
    vendedor = persona_en(b, ch["x"], (0.25, 0, -b.p / 2 - 0.3))
    al_lado = persona_en(b, ch["x"], (b.w / 2 + 0.55, 0, 0.3))
    tres = [o for t in esc.values() for o in t["carro"] + t["modelo"]["visibles"]] + [persona]
    pedidos = [
        ("Los tres tamaños sobre su base · frente · día", tres, "frente", "dia",
         persona_en(b, ch["x"], (-b.w / 2 - 0.5, 0, 0.3))),
        ("Chico sobre la barra chica · frente · día", todo_ch + [persona], "frente", "dia", al_lado),
        ("Chico · costado (manija) · vendedor de 1,75 m", todo_ch + [persona], "costado", "dia", vendedor),
        ("Chico · 3/4 · día (foco_calido en el colgador)", todo_ch, "tres_cuartos", "dia", None),
        ("Chico · 3/4 lado del vendedor · día", todo_ch + [persona], "vendedor", "dia", vendedor),
        ("Chico · 3/4 · atardecer", todo_ch, "tres_cuartos", "atardecer", None),
        ("Mediano sobre la barra mediana · 3/4 · día", todo_me, "tres_cuartos", "dia", None),
        ("Grande sobre el carro grande · 3/4 · día", todo_gr, "tres_cuartos", "dia", None),
        ("Grande · 3/4 lado del vendedor · atardecer", todo_gr + [persona], "vendedor", "atardecer",
         persona_en(gr["base"], gr["x"], (0.3, 0, -gr["base"].p / 2 - 0.3))),
    ]
    if extra:
        pedidos = extra(esc, pedidos)
    cuadros = sacar_fotos(pedidos)
    componer(ID, titulo, cuadros, revision)


def revisar_techo(m):
    """Revisión de un techo (anclaje `techo`): comun.revisar() con medidas y origen propios,
    más lo que pide la lista (cubre la mesada, alero, caños, colgadores, tramo)."""
    g, b = m["g"], m["b"]
    piezas3 = m["piezas"]
    vis = m["visibles"]
    res = [chequeo_medidas(vis, m["esperado"], m["desc"], tol=m.get("tol", 0.003))]
    todos = verts_g(vis)
    techo = verts_mat(piezas3, m.get("sup_techo", {0, 1}))
    chapa = verts_mat(piezas3, {0})
    lo, hi = caja_g(todos)
    clo, chi = caja_g(chapa)
    zc = (clo.z + chi.z) / 2
    ok = abs(lo.x + hi.x) < 0.003 and abs(zc - g.zc) < 0.003 and abs(lo.y - b.a) < 0.001
    res.append((ok, ("Origen en el anclaje `techo` de %s (z %.2f del centro): centrado en X, chapa "
                     "centrada sobre la mesada (z %.3f), caños apoyados en la mesada (y = %.2f)" %
                     (b.id, b.anclajes["techo"][2], zc, lo.y))))
    res += revisar_basico(vis, m["presup"])
    tlo, thi = caja_g(techo)
    lat = thi.x - g.mesada_x
    ade = thi.z - g.mesada_z[1]
    atr = g.mesada_z[0] - tlo.z
    ok = min(lat, ade, atr) >= 0.03 and abs(tlo.x + thi.x) < 0.003
    res.append((ok, ("Cubre la mesada (%.2f × %.2f): alero de %.2f a los costados, %.2f adelante "
                     "y %.2f atrás" % (2 * g.mesada_x, g.mesada_z[1] - g.mesada_z[0], lat, ade, atr)
                     )))
    res.append((tlo.y >= ALERO_MIN - 1e-4,
                ("Alero (lo más bajo del techo) a %.2f m (mín. %.2f: vendedor de 1,75 m + margen)" %
                 (tlo.y, ALERO_MIN))))
    bridas_ok = (g.xp + BRIDA[0] / 2 <= g.mesada_x and g.zpf + BRIDA[2] / 2 <= g.mesada_z[1] and
                 g.zpb - BRIDA[2] / 2 >= g.mesada_z[0])
    res.append((bridas_ok, ("Caños parados sobre la mesada, en x = ±%.2f, z = %.2f y %.2f: no tocan "
                            "ruedas, manija ni al vendedor (lado −Z)" % (g.xp, g.zpb, g.zpf)
                            )))
    pf = m.get("puntos_foco", [])
    ok = len(pf) == len(g.luces) and all(
        (p.matrix_world.translation - g2b(l)).length < 1e-4 for p, l in zip(pf, g.luces))
    res.append((ok, "Colgadores: %d punto_foco_N = luz_N del .ron (el foco_calido cuelga del techo)"
                % len(pf)))
    res.append(chequeo_tramo(piezas3[1], g.corte))
    return res


# ── Revisión y hoja de los toldos ──────────────────────────────────────

TELON = (0.65, 0.31, 0.73, 0.012)   # telon_panchos en `frente`: medio ancho, de y a y, espesor
TECHO_FRENTE = 0.14                 # desde acá (z del frente) empiezan los faldones de los techos
TECHO_ABAJO = 2.11                  # ... que bajan hasta 2,12


def revisar_toldo(m):
    """Revisión de un toldo (anclaje `frente`)."""
    b, r = m["b"], m["r"]
    piezas3 = m["piezas"]
    vis = m["visibles"]
    res = [chequeo_medidas(vis, m["esperado"], m["desc"])]
    todos = verts_g(vis)
    lo, hi = caja_g(todos)
    ok = abs(lo.x + hi.x) < 0.003 and abs(lo.z - m["apoyo_z"]) < 0.002
    res.append((ok, "Origen en el anclaje `frente` de %s (cara del carrito, a nivel del piso): "
                    "centrado en X, %s" % (b.id, m["origen_txt"])))
    res += revisar_basico(vis, m["presup"])
    lona = verts_mat(piezas3, {0, 1})
    llo, lhi = caja_g(lona)
    ok = llo.y >= m["lona_min"] - 1e-4
    res.append((ok, "Lona de %.2f a %.2f m (mín. %.2f): %s" % (llo.y, lhi.y, m["lona_min"], m["lona_txt"])))
    tw, ty0, ty1, te = TELON
    choca = [v for v in todos if abs(v.x) < tw + 0.01 and ty0 - 0.01 < v.y < ty1 + 0.01 and v.z < te + 0.01]
    res.append((not choca, "No toca el telón (|x| < %.2f, y %.2f a %.2f, z 0 a %.3f)%s" %
                (tw, ty0, ty1, te, "" if not choca else f": {len(choca)} vértices adentro")))
    if m.get("con_techo", True):
        alto = [v for v in todos if v.y > TECHO_ABAJO and v.z > TECHO_FRENTE - 0.01]
        ok = hi.y <= 2.15 + 1e-4 and not alto
        res.append((ok, "Entra debajo de los techos: tope a %.2f m (máx. 2,15) y nada por encima de "
                        "%.2f delante de z = %.2f (sus faldones)" % (hi.y, TECHO_ABAJO, TECHO_FRENTE)))
    if m.get("mastiles"):
        y0 = min(v.y for v in todos)
        ok = y0 > b.rueda_r * 2 + 0.05 and m["mastiles"] > tw + 0.03
        res.append((ok, "Mástiles en x = ±%.2f (afuera del telón), desde y = %.2f (arriba de las "
                        "ruedas), a 9 cm de los caños de los techos" % (m["mastiles"], y0)))
    res.append(chequeo_tramo(piezas3[1], r.corte, r.modulo))
    return res


def cambiar_colores(objetos, mat_a, mat_b):
    """Para la hoja: pone mat_a en la superficie 0 y mat_b en la 1 de las tres piezas."""
    def antes():
        for o in objetos:
            o.data.materials[0] = mat_a
            o.data.materials[1] = mat_b
    return antes


def hoja_toldo(ID, construir, titulo, revision, variantes, telon=True):
    """Hoja estándar de un toldo. variantes = [(texto, mat_a, mat_b)]: la primera es la del
    .glb; la segunda y la tercera se muestran en el mediano y el grande. Con telon=True el
    chico lleva puesto el telon_panchos (mismo anclaje `frente`), para ver que no choca."""
    import techo_plano
    esc = armar_escena(construir, "frente")
    persona = bpy.data.objects["ref_persona_1,75m"]
    persona.hide_render = False
    ch, me, gr = esc["chico"], esc["mediano"], esc["grande"]
    b = ch["base"]
    techo = techo_plano.construir("chico")
    techo["raiz"].location = Vector((ch["x"], 0, 0)) + g2b(b.anclajes["techo"])
    todo_ch = ch["carro"] + ch["modelo"]["visibles"]
    if telon:
        import telon_panchos
        tel = telon_panchos.construir()
        tel.location = Vector((ch["x"], 0, 0)) + g2b(b.anclajes["frente"])
        todo_ch.append(tel)
    todo_me = me["carro"] + me["modelo"]["visibles"]
    todo_gr = gr["carro"] + gr["modelo"]["visibles"]
    fila = b.anclajes.get("frente")
    cliente = persona_en(b, ch["x"], (0.15, 0, b.p / 2 + 0.65))
    al_lado = persona_en(b, ch["x"], (b.w / 2 + 0.55, 0, 0.3))
    tres = [o for t in esc.values() for o in t["carro"] + t["modelo"]["visibles"]] + [persona]
    texto0, a0, b0 = variantes[0]
    texto1, a1, b1 = variantes[1 % len(variantes)]
    texto2, a2, b2 = variantes[2 % len(variantes)]
    pch, pme, pgr = (t["modelo"]["piezas"] for t in (ch, me, gr))

    def todos_en(a, bb):
        return lambda: [cambiar_colores(p, a, bb)() for p in (pch, pme, pgr)]

    def y(*fs):
        return lambda: [f() for f in fs]

    pedidos = [
        ("Los tres tamaños sobre su base · frente · día", tres, "frente", "dia",
         y(todos_en(a0, b0), persona_en(b, ch["x"], (-b.w / 2 - 0.5, 0, 0.3)))),
        ("Chico sobre la barra chica · frente · día", todo_ch + [persona], "frente", "dia", al_lado),
        ("Chico · costado · cliente de 1,75 m en la fila", todo_ch + [persona], "costado", "dia", cliente),
        ("Chico · 3/4 · día · " + texto0, todo_ch, "tres_cuartos", "dia", None),
        ("Chico con techo_plano_chico · 3/4 · día", todo_ch + techo["visibles"], "tres_cuartos", "dia", None),
        ("Chico · 3/4 · atardecer", todo_ch, "tres_cuartos", "atardecer", None),
        ("Mediano · 3/4 · día · " + texto1, todo_me, "tres_cuartos", "dia", cambiar_colores(pme, a1, b1)),
        ("Grande · 3/4 · día · " + texto2, todo_gr, "tres_cuartos", "dia", cambiar_colores(pgr, a2, b2)),
        ("Chico · a la altura de los ojos del cliente · día", todo_ch + techo["visibles"], "bajo", "dia", None),
    ]
    del fila
    cuadros = sacar_fotos(pedidos)
    componer(ID, titulo, cuadros, revision)
