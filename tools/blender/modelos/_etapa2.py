"""Piezas y fotos compartidas por los modelos de la etapa 2 (aderezos, proveedor, entrega).

Lo usan: pomo_aderezo, aderecera_tres, repuesto_aderezo, pack_repuestos, bandeja_entrega,
pallet y chorrito_aderezo. Complementa a comun.py y piezas.py (que no se tocan).

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

import comun  # noqa: E402
import piezas  # noqa: E402
from piezas import g2b  # noqa: E402

# Colores de godot/data/aderezos.ron (solo para la hoja: el color lo pone el juego).
ADEREZOS = [
    ("mostaza", (0.92, 0.72, 0.08)),
    ("ketchup", (0.8, 0.08, 0.05)),
    ("mayonesa", (0.97, 0.94, 0.78)),
]


def hexa(c):
    return "#%02X%02X%02X" % tuple(round(v * 255) for v in c)


def materiales_aderezo(rugosidad=0.5):
    """Materiales de referencia (no se exportan) con los tres colores del dato."""
    return {n: comun.crear_material(f"ref_{n}", hexa(c), rugosidad=rugosidad) for n, c in ADEREZOS}


# ── Tornos ─────────────────────────────────────────────────────────────

def anillo_circulo(r, y, lados, fase=0.0, cx=0.0, cz=0.0):
    """Puntos (Godot) de un círculo horizontal. Con fase 0 hay vértices sobre ±X y ±Z
    (si lados es múltiplo de 4), así la caja envolvente mide justo 2r."""
    return [(cx + r * math.cos(fase + 2 * math.pi * k / lados), y,
             cz + r * math.sin(fase + 2 * math.pi * k / lados)) for k in range(lados)]


def anillo_rr(medio_x, medio_z, radio, y, segs=2, cx=0.0, cz=0.0):
    """Rectángulo de esquinas redondeadas (Godot, a la altura y). Gira igual que
    anillo_circulo: arranca en la esquina +X+Z y va hacia +Z."""
    radio = max(1e-4, min(radio, medio_x, medio_z))
    pts = []
    for sx, sz, a0 in ((1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)):
        ox, oz = sx * (medio_x - radio), sz * (medio_z - radio)
        for i in range(segs + 1):
            a = math.radians(a0 + 90 * i / segs)
            pts.append((cx + ox + radio * math.cos(a), y, cz + oz + radio * math.sin(a)))
    return pts


def _unir(bm, anillos, mats, tapa_ini, tapa_fin):
    """Une anillos (listas de BMVert del mismo largo, o un solo vértice = polo) con caras.
    Orientación: si el perfil sube por afuera, la normal mira hacia afuera."""
    caras = []
    for i, (a, b) in enumerate(zip(anillos, anillos[1:])):
        m = mats[i] if isinstance(mats, (list, tuple)) else mats
        if len(a) == 1:
            n = len(b)
            nuevas = [bm.faces.new((a[0], b[k], b[(k + 1) % n])) for k in range(n)]
        elif len(b) == 1:
            n = len(a)
            nuevas = [bm.faces.new((a[k], b[0], a[(k + 1) % n])) for k in range(n)]
        else:
            n = len(a)
            nuevas = [bm.faces.new((a[k], b[k], b[(k + 1) % n], a[(k + 1) % n])) for k in range(n)]
        for f in nuevas:
            f.material_index = m
        caras += nuevas
    m0 = mats[0] if isinstance(mats, (list, tuple)) else mats
    m1 = mats[-1] if isinstance(mats, (list, tuple)) else mats
    if tapa_ini and len(anillos[0]) > 1:
        f = bm.faces.new(anillos[0])
        f.material_index = m0
        caras.append(f)
    if tapa_fin and len(anillos[-1]) > 1:
        f = bm.faces.new(list(reversed(anillos[-1])))
        f.material_index = m1
        caras.append(f)
    return caras


def torno(bm, perfil, lados, centro=(0.0, 0.0, 0.0), mats=0, tapa_ini=False, tapa_fin=False, fase=0.0):
    """Superficie de revolución sobre Y (Godot). perfil = [(radio, y)] relativo a `centro`.
    radio 0 = polo (abanico). tapa_ini/tapa_fin = cierra el primer/último anillo con una
    cara plana. mats = un índice o uno por banda (len(perfil) − 1)."""
    cx, cy, cz = centro
    anillos = []
    for r, y in perfil:
        if r <= 1e-9:
            anillos.append([bm.verts.new(g2b((cx, cy + y, cz)))])
        else:
            anillos.append([bm.verts.new(g2b(p)) for p in anillo_circulo(r, cy + y, lados, fase, cx, cz)])
    return _unir(bm, anillos, mats, tapa_ini, tapa_fin)


def torno_rr(bm, perfil, medio_x, medio_z, radio, segs=2, centro=(0.0, 0.0, 0.0), mats=0,
             tapa_ini=False, tapa_fin=False):
    """Como torno() pero con anillos de rectángulo redondeado. perfil = [(meter, y)] o
    [(meter, y, radio)]: `meter` = cuánto se mete desde el contorno (medio_x, medio_z)."""
    cx, cy, cz = centro
    anillos = []
    for p in perfil:
        meter, y = p[0], p[1]
        r = p[2] if len(p) > 2 else max(radio - meter, 0.002)
        anillos.append([bm.verts.new(g2b(q)) for q in
                        anillo_rr(medio_x - meter, medio_z - meter, r, cy + y, segs, cx, cz)])
    return _unir(bm, anillos, mats, tapa_ini, tapa_fin)


def borrar_caras(bm, caras, normal_godot, umbral=0.999):
    """Borra, de `caras`, las que miran hacia normal_godot (las que nunca se ven)."""
    n = g2b(normal_godot)
    fuera = []
    for f in caras:
        if not f.is_valid:
            continue
        f.normal_update()
        if f.normal.dot(n) > umbral:
            fuera.append(f)
    bmesh.ops.delete(bm, geom=fuera, context="FACES")


def objeto_en(nombre, bm, materiales, origen_godot, sombreado="duro"):
    """Termina el bmesh y deja el origen del objeto en origen_godot (sin mover la malla)."""
    bmesh.ops.translate(bm, vec=-g2b(origen_godot), verts=bm.verts)
    obj = piezas.terminar(nombre, bm, materiales, sombreado=sombreado)
    obj.location = g2b(origen_godot)
    return obj


def verts_godot(obj):
    m = obj.matrix_world
    return [Vector(((m @ v.co).x, (m @ v.co).z, -(m @ v.co).y)) for v in obj.data.vertices]


def limites_godot(objetos):
    vs = [v for o in objetos for v in verts_godot(o)]
    mn = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
    mx = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    return mn, mx


# ── Fotos ──────────────────────────────────────────────────────────────

DIRECCIONES = {  # en Blender (frente = −Y). (dirección, ortográfica)
    "frente": (Vector((0, -1, 0)), True),
    "costado": (Vector((1, 0, 0)), True),
    "arriba": (Vector((0, -0.0001, 1)), True),
    "tres_cuartos": (Vector((1, -1.3, 0.9)), False),
    "vendedor": (Vector((-0.9, 1.3, 1.0)), False),      # 3/4 desde atrás (lado vendedor)
    "vendedor_alto": (Vector((-0.5, 1.0, 1.6)), False),  # como lo ve el jugador parado atrás
    "bajo": (Vector((1, -1.2, 0.35)), False),
}


def encuadrar(objetos, vista, margen=1.2, lente=50):
    """Cámara mirando la caja que envuelve `objetos` (los demás pueden verse igual)."""
    bpy.context.view_layer.update()
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
    radio = max(tam.length / 2, 0.02)
    if orto:
        cam.data.type = "ORTHO"
        if vista == "arriba":
            vis = (tam.x, tam.y)
        else:
            vis = (abs(d.y) * tam.x + abs(d.x) * tam.y, tam.z)
        cam.data.ortho_scale = max(vis[0], vis[1] * aspecto) * margen
        cam.location = centro + d * (radio * 4 + 1)
    else:
        cam.data.type = "PERSP"
        cam.data.lens = lente
        medio = math.atan(cam.data.sensor_width / aspecto / 2 / cam.data.lens)
        cam.location = centro + d * (radio * margen * 0.75 / math.sin(medio))
    cam.data.clip_start = 0.005
    cam.data.clip_end = radio * 100 + 20
    cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()


def sacar_fotos(pedidos):
    """pedidos = [(etiqueta, visibles, vista, luz)] o con un 5.º elemento: los objetos a
    encuadrar (por defecto, los visibles). Se ocultan los objetos de otros pedidos."""
    tmp = Path(tempfile.mkdtemp())
    todos = {o for p in pedidos for o in p[1]}
    cuadros = []
    for p in pedidos:
        etiqueta, objs, vista, luz = p[:4]
        encuadre = p[4] if len(p) > 4 else objs
        margen = p[5] if len(p) > 5 else 1.2
        comun.poner_luz(luz)
        for o in todos:
            o.hide_render = o not in objs
        encuadrar(encuadre, vista, margen=margen)
        cuadros.append((etiqueta, comun.render(tmp / f"{len(cuadros)}.png")))
    return cuadros


def copiar(obj, nombre, material=None, indice=0):
    """Copia un objeto (con malla propia) para las fotos; opcionalmente cambia un material."""
    c = obj.copy()
    c.data = obj.data.copy()
    c.name = nombre
    if material is not None:
        c.data.materials[indice] = material
    bpy.context.scene.collection.objects.link(c)
    return c


def sin_cara_de_atras(obj):
    """Solo para las fotos: el plástico transparente del objeto no dibuja las caras de atrás
    (en Godot el material transparente tiene el culling de atrás prendido; Cycles dibuja las
    dos capas y el plástico se ve el doble de blanco)."""
    for i, mat in enumerate(obj.data.materials):
        if mat is None or mat.node_tree is None:
            continue
        bsdf = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if bsdf is None or bsdf.inputs["Alpha"].default_value >= 1.0:
            continue
        nuevo = mat.copy()
        nuevo.name = f"ref_{mat.name}_una_cara"
        nt = nuevo.node_tree
        b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
        salida = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        transp = nt.nodes.new("ShaderNodeBsdfTransparent")
        mezcla = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(geo.outputs["Backfacing"], mezcla.inputs[0])
        nt.links.new(b.outputs[0], mezcla.inputs[1])
        nt.links.new(transp.outputs[0], mezcla.inputs[2])
        nt.links.new(mezcla.outputs[0], salida.inputs["Surface"])
        obj.data.materials[i] = nuevo


def barra_chica():
    """La barra chica terminada (para fotos de escala sobre el mostrador)."""
    import _base_carrito
    m = _base_carrito.construir("barra_chica")
    return [m["pintura"], m["estructura"]]


def suavizar_hasta(obj, grados):
    """Suaviza las aristas entre caras del mismo material que doblan `grados` o menos.
    piezas.terminar marca duras las de más de 30°, y un cilindro de 12 lados dobla justo
    30° (por redondeo, a veces queda facetado); uno de 8 lados dobla 45°."""
    lim = math.radians(grados)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.normal_update()
    for e in bm.edges:
        caras = e.link_faces
        if len(caras) == 2 and caras[0].material_index == caras[1].material_index \
                and caras[0].normal.angle(caras[1].normal, 0.0) <= lim:
            e.smooth = True
    bm.to_mesh(obj.data)
    bm.free()
