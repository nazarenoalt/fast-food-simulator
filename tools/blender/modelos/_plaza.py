"""Piezas y ayudas comunes de los modelos de la plaza (familia `plaza`).

Complementa a piezas.py (que no se toca) con lo que necesitan el banco, el farol, la fuente,
los árboles y los tramos (cordón, cantero). Como en piezas.py, todo se da en **ejes de Godot**
(X derecha, Y arriba, Z hacia el frente) y se pasa a Blender con piezas.g2b.

- barra(): caja larga entre dos puntos del plano YZ (patas inclinadas, respaldo).
- torno(): pieza de revolución sobre el eje Y (fuente, farol), con un perfil (radio, y).
- perfil_extruido(): perfil (z, y) estirado a lo largo de X (cordón, cantero).
- colision_cilindro(): como piezas.colision_cilindro pero con giro (troncos inclinados).
- poste(): prisma entre dos puntos con las tapas horizontales (patas inclinadas que apoyan
  planas en el piso: juegos de plaza).
- caño(): cilindro entre dos puntos cualesquiera (cadenas, pasamanos, travesaños).
- colision_cajas(): varias cajas en un solo `<nombre>-colonly` (guía 6.1).
- verts_mundo(), limites(): para los chequeos propios.
- reemplazar(): cambia una línea de la revisión de comun.revisar() por un chequeo propio.
- hoja(): fotos y hoja de revisión con la persona de 1,75 m.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import bpy  # noqa: E402  (antes que bmesh)
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

import comun  # noqa: E402
import piezas  # noqa: E402
from piezas import g2b  # noqa: E402

FAMILIA = "plaza"


# ── Piezas ─────────────────────────────────────────────────────────────

def barra(bm, x, a, b, ancho, grosor, mat=0, bisel=0.0):
    """Caja larga de `a` a `b` (puntos (y, z) de Godot) en el plano x = cte.

    ancho = medida en el plano YZ, perpendicular al largo; grosor = medida en X.
    """
    (y1, z1), (y2, z2) = a, b
    largo = math.hypot(y2 - y1, z2 - z1)
    angulo = math.degrees(math.atan2(z2 - z1, y2 - y1))  # giro sobre X: Y hacia +Z
    return piezas.caja(bm, (grosor, largo, ancho), (x, (y1 + y2) / 2, (z1 + z2) / 2),
                       mat=mat, bisel=bisel, rot=(angulo, 0, 0))


def torno(bm, perfil, lados, mats=None, centro=(0.0, 0.0, 0.0), tapa_abajo=False,
          tapa_arriba=False, abierta=False):
    """Pieza de revolución sobre el eje Y de Godot. perfil = [(radio, y)] de abajo hacia
    arriba (o de afuera hacia adentro); un radio 0 cierra en punta. mats[i] = material de la
    banda entre el punto i y el i+1. Una cara plana queda hacia +Z (el frente).
    Los radios son de las caras planas (apotema), no de las aristas: así un torno de radio 3
    mide justo 6 m de lado a lado, y uno de 4 lados y radio a es un cuadrado de lado 2a.
    abierta=True: superficie suelta (una cortina de agua), con las caras mirando hacia afuera
    del eje en vez de recalcular las normales."""
    mats = mats or [0] * (len(perfil) - 1)
    previas = set(bm.faces)
    giro = math.pi / lados - math.pi / 2
    aj = 1 / math.cos(math.pi / lados)
    anillos = []
    for r, y in perfil:
        r *= aj
        if r < 1e-9:
            anillos.append([bm.verts.new(g2b((centro[0], centro[1] + y, centro[2])))])
        else:
            anillos.append([bm.verts.new(g2b((centro[0] + r * math.cos(giro + 2 * math.pi * k / lados),
                                                  centro[1] + y,
                                                  centro[2] + r * math.sin(giro + 2 * math.pi * k / lados))))
                            for k in range(lados)])
    for i, (a, b) in enumerate(zip(anillos, anillos[1:])):
        for k in range(lados):
            if len(a) == 1:
                vs = (a[0], b[(k + 1) % lados], b[k])
            elif len(b) == 1:
                vs = (a[k], a[(k + 1) % lados], b[0])
            else:
                vs = (a[k], a[(k + 1) % lados], b[(k + 1) % lados], b[k])
            f = bm.faces.new(vs)
            f.material_index = mats[i]
    if tapa_abajo and len(anillos[0]) > 1:
        bm.faces.new(anillos[0]).material_index = mats[0]
    if tapa_arriba and len(anillos[-1]) > 1:
        bm.faces.new(anillos[-1]).material_index = mats[-1]
    nuevas = [f for f in bm.faces if f not in previas]
    if abierta:
        eje = g2b(centro)
        for f in nuevas:
            f.normal_update()
            radial = f.calc_center_median() - eje
            radial.z = 0
            if f.normal.dot(radial) < 0:
                f.normal_flip()
    else:
        bmesh.ops.recalc_face_normals(bm, faces=nuevas)
    return nuevas


def disco(bm, radio, y, lados, mat=0, centro=(0.0, 0.0)):
    """Disco plano horizontal (un solo polígono, mirando hacia arriba) a la altura y.
    centro = (x, z) de Godot. Para superficies de agua. radio = apotema, como en torno()."""
    giro = math.pi / lados - math.pi / 2
    radio /= math.cos(math.pi / lados)
    vs = [bm.verts.new(g2b((centro[0] + radio * math.cos(giro + 2 * math.pi * k / lados), y,
                            centro[1] + radio * math.sin(giro + 2 * math.pi * k / lados))))
          for k in range(lados)]
    f = bm.faces.new(vs)
    f.normal_update()
    if f.normal.z < 0:
        f.normal_flip()
    f.material_index = mat
    return [f]


def perfil_extruido(bm, perfil, largo, mat=0, tapas=True):
    """Perfil cerrado [(z, y)] (sentido antihorario visto desde +X) estirado sobre X, de
    −largo/2 a +largo/2. Los lados que quedan apoyados en y = 0 no se crean (no se ven,
    guía 3.6)."""
    previas = set(bm.faces)
    n = len(perfil)
    izq = [bm.verts.new(g2b((-largo / 2, y, z))) for z, y in perfil]
    der = [bm.verts.new(g2b((largo / 2, y, z))) for z, y in perfil]
    for k in range(n):
        k2 = (k + 1) % n
        if perfil[k][1] < 1e-9 and perfil[k2][1] < 1e-9:
            continue  # apoyado en el piso
        bm.faces.new((izq[k], izq[k2], der[k2], der[k]))
    if tapas:
        bm.faces.new(list(reversed(izq)))
        bm.faces.new(der)
    nuevas = [f for f in bm.faces if f not in previas]
    for f in nuevas:
        f.material_index = mat
    bmesh.ops.recalc_face_normals(bm, faces=nuevas)
    return nuevas


def colision_cilindro(nombre, radio, alto, centro, lados=8, rot=(0.0, 0.0, 0.0)):
    """Colisión `<nombre>-colonly` cilíndrica (eje Y), con giro opcional (grados, Godot)."""
    bm = bmesh.new()
    piezas.cilindro(bm, radio, alto, centro, lados=lados, rot=rot)
    malla = bpy.data.meshes.new(f"{nombre}-colonly")
    bm.to_mesh(malla)
    bm.free()
    obj = bpy.data.objects.new(f"{nombre}-colonly", malla)
    bpy.context.scene.collection.objects.link(obj)
    obj.display_type = "WIRE"
    obj.hide_render = True
    return obj


def poste(bm, base, tope, radio, lados, mat=0, tapa_abajo=False, tapa_arriba=True):
    """Prisma de `lados` caras de `base` a `tope` (puntos de Godot) con las dos tapas
    horizontales: una pata inclinada apoya plana en el piso (no se hunde ni flota) y su
    punta queda a una altura justa. La sección horizontal es un círculo de `radio` (apotema,
    como torno); medida perpendicular al eje queda apenas más fina (cos de la inclinación).
    tapa_abajo=False: la tapa apoyada en el piso no se crea (guía 3.6)."""
    previas = set(bm.faces)
    giro = math.pi / lados - math.pi / 2
    r = radio / math.cos(math.pi / lados)
    anillos = [[bm.verts.new(g2b((c[0] + r * math.cos(giro + 2 * math.pi * k / lados), c[1],
                                  c[2] + r * math.sin(giro + 2 * math.pi * k / lados))))
                for k in range(lados)] for c in (base, tope)]
    a, b = anillos
    for k in range(lados):
        bm.faces.new((a[k], a[(k + 1) % lados], b[(k + 1) % lados], b[k]))
    if tapa_abajo:
        bm.faces.new(a)
    if tapa_arriba:
        bm.faces.new(b)
    nuevas = [f for f in bm.faces if f not in previas]
    for f in nuevas:
        f.material_index = mat
    bmesh.ops.recalc_face_normals(bm, faces=nuevas)
    return nuevas


def caño(bm, a, b, radio, lados, mat=0, tapas=(True, True)):
    """Cilindro de `a` a `b` (puntos de Godot), con los anillos perpendiculares al eje."""
    a, b = Vector(a), Vector(b)
    d = (b - a).normalized()
    ref = Vector((0, 1, 0)) if abs(d.y) < 0.9 else Vector((1, 0, 0))
    u = d.cross(ref).normalized()
    w = d.cross(u).normalized()
    previas = set(bm.faces)
    anillos = [[bm.verts.new(g2b(c + (u * math.cos(2 * math.pi * k / lados) +
                                       w * math.sin(2 * math.pi * k / lados)) * radio))
                for k in range(lados)] for c in (a, b)]
    p0, p1 = anillos
    for k in range(lados):
        bm.faces.new((p0[k], p0[(k + 1) % lados], p1[(k + 1) % lados], p1[k]))
    if tapas[0]:
        bm.faces.new(p0)
    if tapas[1]:
        bm.faces.new(p1)
    nuevas = [f for f in bm.faces if f not in previas]
    for f in nuevas:
        f.material_index = mat
    bmesh.ops.recalc_face_normals(bm, faces=nuevas)
    return nuevas


def colision_cajas(nombre, cajas):
    """Varias cajas en un solo objeto `<nombre>-colonly` (guía 6.1: Godot lo importa como
    malla de triángulos, sirve para objetos fijos). cajas = [(medidas, centro, rot)]."""
    bm = bmesh.new()
    for medidas, centro, rot in cajas:
        piezas.caja(bm, medidas, centro, rot=rot)
    malla = bpy.data.meshes.new(f"{nombre}-colonly")
    bm.to_mesh(malla)
    bm.free()
    obj = bpy.data.objects.new(f"{nombre}-colonly", malla)
    bpy.context.scene.collection.objects.link(obj)
    obj.display_type = "WIRE"
    obj.hide_render = True
    return obj


def borrar_apoyadas(bm, y=0.0):
    """Borra las caras horizontales que miran abajo y están apoyadas en el piso (guía 3.6)."""
    z = y
    abajo = [f for f in bm.faces if f.normal.z < -0.999 and all(abs(v.co.z - z) < 1e-5 for v in f.verts)]
    bmesh.ops.delete(bm, geom=abajo, context="FACES_ONLY")


# ── Chequeos ───────────────────────────────────────────────────────────

def verts_mundo(objetos):
    bpy.context.view_layer.update()
    return [o.matrix_world @ v.co for o in objetos for v in o.data.vertices]


def limites(objetos):
    """(mínimo, máximo) en ejes de GODOT a partir de los vértices."""
    vs = [Vector((v.x, v.z, -v.y)) for v in verts_mundo(objetos)]
    return Vector(map(min, *vs)), Vector(map(max, *vs))


def reemplazar(res, prefijo, ok, texto):
    """Cambia la línea de comun.revisar() que empieza con `prefijo` por un chequeo propio."""
    return [(ok, texto) if t.startswith(prefijo) else (o, t) for o, t in res]


def m(texto):
    """Números con coma decimal para los títulos de las hojas."""
    return texto.replace(".", ",")


# ── Hoja de revisión ───────────────────────────────────────────────────

# Vistas en perspectiva (dirección desde el objeto hacia la cámara, en ejes de Blender).
PERSPECTIVAS = {
    "tres_cuartos": Vector((1, -1.3, 0.8)),
    "tres_cuartos_bajo": Vector((1, -1.3, 0.35)),   # objetos altos (farol, árboles)
    "tres_cuartos_atras": Vector((-1, 1.3, 0.6)),
}


def encuadre_ajustado(objetos, vista, margen=1.1):
    """Cámara en perspectiva que deja todo el objeto adentro del cuadro y lo llena (la de
    comun.encuadrar corta los objetos altos y finitos)."""
    esquinas = [o.matrix_world @ Vector(c) for o in objetos for c in o.bound_box]
    d = PERSPECTIVAS[vista].normalized()
    cam = comun._camara()
    cam.data.type = "PERSP"
    cam.data.lens = 50
    escena = bpy.context.scene
    aspecto = escena.render.resolution_x / escena.render.resolution_y
    tan_h = cam.data.sensor_width / 2 / cam.data.lens
    tan_v = tan_h / aspecto
    rot = (-d).to_track_quat("-Z", "Y")
    derecha, arriba = rot @ Vector((1, 0, 0)), rot @ Vector((0, 1, 0))
    centro = sum(esquinas, Vector()) / len(esquinas)
    for _ in range(4):  # centrar lo que se ve y alejar lo justo
        dist = max(max((p - centro).dot(d) + abs((p - centro).dot(derecha)) * margen / tan_h,
                       (p - centro).dot(d) + abs((p - centro).dot(arriba)) * margen / tan_v)
                   for p in esquinas)
        ojo = centro + d * dist
        us = [(p - ojo).dot(derecha) / -(p - ojo).dot(d) for p in esquinas]
        vs = [(p - ojo).dot(arriba) / -(p - ojo).dot(d) for p in esquinas]
        prof = -(centro - ojo).dot(d)
        centro = centro + derecha * (max(us) + min(us)) / 2 * prof + arriba * (max(vs) + min(vs)) / 2 * prof
    cam.location = centro + d * dist
    cam.rotation_euler = rot.to_euler()
    cam.data.clip_start = 0.05
    cam.data.clip_end = dist * 10 + 50


def hoja(id_, titulo, cuadros_pedidos, revision, persona_en=None):
    """cuadros_pedidos = [(etiqueta, objetos, vista, luz, de_cerca)] como comun.sacar_fotos,
    con las vistas en perspectiva de PERSPECTIVAS (ajustadas al objeto). En los objetos se
    puede poner el texto "persona": se cambia por la silueta de 1,75 m, en persona_en (Godot)."""
    import tempfile
    comun.preparar_revision()
    persona = bpy.data.objects["ref_persona_1,75m"]
    if persona_en is not None:
        persona.location = g2b(persona_en)
    pedidos = [(e, [persona if o == "persona" else o for o in objs], v, l, c)
               for e, objs, v, l, c in cuadros_pedidos]
    tmp = Path(tempfile.mkdtemp())
    todos = {o for _, objs, *_ in pedidos for o in objs}
    cuadros = []
    for etiqueta, objs, vista, luz, de_cerca in pedidos:
        comun.poner_luz(luz)
        for o in todos:
            o.hide_render = o not in objs
        if vista in PERSPECTIVAS:
            encuadre_ajustado(objs, vista)
        else:
            comun.encuadrar(objs, vista, de_cerca=de_cerca)
        cuadros.append((etiqueta, comun.render(tmp / f"{len(cuadros)}.png")))
    comun.componer_hoja(titulo, cuadros, revision, comun.RAIZ / f"docs/arte/revisiones/{id_}.jpg")


def guardar_y_exportar(id_, exportar):
    comun.guardar_blend(comun.RAIZ / f"arte/fuentes/{FAMILIA}/{id_}.blend")
    comun.exportar_glb(exportar, comun.RAIZ / f"godot/modelos/{FAMILIA}/{id_}.glb")
