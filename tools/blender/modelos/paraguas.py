"""Modelo: paraguas abierto para los NPC (id `paraguas`, etapa 6; para el clima con lluvia).

Genera:
    arte/fuentes/personajes/paraguas.blend
    godot/modelos/personajes/paraguas.glb
    docs/arte/revisiones/paraguas.jpg

Uso:
    python tools/blender/modelos/paraguas.py [--sin-hoja]

Forma: paraguas común abierto, de Ø 1,0 × 0,90 (lista de modelos): puño recto negro con
regatón, caño de acero, tela de 8 gajos en cúpula (cada gajo plano entre dos varillas y con
el borde en festón: entre varilla y varilla la tela sube 2,5 cm), punta negra arriba. Por
debajo: 8 varillas (prismas de 3 lados de 4 mm, la excepción de cables de la guía 2.2), 8
tensores y la corredera. La tela tiene dos caras (se ve de abajo) que se juntan en el borde.
16 cortes alrededor (2 por gajo): la tabla 3.2 pide 24 para este radio, pero no entra en
el presupuesto de 400 con las varillas; con el festón ya se lee redondo.

Un solo modelo para todos los colores (guía 4.2, regla 5), como `pieza_pano` de la
sombrilla: la tela es `pieza_tela`, con dos superficies: 0 = gajos pares (el primero arranca
en +X) y 1 = gajos impares. El .glb trae M_AzulAcento en las dos; para uno rayado, el juego
pone otro material en la superficie 1 (en la hoja: rojo y crema, y negro liso).

Objetos (hijos del Empty `paraguas`):
    paraguas_cuerpo  puño, regatón, caño, punta, corredera, varillas y tensores (Acero,
                     PlasticoNegro).
    pieza_tela       la tela (dos superficies).
Origen = centro del puño (donde lo agarra la mano del NPC), con el caño sobre el eje Y: el
juego lo cuelga del hueso de la mano. Sin colisión (lo lleva un personaje). Familia
`personajes` (accesorio de NPC). El chequeo de origen de comun.revisar() mide el centro de
la caja total (la tela queda arriba): se reemplaza por uno propio.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402,F401  (antes que bmesh)
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

import comun  # noqa: E402
import piezas  # noqa: E402
import _etapa2 as e2  # noqa: E402
import _plaza as plaza  # noqa: E402
import _techo as t  # noqa: E402
from piezas import g2b  # noqa: E402

ID = "paraguas"
FAMILIA = "personajes"
PRESUPUESTO = 400
ACERO, NEGRO = range(2)

PUNO = (0.016, -0.05, 0.05)          # radio, abajo, arriba (Godot, relativo al origen)
Y_ABAJO, Y_ARRIBA = -0.06, 0.84      # regatón y punta: 0,90 en total
R = 0.50                             # radio de la tela (en las varillas)
Y_CENTRO, Y_MEDIO, Y_BORDE = 0.80, 0.72, 0.52     # cúpula: centro, a r = R_MEDIO, borde
R_MEDIO = 0.30
ESPESOR = 0.012                      # tela (de abajo, se ve)
FESTON = 0.025                       # cuánto sube el borde entre varillas
GAJOS, CORTES = 8, 16
Y_CORREDERA = 0.50
MEDIDAS = (2 * R, Y_ARRIBA - Y_ABAJO, 2 * R)


def punto_tela(j, capa):
    """Puntos (Godot) del corte j: [centro, medio, borde]; capa 0 = arriba, 1 = abajo."""
    a = 2 * math.pi * j / CORTES
    entre = j % 2 == 1                    # corte en el medio del gajo
    c, s = math.cos(a), math.sin(a)
    r_borde = R * (0.97 if entre else 1.0)
    y_borde = Y_BORDE + (FESTON if entre else 0.0)
    y_medio = Y_MEDIO - (0.008 if entre else 0.0)
    baja = ESPESOR * capa
    return [Vector((0, Y_CENTRO - baja, 0)),
            Vector((R_MEDIO * c, y_medio - baja * 0.85, R_MEDIO * s)),
            Vector((r_borde * c, y_borde, r_borde * s))]


def tela(bm):
    centro_a = bm.verts.new(g2b(punto_tela(0, 0)[0]))
    centro_b = bm.verts.new(g2b(punto_tela(0, 1)[0]))
    cortes = []
    for j in range(CORTES):
        a, b = punto_tela(j, 0), punto_tela(j, 1)
        cortes.append([bm.verts.new(g2b(a[1])), bm.verts.new(g2b(a[2])), bm.verts.new(g2b(b[1]))])
    for j in range(CORTES):
        m1, b1, n1 = cortes[j]
        m2, b2, n2 = cortes[(j + 1) % CORTES]
        gajo = (j // 2) % 2
        for vs in ((centro_a, m1, m2), (m1, b1, b2, m2), (centro_b, n2, n1), (n1, n2, b2, b1)):
            bm.faces.new(vs).material_index = gajo


def cuerpo(bm):
    r, y0, y1 = PUNO
    piezas.cilindro(bm, r, y1 - y0, (0, (y0 + y1) / 2, 0), lados=12, mat=NEGRO, radio_a_caras=True)
    piezas.cilindro(bm, 0.012, y0 - Y_ABAJO, (0, (Y_ABAJO + y0) / 2, 0), lados=12, mat=NEGRO,
                    radio_arriba=r * 0.9, tapas=(True, False), radio_a_caras=True)
    piezas.cilindro(bm, 0.006, Y_CENTRO - y1, (0, (y1 + Y_CENTRO) / 2, 0), lados=8, mat=ACERO,
                    tapas=(False, False), radio_a_caras=True)
    alto_punta = Y_ARRIBA - (Y_CENTRO - 0.02)
    piezas.cilindro(bm, 0.008, alto_punta, (0, Y_ARRIBA - alto_punta / 2, 0), lados=8, mat=NEGRO,
                    radio_arriba=0.003, tapas=(False, True), radio_a_caras=True)
    piezas.cilindro(bm, 0.011, 0.04, (0, Y_CORREDERA, 0), lados=8, mat=NEGRO, radio_a_caras=True)
    baja = Vector((0, ESPESOR + 0.006, 0))
    for g in range(GAJOS):
        c, m, b = punto_tela(2 * g, 0)
        dentro = c - baja + (m - c).normalized() * 0.012
        medio = m - baja
        punta = m.lerp(b, 0.97) - Vector((0, ESPESOR * 0.2 + 0.005, 0))
        t.varilla(bm, dentro, medio, 0.004, lados=3, mat=ACERO, tapas=(False, False))
        t.varilla(bm, medio, punta, 0.004, lados=3, mat=ACERO, tapas=(False, True))
        desde = Vector((0, Y_CORREDERA + 0.01, 0)) + (m - c).normalized() * 0.01
        t.varilla(bm, desde, dentro.lerp(medio, 0.7), 0.0035, lados=3, mat=ACERO, tapas=(False, False))


def construir():
    acero, negro, azul = comun.cargar_materiales("M_Acero", "M_PlasticoNegro", "M_AzulAcento")
    bm = bmesh.new()
    cuerpo(bm)
    c = piezas.terminar(f"{ID}_cuerpo", bm, [acero, negro])
    e2.suavizar_hasta(c, 50)
    bm = bmesh.new()
    tela(bm)
    tl = piezas.terminar("pieza_tela", bm, [azul, azul])
    raiz = piezas.raiz(ID, [c, tl])
    return raiz, c, tl


def chequeo_origen(c, tl):
    vs = e2.verts_godot(c)
    puno = [v for v in vs if PUNO[1] - 1e-6 <= v.y <= PUNO[2] + 1e-6 and math.hypot(v.x, v.z) > 0.014]
    cx = (max(v.x for v in puno) + min(v.x for v in puno)) / 2
    cz = (max(v.z for v in puno) + min(v.z for v in puno)) / 2
    cy = (max(v.y for v in puno) + min(v.y for v in puno)) / 2
    vt = e2.verts_godot(tl)
    tx = (max(v.x for v in vt) + min(v.x for v in vt)) / 2
    tz = (max(v.z for v in vt) + min(v.z for v in vt)) / 2
    ok = max(abs(cx), abs(cy), abs(cz), abs(tx), abs(tz)) < 1e-4
    return ok, "Origen en el centro del puño (%.3f, %.3f, %.3f); tela centrada sobre el caño (eje Y)" % (cx, cy, cz)


def chequeo_tela(tl):
    vs = e2.verts_godot(tl)
    borde = min(v.y for v in vs)
    ok = len(tl.data.materials) == 2 and \
        {p.material_index for p in tl.data.polygons} == {0, 1} and abs(borde - Y_BORDE) < 1e-6
    return ok, "pieza_tela: 2 superficies (gajos pares / impares), Ø %.2f, borde a %.2f del puño y punta a %.2f" % (
        2 * R, Y_BORDE, Y_ARRIBA)


def revisar(c, tl):
    res = comun.revisar([c, tl], PRESUPUESTO, MEDIDAS, origen="base")
    res = plaza.reemplazar(res, "Origen", *chequeo_origen(c, tl))
    res.insert(1, chequeo_tela(tl))
    return res


def _vista_desde_abajo():
    """Vista extra para la hoja (sin tocar comun.py): debajo del paraguas, mirando arriba."""
    original = comun.encuadrar

    def encuadrar(objetos, vista, margen=1.25, de_cerca=False):
        if vista != "desde_abajo":
            return original(objetos, vista, margen, de_cerca)
        original(objetos, "tres_cuartos", margen, de_cerca)
        cam = bpy.context.scene.camera
        cam.data.lens = 20
        base = objetos[0].matrix_world.translation
        cam.location = base + g2b((0.55, 0.05, 0.45))
        mira = base + g2b((-0.05, 0.75, -0.05))
        cam.rotation_euler = (mira - cam.location).to_track_quat("-Z", "Y").to_euler()

    comun.encuadrar = encuadrar


def hoja_revision(c, tl, revision):
    comun.preparar_revision()
    persona = bpy.data.objects["ref_persona_1,75m"]
    rojo, crema, negro = comun.cargar_materiales("M_RojoAcento", "M_BlancoCrema", "M_PlasticoNegro")
    rayada = e2.copiar(tl, "ref_tela_rayada", rojo, 0)
    rayada.data.materials[1] = crema
    lisa = e2.copiar(tl, "ref_tela_negra", negro, 0)
    lisa.data.materials[1] = negro
    alto = 0.5 + R  # para las fotos: apoyado con el borde a la altura justa sobre el piso
    for o in (c, tl, rayada, lisa):
        o.location.z = alto
    # Con la persona: el puño en la mano, a 1,32 m, un poco adelante y al costado.
    c2 = e2.copiar(c, "ref_cuerpo_persona")
    t2 = e2.copiar(tl, "ref_tela_persona")
    for o in (c2, t2):
        o.location = g2b((0.18, 1.32, 0.12))
    persona.location = (0, 0, 0)
    bpy.context.view_layer.update()
    azul = [c, tl]
    raya = [c, rayada]
    cuadros = comun.sacar_fotos([
        ("Frente · día", azul, "frente", "dia", True),
        ("Azul (el .glb) · 3/4 · día", azul, "tres_cuartos", "dia", False),
        ("Rayado (sup. 1 crema) · 3/4 · día", raya, "tres_cuartos", "dia", False),
        ("Desde abajo: varillas y tensores · día", raya, "desde_abajo", "dia", False),
        ("Negro liso · 3/4 · atardecer", [c, lisa], "tres_cuartos", "atardecer", False),
        ("Con la persona de 1,75 m (puño a 1,32 m) · día", [c2, t2, persona], "frente", "dia", True),
    ])
    comun.componer_hoja(f"{ID} · Ø 1,0 × 0,90 m · accesorio de NPC (un modelo, colores por superficie)",
                        cuadros, revision, comun.RAIZ / f"docs/arte/revisiones/{ID}.jpg")


def main():
    comun.escena_vacia()
    raiz, c, tl = construir()
    revision = revisar(c, tl)
    ok = comun.imprimir_revision(ID, revision)
    comun.guardar_blend(comun.RAIZ / f"arte/fuentes/{FAMILIA}/{ID}.blend")
    comun.exportar_glb([raiz, c, tl], comun.RAIZ / f"godot/modelos/{FAMILIA}/{ID}.glb")
    if "--sin-hoja" not in sys.argv:
        _vista_desde_abajo()
        hoja_revision(c, tl, revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
