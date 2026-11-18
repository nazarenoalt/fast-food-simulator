"""Modelo: plancha a gas (id `plancha`, etapa 4; todavía sin dato en accesorios.ron).

Genera:
    arte/fuentes/cocina/plancha.blend
    godot/modelos/cocina/plancha.glb
    docs/arte/revisiones/plancha.jpg

Uso:
    blender -b -P tools/blender/modelos/plancha.py
    python tools/blender/modelos/plancha.py

Forma (mismo estilo que `hervidor_chico`): cuerpo de acero sobre 4 patas negras, con la
plancha de hierro (M_MetalOscuro) arriba. La plancha tiene un respaldo de acero del lado del
cliente (+Z) y costados en cuña (más altos atrás), y del lado del vendedor (−Z) la canaleta
para la grasa: un canal de 2,8 cm entre el borde de la plancha y un labio de acero, con el
agujero de desagote en la punta +X, que cae al cajón de grasa (con tirador negro) que está
justo abajo. En la cara del vendedor, dos perillas (una por quemador) y la luz piloto.

Medidas (lista de modelos: ≈ 0,60 × 0,25 × 0,45): 0,60 × 0,25 × 0,45 justos (de la aleta
de las perillas al respaldo).
- Superficie de trabajo (la plancha que se ve, entre costados, respaldo y canaleta):
  0,56 × 0,36 m, arriba a 0,17 m del apoyo, centrada en el origen. Ahí va `punto_superficie`.
- Canaleta: de z = −0,18 a −0,208, piso a 0,155 (1,5 cm por debajo de la plancha).

Objetos (hijos del Empty `plancha`, origen = centro de la superficie, a nivel del mostrador):
- `plancha_cuerpo`: todo lo que se ve (Acero, MetalOscuro, PlasticoNegro).
- `pieza_piloto` (M_PilotoApagado): la lente de la luz piloto; el juego la enciende.
- `punto_superficie`: centro de la superficie de trabajo (0; 0,17; 0). La física de la
  plancha (lo que cocina) arranca ahí.
- `plancha-colonly`: cuerpo hasta la superficie (0,60 × 0,17 × 0,42) + respaldo y costados
  (cajas simples). La canaleta y las perillas no chocan.

Qué se mide: el total en el chequeo de medidas y, aparte, la superficie de trabajo. El
chequeo de origen de comun.revisar() mide el centro de la caja total, que se corre hacia el
vendedor por las perillas; se reemplaza por uno propio (superficie centrada en el origen y
base a nivel del mostrador).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402,F401  (antes que bmesh)
import bmesh  # noqa: E402

import comun  # noqa: E402
import piezas  # noqa: E402
import _equipos as eq  # noqa: E402

ID = "plancha"
FAMILIA = "cocina"
PRESUPUESTO = 1500  # equipos de cocina (guía 3.1)
ACERO, OSCURO, NEGRO = range(3)

W = 0.60
Z_VEND, Z_CLI = -0.22, 0.20          # caras del cuerpo (vendedor / cliente)
Y_PATA, Y_CUERPO = 0.025, 0.155      # alto de las patas / arriba del cuerpo
SUP = (0.56, 0.36)                   # superficie de trabajo (X, Z)
Y_SUP = 0.17                         # arriba de la plancha
ESP_GUARDA = 0.01
Y_GUARDA = 0.25                      # respaldo y costados, atrás
BAJA_COSTADO = 0.05                  # los costados bajan 5 cm hacia el vendedor
Z_LABIO = Z_VEND + 0.012             # cara de adentro del labio de la canaleta (−0,208)
Y_CONTROLES = 0.085
PERILLAS_X = (-0.20, -0.08)
PILOTO_X = 0.04
DESAGOTE_X = 0.25
CAJON = (0.14, 0.045, 0.012)         # frente del cajón de grasa
CAJON_X = 0.20

MEDIDAS = (W, Y_GUARDA, Z_CLI - (Z_VEND - eq.SALE_PERILLA))


def construir():
    acero, oscuro, negro, piloto_m = comun.cargar_materiales(
        "M_Acero", "M_MetalOscuro", "M_PlasticoNegro", "M_PilotoApagado")
    bm = bmesh.new()
    hx, hz = SUP[0] / 2, SUP[1] / 2

    # Cuerpo de acero (la cara de abajo no se ve).
    alto = Y_CUERPO - Y_PATA
    piezas.caja(bm, (W, alto, Z_CLI - Z_VEND), (0, Y_PATA + alto / 2, (Z_CLI + Z_VEND) / 2),
                mat=ACERO, bisel=0.005, sin_abajo=True)
    # Plancha de hierro: exactamente la superficie de trabajo.
    # (2 mm más grande por lado: con el bisel, la cara de arriba mide justo SUP; el borde
    # metido debajo del respaldo y los costados no se ve)
    caras = piezas.caja(bm, (SUP[0] + 0.004, Y_SUP - Y_CUERPO + 0.002, SUP[1] + 0.004),
                        (0, (Y_SUP + Y_CUERPO - 0.002) / 2, 0), mat=OSCURO, bisel=0.002)
    eq.borrar_caras(bm, caras, (0, -1, 0))
    # Respaldo (cliente) y costados en cuña, de 1 cm, apoyados en el cuerpo.
    alto_g = Y_GUARDA - Y_CUERPO
    # (el respaldo va entre los costados, sin pisarse con ellos)
    caras = piezas.caja(bm, (SUP[0], alto_g, ESP_GUARDA),
                        (0, Y_CUERPO + alto_g / 2, hz + ESP_GUARDA / 2), mat=ACERO, bisel=0.003)
    eq.borrar_caras(bm, caras, (0, -1, 0))
    largo_c = hz + ESP_GUARDA - Z_LABIO
    for lado in (-1, 1):
        caras = piezas.caja(bm, (ESP_GUARDA, alto_g, largo_c),
                            (lado * (hx + ESP_GUARDA / 2), Y_CUERPO + alto_g / 2, Z_LABIO + largo_c / 2),
                            mat=ACERO, bisel=0.003)
        eq.borrar_caras(bm, caras, (0, -1, 0))
        eq.inclinar_arriba(caras, Y_CUERPO + 0.02, hz, -hz, BAJA_COSTADO)
    # Labio de la canaleta, al ras de la cara del vendedor.
    caras = piezas.caja(bm, (2 * (hx + ESP_GUARDA), Y_SUP + 0.003 - Y_CUERPO, 0.012),
                        (0, (Y_SUP + 0.003 + Y_CUERPO) / 2, Z_VEND + 0.006), mat=ACERO, bisel=0.003)
    eq.borrar_caras(bm, caras, (0, -1, 0))
    # Agujero del desagote (un disco oscuro en el piso de la canaleta).
    piezas.cilindro(bm, 0.008, 0.001, (DESAGOTE_X, Y_CUERPO + 0.0005, (Z_LABIO - hz) / 2), lados=12,
                    mat=NEGRO, tapas=(False, True))
    # Patas negras.
    for x in (-0.26, 0.26):
        for z in (Z_VEND + 0.04, Z_CLI - 0.04):
            piezas.cilindro(bm, 0.016, Y_PATA + 0.002, (x, (Y_PATA + 0.002) / 2, z), lados=12, mat=NEGRO,
                            tapas=(False, False))
    # Cara del vendedor: perillas, aro del piloto, cajón de grasa con su tirador.
    for x in PERILLAS_X:
        eq.perilla(bm, x, Y_CONTROLES, Z_VEND, NEGRO)
    eq.aro_piloto(bm, PILOTO_X, Y_CONTROLES, Z_VEND, ACERO)
    y_cajon = Y_CUERPO - 0.012 - CAJON[1] / 2
    caras = piezas.caja(bm, (CAJON[0], CAJON[1], CAJON[2] + 0.002),
                        (CAJON_X, y_cajon, Z_VEND - CAJON[2] / 2 + 0.002), mat=ACERO, bisel=0.004)
    eq.borrar_caras(bm, caras, (0, 0, 1))
    piezas.caja(bm, (0.06, 0.012, 0.012), (CAJON_X, y_cajon, Z_VEND - CAJON[2] - 0.004), mat=NEGRO,
                bisel=0.003)
    cuerpo = piezas.terminar(f"{ID}_cuerpo", bm, [acero, oscuro, negro])
    eq.e2.suavizar_hasta(cuerpo, 31)

    piloto = eq.lente_piloto(PILOTO_X, Y_CONTROLES, Z_VEND, piloto_m)
    sup = piezas.punto("punto_superficie", (0, Y_SUP, 0))
    col = eq.colision_cajas(ID, [
        ((W, Y_SUP, Z_CLI - Z_VEND), (0, Y_SUP / 2, (Z_CLI + Z_VEND) / 2)),
        ((SUP[0] + 2 * ESP_GUARDA, Y_GUARDA - Y_SUP, ESP_GUARDA), (0, (Y_GUARDA + Y_SUP) / 2, hz + ESP_GUARDA / 2)),
        ((ESP_GUARDA, Y_GUARDA - Y_SUP, largo_c), (-(hx + ESP_GUARDA / 2), (Y_GUARDA + Y_SUP) / 2, Z_LABIO + largo_c / 2)),
        ((ESP_GUARDA, Y_GUARDA - Y_SUP, largo_c), (hx + ESP_GUARDA / 2, (Y_GUARDA + Y_SUP) / 2, Z_LABIO + largo_c / 2)),
    ])
    raiz = piezas.raiz(ID, [cuerpo, piloto, sup, col])
    return {"raiz": raiz, "cuerpo": cuerpo, "piloto": piloto, "sup": sup, "col": col}


def revisar(m):
    vis = [m["cuerpo"], m["piloto"]]
    res = comun.revisar(vis, PRESUPUESTO, MEDIDAS, origen="base", max_materiales=6)
    sup = eq.chequeo_superficie(m["cuerpo"], OSCURO, SUP, Y_SUP, m["sup"])
    res = eq.reemplazar(res, "Origen", eq.chequeo_base(
        vis, "Origen en el centro de la superficie, a nivel del mostrador (las perillas corren la caja total)")
        if sup[0] else (False, "Origen: la superficie no está centrada"))
    res.insert(1, sup)
    return res


def hoja(m, revision):
    eq.hoja_equipo(ID, "plancha · superficie 0,56 × 0,36 m a 0,17 m · equipo de cocina",
                   m["raiz"], [m["cuerpo"], m["piloto"]], revision,
                   etiqueta_vendedor="Lado del vendedor: perillas, piloto, canaleta y cajón de grasa · día",
                   etiqueta_arriba="Arriba: superficie, respaldo y canaleta · día")


def main():
    eq.main_modelo(ID, FAMILIA, construir, revisar, hoja,
                   lambda m: [m["raiz"], m["cuerpo"], m["piloto"], m["sup"], m["col"]])


if __name__ == "__main__":
    main()
