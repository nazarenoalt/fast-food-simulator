"""Piezas, chequeos y fotos compartidos por los equipos y el stock de la etapa 4.

Lo usan: plancha, parrilla_carbon, carbon_brasa, tostador, heladera, garrafa, espatula,
pinza, tabla_picar, caja_medallones_12, bolsa_panes_hamburguesa_6, bandeja_chorizos_6,
bolsa_panes_frances_6 y bolsa_carbon. Complementa a comun.py, piezas.py y _etapa2.py (que no
se tocan). Todo en ejes de Godot (X derecha, Y arriba, Z hacia el cliente), como piezas.py.

Equipos de mostrador: mismo criterio que `hervidor_chico` (acero, perillas y mangos negros,
controles y `pieza_piloto` del lado del vendedor = −Z de Godot, biseles de 4–6 mm). La
perilla y la luz piloto son las mismas del hervidor (copiadas acá para no tocar ese script).
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
import piezas  # noqa: E402
import _etapa2 as e2  # noqa: E402
from piezas import g2b  # noqa: E402

objeto_en = e2.objeto_en
verts_godot = e2.verts_godot
limites_godot = e2.limites_godot
borrar_caras = e2.borrar_caras

# Vista extra para las fotos (sin tocar _etapa2.py): de frente al lado del vendedor, un poco
# de costado y desde arriba (para ver adentro de la heladera con la puerta abierta).
e2.DIRECCIONES.setdefault("vendedor_frente", (Vector((0.35, 1.0, 0.55)), False))

LARGO_PERILLA = 0.018
SALE_PERILLA = 0.004 + LARGO_PERILLA + 0.008   # cuánto sale la perilla desde la cara (0,030)


# ── Piezas de los equipos ──────────────────────────────────────────────

def perilla(bm, x, y, z_cara, mat_negro):
    """Perilla negra del hervidor, en la cara del vendedor (z_cara), saliendo hacia −Z:
    base, cuerpo un poco cónico y una aleta para agarrarla. Sale SALE_PERILLA."""
    piezas.cilindro(bm, 0.022, 0.004, (x, y, z_cara - 0.002), eje="z", lados=12, mat=mat_negro,
                    tapas=(True, False))
    piezas.cilindro(bm, 0.016, LARGO_PERILLA, (x, y, z_cara - 0.004 - LARGO_PERILLA / 2),
                    eje="z", lados=12, mat=mat_negro, radio_arriba=0.019, tapas=(True, False))
    piezas.caja(bm, (0.008, 0.036, 0.012), (x, y, z_cara - 0.004 - LARGO_PERILLA - 0.002),
                mat=mat_negro, bisel=0.002)


def aro_piloto(bm, x, y, z_cara, mat_acero):
    """Aro de acero de la luz piloto (la lente va aparte, `pieza_piloto`)."""
    piezas.cilindro(bm, 0.013, 0.006, (x, y, z_cara - 0.003), eje="z", lados=12, mat=mat_acero,
                    tapas=(True, False))


def lente_piloto(x, y, z_cara, material, nombre="pieza_piloto"):
    """Lente de la luz piloto (media esfera achatada que asoma del aro), objeto aparte con
    M_PilotoApagado: el juego la enciende. Origen en el centro de la lente."""
    bm = bmesh.new()
    zl = z_cara - 0.006
    caras = piezas.esfera(bm, 0.009, (0, 0, 0), lados=12, escala=(1, 1, 0.6))
    borrar = [f for f in caras if all(v.co.y < 1e-6 for v in f.verts)]  # mitad de atrás
    bmesh.ops.delete(bm, geom=borrar, context="FACES")
    abiertos = [e for e in bm.edges if len(e.link_faces) == 1]
    bmesh.ops.edgeloop_fill(bm, edges=abiertos)
    for f in bm.faces:
        f.material_index = 0
    piezas.mover(bm, list(bm.faces), (x, y, zl))
    return objeto_en(nombre, bm, [material], (x, y, zl))


def inclinar_arriba(caras, y_desde, z_alto, z_bajo, baja):
    """Baja los vértices de arriba (y > y_desde) de unas caras recién hechas, en rampa: en
    z_alto no bajan nada y en z_bajo bajan `baja` (costados de la plancha, en cuña)."""
    vs = {v for f in caras if f.is_valid for v in f.verts}
    for v in vs:
        if v.co.z > y_desde:              # Blender Z = Godot Y
            zg = -v.co.y                   # Godot Z
            t = (z_alto - zg) / (z_alto - z_bajo)
            v.co.z -= baja * max(0.0, min(1.0, t))


def colision_cajas(nombre, cajas, padre=None):
    """Objeto `<nombre>-colonly` con varias cajas [(medidas, centro)] (guía 6.1).
    padre = objeto del que cuelga (la colisión de una pieza que se mueve va como hija de su
    `pieza_`, guía v1.5); las cajas se dan igual en ejes del modelo."""
    bm = bmesh.new()
    for c in cajas:
        piezas.caja(bm, c[0], c[1], rot=c[2] if len(c) > 2 else (0, 0, 0))
    malla = bpy.data.meshes.new(f"{nombre}-colonly")
    bm.to_mesh(malla)
    bm.free()
    obj = bpy.data.objects.new(f"{nombre}-colonly", malla)
    bpy.context.scene.collection.objects.link(obj)
    obj.display_type = "WIRE"
    obj.hide_render = True
    if padre is not None:
        obj.parent = padre
        obj.matrix_parent_inverse = padre.matrix_world.inverted()
    return obj


def reemplazar(res, prefijo, nuevo):
    return [nuevo if texto.startswith(prefijo) else (ok, texto) for ok, texto in res]


def caras_material(obj, indice):
    """Vértices (Godot) de las caras de un material."""
    m = obj.matrix_world
    vs = []
    for p in obj.data.polygons:
        if p.material_index == indice:
            for i in p.vertices:
                c = m @ obj.data.vertices[i].co
                vs.append(Vector((c.x, c.z, -c.y)))
    return vs


def chequeo_superficie(obj, indice, medidas, alto, punto, tol=1e-4):
    """La superficie de trabajo (las caras de arriba del material `indice`) mide `medidas`
    (X, Z) a la altura `alto`, centrada en el origen, y `punto` está en su centro."""
    vs = [v for v in caras_material(obj, indice) if abs(v.y - alto) < 1e-5]
    if not vs:
        return False, "Superficie de trabajo: no se encontró a %.3f m" % alto
    ancho = max(v.x for v in vs) - min(v.x for v in vs)
    prof = max(v.z for v in vs) - min(v.z for v in vs)
    cx = (max(v.x for v in vs) + min(v.x for v in vs)) / 2
    cz = (max(v.z for v in vs) + min(v.z for v in vs)) / 2
    pg = Vector((punto.location.x, punto.location.z, -punto.location.y))
    ok = (abs(ancho - medidas[0]) < tol and abs(prof - medidas[1]) < tol and abs(cx) < tol
          and abs(cz) < tol and (pg - Vector((0, alto, 0))).length < tol)
    return ok, ("Superficie de trabajo %.3f × %.3f m a %.3f m del apoyo, centrada; %s en su centro"
                % (ancho, prof, alto, punto.name))


def chequeo_base(objetos, texto):
    """Apoya en y = 0 (para el chequeo de origen propio de los equipos no simétricos)."""
    mn, _ = limites_godot(objetos)
    return abs(mn.y) < 1e-4, texto


# ── Fotos ──────────────────────────────────────────────────────────────

def hoja_equipo(id_, titulo, raiz, visibles, revision, ancla=(-0.4, 0.95, 0.0),
                etiqueta_vendedor="Lado del vendedor: perillas y piloto · día",
                etiqueta_arriba="Arriba: superficie de trabajo · día", extras=(), en_barra=None,
                vista_barra="vendedor_alto", margen_barra=2.2, etiqueta_barra=None):
    """Hoja de los equipos: frente, vendedor, arriba, 3/4 de día y de atardecer, y sobre la
    barra chica (en `ancla`, un anclaje de barra_chica.ron)."""
    comun.preparar_revision()
    cuadros = e2.sacar_fotos([
        ("Frente (lo que ve el cliente) · día", visibles, "frente", "dia"),
        (etiqueta_vendedor, visibles, "vendedor", "dia"),
        (etiqueta_arriba, visibles, "arriba", "dia"),
        ("3/4 · día", visibles, "tres_cuartos", "dia"),
        ("3/4 · atardecer", visibles, "tres_cuartos", "atardecer"),
    ])
    barra = e2.barra_chica()
    raiz.location = g2b(ancla)
    for o in extras:
        o.location += g2b(ancla)
    bpy.context.view_layer.update()
    cuadros += e2.sacar_fotos([
        (etiqueta_barra or "Sobre la barra chica (%s) · día" % "mostrador_izq",
         visibles + list(extras) + barra, vista_barra, "dia", en_barra or visibles, margen_barra),
    ])
    comun.componer_hoja(titulo, cuadros, revision, comun.RAIZ / f"docs/arte/revisiones/{id_}.jpg")


# ── Referencias de comida para las hojas del stock (no se exportan) ────
# Formas simples con los colores de la paleta, solo para ver cómo entran las unidades: los
# modelos de comida de la etapa 4 los hace otra tanda.

def _mat_ref(nombre_paleta):
    p = comun.paleta()[nombre_paleta]
    return comun.crear_material(f"ref_{nombre_paleta}", p["hex"], rugosidad=p.get("rugosidad", 0.7))


def ref_medallon(nombre):
    bm = bmesh.new()
    e2.torno(bm, [(0.0, 0.0), (0.05, 0.0), (0.055, 0.004), (0.055, 0.008), (0.05, 0.012), (0.0, 0.012)],
             16, centro=(0, -0.006, 0))
    return objeto_en(nombre, bm, [_mat_ref("M_CarneCruda")], (0, 0, 0), sombreado="suave")


def ref_pan_hamburguesa(nombre):
    """Pan entero (base + tapa juntas), Ø 0,11 × 0,075, centrado."""
    bm = bmesh.new()
    perfil = [(0.0, 0.0), (0.05, 0.0), (0.055, 0.008), (0.055, 0.03), (0.052, 0.045),
              (0.042, 0.062), (0.024, 0.072), (0.0, 0.075)]
    mats = [1, 0, 0, 0, 0, 0, 0]
    e2.torno(bm, perfil, 16, centro=(0, -0.0375, 0), mats=mats)
    return objeto_en(nombre, bm, [_mat_ref("M_PanCorteza"), _mat_ref("M_PanMiga")], (0, 0, 0),
                     sombreado="suave")


def ref_chorizo(nombre):
    return comun.capsula(nombre, 0.015, 0.14, lados=8, material=_mat_ref("M_CarneCruda"))


def ref_pan_frances(nombre):
    """Pan francés 0,16 × 0,06 × 0,08 (cápsula achatada), centrado."""
    obj = comun.capsula(nombre, 0.04, 0.16, lados=12, material=_mat_ref("M_PanCorteza"))
    obj.scale = (1.0, 1.0, 0.75)
    bpy.context.view_layer.update()
    return obj


def posiciones(grilla, separacion):
    """Lo mismo que DefBloque::posicion_unidad (rust/core/src/deposito.rs), en Godot."""
    cols, filas, capas = grilla
    sx, sy, sz = separacion
    for i in range(cols * filas * capas):
        capa, resto = divmod(i, cols * filas)
        fila, col = divmod(resto, cols)
        yield ((col - (cols - 1) / 2) * sx, capa * sy + sy / 2, ((filas - 1) / 2 - fila) * sz)


def unidades(fabrica, grilla, separacion, prefijo):
    objs = []
    for i, pos in enumerate(posiciones(grilla, separacion)):
        o = fabrica(f"{prefijo}_{i}")
        o.location = g2b(pos)
        objs.append(o)
    return objs


def hoja_stock(id_, titulo, paquete, llena, revision, arriba=True):
    """Hoja del stock: con las unidades de referencia (frente, costado, 3/4, arriba,
    atardecer) y sola (lo que exporta el .glb)."""
    comun.preparar_revision()
    for o in paquete:
        e2.sin_cara_de_atras(o)
    sola = list(paquete)
    pedidos = [
        ("Frente (cliente, +Z) con las unidades · día", llena, "frente", "dia"),
        ("Costado: lado del vendedor a la derecha · día", llena, "costado", "dia"),
        ("3/4 con las unidades · día", llena, "tres_cuartos", "dia"),
    ]
    if arriba:
        pedidos.append(("Arriba · día", llena, "arriba", "dia"))
    pedidos += [
        ("3/4 con las unidades · atardecer", llena, "tres_cuartos", "atardecer"),
        ("Sola (lo que exporta el .glb) · día", sola, "tres_cuartos", "dia"),
    ]
    cuadros = e2.sacar_fotos(pedidos)
    comun.componer_hoja(titulo, cuadros, revision, comun.RAIZ / f"docs/arte/revisiones/{id_}.jpg")


def main_modelo(id_, familia, construir, revisar, hoja, exportar):
    """Esqueleto común de main(): construir, revisar, guardar, exportar y hoja."""
    comun.escena_vacia()
    m = construir()
    revision = revisar(m)
    ok = comun.imprimir_revision(id_, revision)
    comun.guardar_blend(comun.RAIZ / f"arte/fuentes/{familia}/{id_}.blend")
    comun.exportar_glb(exportar(m), comun.RAIZ / f"godot/modelos/{familia}/{id_}.glb")
    if "--sin-hoja" not in sys.argv:
        hoja(m, revision)
    if not ok:
        sys.exit(1)


# ── Utensilios (objetos de mano) ───────────────────────────────────────

def prisma(bm, contorno_xz, y0, y1, mat=0):
    """Prisma vertical (Godot): un contorno en planta [(x, z)] (convexo, sin repetir el primero)
    extruido de y0 a y1. Tapas como polígonos planos."""
    abajo = [bm.verts.new(g2b((x, y0, z))) for x, z in contorno_xz]
    arriba = [bm.verts.new(g2b((x, y1, z))) for x, z in contorno_xz]
    n = len(abajo)
    caras = [bm.faces.new(abajo), bm.faces.new(list(reversed(arriba)))]
    for k in range(n):
        caras.append(bm.faces.new((abajo[k], abajo[(k + 1) % n], arriba[(k + 1) % n], arriba[k])))
    for f in caras:
        f.material_index = mat
    return caras


def centrar(bm):
    """Mueve la malla para que el centro de su caja quede en el origen (objetos de mano,
    guía 2.4: el origen coincide con el centro de la colisión del dato)."""
    mn = Vector(map(min, *(v.co for v in bm.verts)))
    mx = Vector(map(max, *(v.co for v in bm.verts)))
    bmesh.ops.translate(bm, vec=-(mn + mx) / 2, verts=bm.verts)


def hoja_mano(id_, titulo, obj, revision, escena=None):
    """Hoja de un utensilio: frente, costado, arriba, 3/4 de día y de atardecer, y al lado de
    un pan de pancho (escala, guía 8.1). escena(obj) puede devolver (etiqueta, visibles,
    encuadre) para una última foto en uso (sobre la plancha, la parrilla...)."""
    import pan_pancho
    comun.preparar_revision()
    vis = [obj]
    pan = pan_pancho.construir("ref_pan")
    mn, mx = limites_godot([obj])
    obj.location = g2b((0, (mx.y - mn.y) / 2, 0))     # apoyado en el piso de la foto
    pan.location = g2b((0, 0.0225, -(mx.z - mn.z) / 2 - 0.05))
    pedidos = [
        ("Frente · día", vis, "frente", "dia"),
        ("Costado · día", vis, "costado", "dia"),
        ("Arriba · día", vis, "arriba", "dia"),
        ("3/4 · atardecer", vis, "tres_cuartos", "atardecer"),
        ("3/4, al lado de un pan de pancho (escala) · día", vis + [pan], "tres_cuartos", "dia"),
    ]
    cuadros = e2.sacar_fotos(pedidos)
    if escena is not None:
        etiqueta, visibles, encuadre, margen = escena(obj)
        cuadros += e2.sacar_fotos([(etiqueta, visibles, "vendedor_alto", "dia", encuadre, margen)])
    comun.componer_hoja(titulo, cuadros, revision, comun.RAIZ / f"docs/arte/revisiones/{id_}.jpg")


# ── Bolsas de papel (bolsa_panes_frances_6, bolsa_carbon) ──────────────

def seccion_papel(ancho, alto, fuelle, radio=0.012):
    """Sección de bolsa de papel en el plano (a, b): rectángulo de ancho × alto, centrado, con
    las esquinas ochavadas (2 puntos) y un pliegue hacia adentro (el fuelle) en el medio de
    los lados ±a. Arranca en +a y gira hacia +b. 10 puntos."""
    r = min(radio, alto / 2.2, ancho / 4)
    ha, hb = ancho / 2, alto / 2
    return [
        (ha - fuelle, 0.0),
        (ha, hb - r), (ha - r, hb),
        (-ha + r, hb), (-ha, hb - r),
        (-ha + fuelle, 0.0),
        (-ha, -hb + r), (-ha + r, -hb),
        (ha - r, -hb), (ha, -hb + r),
    ]


def loft_papel(bm, estaciones, eje="z", tapas=(True, True)):
    """Bolsa de papel como una serie de secciones a lo largo de `eje` (Godot):
    estaciones = [(t, ancho, alto, centro, fuelle, material)], con ancho en X y alto en el otro
    eje (Y si eje = "z": bolsa acostada; Z si eje = "y": bolsa parada); centro = dónde está el
    medio de la sección en ese eje. El material es el de la banda que arranca en la estación.
    Las puntas se cierran en abanico hacia el centro (el fuelle hace la sección cóncava)."""
    def punto(t, a, b):
        return (a, b, t) if eje == "z" else (a, t, b)
    anillos, centros = [], []
    for t, ancho, alto, c, fuelle, _ in estaciones:
        anillos.append([bm.verts.new(g2b(punto(t, a, c + b))) for a, b in seccion_papel(ancho, alto, fuelle)])
        centros.append(punto(t, 0.0, c))
    caras = []
    n = len(anillos[0])
    for i, (p, q) in enumerate(zip(anillos, anillos[1:])):
        for k in range(n):
            f = bm.faces.new((p[k], p[(k + 1) % n], q[(k + 1) % n], q[k]))
            f.material_index = estaciones[i][5]
            caras.append(f)
    for usar, anillo, centro, est in ((tapas[0], anillos[0], centros[0], estaciones[0]),
                                      (tapas[1], anillos[-1], centros[-1], estaciones[-1])):
        if usar:
            v = bm.verts.new(g2b(centro))
            for k in range(n):
                f = bm.faces.new((anillo[k], anillo[(k + 1) % n], v))
                f.material_index = est[5]
                caras.append(f)
    return caras
