"""Modelo: carpa 2 × 2 (id `carpa_2x2`, godot/data/accesorios.ron).

Genera:
    arte/fuentes/accesorios/carpa_2x2.blend
    godot/modelos/accesorios/carpa_2x2.glb
    docs/arte/revisiones/carpa_2x2.jpg

Uso:
    blender -b -P tools/blender/modelos/carpa_2x2.py
    python tools/blender/modelos/carpa_2x2.py

Forma: carpa plegable de feria. 4 patas telescópicas de acero (tramo de abajo más grueso,
traba negra a mitad de altura, pie negro), tijeras en X entre las patas justo debajo del
techo, escuadras negras en las esquinas, y techo de lona a dos aguas bajo (cumbrera a lo
largo de X, 17°) con faldón festoneado de 14 a 18 cm alrededor. Por dentro: cumbrera y
cuatro cabios de acero que sostienen la lona. La lona tiene dos caras y 1,2 cm de grosor
(se ve desde abajo, guía 2.2).

Respeta la `forma` de accesorios.ron: patas de radio 0,025 y 2,3 m de alto en (±1,1; ±0,9),
huella del techo 2,3 × 1,9 con el borde (alero) a 2,30 m. Diferencia: el dato es una losa
plana de 2,30 a 2,36; acá el techo es a dos aguas y la cumbrera llega a 2,60 m, así que la
caja total es 2,3 × 2,60 × 1,9 (en la lista figura 2,36 de alto).

Objetos (hijos del Empty `carpa_2x2`, origen = centro de la base, a nivel del piso, como el
anclaje `techo`):
- `carpa_2x2_cuerpo`: patas y armazón (M_Acero, M_PlasticoNegro).
- `carpa_2x2_lona`: techo y faldón (M_Lona), sin colisión (como hoy, colision: false).
- `carpa_2x2-colonly`: las 4 patas (cilindros del dato).
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

ID = "carpa_2x2"
FAMILIA = "accesorios"
PRESUPUESTO = 2000  # accesorios grandes (guía 3.1)

# Datos (accesorios.ron)
PATA_X, PATA_Z, PATA_R, PATA_ALTO = 1.1, 0.9, 0.025, 2.3
TECHO_X, TECHO_Z = 1.15, 0.95     # media huella del techo (2,3 × 1,9)
ALERO = 2.30
CUMBRERA = 2.60
ESPESOR = 0.012
FALDON_ALTO, FALDON_FESTON = 0.14, 0.04
FESTONES_X, FESTONES_Z = 6, 5      # festones por lado (frente/atrás y costados)
POR_FESTON = 4
TIJERA_ABAJO, TIJERA_ARRIBA = 2.03, 2.27
MEDIDAS = (2 * TECHO_X, CUMBRERA, 2 * TECHO_Z)


def varilla(bm, p0, p1, radio, lados=8, mat=0, tapas=(True, True)):
    """Cilindro entre dos puntos de Godot."""
    a, b = g2b(p0), g2b(p1)
    eje = (b - a).normalized()
    u = eje.orthogonal().normalized()
    v = eje.cross(u)
    anillos = [[bm.verts.new(c + radio * (math.cos(t) * u + math.sin(t) * v))
                for t in (2 * math.pi * (k + 0.5) / lados for k in range(lados))] for c in (a, b)]
    caras = [bm.faces.new((anillos[0][k], anillos[0][(k + 1) % lados], anillos[1][(k + 1) % lados], anillos[1][k]))
             for k in range(lados)]
    if tapas[0]:
        caras.append(bm.faces.new(list(reversed(anillos[0]))))
    if tapas[1]:
        caras.append(bm.faces.new(anillos[1]))
    for f in caras:
        f.material_index = mat
    return caras


# ── Lona ───────────────────────────────────────────────────────────────

def perimetro(mx, mz):
    """Puntos del borde del techo (x, z, fase del festón 0..1), dando la vuelta desde la
    esquina (+x, +z) por el frente hacia −x. Cada lado empieza en su esquina."""
    lados = [((mx, mz), (-mx, mz), FESTONES_X), ((-mx, mz), (-mx, -mz), FESTONES_Z),
             ((-mx, -mz), (mx, -mz), FESTONES_X), ((mx, -mz), (mx, mz), FESTONES_Z)]
    pts, cortes = [], []
    for (x0, z0), (x1, z1), n in lados:
        cortes.append(len(pts))
        pasos = n * POR_FESTON
        for i in range(pasos):
            t = i / pasos
            fase = (i % POR_FESTON) / POR_FESTON
            pts.append((x0 + (x1 - x0) * t, z0 + (z1 - z0) * t, fase))
    return pts, cortes


def lona(bm):
    afuera, cortes = perimetro(TECHO_X, TECHO_Z)
    adentro, _ = perimetro(TECHO_X - ESPESOR, TECHO_Z - ESPESOR)
    n = len(afuera)
    pendiente = (CUMBRERA - ALERO) / TECHO_Z
    baja_cumbrera = ESPESOR * math.sqrt(1 + pendiente ** 2)

    def caida(fase):
        return FALDON_ALTO + FALDON_FESTON * math.sin(math.pi * fase)

    # Alero (arriba del faldón) y borde de abajo, afuera y adentro.
    ea = [bm.verts.new(g2b((x, ALERO, z))) for x, z, _ in afuera]
    va = [bm.verts.new(g2b((x, ALERO - caida(f), z))) for x, z, f in afuera]
    vi = [bm.verts.new(g2b((x, ALERO - caida(f), z))) for x, z, f in adentro]
    ei = [bm.verts.new(g2b((x, ALERO - ESPESOR, z))) for x, z, _ in adentro]
    for k in range(n):
        k2 = (k + 1) % n
        bm.faces.new((ea[k], ea[k2], va[k2], va[k]))     # faldón de afuera
        bm.faces.new((va[k], va[k2], vi[k2], vi[k]))     # borde de abajo
        bm.faces.new((vi[k], vi[k2], ei[k2], ei[k]))     # faldón de adentro
    # Techo: dos faldones inclinados y dos hastiales (triángulos), afuera y adentro.
    for borde, ext in ((ea, False), (ei, True)):
        mx = TECHO_X - (ESPESOR if ext else 0)
        yc = CUMBRERA - (baja_cumbrera if ext else 0)
        c_pos = bm.verts.new(g2b((mx, yc, 0)))
        c_neg = bm.verts.new(g2b((-mx, yc, 0)))
        frente = borde[cortes[0]:cortes[1] + 1]           # de (+x,+z) a (−x,+z)
        costado_neg = borde[cortes[1]:cortes[2] + 1]      # de (−x,+z) a (−x,−z)
        atras = borde[cortes[2]:cortes[3] + 1]            # de (−x,−z) a (+x,−z)
        costado_pos = borde[cortes[3]:] + [borde[0]]      # de (+x,−z) a (+x,+z)
        mitad = len(costado_neg) // 2                     # el punto del medio queda bajo la cumbrera
        caras = [
            frente + [c_neg, c_pos],
            atras + [c_pos, c_neg],
            costado_neg[:mitad + 1] + [c_neg],
            costado_neg[mitad:] + [c_neg],
            costado_pos[:mitad + 1] + [c_pos],
            costado_pos[mitad:] + [c_pos],
        ]
        for vs in caras:
            bm.faces.new(list(reversed(vs)) if ext else vs)


# ── Modelo ─────────────────────────────────────────────────────────────

def construir():
    acero, negro, lona_mat = comun.cargar_materiales("M_Acero", "M_PlasticoNegro", "M_Lona")
    bm = bmesh.new()
    esquinas = [(sx * PATA_X, sz * PATA_Z) for sx in (-1, 1) for sz in (-1, 1)]
    for x, z in esquinas:
        piezas.caja(bm, (0.09, 0.012, 0.09), (x, 0.006, z), mat=1, bisel=0.004, sin_abajo=True)   # pie
        varilla(bm, (x, 0.012, z), (x, 1.25, z), PATA_R, lados=12, tapas=(False, False))
        piezas.cilindro(bm, 0.031, 0.06, (x, 1.25, z), lados=12, mat=1)                          # traba
        varilla(bm, (x, 1.25, z), (x, PATA_ALTO - 0.03, z), 0.02, lados=12, tapas=(False, False))
        piezas.caja(bm, (0.06, 0.07, 0.06), (x, PATA_ALTO - 0.035, z), mat=1, bisel=0.006)        # escuadra
    # Tijeras en X entre patas, y el caño de arriba que hace de alero.
    lados = [((-PATA_X, PATA_Z), (PATA_X, PATA_Z), 3), ((-PATA_X, -PATA_Z), (PATA_X, -PATA_Z), 3),
             ((PATA_X, -PATA_Z), (PATA_X, PATA_Z), 2), ((-PATA_X, -PATA_Z), (-PATA_X, PATA_Z), 2)]
    for (x0, z0), (x1, z1), n in lados:
        a, b = Vector((x0, 0, z0)), Vector((x1, 0, z1))
        d = (b - a).normalized()
        a, b = a + d * 0.03, b - d * 0.03
        for i in range(n):
            p, q = a.lerp(b, i / n), a.lerp(b, (i + 1) / n)
            varilla(bm, (p.x, TIJERA_ABAJO, p.z), (q.x, TIJERA_ARRIBA, q.z), 0.009, lados=6, tapas=(False, False))
            varilla(bm, (p.x, TIJERA_ARRIBA, p.z), (q.x, TIJERA_ABAJO, q.z), 0.009, lados=6, tapas=(False, False))
        varilla(bm, (a.x, TIJERA_ARRIBA + 0.012, a.z), (b.x, TIJERA_ARRIBA + 0.012, b.z), 0.012, tapas=(False, False))
    # Cumbrera y cabios (debajo de la lona).
    yc = CUMBRERA - 0.045
    varilla(bm, (-PATA_X, yc, 0), (PATA_X, yc, 0), 0.012, tapas=(True, True))
    for x, z in esquinas:
        varilla(bm, (x, PATA_ALTO - 0.03, z * 0.97), (x, yc, 0), 0.011, tapas=(False, False))
    cuerpo = piezas.terminar(f"{ID}_cuerpo", bm, [acero, negro])

    bm = bmesh.new()
    lona(bm)
    techo = piezas.terminar(f"{ID}_lona", bm, [lona_mat], sombreado="duro")

    # Colisión: las 4 patas del dato.
    bm = bmesh.new()
    for x, z in esquinas:
        piezas.cilindro(bm, PATA_R, PATA_ALTO, (x, PATA_ALTO / 2, z), lados=8)
    malla = bpy.data.meshes.new(f"{ID}-colonly")
    bm.to_mesh(malla)
    bm.free()
    col = bpy.data.objects.new(f"{ID}-colonly", malla)
    bpy.context.scene.collection.objects.link(col)
    col.display_type = "WIRE"
    col.hide_render = True

    raiz = piezas.raiz(ID, [cuerpo, techo, col])
    return raiz, cuerpo, techo, col


# ── Hoja de revisión ───────────────────────────────────────────────────

def _vista_desde_abajo():
    """Vista extra (sin tocar comun.py): desde adentro, a la altura de los ojos (1,65 m),
    del lado del vendedor, mirando hacia arriba y al frente."""
    original = comun.encuadrar

    def encuadrar(objetos, vista, margen=1.25, de_cerca=False):
        if vista != "desde_abajo":
            return original(objetos, vista, margen, de_cerca)
        original(objetos, "tres_cuartos", margen, de_cerca)
        cam = bpy.context.scene.camera
        cam.data.lens = 16
        cam.location = g2b((-0.6, 1.65, -0.7))
        mira = g2b((0.4, 2.3, 0.6))
        cam.rotation_euler = (mira - cam.location).to_track_quat("-Z", "Y").to_euler()

    comun.encuadrar = encuadrar


def hoja_revision(cuerpo, techo, revision):
    comun.preparar_revision()
    persona = bpy.data.objects["ref_persona_1,75m"]
    persona.location = g2b((0.4, 0, -0.5))
    mostrador = bpy.data.objects["ref_mostrador_0,95m"]
    todo = [cuerpo, techo]
    cuadros = comun.sacar_fotos([
        ("Frente, con la persona de 1,75 m · día", todo + [persona], "frente", "dia", True),
        ("Costado (hastial) · día", todo, "costado", "dia", True),
        ("3/4 · día", todo, "tres_cuartos", "dia", False),
        ("Desde adentro, a la altura de los ojos · día", todo, "desde_abajo", "dia", False),
        ("3/4 · atardecer", todo, "tres_cuartos", "atardecer", False),
    ])
    # Última: sobre el mostrador de referencia (anclaje `techo` de barra_chica: z = −0,1).
    cuerpo.parent.location = mostrador.location + g2b((0, 0, -0.1))
    persona.location = mostrador.location + g2b((0.3, 0, -0.65))   # el vendedor, atrás del carrito
    cuadros += comun.sacar_fotos([
        ("Sobre la barra chica (anclaje techo) · día", todo + [mostrador, persona], "tres_cuartos", "dia", False),
    ])
    comun.componer_hoja(
        "carpa_2x2 · 2,3 × 2,60 × 1,9 m · accesorio grande",
        cuadros, revision, comun.RAIZ / f"docs/arte/revisiones/{ID}.jpg",
    )


def main():
    comun.escena_vacia()
    raiz, cuerpo, techo, col = construir()
    revision = comun.revisar([cuerpo, techo], PRESUPUESTO, MEDIDAS, origen="base")
    ok = comun.imprimir_revision(ID, revision)
    comun.guardar_blend(comun.RAIZ / f"arte/fuentes/{FAMILIA}/{ID}.blend")
    comun.exportar_glb([raiz, cuerpo, techo, col], comun.RAIZ / f"godot/modelos/{FAMILIA}/{ID}.glb")
    if "--sin-hoja" not in sys.argv:
        _vista_desde_abajo()
        hoja_revision(cuerpo, techo, revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
