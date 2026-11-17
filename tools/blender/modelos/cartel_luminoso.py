"""Modelo: cartel luminoso (id `cartel_luminoso`, lista de modelos, etapa 5).

Genera:
    godot/modelos/accesorios/texturas/cartel_luminoso.png   ← el cartel (guía 4.5)
    arte/fuentes/accesorios/cartel_luminoso.blend
    godot/modelos/accesorios/cartel_luminoso.glb
    docs/arte/revisiones/cartel_luminoso.jpg

Uso:
    python tools/blender/modelos/cartel_luminoso.py [--sin-hoja]

Forma: cartel de marquesina chico, parado sobre dos patitas: caja de chapa oscura
(M_MetalOscuro) de 0,80 × 0,25 × 0,08 con el frente ocupado por el cartel `pieza_cartel`
(texto FIJO "PANCHOS", guía 4.5: letras de carrito rojas con sombra, borde azul y dos
guardas de filete, en una imagen con colores de la paleta) y una fila de lamparitas arriba y
otra abajo, más una a cada lado (`pieza_lamparitas`, M_LuzCalida, medias esferas pegadas a
la chapa: el juego las prende de noche, como las de la marquesina). `punto_luz` adelante,
en el medio del cartel. Si se quiere que el cartel mismo brille de noche, el juego puede
sumarle emisión a `pieza_cartel` (la imagen es opaca).
Se apoya plano en cualquier superficie: el mostrador (anclajes `mostrador_*`, categoría
Decoración) o arriba de un techo de chapa.
Medidas: 0,80 × 0,30 × 0,10 (lista): patitas de 5 cm, caja de 0,05 a 0,30 m; de fondo,
las patitas (±0,05).
Origen: centro de la base (las patitas), a nivel de donde se apoya.
Objetos (hijos del Empty `cartel_luminoso`): cartel_luminoso_cuerpo, pieza_cartel (T_ +
M_MetalOscuro en los cantos), pieza_lamparitas, punto_luz y `cartel_luminoso-colonly` (una
caja del tamaño total).
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

import _accesorios5 as a5  # noqa: E402
import comun  # noqa: E402
import piezas  # noqa: E402
from piezas import g2b  # noqa: E402
from pizarra_precios import (color_paleta, fuente, guardar_textura, lienzo,  # noqa: E402
                             mapear_cara, material_cartel, revisar_cartel)
from telon_panchos import guarda  # noqa: E402

ID = "cartel_luminoso"
PRESUPUESTO = 400
MEDIDAS = (0.80, 0.30, 0.10)
TEXTO = "PANCHOS"
PATA = (0.03, 0.05, 0.10)           # ancho, alto, fondo
PATA_X = 0.30
CAJA = (0.80, 0.25, 0.08)
CAJA_Z = (-0.05, 0.03)              # espalda, frente
CARTEL = (0.70, 0.16, 0.008)
LAMPARITA = 0.013
FILA = 7                            # lamparitas por fila (arriba y abajo)
TEXTURA = comun.RAIZ / f"godot/modelos/{a5.FAMILIA}/texturas/{ID}.png"
TEXTURA_TAM = (512, round(512 * CARTEL[1] / CARTEL[0]))


def dibujar_textura():
    w, h = TEXTURA_TAM
    img, dib = lienzo(TEXTURA_TAM, "M_BlancoCrema")
    rojo, azul = color_paleta("M_RojoAcento"), color_paleta("M_AzulAcento")
    crema, sombra = color_paleta("M_BlancoCrema"), color_paleta("M_Hierro")
    dib.rectangle((3, 3, w - 4, h - 4), outline=azul, width=3)
    dib.rectangle((9, 9, w - 10, h - 10), outline=rojo, width=2)
    letra = fuente(round(h * 0.46))      # deja lugar para las guardas adentro del borde
    medio = h / 2 + 2
    for dx, dy, color in ((3, 3, sombra), (0, 0, rojo)):
        dib.text((w / 2 + dx, medio + dy), TEXTO, font=letra, fill=color, anchor="mm")
    x = dib.textlength(TEXTO, font=letra) / 2 + 26
    for hacia in (-1, 1):
        guarda(dib, w / 2 + hacia * x, medio, hacia, azul, crema, rojo)
    guardar_textura(img, TEXTURA)


def media_esfera(bm, centro, r, lados=6):
    """Media esfera pegada a una cara que mira a +Z (sin la tapa de atrás)."""
    cx, cy, cz = centro
    anillos = []
    for a in (0.0, math.pi / 4):
        anillos.append([bm.verts.new(g2b((cx + r * math.cos(a) * math.cos(2 * math.pi * k / lados),
                                          cy + r * math.cos(a) * math.sin(2 * math.pi * k / lados),
                                          cz + r * math.sin(a)))) for k in range(lados)])
    polo = bm.verts.new(g2b((cx, cy, cz + r)))
    a, b = anillos
    for k in range(lados):
        j = (k + 1) % lados
        bm.faces.new((a[k], a[j], b[j], b[k]))
        bm.faces.new((b[k], b[j], polo))


def construir():
    dibujar_textura()
    oscuro, luz = comun.cargar_materiales("M_MetalOscuro", "M_LuzCalida")
    m_cartel = material_cartel(f"T_{ID}", TEXTURA, rugosidad=0.5)
    y0 = PATA[1]
    yc = y0 + CAJA[1] / 2
    zc = (CAJA_Z[0] + CAJA_Z[1]) / 2
    bm = bmesh.new()
    piezas.caja(bm, CAJA, (0, yc, zc), bisel=0.01)
    for sx in (-1, 1):
        # Del piso hasta 4 mm adentro de la caja (no queda luz entre las dos).
        piezas.caja(bm, (PATA[0], PATA[1] + 0.004, PATA[2]), (sx * PATA_X, (PATA[1] + 0.004) / 2, 0),
                    sin_abajo=True)
    cuerpo = piezas.terminar(f"{ID}_cuerpo", bm, [oscuro])

    bm = bmesh.new()
    caras = piezas.caja(bm, CARTEL, (0, yc, CAJA_Z[1] + CARTEL[2] / 2), mat=1)
    frente = max(caras, key=lambda f: -f.calc_center_median().y)
    frente.material_index = 0
    mapear_cara(bm, frente, Vector((1, 0, 0)), Vector((0, 0, 1)))
    cartel = piezas.terminar("pieza_cartel", bm, [m_cartel, oscuro])

    bm = bmesh.new()
    margen_y = (CAJA[1] - CARTEL[1]) / 4
    xs = [-CARTEL[0] / 2 + CARTEL[0] * i / (FILA - 1) for i in range(FILA)]
    puntos = [(x, yc + s * (CARTEL[1] / 2 + margen_y), CAJA_Z[1]) for s in (-1, 1) for x in xs]
    puntos += [(s * (CARTEL[0] / 2 + (CAJA[0] - CARTEL[0]) / 4), yc, CAJA_Z[1]) for s in (-1, 1)]
    for p in puntos:
        media_esfera(bm, p, LAMPARITA)
    lamparitas = piezas.terminar("pieza_lamparitas", bm, [luz], sombreado="suave")
    p_luz = piezas.punto("punto_luz", (0, yc, MEDIDAS[2] / 2 + 0.03))
    col = piezas.colision_caja(ID, MEDIDAS, (0, MEDIDAS[1] / 2, 0))
    raiz = piezas.raiz(ID, [cuerpo, cartel, lamparitas, p_luz, col])
    return {"raiz": raiz, "cuerpo": cuerpo, "cartel": cartel, "lamparitas": lamparitas,
            "punto_luz": p_luz, "col": col, "m_cartel": m_cartel, "n": len(puntos)}


def revisar(m):
    vis = [m["cuerpo"], m["cartel"], m["lamparitas"]]
    res = comun.revisar(vis, PRESUPUESTO, MEDIDAS, origen="base")
    res = revisar_cartel(res, [m["m_cartel"]])
    res = a5.chequeo_normales(res, vis)
    res.append((True, "pieza_cartel con texto fijo \"%s\" (UV de 0 a 1 en la cara de adelante) y %d "
                      "lamparitas en pieza_lamparitas (M_LuzCalida); punto_luz adelante del cartel"
                % (TEXTO, m["n"])))
    return res


def hoja_revision(m, revision):
    import techo_plano
    comun.preparar_revision()
    solo = [m["cuerpo"], m["cartel"], m["lamparitas"]]
    carro, b = a5.carrito("barra_chica")
    techo = techo_plano.construir("chico")
    techo["raiz"].location = g2b(b.anclajes["techo"])
    copias = [a5.e2.copiar(o, f"ref_{o.name}") for o in solo]
    for c in copias:
        c.location = g2b(b.anclajes["mostrador_der"])
    arriba = [a5.e2.copiar(o, f"ref2_{o.name}") for o in solo]
    for c in arriba:
        c.location = g2b((0, 2.28, 0.42))
    persona = a5.persona()
    en_mostrador = carro + copias + [persona]
    en_techo = carro + techo["visibles"] + arriba
    pedidos = [
        ("Frente · día", solo, "frente", "dia"),
        ("Costado · día", solo, "costado", "dia"),
        ("3/4 · día", solo, "tres_cuartos", "dia"),
        ("3/4 · atardecer (las lamparitas brillan)", solo, "tres_cuartos", "atardecer"),
        ("Lado del vendedor (espalda de chapa) · día", solo, "vendedor", "dia"),
        ("Arriba · día", solo, "arriba", "dia"),
        ("En el mostrador (mostrador_der) · día", en_mostrador, "tres_cuartos", "dia", None,
         a5.mover_persona((-0.3, 0, -0.65)), 1.05),
        ("Arriba del techo_plano_chico · día", en_techo, "tres_cuartos", "dia", None, None, 1.05),
        ("Arriba del techo · atardecer", en_techo, "bajo", "atardecer", None, None, 1.05),
    ]
    a5.hoja(ID, "cartel_luminoso · 0,80 × 0,30 × 0,10 m · accesorio (texto fijo, lamparitas que se "
            "prenden)", pedidos, revision)


def main():
    comun.escena_vacia()
    m = construir()
    bpy.context.view_layer.update()
    revision = revisar(m)
    ok = comun.imprimir_revision(ID, revision)
    a5.guardar_y_exportar(ID, [m["raiz"], m["cuerpo"], m["cartel"], m["lamparitas"], m["punto_luz"],
                               m["col"]], uvs=True)
    if "--sin-hoja" not in sys.argv:
        hoja_revision(m, revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
