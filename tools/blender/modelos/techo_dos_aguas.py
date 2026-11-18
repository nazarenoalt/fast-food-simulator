"""Modelo: techo de chapa a dos aguas (id `techo_dos_aguas`, tres tamaños).

Genera, para cada tamaño (chico = barra_chica, mediano = barra_mediana, grande = carro_grande):
    arte/fuentes/accesorios/techo_dos_aguas_<tamaño>.blend
    godot/modelos/accesorios/techo_dos_aguas_<tamaño>.glb
y una sola hoja con los tres: docs/arte/revisiones/techo_dos_aguas.jpg

Uso:
    python tools/blender/modelos/techo_dos_aguas.py [--sin-hoja]

Forma: puesto de feria. Chapa de 3 cm a dos aguas (25°, cumbrera a lo largo de X) con alero
hacia el cliente y hacia el vendedor, cumbrera pintada arriba y dos frontones pintados en las
puntas (M_PinturaCarrito: el juego los puede teñir del color del carrito); abajo, 4 caños de
acero parados en las esquinas de la mesada, dos vigas de alero y la viga de cumbrera de
frontón a frontón. Un colgador por cada luz_N de la base (`pieza_colgadores` + `punto_foco_N`):
el foco_calido, en luz_N como hoy, queda colgado del techo.

Medidas (relativas al anclaje `techo`): ancho = ancho de la base + 0,10; fondo = profundidad +
0,40, centrado sobre la mesada; aleros a 2,14 m; la cumbrera a 2,45 / 2,48 / 2,57 m
(chico / mediano / grande: sube con el fondo). Los caños arrancan en la mesada.

Objetos (hijos del Empty `techo_dos_aguas_<tamaño>`): pieza_punta_izq, pieza_tramo,
pieza_punta_der (superficies 0 chapa, 1 pintura, 2 acero; el tramo es estirable en X),
pieza_colgadores, punto_foco_N y `techo_dos_aguas_<tamaño>-colonly` (los 4 caños).
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402,F401  (antes que bmesh)
import bmesh  # noqa: E402

import comun  # noqa: E402
import piezas  # noqa: E402
import _techo as t  # noqa: E402

ID = "techo_dos_aguas"
PRESUPUESTO = 1500
ALERO = 2.14
PENDIENTE = math.tan(math.radians(25))
CHAPA = 0.03
FRONTON_ESP = 0.015


def construir(tam):
    b = t.base(tam)
    g = t.geometria_techo(b, extra=0.40)
    oscuro, pintura, acero = comun.cargar_materiales("M_MetalOscuro", "M_PinturaCarrito", "M_Acero")
    h = g.D / 2
    tv = CHAPA / math.cos(math.atan(PENDIENTE))

    def abajo(z):                                       # cara de abajo de la chapa
        return ALERO + (h - abs(z - g.zc)) * PENDIENTE

    yr = abajo(g.zc)
    bm = bmesh.new()
    perfil = [(ALERO, g.zb), (ALERO + tv, g.zb), (yr + tv, g.zc), (ALERO + tv, g.zf), (ALERO, g.zf),
              (yr, g.zc)]
    caras = t.prisma_x(bm, perfil, -g.W / 2, g.W / 2, bisel=t.BISEL)
    t.pintar(caras, lambda n, c: 0 if abs(n.y) > 0.75 else 1)
    # Cumbrera pintada: un cheurón de 2 cm apoyado sobre la chapa.
    d = 0.07
    cumbrera = [(abajo(g.zc - d) + tv + 0.003, g.zc - d), (yr + tv + 0.023, g.zc),
                (abajo(g.zc + d) + tv + 0.003, g.zc + d), (yr + tv + 0.003, g.zc)]
    t.prisma_x(bm, cumbrera, -g.W / 2 - 0.005, g.W / 2 + 0.005, mat=1)
    # Frontones pintados en las puntas, debajo de la chapa, entre las vigas de alero.
    y_viga = abajo(g.zpf)
    yb = y_viga - t.VIGA
    fronton = [(yb, g.zpb), (abajo(g.zpb), g.zpb), (yr, g.zc), (abajo(g.zpf), g.zpf), (yb, g.zpf)]
    xf = g.W / 2 - 0.04
    for sx in (-1, 1):
        x0, x1 = sorted((sx * (xf - FRONTON_ESP / 2), sx * (xf + FRONTON_ESP / 2)))
        t.prisma_x(bm, fronton, x0, x1, mat=1)
    # Estructura de acero.
    col = t.canos(bm, g, lambda z: abajo(z) - t.VIGA, 2)
    t.vigas_x(bm, g, abajo, 2)
    largo = 2 * (xf - FRONTON_ESP / 2)
    piezas.caja(bm, (largo, t.VIGA, t.VIGA), (0, yr - t.VIGA / 2 - 0.004, g.zc), mat=2, bisel=0.005)
    piezas3 = t.tres_piezas(bm, g.corte, [oscuro, pintura, acero])

    colg, puntos_foco = t.colgadores(g, abajo, acero)
    choque = t.colision(f"{ID}_{tam}", cilindros=col)
    hijos = piezas3 + [colg] + puntos_foco + [choque]
    raiz = t.raiz_modelo(ID, tam, hijos)
    tope = yr + tv + 0.023
    return {
        "raiz": raiz, "piezas": piezas3, "visibles": piezas3 + [colg],
        "exportar": [raiz] + hijos, "g": g, "b": b, "puntos_foco": puntos_foco,
        "presup": PRESUPUESTO,
        "esperado": ((-g.W / 2 - 0.005, g.W / 2 + 0.005), (b.a, tope), (g.zb, g.zf)),
        "desc": "techo %.2f × %.2f, aleros a %.2f, cumbrera a %.2f" % (g.W, g.D, ALERO, tope),
    }


def hoja(revision):
    t.hoja_techo(ID, construir, "techo_dos_aguas · chico / mediano / grande: 1,70 / 2,50 / 3,50 m "
                 "de ancho · aleros a 2,14 m, chapa a 25°", revision)


if __name__ == "__main__":
    t.main(ID, construir, t.revisar_techo, hoja)
