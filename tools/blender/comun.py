"""Funciones compartidas por los scripts de Blender del proyecto.

Aplica la guía de modelado (docs/arte/guia-modelado-3d.md): materiales de la paleta,
revisión automática de cada modelo, exportación a .glb y hoja de revisión.
"""
import json
import math
from pathlib import Path

import bpy  # antes que bmesh: con el paquete bpy, bmesh existe recién después
import bmesh
from mathutils import Vector

RAIZ = Path(__file__).resolve().parents[2]
PALETA_JSON = RAIZ / "tools/arte/paleta.json"
BIBLIOTECA = RAIZ / "arte/biblioteca"
MATERIALES_BLEND = BIBLIOTECA / "materiales.blend"
REFERENCIAS_BLEND = BIBLIOTECA / "referencias.blend"
COLECCION_REFERENCIAS = "Referencias"

# Luz de la escena de referencia, tomada del ciclo de día del juego (rust/core/src/reloj.rs).
LUCES = {
    "dia": {
        "sol_color": "#FFF7EB", "sol_fuerza": 4.0, "sol_altura": 50.0, "sol_rumbo": -35.0,
        "cielo_arriba": "#4D85E0", "cielo_horizonte": "#ADC7E6", "cielo_fuerza": 1.0,
    },
    "atardecer": {
        "sol_color": "#FF8040", "sol_fuerza": 3.0, "sol_altura": 8.0, "sol_rumbo": -60.0,
        "cielo_arriba": "#2E4475", "cielo_horizonte": "#F2804D", "cielo_fuerza": 0.6,
    },
}


# ── Color ──────────────────────────────────────────────────────────────

def hex_a_lineal(hexa, alfa=1.0):
    """'#RRGGBB' (sRGB, lo que muestra el campo Hex de Blender) → RGBA lineal."""
    def canal(c):
        c = int(hexa[c:c + 2], 16) / 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (canal(1), canal(3), canal(5), alfa)


def paleta():
    """Todos los materiales de la paleta (sin los de solo referencia), por nombre."""
    datos = json.loads(PALETA_JSON.read_text())
    return {
        m["nombre"]: m
        for g in datos["grupos"] for m in g["materiales"]
        if not m.get("solo_referencia")
    }


def crear_material(nombre, hexa, metalico=0.0, rugosidad=0.7, alfa=1.0, emision=0.0):
    """Un material de la guía: un Principled BSDF, sin texturas."""
    mat = bpy.data.materials.get(nombre) or bpy.data.materials.new(nombre)
    if mat.node_tree is None:  # Blender < 5 necesita activar los nodos
        mat.use_nodes = True
    bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    color = hex_a_lineal(hexa)
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Metallic"].default_value = metalico
    bsdf.inputs["Roughness"].default_value = rugosidad
    bsdf.inputs["Alpha"].default_value = alfa
    if emision > 0:
        bsdf.inputs["Emission Color"].default_value = color
        bsdf.inputs["Emission Strength"].default_value = emision
    mat.diffuse_color = hex_a_lineal(hexa, alfa)  # color en la vista sólida de Blender
    if alfa < 1.0:
        if hasattr(mat, "surface_render_method"):
            mat.surface_render_method = "BLENDED"
        if hasattr(mat, "blend_method"):
            mat.blend_method = "BLEND"
    return mat


def cargar_materiales(*nombres):
    """Trae materiales de arte/biblioteca/materiales.blend (no se crean a mano)."""
    faltan = [n for n in nombres if n not in bpy.data.materials]
    if faltan:
        if not MATERIALES_BLEND.exists():
            raise SystemExit(f"Falta {MATERIALES_BLEND}: corré primero tools/blender/biblioteca.py")
        with bpy.data.libraries.load(str(MATERIALES_BLEND), link=False) as (src, dst):
            no_estan = [n for n in faltan if n not in src.materials]
            if no_estan:
                raise SystemExit(f"Materiales que no están en la paleta: {no_estan}")
            dst.materials = faltan
    return [bpy.data.materials[n] for n in nombres]


# ── Escena ─────────────────────────────────────────────────────────────

def escena_vacia():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    escena = bpy.context.scene
    escena.unit_settings.system = "METRIC"
    escena.unit_settings.scale_length = 1.0
    return escena


def objeto_desde_bmesh(nombre, bm, materiales):
    malla = bpy.data.meshes.new(nombre)
    bm.to_mesh(malla)
    bm.free()
    for m in materiales:
        malla.materials.append(m)
    obj = bpy.data.objects.new(nombre, malla)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def capsula(nombre, radio, largo, lados=8, material=None):
    """Cápsula acostada sobre X (como las de productos.ron), centrada en el origen."""
    bm = bmesh.new()
    mitad = largo / 2 - radio
    anillos = []
    pasos = max(2, lados // 4)
    perfiles = [(-mitad - radio * math.cos(a), radio * math.sin(a))
                for a in (i * math.pi / 2 / pasos for i in range(1, pasos + 1))]
    perfiles += [(-x, r) for x, r in reversed(perfiles)]
    for x, r in perfiles:
        anillos.append([bm.verts.new((x, r * math.cos(t), r * math.sin(t)))
                        for t in (2 * math.pi * k / lados for k in range(lados))])
    for a, b in zip(anillos, anillos[1:]):
        for k in range(lados):
            bm.faces.new((a[k], a[(k + 1) % lados], b[(k + 1) % lados], b[k]))
    for punta, anillo in (((-largo / 2, 0, 0), anillos[0]), ((largo / 2, 0, 0), anillos[-1])):
        v = bm.verts.new(punta)
        for k in range(lados):
            bm.faces.new((anillo[(k + 1) % lados], anillo[k], v))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        f.smooth = True
    return objeto_desde_bmesh(nombre, bm, [material] if material else [])


# ── Revisión automática (guía, sección 8.2) ────────────────────────────

def contar_triangulos(obj):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    malla = ev.to_mesh()
    tris = sum(len(p.vertices) - 2 for p in malla.polygons)
    ev.to_mesh_clear()
    return tris


def _volumen_con_signo(obj):
    """> 0 si las normales apuntan hacia afuera."""
    m = obj.data
    vol = 0.0
    for p in m.polygons:
        v = [m.vertices[i].co for i in p.vertices]
        for i in range(1, len(v) - 1):
            vol += v[0].dot(v[i].cross(v[i + 1])) / 6
    return vol


def revisar(obj, presupuesto, medidas_godot, origen="centro", max_materiales=4, tolerancia=0.002):
    """Revisa un modelo contra la guía. Devuelve [(ok, texto)].

    medidas_godot = (ancho X, alto Y, profundidad Z) en metros, como en los .ron.
    origen = "centro" (comida, objetos de mano) o "base" (todo lo que se apoya).
    """
    res = []
    esperado = Vector((medidas_godot[0], medidas_godot[2], medidas_godot[1]))  # a ejes de Blender
    d = obj.dimensions
    ok = all(abs(d[i] - esperado[i]) <= tolerancia for i in range(3))
    res.append((ok, "Medidas %.3f × %.3f × %.3f m (esperado %.3f × %.3f × %.3f)" % (
        d.x, d.z, d.y, medidas_godot[0], medidas_godot[1], medidas_godot[2])))

    tris = contar_triangulos(obj)
    res.append((tris <= presupuesto, f"Triángulos: {tris} (máx. {presupuesto})"))

    limpio = (obj.rotation_euler.to_quaternion().angle < 1e-5
              and all(abs(s - 1) < 1e-5 for s in obj.scale))
    res.append((limpio, "Rotación 0 y escala 1 aplicadas"))

    esquinas = [Vector(c) for c in obj.bound_box]
    minimo = Vector(map(min, *esquinas))
    maximo = Vector(map(max, *esquinas))
    centro = (minimo + maximo) / 2
    if origen == "centro":
        ok = centro.length <= tolerancia
        texto = "Origen en el centro del objeto"
    else:
        ok = abs(minimo.z) <= tolerancia and Vector((centro.x, centro.y)).length <= tolerancia
        texto = "Origen en el centro de la base, a nivel del piso"
    res.append((ok, texto))

    nombres = [m.name for m in obj.data.materials if m]
    validos = paleta()
    fuera = [n for n in nombres if n not in validos]
    res.append((not fuera, "Materiales de la paleta: " + ", ".join(nombres) +
                (f" (NO están en la paleta: {fuera})" if fuera else "")))
    res.append((len(nombres) <= max_materiales, f"Materiales: {len(nombres)} (máx. {max_materiales})"))
    usados = {p.material_index for p in obj.data.polygons}
    res.append((usados == set(range(len(nombres))), "Todos los materiales se usan"))

    bm = bmesh.new()
    bm.from_mesh(obj.data)
    sueltos = sum(1 for v in bm.verts if not v.link_faces)
    antes = len(bm.verts)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    dobles = antes - len(bm.verts)
    bm.free()
    res.append((sueltos == 0 and dobles == 0, f"Sin vértices sueltos ({sueltos}) ni duplicados ({dobles})"))
    res.append((_volumen_con_signo(obj) > 0, "Normales hacia afuera"))
    return res


def imprimir_revision(nombre, res):
    print(f"\nRevisión de {nombre}:")
    for ok, texto in res:
        print(("  ✔ " if ok else "  ✘ ") + texto)
    if not all(ok for ok, _ in res):
        print("  → El modelo NO cumple la guía.")
    return all(ok for ok, _ in res)


# ── Archivos ───────────────────────────────────────────────────────────

def guardar_blend(ruta):
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    bpy.context.preferences.filepaths.save_version = 0  # sin copias .blend1
    bpy.ops.wm.save_as_mainfile(filepath=str(ruta), compress=True)
    print(f"Guardado {ruta.relative_to(RAIZ)}")


def exportar_glb(objetos, ruta):
    """Exporta con las opciones de la guía (sección 7.3)."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for o in objetos:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objetos[0]
    bpy.ops.export_scene.gltf(
        filepath=str(ruta),
        export_format="GLB",
        use_selection=True,
        export_yup=True,
        export_apply=True,
        export_texcoords=False,
        export_normals=True,
        export_materials="EXPORT",
        export_cameras=False,
        export_lights=False,
        export_animations=False,
        export_extras=False,
    )
    print(f"Exportado {ruta.relative_to(RAIZ)}")


# ── Escena de referencia y hoja de revisión ────────────────────────────

def cargar_referencias():
    """Trae la colección de referencias, los soles y los cielos de referencias.blend."""
    with bpy.data.libraries.load(str(REFERENCIAS_BLEND), link=False) as (src, dst):
        dst.collections = [COLECCION_REFERENCIAS]
        dst.worlds = [w for w in src.worlds]
    col = bpy.data.collections[COLECCION_REFERENCIAS]
    bpy.context.scene.collection.children.link(col)
    return col


def poner_luz(modo):
    """Prende el sol y el cielo de 'dia' o 'atardecer'."""
    escena = bpy.context.scene
    for o in bpy.data.objects:
        if o.type == "LIGHT" and o.name.startswith("sol_"):
            o.hide_render = o.name != f"sol_{modo}"
    escena.world = bpy.data.worlds[f"cielo_{modo}"]


def configurar_render(ancho=640, alto=480, muestras=48):
    escena = bpy.context.scene
    escena.render.engine = "CYCLES"
    escena.cycles.device = "CPU"
    escena.cycles.samples = muestras
    try:
        escena.cycles.use_denoising = True
        escena.cycles.denoiser = "OPENIMAGEDENOISE"
    except (AttributeError, TypeError):
        escena.cycles.use_denoising = False
    escena.render.resolution_x = ancho
    escena.render.resolution_y = alto
    escena.render.resolution_percentage = 100
    escena.render.film_transparent = False
    escena.render.image_settings.file_format = "PNG"
    # El juego usa tonemap Filmic (dia_noche.rs).
    for vista in ("Filmic", "AgX", "Standard"):
        try:
            escena.view_settings.view_transform = vista
            break
        except TypeError:
            continue


def _camara():
    cam = bpy.data.objects.get("cam_revision")
    if cam is None:
        cam = bpy.data.objects.new("cam_revision", bpy.data.cameras.new("cam_revision"))
        bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    return cam


def encuadrar(objetos, vista, margen=1.25, de_cerca=False):
    """Ubica la cámara. vista: frente | costado | arriba | tres_cuartos.

    Las vistas planas usan todas la misma escala (para comparar proporciones), salvo
    con de_cerca=True, que llena el cuadro con lo que se ve desde esa vista.
    """
    esquinas = [o.matrix_world @ Vector(c) for o in objetos for c in o.bound_box]
    minimo = Vector(map(min, *esquinas))
    maximo = Vector(map(max, *esquinas))
    centro = (minimo + maximo) / 2
    tam = maximo - minimo
    cam = _camara()
    escena = bpy.context.scene
    aspecto = escena.render.resolution_x / escena.render.resolution_y
    direcciones = {
        "frente": Vector((0, -1, 0)),       # lo que ve el cliente
        "costado": Vector((1, 0, 0)),
        "arriba": Vector((0, 0, 1)),
        "tres_cuartos": Vector((1, -1.3, 0.9)).normalized(),
    }
    d = direcciones[vista]
    radio = tam.length / 2
    if vista != "tres_cuartos":
        # Misma escala en las tres vistas planas, para comparar proporciones.
        cam.data.type = "ORTHO"
        visibles = {"frente": (tam.x, tam.z), "costado": (tam.y, tam.z), "arriba": (tam.x, tam.y)}[vista]
        cam.data.ortho_scale = (max(visibles[0], visibles[1] * aspecto) if de_cerca else max(tam)) * margen
        cam.location = centro + d * (radio * 4 + 1)
    else:
        cam.data.type = "PERSP"
        cam.data.lens = 50
        medio_fov_vertical = math.atan(cam.data.sensor_width / aspecto / 2 / cam.data.lens)
        cam.location = centro + d * (radio * 0.9 / math.sin(medio_fov_vertical))
    cam.data.clip_start = radio * 0.01
    cam.data.clip_end = radio * 100 + 10
    cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()


def render(ruta):
    bpy.context.scene.render.filepath = str(ruta)
    bpy.ops.render.render(write_still=True)
    return Path(ruta)


def componer_hoja(titulo, cuadros, revision, ruta, columnas=3):
    """Arma la hoja de revisión (guía 8.1) con PIL: cuadros = [(etiqueta, png)]."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("PIL no está instalado: quedan los renders sueltos, sin hoja.")
        return
    imgs = [(e, Image.open(p)) for e, p in cuadros]
    w, h = imgs[0][1].size
    filas = (len(imgs) + columnas - 1) // columnas
    pie = 34 + 26 * len(revision)
    margen, cab = 16, 64
    hoja = Image.new("RGB", (margen + columnas * (w + margen), cab + filas * (h + 40) + pie),
                     (245, 243, 238))
    dib = ImageDraw.Draw(hoja)

    def fuente(n, t):
        try:
            return ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{n}", t)
        except OSError:
            return ImageFont.load_default()

    f, fb = fuente("DejaVuSans.ttf", 18), fuente("DejaVuSans-Bold.ttf", 28)
    dib.text((margen, 18), titulo, fill=(30, 30, 30), font=fb)
    for i, (etiqueta, im) in enumerate(imgs):
        x = margen + (i % columnas) * (w + margen)
        y = cab + (i // columnas) * (h + 40)
        hoja.paste(im, (x, y))
        dib.text((x, y + h + 8), etiqueta, fill=(50, 50, 50), font=f)
    y = cab + filas * (h + 40) + 4
    dib.text((margen, y), "Revisión automática (guía 8.2)", fill=(30, 30, 30), font=fuente("DejaVuSans-Bold.ttf", 18))
    for ok, texto in revision:
        y += 26
        dib.text((margen, y), ("✔ " if ok else "✘ ") + texto,
                 fill=(30, 120, 50) if ok else (190, 40, 30), font=f)
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    hoja.save(ruta, quality=88, optimize=True)
    print(f"Hoja de revisión: {ruta.relative_to(RAIZ)}")
