"""Modelo: sombrilla de carrito (id `sombrilla`, para `sombrilla_roja` y `sombrilla_rayada`
de godot/data/accesorios.ron).

Genera:
    arte/fuentes/accesorios/sombrilla.blend
    godot/modelos/accesorios/sombrilla.glb
    docs/arte/revisiones/sombrilla.jpg

Uso:
    blender -b -P tools/blender/modelos/sombrilla.py
    python tools/blender/modelos/sombrilla.py

Forma: base pesada de hierro (cono truncado de 16 lados con un cuello para el caño), caño
de acero inclinado 15° hacia +X, una articulación arriba y un tramo corto vertical que
sostiene el paño horizontal. Paño de 8 gajos: cada gajo es plano entre dos varillas, con
una leve panza hacia arriba a mitad de camino y una caída (faldón) de 7 a 10,5 cm con
festón en el borde. Por debajo: 8 varillas, 8 tensores y la corredera.

Respeta la `forma` de accesorios.ron: base de radio 0,25 (alto 0,08), caño de radio 0,022
del origen a (0,62; 2,32) inclinado 15°, paño de radio 1,35 con el borde a 2,225 m y la
punta a 2,675 m, centrado en x = 0,62 (las varillas llegan a 1,35 del centro). Caja total
2,70 × 2,715 × 2,70 (arriba asoma el remate).

Un solo modelo para las dos sombrillas (guía 4.2, regla 5): el paño es `pieza_pano`, con
dos materiales en dos superficies: superficie 0 = gajos pares (el primero mira a +X) y
superficie 1 = gajos impares. El .glb trae la roja (las dos superficies con M_RojoAcento).
Para la rayada, el juego pone M_BlancoCrema en la superficie 0 y M_AzulAcento en la 1:
gajos blancos y azules alternados. Mismo truco para cualquier color nuevo, sin otro modelo.

Objetos (hijos del Empty `sombrilla`, origen = centro de la base, a nivel del piso, como el
anclaje `sombra`):
- `sombrilla_cuerpo`: base, caño, articulación, varillas (M_Hierro, M_Acero).
- `pieza_pano`: el paño (sin colisión, igual que hoy).
- `sombrilla-colonly`: la base (cilindro) y el caño inclinado.

El chequeo de origen de comun.revisar() mide el centro de la caja total, que está corrida
0,62 m en X por el caño inclinado: se reemplaza por uno propio (la base centrada en el
origen y apoyada en el piso).
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

import comun  # noqa: E402
import piezas  # noqa: E402
from piezas import g2b  # noqa: E402

ID = "sombrilla"
FAMILIA = "accesorios"
PRESUPUESTO = 2000  # accesorios grandes (guía 3.1)

# Datos (accesorios.ron)
BASE_R, BASE_ALTO = 0.25, 0.08
CANO_R, CANO_LARGO, INCLINACION = 0.022, 2.4, math.radians(15)
PANO_X, PANO_R, PANO_BORDE, PANO_PUNTA = 0.62, 1.35, 2.225, 2.675

EJE = Vector((math.sin(INCLINACION), math.cos(INCLINACION), 0))   # dirección del caño (Godot)
TOPE_CANO = EJE * CANO_LARGO                                       # (0,621; 2,318)
GAJOS = 8
POR_GAJO = 4               # 32 cortes alrededor (guía 3.2: más de 1 m → 32 lados)
ESPESOR = 0.012            # paño con dos caras (se ve de abajo) y 1 cm de grosor (guía 2.2)
R_CUBO = 0.045             # agujero del centro del paño (lo tapa el sombrerete)
PANZA = 0.04               # cuánto sube el paño a mitad de la varilla
FALDON, FESTON = 0.07, 0.035
REMATE_TOPE = 2.715

MEDIDAS = (2 * PANO_R, REMATE_TOPE, 2 * PANO_R)


def pos_pano(x, y, z):
    return Vector((PANO_X + x, y, z))


def alto_cono(r):
    return PANO_PUNTA - (PANO_PUNTA - PANO_BORDE) * r / PANO_R


def varilla_pts(g, filas):
    """Puntos (Godot) de la varilla g a las distancias `filas`, con la panza del paño."""
    a = 2 * math.pi * g / GAJOS
    out = []
    for r in filas:
        panza = PANZA * math.sin(math.pi * (r - R_CUBO) / (PANO_R - R_CUBO))
        out.append(pos_pano(r * math.cos(a), alto_cono(r) + panza, r * math.sin(a)))
    return out


FILAS = (R_CUBO, 0.70, PANO_R)


# ── Piezas propias ─────────────────────────────────────────────────────

def varilla(bm, p0, p1, radio, lados=8, mat=0, tapas=(True, True)):
    """Cilindro entre dos puntos de Godot (caños, varillas, tensores)."""
    a, b = g2b(p0), g2b(p1)
    eje = (b - a).normalized()
    u = eje.orthogonal().normalized()
    v = eje.cross(u)
    anillos = []
    for c in (a, b):
        anillos.append([bm.verts.new(c + radio * (math.cos(t) * u + math.sin(t) * v))
                        for t in (2 * math.pi * (k + 0.5) / lados for k in range(lados))])
    caras = [bm.faces.new((anillos[0][k], anillos[0][(k + 1) % lados], anillos[1][(k + 1) % lados], anillos[1][k]))
             for k in range(lados)]
    if tapas[0]:
        caras.append(bm.faces.new(list(reversed(anillos[0]))))
    if tapas[1]:
        caras.append(bm.faces.new(anillos[1]))
    for f in caras:
        f.material_index = mat
    return caras


def pano(bm):
    """Paño cerrado (arriba, faldón con festón y abajo), 32 cortes alrededor."""
    cortes = []
    for j in range(GAJOS * POR_GAJO):
        g, u = divmod(j, POR_GAJO)
        u /= POR_GAJO
        va, vb = varilla_pts(g, FILAS), varilla_pts((g + 1) % GAJOS, FILAS)
        arriba = [pa.lerp(pb, u) for pa, pb in zip(va, vb)]
        # El gajo es plano entre varillas; en el medio cede un poco (tela tensada).
        arriba[1].y -= 0.02 * 4 * u * (1 - u)
        borde = arriba[2]
        adentro = pos_pano(0, 0, 0)
        hacia_adentro = Vector((adentro.x - borde.x, 0, adentro.z - borde.z)).normalized() * 0.01
        caida = FALDON + FESTON * math.sin(math.pi * u)
        perfil = [
            arriba[0], arriba[1], borde,
            borde - Vector((0, caida, 0)),
            borde + hacia_adentro - Vector((0, caida, 0)),
            borde + hacia_adentro - Vector((0, ESPESOR, 0)),
            arriba[1] - Vector((0, ESPESOR, 0)),
            arriba[0] - Vector((0, ESPESOR, 0)),
        ]
        cortes.append(([bm.verts.new(g2b(p)) for p in perfil], g % 2))
    n = len(cortes)
    m = len(cortes[0][0])
    for j in range(n):
        (c1, gajo), (c2, _) = cortes[j], cortes[(j + 1) % n]
        for k in range(m):
            f = bm.faces.new((c1[k], c2[k], c2[(k + 1) % m], c1[(k + 1) % m]))
            f.material_index = gajo


def construir():
    hierro, acero, rojo = comun.cargar_materiales("M_Hierro", "M_Acero", "M_RojoAcento")
    bm = bmesh.new()
    # Base: cono truncado bajo + tapa en pendiente + cuello inclinado para el caño.
    piezas.cilindro(bm, BASE_R, 0.06, (0, 0.03, 0), lados=16, mat=0, radio_arriba=0.23, tapas=(False, False))
    piezas.cilindro(bm, 0.23, BASE_ALTO - 0.06, (0, 0.06 + (BASE_ALTO - 0.06) / 2, 0), lados=16, mat=0,
                    radio_arriba=0.07, tapas=(False, True))
    varilla(bm, EJE * 0.03, EJE * 0.17, 0.036, lados=12, mat=0)
    # Caño (arranca adentro del cuello: no asoma por debajo del piso).
    varilla(bm, EJE * 0.05, TOPE_CANO, CANO_R, lados=12, mat=1)
    # Articulación: un perno horizontal (eje Z) en la punta del caño.
    varilla(bm, TOPE_CANO + Vector((0, 0, -0.035)), TOPE_CANO + Vector((0, 0, 0.035)), 0.03, lados=12, mat=0)
    # Tramo vertical hasta el sombrerete, corredera y sombrerete con remate.
    centro = pos_pano(0, 0, 0)
    varilla(bm, Vector((PANO_X, TOPE_CANO.y, 0)), Vector((PANO_X, PANO_PUNTA - 0.02, 0)), 0.018, lados=12, mat=1,
            tapas=(False, False))
    corredera_y = 2.40
    varilla(bm, Vector((PANO_X, corredera_y - 0.03, 0)), Vector((PANO_X, corredera_y + 0.03, 0)), 0.03,
            lados=12, mat=0)
    varilla(bm, Vector((PANO_X, PANO_PUNTA - 0.03, 0)), Vector((PANO_X, PANO_PUNTA + 0.01, 0)), 0.06,
            lados=16, mat=0)
    piezas.cilindro(bm, 0.03, REMATE_TOPE - PANO_PUNTA - 0.01, (PANO_X, (PANO_PUNTA + 0.01 + REMATE_TOPE) / 2, 0),
                    lados=12, mat=0, radio_arriba=0.012, tapas=(False, True))
    # Varillas (debajo del paño) y tensores desde la corredera.
    for g in range(GAJOS):
        hub, medio, borde = varilla_pts(g, FILAS)
        baja = Vector((0, ESPESOR + 0.007, 0))
        varilla(bm, hub - baja, medio - baja, 0.006, mat=1, tapas=(True, False))
        punta = medio.lerp(borde, 0.995) - baja   # no asoma del borde del paño
        varilla(bm, medio - baja, punta, 0.006, mat=1, tapas=(False, True))
        varilla(bm, Vector((PANO_X, corredera_y, 0)) + (medio - centro).normalized() * 0.03,
                hub.lerp(medio, 0.75) - baja, 0.005, mat=1)
    cuerpo = piezas.terminar(f"{ID}_cuerpo", bm, [hierro, acero])

    bm = bmesh.new()
    pano(bm)
    tela = piezas.terminar("pieza_pano", bm, [rojo, rojo])

    # Colisión: base y caño (como la forma del dato).
    bm = bmesh.new()
    piezas.cilindro(bm, BASE_R, BASE_ALTO, (0, BASE_ALTO / 2, 0), lados=16)
    varilla(bm, EJE * 0.05, TOPE_CANO, CANO_R, lados=8)
    malla = bpy.data.meshes.new(f"{ID}-colonly")
    bm.to_mesh(malla)
    bm.free()
    col = bpy.data.objects.new(f"{ID}-colonly", malla)
    bpy.context.scene.collection.objects.link(col)
    col.display_type = "WIRE"
    col.hide_render = True

    raiz = piezas.raiz(ID, [cuerpo, tela, col])
    return raiz, cuerpo, tela, col


# ── Chequeos propios ───────────────────────────────────────────────────

def _verts_godot(obj):
    m = obj.matrix_world
    return [Vector(((m @ v.co).x, (m @ v.co).z, -(m @ v.co).y)) for v in obj.data.vertices]


def chequeo_origen(cuerpo):
    base = [v for v in _verts_godot(cuerpo) if v.y < 0.001]
    cx = (max(v.x for v in base) + min(v.x for v in base)) / 2
    cz = (max(v.z for v in base) + min(v.z for v in base)) / 2
    ancho = max(v.x for v in base) - min(v.x for v in base)
    piso = min(v.y for v in _verts_godot(cuerpo))
    ok = abs(cx) < 1e-3 and abs(cz) < 1e-3 and abs(piso) < 1e-4 and abs(ancho - 2 * BASE_R) < 0.012
    return ok, "Origen en el centro de la base (Ø %.2f), a nivel del piso (el paño va corrido 0,62 en X)" % ancho


def chequeo_pano(tela):
    vs = _verts_godot(tela)
    cx = (max(v.x for v in vs) + min(v.x for v in vs)) / 2
    punta = max(v.y for v in vs)
    ok = abs(cx - PANO_X) < 1e-3 and abs(punta - (PANO_PUNTA - (PANO_PUNTA - PANO_BORDE) * R_CUBO / PANO_R)) < 1e-3
    return ok, "pieza_pano centrada en x = %.2f, radio %.2f, borde a %.3f (dato 0,62 / 1,35 / 2,225)" % (
        cx, (max(v.x for v in vs) - min(v.x for v in vs)) / 2,
        max(v.y for v in vs if abs(math.hypot(v.x - PANO_X, v.z) - PANO_R) < 1e-3))


def revisar(cuerpo, tela):
    res = comun.revisar([cuerpo, tela], PRESUPUESTO, MEDIDAS, origen="base")
    res = [chequeo_origen(cuerpo) if t.startswith("Origen") else (ok, t) for ok, t in res]
    res.insert(1, chequeo_pano(tela))
    return res


# ── Hoja de revisión ───────────────────────────────────────────────────

def _vista_desde_abajo():
    """Vista extra para la hoja (sin tocar comun.py): parado debajo de la sombrilla,
    mirando hacia arriba, para ver varillas y tensores."""
    original = comun.encuadrar

    def encuadrar(objetos, vista, margen=1.25, de_cerca=False):
        if vista != "desde_abajo":
            return original(objetos, vista, margen, de_cerca)
        original(objetos, "tres_cuartos", margen, de_cerca)
        cam = bpy.context.scene.camera
        cam.data.lens = 18
        cam.location = g2b((PANO_X - 1.1, 1.5, 1.0))
        mira = g2b((PANO_X + 0.2, 2.3, -0.2))
        cam.rotation_euler = (mira - cam.location).to_track_quat("-Z", "Y").to_euler()

    comun.encuadrar = encuadrar


def hoja_revision(cuerpo, tela, revision):
    comun.preparar_revision()
    persona = bpy.data.objects["ref_persona_1,75m"]
    persona.location = g2b((-0.7, 0, 0.6))
    blanco, azul = comun.cargar_materiales("M_BlancoCrema", "M_AzulAcento")
    rayada = tela.copy()
    rayada.data = tela.data.copy()
    rayada.data.materials[0] = blanco
    rayada.data.materials[1] = azul
    bpy.context.scene.collection.objects.link(rayada)
    roja = [cuerpo, tela]
    raya = [cuerpo, rayada]
    cuadros = comun.sacar_fotos([
        ("Frente, con la persona de 1,75 m · día", roja + [persona], "frente", "dia", True),
        ("Costado · día", roja, "costado", "dia", True),
        ("Roja (el .glb) · 3/4 · día", roja, "tres_cuartos", "dia", False),
        ("Rayada (superficie 0 blanca, 1 azul) · 3/4 · día", raya, "tres_cuartos", "dia", False),
        ("Desde abajo: varillas y tensores · día", raya, "desde_abajo", "dia", False),
        ("Rayada · 3/4 · atardecer", raya, "tres_cuartos", "atardecer", False),
    ])
    comun.componer_hoja(
        "sombrilla · Ø 2,7 × 2,72 m · accesorio grande (roja y rayada)",
        cuadros, revision, comun.RAIZ / f"docs/arte/revisiones/{ID}.jpg",
    )


def main():
    comun.escena_vacia()
    raiz, cuerpo, tela, col = construir()
    revision = revisar(cuerpo, tela)
    ok = comun.imprimir_revision(ID, revision)
    comun.guardar_blend(comun.RAIZ / f"arte/fuentes/{FAMILIA}/{ID}.blend")
    comun.exportar_glb([raiz, cuerpo, tela, col], comun.RAIZ / f"godot/modelos/{FAMILIA}/{ID}.glb")
    if "--sin-hoja" not in sys.argv:
        _vista_desde_abajo()
        hoja_revision(cuerpo, tela, revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
