"""Modelo: fachada de casa baja de barrio (id `fachada_casa_a`, familia `ciudad`).

Genera:
    arte/fuentes/ciudad/fachada_casa_a.blend
    godot/modelos/ciudad/fachada_casa_a.glb
    docs/arte/revisiones/fachada_casa_a.jpg

Uso:
    python tools/blender/modelos/fachada_casa_a.py [--sin-hoja]

Casa porteña de dos plantas (el edificio más bajo que arma el juego: 2 plantas), en el ancho
de referencia de 9 m. Ver _fachada.py para los módulos, los vidrios y el origen.

Planta baja: puerta de madera de dos hojas con tableros y banderola, en la columna 0 (donde
el código pone la puerta: a 1,2 m del borde izquierdo), con jambas y dintel claros; tres
ventanas con alféizar, guardapolvo y reja saliente de hierro; zócalo de 0,5 m; moldura a 3,6.
Piso: cuatro ventanas (las del código) con molduras y postigos de madera abiertos.
Cornisa: corona saliente y pretil, 0,35 m.

Materiales: muro M_Camino (el juego lo cambia), molduras M_BlancoCrema, zócalo M_Piedra,
puerta y postigos M_Madera, rejas y vidrios oscuros M_Hierro, vidrios que se prenden
M_LuzCalida.

Medidas: 9,00 × 6,95 × 0,55 (lista ≈ 9 × 6 × 1). Alto = 3,6 + 3,0 + cornisa 0,35.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402, F401  (antes que bmesh)
import bmesh  # noqa: E402

import _ciudad as ciudad  # noqa: E402
import _fachada as fa  # noqa: E402
from _fachada import CARPINTERIA, MURO, PROF  # noqa: E402
import comun  # noqa: E402

P = {
    "id": "fachada_casa_a",
    "materiales": ("M_Camino", "M_BlancoCrema", "M_Piedra", "M_Madera", "M_Hierro", "M_LuzCalida"),
    "pisos": 2,
    "luz": [False, True, False, False],
}
MEDIDAS = (9.0, 6.95, 0.55)
PUERTA = (1.2, 2.6)
VENTANA_PB = (0.95, 2.45)


def planta_baja(f):
    bm = bmesh.new()
    xp = fa.col_x(0)
    vanos = [(xp - PUERTA[0] / 2, xp + PUERTA[0] / 2, 0.0, PUERTA[1])]
    vanos += [(fa.col_x(c) - 0.55, fa.col_x(c) + 0.55, *VENTANA_PB) for c in (1, 2, 3)]
    fondos = ciudad.muro_con_vanos(bm, -fa.ANCHO / 2, fa.ANCHO / 2, 0, fa.ALTO_PB, vanos, PROF, MURO,
                                   espesor=fa.ESPESOR)
    fa.puerta_madera(bm, f, xp, PUERTA[0], PUERTA[1], fondos[0][4])
    for xa, xb, ya, yb, zf in fondos[1:]:
        x = (xa + xb) / 2
        f.vidrio(xa, xb, ya, yb, zf)
        fa.molduras_ventana(bm, x, ya, yb)
        fa.reja(bm, x, ya, yb)
    xa, xb = vanos[0][0] - 0.16, vanos[0][1] + 0.16
    fa.zocalo(bm, [(-fa.ANCHO / 2, xa), (xb, fa.ANCHO / 2)])
    fa.moldura_pb(bm)
    f.objeto("pieza_planta_baja", bm, modulo=True)


def piso(bm, f, n):
    vanos = [(fa.col_x(c) - 0.55, fa.col_x(c) + 0.55, *fa.ventana_y()) for c in range(fa.COLUMNAS)]
    fondos = ciudad.muro_con_vanos(bm, -fa.ANCHO / 2, fa.ANCHO / 2, 0, fa.ALTO_PISO, vanos, PROF, MURO,
                                   espesor=fa.ESPESOR)
    for xa, xb, ya, yb, zf in fondos:
        x = (xa + xb) / 2
        fa.molduras_ventana(bm, x, ya, yb)
        for s in (-1, 1):  # postigos abiertos contra la pared
            ciudad.caja_frente(bm, (0.40, yb - ya, 0.03), (x + s * 0.865, (ya + yb) / 2, 0.015),
                               CARPINTERIA)
    return fondos


def construir():
    f = fa.Fachada(P)
    planta_baja(f)
    f.pisos(piso)
    f.cornisa(fa.cornisa_casa)
    f.terminar_vidrios()
    f.colision()
    f.raiz()
    return f


def main():
    comun.escena_vacia()
    f = construir()
    fa.main(f, MEDIDAS, ciudad.m("fachada_casa_a · 9 × 6.95 × 0.55 m · casa baja (PB + 1 piso) · "
                                 "fachada"))


if __name__ == "__main__":
    main()
