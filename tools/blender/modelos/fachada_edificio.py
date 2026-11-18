"""Modelo: fachada de edificio de departamentos (id `fachada_edificio`, familia `ciudad`).

Genera:
    arte/fuentes/ciudad/fachada_edificio.blend
    godot/modelos/ciudad/fachada_edificio.glb
    docs/arte/revisiones/fachada_edificio.jpg

Uso:
    python tools/blender/modelos/fachada_edificio.py [--sin-hoja]

Edificio de departamentos de 6 plantas (planta baja y 5 pisos; el juego arma de 2 a 7), en
el ancho de referencia de 9 m. Ver _fachada.py para los módulos, los vidrios y el origen.

Planta baja revestida en piedra (M_Baldosa, no toma el color del edificio): puerta de
entrada de hierro y vidrio en la columna 0 (la del código), una ventana con reja y el
portón de la cochera (columnas 2 y 3).
Pisos (pieza_piso_1 a pieza_piso_5, iguales): cuatro puertas-ventana en las columnas del
código (1,1 de ancho, de 0,15 a 2,2 sobre el piso) y dos balcones corridos de 4,1 × 1,0, cada
uno para dos ventanas, con losa y antepecho de 0,5 m (M_BlancoCrema) y baranda de hierro arriba (pasamanos y
parantes, hasta 0,92 m).
Cornisa: un pretil liso de 0,35 m (edificio moderno, sin corona).

Materiales: muro M_Piedra (el juego lo cambia), balcones y molduras M_BlancoCrema,
revestimiento de la planta baja M_Baldosa, herrería y vidrios oscuros M_Hierro, vidrios que
se prenden M_LuzCalida.

Medidas: 9,00 × 18,95 × 1,25 (lista ≈ 9 × 18 × 1). Alto = 3,6 + 5 × 3,0 + 0,35.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402, F401  (antes que bmesh)
import bmesh  # noqa: E402

import _ciudad as ciudad  # noqa: E402
import _fachada as fa  # noqa: E402
from _fachada import BISEL, CLARO, HIERRO, MURO, OSCURO, PROF  # noqa: E402
import comun  # noqa: E402

P = {
    "id": "fachada_edificio",
    # El lugar de la carpintería (3) no se usa: la herrería es toda de hierro.
    "materiales": ("M_Piedra", "M_BlancoCrema", "M_Baldosa", "M_Madera", "M_Hierro", "M_LuzCalida"),
    "pisos": 6,
    "luz": [False, True, False, False,
            True, False, False, True,
            False, False, True, False,
            False, True, False, False,
            True, False, False, True],
}
MEDIDAS = (9.0, 18.95, 1.25)
ENTRADA = (1.6, 2.7)
COCHERA = (0.85, 3.65, 0.0, 2.4)
VENTANA = (0.15, 2.2)          # puerta-ventana del balcón, sobre el piso
BALCON = (4.1, 1.0)            # ancho × salida
LOSA = (-0.05, 0.13)           # de y a y (sobre el piso del módulo)
BARANDA = 0.92                 # alto de la baranda sobre la losa
MURETE = 0.5                   # parte llena de la baranda


def planta_baja(f):
    bm = bmesh.new()
    xe, xv = fa.col_x(0), fa.col_x(1)
    vanos = [(xe - ENTRADA[0] / 2, xe + ENTRADA[0] / 2, 0.0, ENTRADA[1]),
             (xv - 0.55, xv + 0.55, 0.95, 2.45),
             (*COCHERA, 0.15)]
    # El paño de la planta baja es de piedra (OSCURO), no del color del edificio.
    fondos = ciudad.muro_con_vanos(bm, -fa.ANCHO / 2, fa.ANCHO / 2, 0, fa.ALTO_PB, vanos, PROF, OSCURO,
                                   espesor=fa.ESPESOR)
    fa.puerta_hierro(bm, f, xe, ENTRADA[0], ENTRADA[1], fondos[0][4])
    xa, xb, ya, yb, zf = fondos[1]
    f.vidrio(xa, xb, ya, yb, zf)
    fa.molduras_ventana(bm, xv, ya, yb, jambas=False)
    fa.reja(bm, xv, ya, yb)
    # Portón de la cochera: chapa con tres juntas y dintel claro.
    xa, xb, ya, yb, zf = fondos[2]
    ciudad.rectangulo(bm, xa, xb, ya, yb, zf, HIERRO)
    for k in (1, 2, 3):
        ciudad.caja_frente(bm, (xb - xa, 0.04, 0.02), ((xa + xb) / 2, yb * k / 4, zf + 0.01), HIERRO)
    ciudad.caja_frente(bm, (xb - xa + 0.3, 0.2, 0.09), ((xa + xb) / 2, yb + 0.1, 0.045), CLARO, fa.BISEL_FINO)
    # Losa que separa la planta baja (de punta a punta, debajo de los balcones del primer piso).
    ciudad.caja_frente(bm, (fa.ANCHO, 0.18, 0.1), (0, fa.ALTO_PB - 0.14, 0.05), CLARO, fa.BISEL_FINO)
    f.objeto("pieza_planta_baja", bm, modulo=True)


def piso(bm, f, n):
    vanos = [(fa.col_x(c) - 0.55, fa.col_x(c) + 0.55, *VENTANA) for c in range(fa.COLUMNAS)]
    fondos = ciudad.muro_con_vanos(bm, -fa.ANCHO / 2, fa.ANCHO / 2, 0, fa.ALTO_PISO, vanos, PROF, MURO,
                                   espesor=fa.ESPESOR)
    ancho, sale = BALCON
    alto = LOSA[1] + BARANDA
    g = 0.08
    for xc in (-fa.PASO, fa.PASO):          # un balcón cada dos columnas
        ciudad.caja_frente(bm, (ancho, LOSA[1] - LOSA[0], sale), (xc, sum(LOSA) / 2, sale / 2), CLARO)
        # Antepecho lleno hasta la mitad y baranda de hierro arriba (pasamanos y parantes).
        ciudad.caja_frente(bm, (ancho, MURETE, g), (xc, LOSA[1] + MURETE / 2, sale - g / 2), CLARO,
                           sin_abajo=True)
        for s in (-1, 1):
            ciudad.caja_frente(bm, (g, MURETE, sale - g), (xc + s * (ancho - g) / 2, LOSA[1] + MURETE / 2,
                                                            (sale - g) / 2), CLARO, sin_abajo=True)
        zp, yp, gp = sale - g / 2, alto - 0.025, 0.05
        for s in (-1, 1):
            xs = xc + s * (ancho - g) / 2
            ciudad.barra(bm, (xs, yp, 0.0), (xs, yp, zp + gp / 2), gp, HIERRO)
        ciudad.barra(bm, (xc - (ancho - g) / 2 - gp / 2, yp, zp), (xc + (ancho - g) / 2 + gp / 2, yp, zp), gp,
                     HIERRO)
        for px in (-(ancho - g) / 2, 0.0, (ancho - g) / 2):
            ciudad.barra(bm, (xc + px, LOSA[1] + MURETE, zp), (xc + px, yp - gp / 2, zp), 0.04, HIERRO)
    return fondos


def cornisa(bm):
    ciudad.caja_frente(bm, (fa.ANCHO, fa.CORNISA, fa.ESPESOR + 0.06),
                       (0, fa.CORNISA / 2, (0.06 - fa.ESPESOR) / 2), CLARO, BISEL)


def construir():
    f = fa.Fachada(P)
    planta_baja(f)
    f.pisos(piso)
    f.cornisa(cornisa)
    f.terminar_vidrios()
    f.colision()
    f.raiz()
    return f


def main():
    comun.escena_vacia()
    f = construir()
    fa.main(f, MEDIDAS, ciudad.m("fachada_edificio · 9 × 18.95 × 1.25 m · departamentos (PB + 5 pisos) · "
                                 "fachada"))


if __name__ == "__main__":
    main()
