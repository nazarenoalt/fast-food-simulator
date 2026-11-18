"""Modelo: cartel de cerrado colgante (id `cartel_cerrado`, accesorios.ron, SPEC-026).

Genera:
    godot/modelos/accesorios/texturas/cartel_cerrado.png   ← el cartel (guía 4.5)
    arte/fuentes/accesorios/cartel_cerrado.blend
    godot/modelos/accesorios/cartel_cerrado.glb
    docs/arte/revisiones/cartel_cerrado.jpg

Uso:
    python tools/blender/modelos/cartel_cerrado.py [--sin-hoja]

Forma: cartel **colgante** de mostrador. Un pórtico de caño oscuro (M_MetalOscuro): dos patas
cortas de apoyo, dos parantes redondos y un travesaño con remates de bocha; del travesaño
cuelga, con dos cadenas de acero (cilindros de 6 lados, sin eslabones, como las de la guía),
un tablero de madera (M_Madera) con el cartel pintado de los dos lados: «CERRADO» en letras
crema con sombra sobre rojo, con doble filete (textura `T_cartel_cerrado`, opaca, solo colores
de la paleta). Atrás el texto también se lee derecho (la UV de la cara de atrás va espejada).
Va en cualquier anclaje de mostrador que acepte Decoración (`mostrador_centro`, `mostrador_der`).

Medidas: 0,42 × 0,451 × 0,12 (remates × alto × patas). Tablero 0,32 × 0,16, de 0,20 a 0,36 m.
Origen: centro de la base (las patas), a nivel de donde se apoya (guía 2.4).
Objetos (hijos del Empty `cartel_cerrado`): `cartel_cerrado_cuerpo` (MetalOscuro, Madera,
Acero, T_cartel_cerrado) y `cartel_cerrado-colonly` (patas, parantes y tablero, sin las
cadenas). No es `pieza_cartel`: ese nombre es de los carteles que se prenden de noche.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

import _accesorios5 as a5  # noqa: E402
import _equipos as eq  # noqa: E402
import comun  # noqa: E402
import piezas  # noqa: E402
from piezas import g2b  # noqa: E402
from pizarra_precios import (color_paleta, fuente, guardar_textura, lienzo,  # noqa: E402
                             mapear_cara, material_cartel, revisar_cartel)
from telon_panchos import letras  # noqa: E402

ID = "cartel_cerrado"
PRESUPUESTO = 1000  # accesorios medianos (guía 3.1)
MEDIDAS = (0.42, 0.451, 0.12)
TEXTO = "CERRADO"
OSCURO, MADERA, ACERO, CARTEL = range(4)
X_PARANTE = 0.18
R_CANO = 0.009
Y_TRAVESANO = 0.436
R_BOCHA = 0.015
TABLERO = (0.32, 0.16, 0.014)
Y_TABLERO = 0.28                     # centro (de 0,20 a 0,36)
PINTADO = (0.296, 0.136)             # la parte pintada, 1 mm afuera de la madera
X_CADENA = 0.11
TEXTURA = comun.RAIZ / f"godot/modelos/{a5.FAMILIA}/texturas/{ID}.png"
TEXTURA_TAM = (512, round(512 * PINTADO[1] / PINTADO[0]))


def dibujar_textura():
    w, h = TEXTURA_TAM
    img, dib = lienzo(TEXTURA_TAM, "M_RojoAcento")
    amarillo, crema = color_paleta("M_Amarillo"), color_paleta("M_BlancoCrema")
    sombra = color_paleta("M_Hierro")
    dib.rectangle((5, 5, w - 6, h - 6), outline=amarillo, width=5)
    dib.rectangle((16, 16, w - 17, h - 17), outline=crema, width=2)
    for x in (30, w - 31):                       # puntitos del filete en las esquinas
        for y in (30, h - 31):
            dib.ellipse((x - 5, y - 5, x + 5, y + 5), fill=amarillo)
    letras(dib, img, TEXTO, (w / 2, h / 2 + 2), fuente(round(h * 0.5)), sombra, crema, w - 110)
    guardar_textura(img, TEXTURA)


def construir():
    dibujar_textura()
    oscuro, madera, acero = comun.cargar_materiales("M_MetalOscuro", "M_Madera", "M_Acero")
    m_cartel = material_cartel(f"T_{ID}", TEXTURA)
    bm = bmesh.new()
    # Pórtico: patas, parantes, travesaño y bochas.
    for sx in (-1, 1):
        piezas.caja(bm, (0.03, 0.014, MEDIDAS[2]), (sx * X_PARANTE, 0.007, 0), mat=OSCURO, bisel=0.004)
        alto = Y_TRAVESANO - 0.01
        piezas.cilindro(bm, R_CANO, alto, (sx * X_PARANTE, 0.01 + alto / 2, 0), lados=8, mat=OSCURO,
                        tapas=(False, False))
        piezas.esfera(bm, R_BOCHA, (sx * (MEDIDAS[0] / 2 - R_BOCHA), Y_TRAVESANO, 0), lados=8, mat=OSCURO)
    piezas.cilindro(bm, R_CANO, MEDIDAS[0] - 2 * R_BOCHA, (0, Y_TRAVESANO, 0), eje="x", lados=8,
                    mat=OSCURO, tapas=(False, False))
    # Cadenas (de 4 mm de radio, guía 2.2: cables y sogas).
    arriba_tablero = Y_TABLERO + TABLERO[1] / 2
    largo = Y_TRAVESANO - arriba_tablero
    for sx in (-1, 1):
        piezas.cilindro(bm, 0.004, largo + 0.004, (sx * X_CADENA, arriba_tablero + largo / 2, 0), lados=6,
                        mat=ACERO, tapas=(False, False))
    # Tablero de madera y la parte pintada (sale 1 mm de cada cara).
    piezas.caja(bm, TABLERO, (0, Y_TABLERO, 0), mat=MADERA, bisel=0.003)
    caras = piezas.caja(bm, (PINTADO[0], PINTADO[1], TABLERO[2] + 0.002), (0, Y_TABLERO, 0), mat=MADERA)
    frente = max(caras, key=lambda f: -f.calc_center_median().y)   # mira a −Y de Blender
    espalda = max(caras, key=lambda f: f.calc_center_median().y)
    for cara, u in ((frente, Vector((1, 0, 0))), (espalda, Vector((-1, 0, 0)))):
        cara.material_index = CARTEL
        mapear_cara(bm, cara, u, Vector((0, 0, 1)))
    cuerpo = piezas.terminar(f"{ID}_cuerpo", bm, [oscuro, madera, acero, m_cartel])
    col = eq.colision_cajas(ID, [
        ((MEDIDAS[0] - 2 * R_BOCHA, 0.014, MEDIDAS[2]), (0, 0.007, 0)),
        ((2 * R_CANO, Y_TRAVESANO, 2 * R_CANO), (-X_PARANTE, Y_TRAVESANO / 2, 0)),
        ((2 * R_CANO, Y_TRAVESANO, 2 * R_CANO), (X_PARANTE, Y_TRAVESANO / 2, 0)),
        ((MEDIDAS[0] - 2 * R_BOCHA, 2 * R_CANO, 2 * R_CANO), (0, Y_TRAVESANO, 0)),
        (TABLERO, (0, Y_TABLERO, 0)),
    ])
    raiz = piezas.raiz(ID, [cuerpo, col])
    return {"raiz": raiz, "cuerpo": cuerpo, "col": col, "m_cartel": m_cartel}


def revisar(m):
    res = comun.revisar([m["cuerpo"]], PRESUPUESTO, MEDIDAS, origen="base")
    res = revisar_cartel(res, [m["m_cartel"]])
    res = a5.chequeo_normales(res, [m["cuerpo"]])
    res.append((True, "Texto fijo \"%s\" de los dos lados (UV de 0 a 1; atrás espejada para que se "
                      "lea derecho); tablero colgado de dos cadenas a %.2f m del apoyo" % (TEXTO, Y_TABLERO)))
    return res


def hoja_revision(m, revision):
    comun.preparar_revision()
    solo = [m["cuerpo"]]
    carro, b = a5.carrito("barra_chica")
    copia = a5.e2.copiar(m["cuerpo"], f"ref_{ID}")
    copia.location = g2b(b.anclajes["mostrador_der"])
    persona = a5.persona()
    en_mostrador = carro + [copia, persona]
    pedidos = [
        ("Frente (lo que ve el cliente) · día", solo, "frente", "dia"),
        ("Costado · día", solo, "costado", "dia"),
        ("3/4 · día", solo, "tres_cuartos", "dia"),
        ("3/4 · atardecer", solo, "tres_cuartos", "atardecer"),
        ("Lado del vendedor (también dice CERRADO) · día", solo, "vendedor", "dia"),
        ("En la barra chica (mostrador_der) · día", en_mostrador, "tres_cuartos", "dia", None,
         a5.mover_persona((-0.3, 0, -0.65)), 1.05),
    ]
    a5.hoja(ID, "cartel_cerrado · 0,42 × 0,451 × 0,12 m · accesorio colgante (texto fijo de los dos lados)",
            pedidos, revision)


def main():
    comun.escena_vacia()
    m = construir()
    bpy.context.view_layer.update()
    revision = revisar(m)
    ok = comun.imprimir_revision(ID, revision)
    a5.guardar_y_exportar(ID, [m["raiz"], m["cuerpo"], m["col"]], uvs=True)
    if "--sin-hoja" not in sys.argv:
        hoja_revision(m, revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
