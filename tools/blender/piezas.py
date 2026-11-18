"""Piezas básicas para armar modelos duros (carritos, equipos, accesorios, plaza).

Complementa a comun.py. Todo se arma dentro de un bmesh y recién al final se convierte en
objeto, así un modelo puede tener muchas piezas en pocos objetos.

Las posiciones y medidas se dan **en ejes de Godot** (X derecha, Y arriba, Z hacia el
cliente), igual que en los .ron, y acá se pasan a Blender (guía 2.3):
    Godot (x, y, z)  →  Blender (x, −z, y)

Uso típico:
    bm = bmesh.new()
    piezas.caja(bm, (0.4, 0.02, 0.3), (0, 0.01, 0), mat=0, bisel=0.004)
    piezas.cilindro(bm, 0.018, 0.02, (0, 0.1, -0.16), eje="z", lados=12, mat=1)
    obj = piezas.terminar("hervidor_chico", bm, [m_acero, m_negro])
    col = piezas.colision_caja("hervidor_chico", (0.4, 0.2, 0.3), (0, 0.1, 0))
    p = piezas.punto("punto_luz", (0, 0, 0))
"""
import math

import bpy  # antes que bmesh
import bmesh
from mathutils import Matrix, Vector

ANGULO_DURO = math.radians(30)  # guía 3.4: Smooth by Angle a 30°


def g2b(p):
    """Punto o medida de Godot (x, y, z) → Blender (x, −z, y)."""
    return Vector((p[0], -p[2], p[1]))


def medidas_g2b(m):
    """Medidas (ancho X, alto Y, profundidad Z) de Godot → tamaños en ejes de Blender."""
    return Vector((m[0], m[2], m[1]))


def _marcar(bm, caras_previas, mat):
    nuevas = [f for f in bm.faces if f not in caras_previas]
    for f in nuevas:
        f.material_index = mat
    return nuevas


def caja(bm, medidas, centro, mat=0, bisel=0.0, rot=(0.0, 0.0, 0.0), sin_abajo=False):
    """Caja de medidas (X, Y, Z de Godot) con su centro en `centro` (Godot).

    bisel = ancho del bisel en metros (guía 3.3), 1 segmento. rot = grados en Godot (X, Y, Z),
    aplicada alrededor del centro de la caja. sin_abajo = borra la cara de abajo (cuando
    nunca se ve, guía 3.6).
    """
    previas = set(bm.faces)
    t = medidas_g2b(medidas)
    res = bmesh.ops.create_cube(bm, size=1.0)
    vs = res["verts"]
    bmesh.ops.scale(bm, vec=t, verts=vs)
    if bisel > 0:
        lim = min(t) / 2 - 1e-4
        aristas = list({e for v in vs for e in v.link_edges})
        bmesh.ops.bevel(bm, geom=vs + aristas, offset=min(bisel, lim), segments=1,
                        affect="EDGES", profile=0.5, clamp_overlap=True)
    nuevas = _marcar(bm, previas, mat)
    if sin_abajo:
        abajo = [f for f in nuevas if f.normal.z < -0.999 and
                 all(abs(v.co.z + t.z / 2) < 1e-6 for v in f.verts)]
        bmesh.ops.delete(bm, geom=abajo, context="FACES_ONLY")
        nuevas = [f for f in nuevas if f.is_valid]
    _transformar(bm, nuevas, centro, rot)
    return nuevas


def cilindro(bm, radio, alto, centro, eje="y", lados=12, mat=0, tapas=(True, True),
             rot=(0.0, 0.0, 0.0), radio_arriba=None, radio_a_caras=False):
    """Cilindro (o cono truncado si radio_arriba) con su centro en `centro` (Godot).

    eje = "x", "y" o "z" de Godot: hacia dónde apunta el largo. lados: guía 3.2.
    tapas = (abajo, arriba) del eje; False la deja abierta (caño, batea).
    Una cara plana queda hacia abajo/adelante, no una arista.
    radio_a_caras=False: el radio se mide en las aristas (los vértices), y las caras planas
    quedan un poco más adentro. Con True, el radio se mide en las caras planas (guía 3.2):
    usarlo cuando la medida importa (ruedas que apoyan, colisiones, piezas que encajan).
    """
    previas = set(bm.faces)
    r2 = radio if radio_arriba is None else radio_arriba
    if radio_a_caras:
        radio, r2 = radio / math.cos(math.pi / lados), r2 / math.cos(math.pi / lados)
    giro = math.pi / lados
    abajo = [bm.verts.new((radio * math.cos(giro + 2 * math.pi * k / lados),
                           radio * math.sin(giro + 2 * math.pi * k / lados), -alto / 2))
             for k in range(lados)]
    arriba = [bm.verts.new((r2 * math.cos(giro + 2 * math.pi * k / lados),
                            r2 * math.sin(giro + 2 * math.pi * k / lados), alto / 2))
              for k in range(lados)]
    for k in range(lados):
        bm.faces.new((abajo[k], abajo[(k + 1) % lados], arriba[(k + 1) % lados], arriba[k]))
    if tapas[0]:
        bm.faces.new(list(reversed(abajo)))
    if tapas[1]:
        bm.faces.new(arriba)
    nuevas = _marcar(bm, previas, mat)
    # El cilindro se armó sobre Z de Blender (= Y de Godot). Se acuesta según el eje.
    if eje == "x":
        bmesh.ops.rotate(bm, verts=_verts(nuevas), matrix=Matrix.Rotation(math.pi / 2, 3, "Y"))
    elif eje == "z":  # Z de Godot = −Y de Blender (abajo del eje = lado vendedor)
        bmesh.ops.rotate(bm, verts=_verts(nuevas), matrix=Matrix.Rotation(math.pi / 2, 3, "X"))
    _transformar(bm, nuevas, centro, rot)
    return nuevas


def esfera(bm, radio, centro, lados=12, mat=0, escala=(1.0, 1.0, 1.0)):
    """UV sphere de `lados` × lados/2 (guía 3.2). escala en ejes de Godot."""
    previas = set(bm.faces)
    bmesh.ops.create_uvsphere(bm, u_segments=lados, v_segments=max(3, lados // 2), radius=radio)
    nuevas = _marcar(bm, previas, mat)
    bmesh.ops.scale(bm, vec=medidas_g2b(escala), verts=_verts(nuevas))
    _transformar(bm, nuevas, centro, (0, 0, 0))
    return nuevas


def _verts(caras):
    return list({v for f in caras for v in f.verts})


def _transformar(bm, caras, centro, rot):
    vs = _verts(caras)
    if any(rot):
        # Rotación en grados de Godot → ejes de Blender (X igual, Y Godot = Z Blender, Z Godot = −Y).
        m = (Matrix.Rotation(math.radians(rot[1]), 3, "Z") @
             Matrix.Rotation(math.radians(rot[0]), 3, "X") @
             Matrix.Rotation(math.radians(-rot[2]), 3, "Y"))
        bmesh.ops.rotate(bm, verts=vs, matrix=m)
    bmesh.ops.translate(bm, vec=g2b(centro), verts=vs)


def mover(bm, caras, desplazamiento):
    """Mueve caras ya creadas (desplazamiento en Godot)."""
    bmesh.ops.translate(bm, vec=g2b(desplazamiento), verts=_verts(caras))


def terminar(nombre, bm, materiales, sombreado="duro"):
    """Convierte el bmesh en objeto. sombreado (guía 3.4):
    "duro"  = suave con aristas marcadas a más de 30° (metal, madera, plástico);
    "suave" = todo suave (comida, telas);
    "plano" = facetado (árboles, piedras).
    También marca como arista dura todo cambio de material.
    """
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        f.smooth = sombreado != "plano"
    if sombreado != "plano":
        for e in bm.edges:
            caras = e.link_faces
            if len(caras) != 2:  # borde abierto
                e.smooth = sombreado == "suave"
                continue
            distinto = caras[0].material_index != caras[1].material_index
            angulo = caras[0].normal.angle(caras[1].normal, 0.0)
            e.smooth = not (distinto or (sombreado == "duro" and angulo > ANGULO_DURO))
    from comun import objeto_desde_bmesh
    return objeto_desde_bmesh(nombre, bm, materiales)


def colision_caja(nombre, medidas, centro, rot=(0.0, 0.0, 0.0)):
    """Colisión invisible para objetos fijos (guía 6.1): objeto `<nombre>-colonly`, sin
    material. No se pasa a comun.revisar() (no se dibuja), pero sí a exportar_glb()."""
    bm = bmesh.new()
    caja(bm, medidas, centro, rot=rot)
    malla = bpy.data.meshes.new(f"{nombre}-colonly")
    bm.to_mesh(malla)
    bm.free()
    obj = bpy.data.objects.new(f"{nombre}-colonly", malla)
    bpy.context.scene.collection.objects.link(obj)
    obj.display_type = "WIRE"
    obj.hide_render = True
    return obj


def colision_cilindro(nombre, radio, alto, centro, eje="y", lados=12, radio_a_caras=False):
    bm = bmesh.new()
    cilindro(bm, radio, alto, centro, eje=eje, lados=lados, radio_a_caras=radio_a_caras)
    malla = bpy.data.meshes.new(f"{nombre}-colonly")
    bm.to_mesh(malla)
    bm.free()
    obj = bpy.data.objects.new(f"{nombre}-colonly", malla)
    bpy.context.scene.collection.objects.link(obj)
    obj.display_type = "WIRE"
    obj.hide_render = True
    return obj


def punto(nombre, pos, tam=0.05):
    """Empty `punto_...` en una posición de Godot (guía 6.2). Se exporta como nodo vacío."""
    e = bpy.data.objects.new(nombre, None)
    e.empty_display_type = "PLAIN_AXES"
    e.empty_display_size = tam
    e.location = g2b(pos)
    bpy.context.scene.collection.objects.link(e)
    return e


def raiz(nombre, hijos):
    """Empty raíz con el id del modelo, padre de todas las piezas (como `pancho`)."""
    r = bpy.data.objects.new(nombre, None)
    r.empty_display_size = 0.1
    bpy.context.scene.collection.objects.link(r)
    for h in hijos:
        h.parent = r
    return r
