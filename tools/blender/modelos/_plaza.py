"""Piezas y ayudas comunes de los modelos de la plaza (familia `plaza`).

Complementa a piezas.py (que no se toca) con lo que necesitan el banco, el farol, la fuente,
los árboles y los tramos (cordón, cantero). Como en piezas.py, todo se da en **ejes de Godot**
(X derecha, Y arriba, Z hacia el frente) y se pasa a Blender con piezas.g2b.

- barra(): caja larga entre dos puntos del plano YZ (patas inclinadas, respaldo).
- torno(): pieza de revolución sobre el eje Y (fuente, farol), con un perfil (radio, y).
- perfil_extruido(): perfil (z, y) estirado a lo largo de X (cordón, cantero).
- colision_cilindro(): como piezas.colision_cilindro pero con giro (troncos inclinados).
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
          tapa_arriba=False):
    """Pieza de revolución sobre el eje Y de Godot. perfil = [(radio, y)] de abajo hacia
    arriba (o de afuera hacia adentro); un radio 0 cierra en punta. mats[i] = material de la
    banda entre el punto i y el i+1. Una cara plana queda hacia +Z (el frente)."""
    mats = mats or [0] * (len(perfil) - 1)
    previas = set(bm.faces)
    giro = math.pi / lados - math.pi / 2
    anillos = []
    for r, y in perfil:
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
    bmesh.ops.recalc_face_normals(bm, faces=nuevas)
    return nuevas


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

def hoja(id_, titulo, cuadros_pedidos, revision, persona_en=None):
    """cuadros_pedidos = [(etiqueta, objetos, vista, luz, de_cerca)] como comun.sacar_fotos;
    en los objetos se puede poner el texto "persona" y se cambia por la silueta de 1,75 m,
    ubicada en persona_en (posición de Godot)."""
    comun.preparar_revision()
    persona = bpy.data.objects["ref_persona_1,75m"]
    if persona_en is not None:
        persona.location = g2b(persona_en)
    pedidos = [(e, [persona if o == "persona" else o for o in objs], v, l, c)
               for e, objs, v, l, c in cuadros_pedidos]
    cuadros = comun.sacar_fotos(pedidos)
    comun.componer_hoja(titulo, cuadros, revision, comun.RAIZ / f"docs/arte/revisiones/{id_}.jpg")


def guardar_y_exportar(id_, exportar):
    comun.guardar_blend(comun.RAIZ / f"arte/fuentes/{FAMILIA}/{id_}.blend")
    comun.exportar_glb(exportar, comun.RAIZ / f"godot/modelos/{FAMILIA}/{id_}.glb")
