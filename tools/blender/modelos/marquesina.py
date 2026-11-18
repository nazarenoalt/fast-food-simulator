"""Modelo: techo con cartel al frente (id `marquesina`, tres tamaños).

Genera, para cada tamaño (chico = barra_chica, mediano = barra_mediana, grande = carro_grande):
    godot/modelos/accesorios/texturas/marquesina_<tamaño>.png   ← el cartel (guía 4.5)
    arte/fuentes/accesorios/marquesina_<tamaño>.blend
    godot/modelos/accesorios/marquesina_<tamaño>.glb
y una sola hoja con los tres: docs/arte/revisiones/marquesina.jpg

Uso:
    python tools/blender/modelos/marquesina.py [--sin-hoja]

Forma: el techo_plano (chapa de 4 cm sobre 4 caños parados en la mesada y dos vigas) con un
tablero de chapa al frente, de 2,12 a 2,44 m, en vez del faldón. Sobre el tablero, el cartel
`pieza_cartel` (letras de carrito "PANCHOS" con guardas de filete, en una imagen con colores de
la paleta: amarillo, rojo, crema y azul) entre dos filas de lamparitas `pieza_lamparitas`
(M_LuzCalida, emisión: el juego las prende de noche). `punto_luz` en el centro del cartel. Un
colgador por cada luz_N de la base (`pieza_colgadores` + `punto_foco_N`) para el foco_calido.

Medidas (relativas al anclaje `techo`): como techo_plano (ancho de la base + 0,10, fondo
profundidad + 0,34, centrado sobre la mesada), con el tablero hasta 2,44 m. El cartel mide
1,20 / 1,80 / 2,40 × 0,20 m (chico / mediano / grande); las lamparitas, cada ≈ 15 cm.

Tamaño dinámico: el tablero, la chapa y las vigas están partidos en pieza_punta_izq, pieza_tramo
(estirable en X) y pieza_punta_der (superficies 0 chapa, 1 acero); el cartel y las lamparitas
van aparte, centrados: no se estiran (las letras no se deforman); al cambiar el ancho se
cambia el cartel por el del tamaño más cercano.

Objetos (hijos del Empty `marquesina_<tamaño>`): las tres piezas, pieza_cartel (imagen T_ +
M_MetalOscuro), pieza_lamparitas, punto_luz, pieza_colgadores, punto_foco_N y
`marquesina_<tamaño>-colonly` (los 4 caños).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

import comun  # noqa: E402
import piezas  # noqa: E402
import _techo as t  # noqa: E402
from pizarra_precios import (color_paleta, fuente, guardar_textura, lienzo,  # noqa: E402
                             mapear_cara, material_cartel, revisar_cartel)
from telon_panchos import guarda  # noqa: E402

ID = "marquesina"
PRESUPUESTO = 1500           # lista (el chico); las lamparitas crecen con el ancho
CHAPA_ABAJO, CHAPA_ARRIBA = 2.24, 2.28
TABLERO = (2.12, 2.44, 0.04)  # de y, a y, espesor
CARTEL_ALTO = 0.20
CARTEL_ANCHO = {"chico": 1.20, "mediano": 1.80, "grande": 2.40}
PX_POR_M = 512 / 1.2         # el chico sale de 512 px de ancho
LAMPARITA = 0.016
PASO = 0.15


def textura(tam):
    return comun.RAIZ / f"godot/modelos/{t.FAMILIA}/texturas/{ID}_{tam}.png"


def dibujar_textura(tam):
    ancho = CARTEL_ANCHO[tam]
    w, h = round(ancho * PX_POR_M), round(CARTEL_ALTO * PX_POR_M)
    img, dib = lienzo((w, h), "M_Amarillo")
    rojo, crema = color_paleta("M_RojoAcento"), color_paleta("M_BlancoCrema")
    azul = color_paleta("M_AzulAcento")
    dib.rectangle((3, 3, w - 4, h - 4), outline=rojo, width=4)
    dib.rectangle((10, 10, w - 11, h - 11), outline=azul, width=2)
    letra = fuente(round(h * 0.62))
    medio = h / 2
    for dx, dy, color in ((3, 3, crema), (0, 0, rojo)):
        dib.text((w / 2 + dx, medio + dy), "PANCHOS", font=letra, fill=color, anchor="mm")
    x = dib.textlength("PANCHOS", font=letra) / 2 + 30
    while w / 2 + x + 70 < w - 14:                     # guardas de filete hasta llenar el cartel
        for hacia in (-1, 1):
            guarda(dib, w / 2 + hacia * x, medio, hacia, azul, crema, rojo)
        x += 105
    guardar_textura(img, textura(tam))


def construir(tam):
    b = t.base(tam)
    g = t.geometria_techo(b, extra=0.34)
    oscuro, acero, luz = comun.cargar_materiales("M_MetalOscuro", "M_Acero", "M_LuzCalida")
    y0, y1, e = TABLERO
    bm = bmesh.new()
    perfil = [(CHAPA_ABAJO, g.zb), (CHAPA_ARRIBA, g.zb), (CHAPA_ARRIBA, g.zf - e), (y1, g.zf - e),
              (y1, g.zf), (y0, g.zf), (y0, g.zf - e), (CHAPA_ABAJO, g.zf - e)]
    t.prisma_x(bm, perfil, -g.W / 2, g.W / 2, bisel=t.BISEL, mat=0)
    col = t.canos(bm, g, lambda z: CHAPA_ABAJO - t.VIGA, 1)
    t.vigas_x(bm, g, lambda z: CHAPA_ABAJO, 1)
    piezas3 = t.tres_piezas(bm, g.corte, [oscuro, acero])

    # Cartel: una placa de 1,2 cm con la imagen en la cara de adelante.
    dibujar_textura(tam)
    m_cartel = material_cartel(f"T_{ID}_{tam}", textura(tam), rugosidad=0.6)
    yc = (y0 + y1) / 2
    ancho = CARTEL_ANCHO[tam]
    bm = bmesh.new()
    caras = piezas.caja(bm, (ancho, CARTEL_ALTO, 0.012), (0, yc, g.zf + 0.006), mat=1)
    frente = max(caras, key=lambda f: -f.calc_center_median().y)
    frente.material_index = 0
    mapear_cara(bm, frente, Vector((1, 0, 0)), Vector((0, 0, 1)))
    cartel = t.objeto("pieza_cartel", bm, [m_cartel, oscuro], recalcular=True)

    bm = bmesh.new()
    n = round((ancho + 0.1) / PASO) + 1
    paso = (ancho + 0.1) / (n - 1)
    for fila in (-1, 1):
        for i in range(n):
            x = -(ancho + 0.1) / 2 + i * paso
            piezas.esfera(bm, LAMPARITA, (x, yc + fila * (CARTEL_ALTO / 2 + 0.03), g.zf + LAMPARITA),
                          lados=6)
    lamparitas = t.objeto("pieza_lamparitas", bm, [luz], sombreado="suave", recalcular=True)
    p_luz = piezas.punto("punto_luz", (0, yc, g.zf + 0.05))

    colg, puntos_foco = t.colgadores(g, lambda z: CHAPA_ABAJO, acero)
    choque = t.colision(f"{ID}_{tam}", cilindros=col)
    hijos = piezas3 + [cartel, lamparitas, p_luz, colg] + puntos_foco + [choque]
    raiz = t.raiz_modelo(ID, tam, hijos)
    return {
        "raiz": raiz, "piezas": piezas3, "visibles": piezas3 + [cartel, lamparitas, colg],
        "exportar": [raiz] + hijos, "g": g, "b": b, "puntos_foco": puntos_foco,
        "presup": t.presupuesto(PRESUPUESTO, b), "sup_techo": {0}, "cartel": m_cartel,
        "lamparitas": 2 * n,
        "esperado": ((-g.W / 2, g.W / 2), (b.a, y1), (g.zb, g.zf + 2 * LAMPARITA)),
        "desc": "techo %.2f × %.2f, tablero de %.2f a %.2f, cartel %.2f × %.2f" % (
            g.W, g.D, y0, y1, ancho, CARTEL_ALTO),
    }


def revisar(m):
    res = revisar_cartel(t.revisar_techo(m), [m["cartel"]])
    res.append((True, "pieza_cartel centrado (no se estira) y %d lamparitas en pieza_lamparitas "
                      "(M_LuzCalida), punto_luz en el centro del cartel" % m["lamparitas"]))
    return res


def hoja(revision):
    t.hoja_techo(ID, construir, "marquesina · chico / mediano / grande: 1,70 / 2,50 / 3,50 m de "
                 "ancho · tablero de 2,12 a 2,44 m con cartel y lamparitas", revision)


if __name__ == "__main__":
    t.main(ID, construir, revisar, hoja, uvs=True)
