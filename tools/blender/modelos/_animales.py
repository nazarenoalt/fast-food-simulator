"""Piezas y fotos compartidas por los animales de la plaza (`paloma`, `perro`; familia
`personajes`).

Complementa a comun.py, piezas.py y _plaza.py (que no se tocan). Todo en ejes de Godot
(X derecha, Y arriba, Z hacia adelante), como piezas.py. Los animales miran hacia +Z y su
origen va en el piso, entre las patas.

Cómo se arma un animal low poly (guía 5.5, "facetado suave"):
    - Cada parte (cuerpo, cuello, cabeza, pata, cola) es un **lofteo**: una serie de anillos
      (cortes transversales elípticos de pocos lados) unidos por caras, con las puntas
      cerradas en abanico hacia un punto (hocico, pico, punta de la cola) o con una tapa
      plana. Así se controla la silueta corte por corte, que es lo que hace que se reconozca.
    - Cada parte es una malla cerrada (las que se meten en otra, como el cuello en el
      cuerpo, se pisan: no se ven las uniones y la pieza puede girar sin abrir un hueco).
    - Sombreado: suave entre caras que doblan poco y arista dura en las que doblan mucho o
      cambian de material (terminar()).
    - Sin esqueleto: lo que el código puede mover va como objeto aparte `pieza_<parte>`, con
      el origen en la articulación (cuello, hombro, cadera, base de la cola).
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402  (antes que bmesh)
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

import comun  # noqa: E402
from piezas import g2b  # noqa: E402

FAMILIA = "personajes"


def V(*p):
    return Vector(p)


# ── Anillos y lofteos ──────────────────────────────────────────────────

def anillo(centro, normal, ancho, alto, lados, arriba=(0, 1, 0), abajo=None, fase=0.0,
           corrido=0.0):
    """Anillo elíptico de `lados` puntos (Godot) alrededor de `centro`, en el plano
    perpendicular a `normal`.

    ancho = medio ancho en X (o en la dirección lateral); alto = medio alto hacia `arriba`;
    abajo = medio alto hacia el otro lado (por defecto = alto): panza más honda que lomo.
    fase = giro del primer punto (0 = un vértice arriba, en el lomo).
    corrido = cuánto se corre el punto de más ancho hacia arriba (−1 a 1): pecho alto.
    """
    c, n = V(*centro), V(*normal).normalized()
    lat = V(1, 0, 0)
    if abs(lat.dot(n)) > 0.95:
        lat = V(0, 0, 1)
    u = (lat - n * lat.dot(n)).normalized()
    a = V(*arriba)
    w = (a - n * a.dot(n) - u * a.dot(u))
    w = w.normalized() if w.length > 1e-6 else n.cross(u).normalized()
    abajo = alto if abajo is None else abajo
    puntos = []
    for k in range(lados):
        t = fase + 2 * math.pi * k / lados
        cy = math.cos(t)
        h = alto if cy >= 0 else abajo
        s = math.sin(t) * (1 - corrido * cy * 0.5)
        puntos.append(c + u * ancho * s + w * h * cy)
    return puntos


def lofteo(bm, anillos, mats=0, punta_ini=None, punta_fin=None, mat_ini=None, mat_fin=None):
    """Une anillos (listas de puntos de Godot, misma cantidad) con caras.

    mats = material de cada banda (número o lista, una por banda entre anillos), o una
    función mats(banda, k) para pintar por cara (k = punto del anillo donde arranca la cara;
    con fase 0, k = 0 es el lomo y k = lados/2 la panza).
    punta_ini / punta_fin = punto (Godot) al que se cierra cada extremo en abanico; None =
    tapa plana. mat_ini / mat_fin = material de esas puntas (por defecto, el de la banda
    vecina). Devuelve las caras nuevas.
    """
    n_b = len(anillos) - 1
    if callable(mats):
        por_cara = mats
    else:
        lista = mats if isinstance(mats, (list, tuple)) else [mats] * n_b
        def por_cara(i, k):
            return lista[i]
    previas = set(bm.faces)
    vs = [[bm.verts.new(g2b(p)) for p in a] for a in anillos]
    n = len(vs[0])
    for i, (a, b) in enumerate(zip(vs, vs[1:])):
        for k in range(n):
            bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k])).material_index = por_cara(i, k)
    for punta, a, m in ((punta_ini, vs[0], por_cara(0, 0) if mat_ini is None else mat_ini),
                        (punta_fin, vs[-1], por_cara(n_b - 1, 0) if mat_fin is None else mat_fin)):
        if punta is None:
            bm.faces.new(a).material_index = m
        else:
            v = bm.verts.new(g2b(punta))
            for k in range(n):
                bm.faces.new((a[k], a[(k + 1) % n], v)).material_index = m
    nuevas = [f for f in bm.faces if f not in previas]
    bmesh.ops.recalc_face_normals(bm, faces=nuevas)
    return nuevas


def tubo(bm, puntos, radios, lados, mats=0, punta_fin=None, arriba=(0, 1, 0), aplastar=1.0,
         fase=0.0):
    """Lofteo que sigue una línea (patas, cola): anillos perpendiculares a la dirección
    media en cada punto. radios = uno por punto. aplastar = alto / ancho del corte."""
    P = [V(*p) for p in puntos]
    anillos = []
    for i, p in enumerate(P):
        d = (P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]).normalized()
        anillos.append(anillo(p, d, radios[i], radios[i] * aplastar, lados, arriba=arriba, fase=fase))
    return lofteo(bm, anillos, mats, punta_fin=punta_fin)


# ── Objetos ────────────────────────────────────────────────────────────

def terminar(nombre, bm, materiales, origen=(0.0, 0.0, 0.0), angulo=40.0):
    """bmesh → objeto con el origen en `origen` (Godot), sin mover la malla.

    Sombreado "facetado suave" (guía 5.5): suave entre caras que doblan `angulo` grados o
    menos; arista dura si doblan más o si cambia el material. El objeto lleva solo los
    materiales que usa (los índices de `materiales` son los de todo el modelo).
    """
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.translate(bm, vec=-g2b(origen), verts=bm.verts)
    lim = math.radians(angulo)
    for f in bm.faces:
        f.smooth = True
    for e in bm.edges:
        caras = e.link_faces
        if len(caras) != 2:
            e.smooth = False
            continue
        distinto = caras[0].material_index != caras[1].material_index
        e.smooth = not (distinto or caras[0].normal.angle(caras[1].normal, 0.0) > lim)
    # Solo los materiales que usa la pieza (en el mismo orden).
    usados = sorted({f.material_index for f in bm.faces})
    mapa = {viejo: nuevo for nuevo, viejo in enumerate(usados)}
    for f in bm.faces:
        f.material_index = mapa[f.material_index]
    obj = comun.objeto_desde_bmesh(nombre, bm, [materiales[i] for i in usados])
    obj.location = g2b(origen)
    return obj


def raiz(nombre, hijos):
    r = bpy.data.objects.new(nombre, None)
    r.empty_display_size = 0.1
    bpy.context.scene.collection.objects.link(r)
    for h in hijos:
        h.parent = r
    return r


# ── Chequeos ───────────────────────────────────────────────────────────

def verts_godot(objetos):
    bpy.context.view_layer.update()
    out = []
    for o in objetos:
        m = o.matrix_world
        for v in o.data.vertices:
            p = m @ v.co
            out.append(V(p.x, p.z, -p.y))
    return out


def limites(objetos):
    vs = verts_godot(objetos)
    return V(*map(min, *vs)), V(*map(max, *vs))


def reemplazar(res, prefijo, ok, texto):
    return [(ok, texto) if t.startswith(prefijo) else (o, t) for o, t in res]


def coma(texto):
    return texto.replace(".", ",")


def chequeo_patas(patas, tol=0.003):
    """Origen en el piso, entre las patas: el punto más bajo de las patas toca Y = 0 y el
    centro de lo que apoya (vértices a menos de 1 cm del piso) cae en X = Z = 0."""
    vs = [v for v in verts_godot(patas)]
    piso = min(v.y for v in vs)
    apoyo = [v for v in vs if v.y < piso + 0.01]
    cx = (max(v.x for v in apoyo) + min(v.x for v in apoyo)) / 2
    cz = (max(v.z for v in apoyo) + min(v.z for v in apoyo)) / 2
    ok = abs(piso) < 1e-4 and abs(cx) < tol and abs(cz) < tol
    return ok, ("Origen en el piso entre las patas (apoyo centrado en x %+.3f, z %+.3f; "
                "la cola corre la caja envolvente)" % (cx, cz))


def chequeo_piezas(piezas_origen):
    """[(objeto, origen esperado en Godot, texto)]: cada pieza con su origen en la articulación."""
    ok = True
    textos = []
    for o, esperado, texto in piezas_origen:
        bpy.context.view_layer.update()
        p = o.matrix_world.translation
        ok &= (p - g2b(esperado)).length < 1e-5
        textos.append(texto)
    return ok, "Piezas con el origen en la articulación: " + "; ".join(textos)


# ── Hoja ───────────────────────────────────────────────────────────────

def guardar_y_exportar(id_, exportar):
    comun.guardar_blend(comun.RAIZ / f"arte/fuentes/{FAMILIA}/{id_}.blend")
    comun.exportar_glb(exportar, comun.RAIZ / f"godot/modelos/{FAMILIA}/{id_}.glb")


def hoja(id_, titulo, pedidos, revision, persona_en=(0.0, 0.0, 0.0)):
    """pedidos = [(etiqueta, objetos, vista, luz, antes)]: vista = frente | costado | arriba
    (ortográficas, de cerca) o una de _plaza.PERSPECTIVAS; antes() se llama antes de la foto
    (para poner una pose). En los objetos, "persona" = la silueta de 1,75 m en persona_en."""
    import tempfile
    import _plaza as plaza
    comun.preparar_revision()
    persona = bpy.data.objects["ref_persona_1,75m"]
    persona.location = g2b(persona_en)
    pedidos = [(e, [persona if o == "persona" else o for o in objs], v, l, a)
               for e, objs, v, l, a in pedidos]
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
        if vista in plaza.PERSPECTIVAS:
            plaza.encuadre_ajustado(objs, vista, margen=1.15)
        else:
            comun.encuadrar(objs, vista, de_cerca=True, margen=1.15)
        cuadros.append((etiqueta, comun.render(tmp / f"{len(cuadros)}.png")))
    comun.componer_hoja(titulo, cuadros, revision, comun.RAIZ / f"docs/arte/revisiones/{id_}.jpg")
