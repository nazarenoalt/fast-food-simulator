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

Parametrizado por la palabra: telon_hamburguesas.py y telon_choripan.py son este mismo modelo
con otra imagen (main(id_, texto)). Una palabra más ancha que "PANCHOS" se angosta (las letras
se comprimen en X, sin suavizado); si ni así entra con las guardas, va sin guardas y con un
filete chico en cada punta.
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


def textura(id_):
    return comun.RAIZ / f"godot/modelos/{FAMILIA}/texturas/{id_}.png"


def letras(dib, img, texto, centro, letra, crema, rojo, ancho_max):
    """Letras de carrito (rojo con sombra crema corrida abajo a la derecha). Si la palabra es
    más ancha que ancho_max, se dibuja aparte y se comprime en X con NEAREST (sin suavizado:
    siguen siendo solo colores de la paleta). Devuelve el ancho final."""
    ancho = dib.textlength(texto, font=letra)
    if ancho <= ancho_max:
        for dx, dy, color in ((4, 4, crema), (0, 0, rojo)):
            dib.text((centro[0] + dx, centro[1] + dy), texto, font=letra, fill=color, anchor="mm")
        return ancho
    from PIL import Image, ImageDraw
    w, h = round(ancho) + 16, img.size[1]
    capa = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    d.fontmode = "1"
    for dx, dy, color in ((4, 4, crema), (0, 0, rojo)):
        d.text((w / 2 + dx, centro[1] + dy), texto, font=letra, fill=color + (255,), anchor="mm")
    nuevo = round(w * ancho_max / ancho)
    capa = capa.resize((nuevo, h), Image.NEAREST)
    img.paste(capa, (round(centro[0] - nuevo / 2), 0), capa)
    return ancho_max


def dibujar_textura(texto="PANCHOS", ruta=TEXTURA):
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
    # Letras de carrito entre dos guardas de filete. "PANCHOS" marca el ancho máximo con
    # guardas; una palabra hasta 20 % más ancha se angosta; más larga, va sin guardas.
    medio = (px(0.73 - 0.63) + px(0.73 - 0.41)) / 2
    letra = fuente(60)
    con_guardas = dib.textlength("PANCHOS", font=letra)
    if dib.textlength(texto, font=letra) <= con_guardas * 1.2:
        ancho = letras(dib, img, texto, (w / 2, medio), letra, crema, rojo, con_guardas)
        for hacia in (-1, 1):
            guarda(dib, w / 2 + hacia * (ancho / 2 + 30), medio, hacia, azul, crema, rojo)
    else:
        ancho = letras(dib, img, texto, (w / 2, medio), letra, crema, rojo, w - 64)
        for hacia in (-1, 1):
            x = w / 2 + hacia * (ancho / 2 + 16)
            dib.ellipse((x - 9, medio - 9, x + 9, medio + 9), fill=azul)
            dib.ellipse((x - 4, medio - 4, x + 4, medio + 4), fill=crema)
    guardar_textura(img, ruta)


def construir(id_=ID, texto="PANCHOS"):
    dibujar_textura(texto, textura(id_))
    (m_amarillo,) = comun.cargar_materiales("M_Amarillo")
    m_cartel = material_cartel(f"T_{id_}", textura(id_), rugosidad=0.7)
    bm = bmesh.new()
    caras = piezas.caja(bm, MEDIDAS, (0, ABAJO + MEDIDAS[1] / 2, MEDIDAS[2] / 2), mat=0)
    frente = max(caras, key=lambda f: -f.calc_center_median().y)   # −Y Blender = +Z Godot
    frente.material_index = 1
    mapear_cara(bm, frente, Vector((1, 0, 0)), Vector((0, 0, 1)))
    # Un solo objeto con el id: no tiene piezas que toque el código ni colisión.
    return piezas.terminar(id_, bm, [m_amarillo, m_cartel], sombreado="suave")


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


def hoja_revision(telon, revision, id_=ID):
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
        f"{id_} · 1,3 × 0,42 × 0,01 m · accesorio (anclaje frente, de 0,31 a 0,73 m)",
        cuadros, revision, comun.RAIZ / f"docs/arte/revisiones/{id_}.jpg",
    )


def main(id_=ID, texto="PANCHOS"):
    comun.escena_vacia()
    telon = construir(id_, texto)
    revision = comun.revisar(telon, PRESUPUESTO, MEDIDAS, origen="base")
    revision = [chequeo_origen(telon) if t.startswith("Origen") else (ok, t) for ok, t in revision]
    revision = revisar_cartel(revision, [bpy.data.materials[f"T_{id_}"]])
    ok = comun.imprimir_revision(id_, revision)
    comun.guardar_blend(comun.RAIZ / f"arte/fuentes/{FAMILIA}/{id_}.blend")
    comun.exportar_glb([telon], comun.RAIZ / f"godot/modelos/{FAMILIA}/{id_}.glb", uvs=True)
    if "--sin-hoja" not in sys.argv:
        hoja_revision(telon, revision, id_)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
