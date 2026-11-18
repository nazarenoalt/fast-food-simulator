"""Modelo: pizarra de precios (id `pizarra_precios`, godot/data/accesorios.ron).

Genera:
    arte/fuentes/accesorios/pizarra_precios.blend
    godot/modelos/accesorios/pizarra_precios.glb
    docs/arte/revisiones/pizarra_precios.jpg

Uso:
    blender -b -P tools/blender/modelos/pizarra_precios.py
    python tools/blender/modelos/pizarra_precios.py

Forma: pizarrita de mostrador tipo atril. Marco de madera de 0,36 × 0,44 con la pizarra
adentro, inclinado 12° hacia atrás como hoy (accesorios.ron), con un apoyo de madera atrás
(pata trasera) y una repisita para la tiza abajo, adelante. La pizarra va **en blanco**
(sin nada escrito): es un objeto aparte, `pieza_pizarra` (M_Pizarra), con la cara de adelante
mapeada (UV de 0 a 1), para que más adelante el juego pueda escribir encima lo que haga falta
(precios que cambian, menú del día).
Este archivo también guarda las funciones de carteles con texto (guía 4.5) que usa
telon_panchos.py.
Medidas: 0,36 de ancho y 0,434 de alto; de fondo, 0,234 con la pata (el marco solo, 0,11).
Origen: centro de la base (del apoyo de las patas), a nivel del mostrador.
Colisión: una caja `pizarra_precios-colonly` inclinada como el marco.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import comun  # noqa: E402
import piezas  # noqa: E402

ID = "pizarra_precios"
FAMILIA = "accesorios"
PRESUPUESTO = 400  # lista de modelos (accesorios medianos: 1.000)

INCLINACION = 12.0                 # grados hacia atrás (rot X = −12 en accesorios.ron)
MARCO = (0.36, 0.44, 0.02)         # ancho, alto, espesor
MARCO_ANCHO = 0.02                 # ancho de la moldura
PIZARRA = (0.32, 0.40, 0.016)      # la parte negra: 4 mm detrás del frente, al ras atrás
PIZARRA_HUNDIDA = 0.004
REPISA = (0.30, 0.012, 0.022)      # repisita de la tiza, abajo adelante
PATA = (0.035, 0.014)              # ancho y espesor de la pata trasera
PATA_ALTO = 0.40                   # dónde se engancha la pata, medido sobre el marco
PATA_ANGULO = 14.0                 # grados de la pata respecto de la vertical, hacia atrás
MEDIDAS = (0.36, 0.434, 0.234)     # con la pata y la repisa


# ── Carteles con texto (guía 4.5): compartido con telon_panchos ───────────

def color_paleta(nombre):
    h = comun.paleta()[nombre]["hex"]
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def fuente(tam, negrita=True):
    from PIL import ImageFont
    nombre = "DejaVuSans-Bold.ttf" if negrita else "DejaVuSans.ttf"
    try:
        return ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{nombre}", tam)
    except OSError:
        return ImageFont.load_default()


def lienzo(tam, fondo):
    """Imagen RGB con fondo de la paleta; se dibuja sin suavizado, así cada píxel es un
    color de la paleta (lo comprueba revisar_cartel)."""
    from PIL import Image, ImageDraw
    img = Image.new("RGB", tam, color_paleta(fondo))
    dib = ImageDraw.Draw(img)
    dib.fontmode = "1"
    return img, dib


def guardar_textura(img, ruta):
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    img.save(ruta, optimize=True)
    print(f"Textura {ruta.relative_to(comun.RAIZ)} ({img.size[0]} × {img.size[1]} px)")


def material_cartel(nombre, ruta_png, rugosidad=0.85):
    """Material T_<id>: un Principled BSDF con la imagen del cartel como color (guía 4.5).
    Es el único material fuera de la paleta permitido, y solo con colores de la paleta."""
    mat = bpy.data.materials.new(nombre)
    if mat.node_tree is None:
        mat.use_nodes = True
    nodos = mat.node_tree.nodes
    bsdf = next(n for n in nodos if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Roughness"].default_value = rugosidad
    bsdf.inputs["Metallic"].default_value = 0.0
    tex = nodos.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(ruta_png))
    tex.interpolation = "Linear"
    mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


def mapear_cara(bm, cara, eje_u, eje_v):
    """UV de una cara plana: la imagen entera estirada sobre ella. eje_u/eje_v = vectores
    (Blender) hacia la derecha y hacia arriba de la imagen. Las demás caras quedan en (0, 0)."""
    uv = bm.loops.layers.uv.verify()
    us = [v.co.dot(eje_u) for v in cara.verts]
    vs = [v.co.dot(eje_v) for v in cara.verts]
    for bucle in cara.loops:
        bucle[uv].uv = ((bucle.vert.co.dot(eje_u) - min(us)) / (max(us) - min(us)),
                        (bucle.vert.co.dot(eje_v) - min(vs)) / (max(vs) - min(vs)))


def revisar_cartel(res, materiales_cartel):
    """Cambia el chequeo de paleta de comun.revisar(): acepta los materiales T_<id> de
    carteles si su imagen usa solo colores de la paleta (guía 4.1 y 4.5)."""
    from PIL import Image
    validos = {color_paleta(n) for n in comun.paleta()}
    notas = []
    ok_cartel = True
    for mat in materiales_cartel:
        img = next(n.image for n in mat.node_tree.nodes if n.type == "TEX_IMAGE")
        colores = {c for _, c in Image.open(bpy.path.abspath(img.filepath)).convert("RGB").getcolors(1 << 20)}
        fuera = colores - validos
        ok_cartel &= not fuera
        notas.append(f"{mat.name}: imagen {img.size[0]}×{img.size[1]}, {len(colores)} colores" +
                     (" de la paleta" if not fuera else f", {len(fuera)} FUERA de la paleta"))
    nombres = {m.name for m in materiales_cartel}
    nuevo = []
    for ok, texto in res:
        if texto.startswith("Materiales de la paleta"):
            fuera = [n for n in texto.split(" (NO están")[0].split(": ", 1)[1].split(", ")
                     if n not in comun.paleta() and n not in nombres]
            ok = not fuera and ok_cartel
            texto = texto.split(" (NO están")[0] + " · cartel " + "; ".join(notas) + (
                f" · NO están en la paleta: {fuera}" if fuera else "")
        nuevo.append((ok, texto))
    return nuevo


# ── La pizarra ────────────────────────────────────────────────────────────

def marco(bm, mat):
    """Moldura del marco: anillo rectangular de una sola malla (sin caras ocultas en las
    esquinas), con todos los cantos biselados."""
    previas = set(bm.faces)
    ax, ay, e = MARCO[0] / 2, MARCO[1], MARCO[2]
    bx, by0, by1 = ax - MARCO_ANCHO, MARCO_ANCHO, ay - MARCO_ANCHO
    afuera = [(ax, 0), (ax, ay), (-ax, ay), (-ax, 0)]
    adentro = [(bx, by0), (bx, by1), (-bx, by1), (-bx, by0)]
    capas = {}
    for z, clave in ((0.0, "f"), (-e, "a")):
        capas[clave] = ([bm.verts.new(piezas.g2b((x, y, z))) for x, y in afuera],
                        [bm.verts.new(piezas.g2b((x, y, z))) for x, y in adentro])
    fo, fi = capas["f"]
    ao, ai = capas["a"]
    for k in range(4):
        j = (k + 1) % 4
        bm.faces.new((fo[k], fo[j], fi[j], fi[k]))     # frente
        bm.faces.new((ao[k], ai[k], ai[j], ao[j]))     # atrás
        bm.faces.new((fo[k], ao[k], ao[j], fo[j]))     # canto de afuera
        bm.faces.new((fi[k], fi[j], ai[j], ai[k]))     # canto de adentro
    nuevas = [f for f in bm.faces if f not in previas]
    bmesh.ops.recalc_face_normals(bm, faces=nuevas)
    aristas = list({ed for f in nuevas for ed in f.edges})
    bmesh.ops.bevel(bm, geom=aristas, offset=0.003, segments=1, affect="EDGES", clamp_overlap=True)
    nuevas = [f for f in bm.faces if f not in previas]
    for f in nuevas:
        f.material_index = mat
    return nuevas


def girar_x(p, grados):
    """Rotación de Godot alrededor de X (positivo: +Y va hacia +Z)."""
    a = math.radians(grados)
    return (p[0], p[1] * math.cos(a) - p[2] * math.sin(a), p[1] * math.sin(a) + p[2] * math.cos(a))


def pata(bm, arriba, mat, plano=None):
    """Pata trasera: listón desde `arriba` (Godot, detrás del marco) hasta el piso, con el
    pie cortado horizontal (apoya plano). plano = (punto, normal) en Godot: la punta de
    arriba se corta contra ese plano (la espalda de la pizarra), así apoya entera."""
    previas = set(bm.faces)
    a = math.radians(PATA_ANGULO)
    d = Vector((0, -math.cos(a), -math.sin(a)))          # hacia abajo y hacia atrás (Godot)
    n = Vector((0, -math.sin(a), math.cos(a)))           # perpendicular, hacia adelante
    ancho, esp = PATA[0] / 2, PATA[1] / 2
    arriba = Vector(arriba)
    vs = []
    for sx in (-1, 1):
        for sn in (-1, 1):
            p = arriba + Vector((sx * ancho, 0, 0)) + n * (sn * esp)
            if plano is not None:                          # sube hasta tocar el plano
                q, m = Vector(plano[0]), Vector(plano[1])
                p = p + d * ((q - p).dot(m) / d.dot(m))
            t = -p.y / d.y                                 # hasta y = 0
            vs.append((bm.verts.new(piezas.g2b(p)), bm.verts.new(piezas.g2b(p + d * t))))
    (a0, b0), (a1, b1), (a2, b2), (a3, b3) = vs           # (−x,−n) (−x,+n) (+x,−n) (+x,+n)
    bm.faces.new((a0, a1, a3, a2))                        # arriba
    for (p, q), (r, s) in (((a0, b0), (a1, b1)), ((a1, b1), (a3, b3)),
                           ((a3, b3), (a2, b2)), ((a2, b2), (a0, b0))):
        bm.faces.new((p, q, s, r))
    nuevas = [f for f in bm.faces if f not in previas]  # sin la cara de abajo (apoyada)
    for f in nuevas:
        f.material_index = mat
    return nuevas


def construir():
    m_pizarra, m_madera = comun.cargar_materiales("M_Pizarra", "M_Madera")
    bm = bmesh.new()        # madera: marco, repisa y pata (material 0 sin usar, ver abajo)
    bm_piz = bmesh.new()    # pieza_pizarra
    # 1) Marco, pizarra y repisa, parados, con el frente en z = 0 y la base en y = 0.
    marco(bm, 1)
    zp = -PIZARRA_HUNDIDA - PIZARRA[2] / 2
    caras_piz = piezas.caja(bm_piz, PIZARRA, (0, MARCO[1] / 2, zp), mat=0)
    frente = max(caras_piz, key=lambda f: -f.calc_center_median().y)   # −Y Blender = +Z Godot
    piezas.caja(bm, REPISA, (0, MARCO_ANCHO * 0.5, REPISA[2] / 2), mat=1, bisel=0.003)
    # 2) Se inclina hacia atrás girando sobre el canto de abajo de atrás del marco
    #    (rot X = −INCLINACION de Godot = la misma rotación alrededor de X en Blender).
    giro = Matrix.Rotation(math.radians(-INCLINACION), 3, "X")
    pivote_g = (0, 0, -MARCO[2])
    for b in (bm, bm_piz):
        bmesh.ops.rotate(b, verts=list(b.verts), cent=piezas.g2b(pivote_g), matrix=giro)
    mapear_cara(bm_piz, frente, Vector((1, 0, 0)), giro @ Vector((0, 0, 1)))

    def inclinado(p):
        q = girar_x((p[0], p[1] - pivote_g[1], p[2] - pivote_g[2]), -INCLINACION)
        return (q[0], q[1] + pivote_g[1], q[2] + pivote_g[2])

    # 3) Pata trasera, enganchada detrás del marco a PATA_ALTO.
    enganche = inclinado((0, PATA_ALTO, -MARCO[2] - PATA[1] / 2))
    espalda = (inclinado((0, 0, -MARCO[2] + 0.002)),       # 2 mm metida: sin luz
               girar_x((0, 0, -1), -INCLINACION))
    pata(bm, enganche, 1, plano=espalda)
    # 4) Se centra la huella en Z (origen = centro de la base, guía 2.4).
    zs = [-v.co.y for b in (bm, bm_piz) for v in b.verts]
    dz = -(max(zs) + min(zs)) / 2
    for b in (bm, bm_piz):
        bmesh.ops.translate(b, vec=piezas.g2b((0, 0, dz)), verts=b.verts)
    for f in bm.faces:          # el cuerpo es todo madera
        f.material_index = 0
    cuerpo = piezas.terminar(f"{ID}_cuerpo", bm, [m_madera], sombreado="duro")
    pizarra = piezas.terminar("pieza_pizarra", bm_piz, [m_pizarra], sombreado="duro")
    # Colisión: el marco inclinado (la pata no hace falta).
    c = inclinado((0, MARCO[1] / 2, -MARCO[2] / 2))
    col = piezas.colision_caja(ID, MARCO, (c[0], c[1], c[2] + dz), rot=(-INCLINACION, 0, 0))
    raiz = piezas.raiz(ID, [cuerpo, pizarra, col])
    return raiz, cuerpo, pizarra, col


def hoja_revision(piezas_vis, revision):
    import pan_pancho
    comun.preparar_revision()
    pan = pan_pancho.construir("ref_pan")
    pan.location = piezas.g2b((0.28, pan_pancho.MEDIO_ALTO, 0.05))
    solo, con_pan = list(piezas_vis), list(piezas_vis) + [pan]
    cuadros = comun.sacar_fotos([
        ("Frente (cliente, +Z) · día", solo, "frente", "dia", True),
        ("Costado: inclinada 12°, con la pata atrás · día", solo, "costado", "dia", True),
        ("3/4 · día", solo, "tres_cuartos", "dia", False),
        ("Escala: al lado de un pan de pancho · día", con_pan, "tres_cuartos", "dia", False),
        ("3/4 · atardecer", solo, "tres_cuartos", "atardecer", False),
    ])
    comun.componer_hoja(
        f"{ID} · 0,36 × 0,434 × 0,234 m (con la pata) · accesorio, pizarra en blanco",
        cuadros, revision, comun.RAIZ / f"docs/arte/revisiones/{ID}.jpg",
    )


def main():
    comun.escena_vacia()
    raiz, cuerpo, pizarra, col = construir()
    bpy.context.view_layer.update()
    revision = comun.revisar([cuerpo, pizarra], PRESUPUESTO, MEDIDAS, origen="base")
    ok = comun.imprimir_revision(ID, revision)
    comun.guardar_blend(comun.RAIZ / f"arte/fuentes/{FAMILIA}/{ID}.blend")
    # Con UV: la cara de adelante de pieza_pizarra queda lista para que el juego escriba.
    comun.exportar_glb([raiz, cuerpo, pizarra, col],
                       comun.RAIZ / f"godot/modelos/{FAMILIA}/{ID}.glb", uvs=True)
    if "--sin-hoja" not in sys.argv:
        hoja_revision([cuerpo, pizarra], revision)
    if not ok:
        sys.exit(1)

if __name__ == "__main__":
    main()
