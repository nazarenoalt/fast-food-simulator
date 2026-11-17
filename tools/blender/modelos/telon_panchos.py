"""Modelo: telón "Panchos" (id `telon_panchos`, godot/data/accesorios.ron).

Genera:
    godot/modelos/accesorios/texturas/telon_panchos.png   ← franjas y letras (guía 4.5)
    arte/fuentes/accesorios/telon_panchos.blend
    godot/modelos/accesorios/telon_panchos.glb
    docs/arte/revisiones/telon_panchos.jpg

Uso:
    blender -b -P tools/blender/modelos/telon_panchos.py
    python tools/blender/modelos/telon_panchos.py

Forma: lona tensada de 1,3 × 0,42 × 0,01 m (tela: sin bisel, guía 3.3). Las franjas rojas,
la palabra "PANCHOS" con letras de carrito (rojo con sombra crema, entre dos guardas de
filete simplificado) y los ojales de las esquinas van en una imagen sobre la cara de
adelante, en colores de la paleta. Los cantos y la espalda son amarillos.
Ubicación igual que hoy: el origen es el anclaje `frente` (a nivel del piso, en la cara del
carrito); la lona va de y = 0,31 a 0,73 y apoya su espalda en z = 0 (chequeo propio).
Sin colisión (colision: false en accesorios.ron).
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

import comun  # noqa: E402
import piezas  # noqa: E402
from pizarra_precios import (color_paleta, fuente, guardar_textura, lienzo,  # noqa: E402
                             mapear_cara, material_cartel, revisar_cartel)

ID = "telon_panchos"
FAMILIA = "accesorios"
MEDIDAS = (1.3, 0.42, 0.01)
PRESUPUESTO = 200
ABAJO = 0.31                       # altura del borde de abajo (pos y 0,52 − 0,21 del dato)
TEXTURA = comun.RAIZ / f"godot/modelos/{FAMILIA}/texturas/{ID}.png"
TEXTURA_TAM = (512, 166)           # misma proporción que la lona (1,3 × 0,42)


def px(m):
    """Metros de la lona → píxeles de la imagen."""
    return round(m * TEXTURA_TAM[0] / MEDIDAS[0])


def guarda(dib, cx, cy, hacia, azul, crema, rojo):
    """Filete simplificado: un rulo en espiral y una hojita que sale hacia afuera (hacia =
    −1 izquierda, +1 derecha)."""
    for r0, color, ancho in ((19, azul, 6), (11, crema, 3)):
        puntos = []
        for i in range(41):
            t = i / 40
            a = math.pi / 2 + hacia * t * 2.2 * math.pi
            r = r0 * (1 - 0.75 * t)
            puntos.append((cx + r * math.cos(a), cy - r * math.sin(a)))
        dib.line(puntos, fill=color, width=ancho, joint="curve")
    x0 = cx + hacia * 20
    hoja = [(x0, cy), (x0 + hacia * 22, cy - 11), (x0 + hacia * 46, cy), (x0 + hacia * 22, cy + 11)]
    dib.polygon(hoja, fill=rojo)
    dib.line([hoja[0], hoja[2]], fill=crema, width=2)
    dib.ellipse((x0 + hacia * 54 - 5, cy - 5, x0 + hacia * 54 + 5, cy + 5), fill=azul)


def dibujar_textura():
    w, h = TEXTURA_TAM
    img, dib = lienzo(TEXTURA_TAM, "M_Amarillo")
    rojo, crema = color_paleta("M_RojoAcento"), color_paleta("M_BlancoCrema")
    azul, acero, hierro = color_paleta("M_AzulAcento"), color_paleta("M_Acero"), color_paleta("M_Hierro")
    # Franjas rojas, a las mismas alturas que las de hoy (0,35–0,41 y 0,63–0,69 desde el piso).
    for y0, y1 in ((0.63, 0.69), (0.35, 0.41)):
        dib.rectangle((0, px(0.73 - y1), w, px(0.73 - y0) - 1), fill=rojo)
    # Ojales en las esquinas.
    for x in (12, w - 13):
        for y in (8, h - 9):
            dib.ellipse((x - 6, y - 6, x + 6, y + 6), fill=acero)
            dib.ellipse((x - 3, y - 3, x + 3, y + 3), fill=hierro)
    # Letras de carrito: rojo con sombra crema corrida abajo a la derecha.
    medio = (px(0.73 - 0.63) + px(0.73 - 0.41)) / 2
    letra = fuente(60)
    for dx, dy, color in ((4, 4, crema), (0, 0, rojo)):
        dib.text((w / 2 + dx, medio + dy), "PANCHOS", font=letra, fill=color, anchor="mm")
    ancho = dib.textlength("PANCHOS", font=letra)
    for hacia in (-1, 1):
        guarda(dib, w / 2 + hacia * (ancho / 2 + 30), medio, hacia, azul, crema, rojo)
    guardar_textura(img, TEXTURA)


def construir():
    dibujar_textura()
    (m_amarillo,) = comun.cargar_materiales("M_Amarillo")
    m_cartel = material_cartel(f"T_{ID}", TEXTURA, rugosidad=0.7)
    bm = bmesh.new()
    caras = piezas.caja(bm, MEDIDAS, (0, ABAJO + MEDIDAS[1] / 2, MEDIDAS[2] / 2), mat=0)
    frente = max(caras, key=lambda f: -f.calc_center_median().y)   # −Y Blender = +Z Godot
    frente.material_index = 1
    mapear_cara(bm, frente, Vector((1, 0, 0)), Vector((0, 0, 1)))
    # Un solo objeto con el id: no tiene piezas que toque el código ni colisión.
    return piezas.terminar(ID, bm, [m_amarillo, m_cartel], sombreado="suave")


def chequeo_origen(obj):
    """El origen es el anclaje `frente`: la lona flota de y 0,31 a 0,73, centrada en X, con
    la espalda en z = 0 (como la pieza simple de hoy en accesorios.ron)."""
    xs = [v.co.x for v in obj.data.vertices]
    ys = [v.co.z for v in obj.data.vertices]       # Y de Godot
    zs = [-v.co.y for v in obj.data.vertices]      # Z de Godot
    ok = (abs(max(xs) + min(xs)) < 0.002 and abs(min(ys) - ABAJO) < 0.002
          and abs(min(zs)) < 0.002)
    return ok, ("Origen en el anclaje `frente`: lona de y %.2f a %.2f, espalda en z = %.3f" %
                (min(ys), max(ys), min(zs)))


def hoja_revision(telon, revision):
    comun.preparar_revision()
    persona = bpy.data.objects["ref_persona_1,75m"]
    persona.hide_render = False
    persona.location = (1.0, 0.6, 0)
    con_persona = [telon, persona]
    solo = [telon]
    cuadros = comun.sacar_fotos([
        ("Frente (cliente, +Z) · día", solo, "frente", "dia", True),
        ("Costado: lona de 1 cm, sin bisel · día", solo, "costado", "dia", True),
        ("3/4 · día", solo, "tres_cuartos", "dia", False),
        ("Escala: al lado de la persona de 1,75 m · día", con_persona, "tres_cuartos", "dia", False),
        ("3/4 · atardecer", solo, "tres_cuartos", "atardecer", False),
    ])
    comun.componer_hoja(
        f"{ID} · 1,3 × 0,42 × 0,01 m · accesorio (anclaje frente, de 0,31 a 0,73 m)",
        cuadros, revision, comun.RAIZ / f"docs/arte/revisiones/{ID}.jpg",
    )


def main():
    comun.escena_vacia()
    telon = construir()
    revision = comun.revisar(telon, PRESUPUESTO, MEDIDAS, origen="base")
    revision = [chequeo_origen(telon) if t.startswith("Origen") else (ok, t) for ok, t in revision]
    revision = revisar_cartel(revision, [bpy.data.materials[f"T_{ID}"]])
    ok = comun.imprimir_revision(ID, revision)
    comun.guardar_blend(comun.RAIZ / f"arte/fuentes/{FAMILIA}/{ID}.blend")
    comun.exportar_glb([telon], comun.RAIZ / f"godot/modelos/{FAMILIA}/{ID}.glb", uvs=True)
    if "--sin-hoja" not in sys.argv:
        hoja_revision(telon, revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
