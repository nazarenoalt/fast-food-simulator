"""Modelo: techo curvo de chapa (id `techo_curvo`, tres tamaños).

Genera, para cada tamaño (chico = barra_chica, mediano = barra_mediana, grande = carro_grande):
    arte/fuentes/accesorios/techo_curvo_<tamaño>.blend
    godot/modelos/accesorios/techo_curvo_<tamaño>.glb
y una sola hoja con los tres: docs/arte/revisiones/techo_curvo.jpg

Uso:
    python tools/blender/modelos/techo_curvo.py [--sin-hoja]

Forma: estilo food truck clásico. Chapa de 2,5 cm curvada en arco de círculo (8 tramos, eje a lo
largo de X: del vendedor al cliente sube y baja), con el borde pintado y un arco pintado de 5 cm
debajo de cada punta (M_PinturaCarrito: el juego los puede teñir del color del carrito); 4 caños
de acero parados en las esquinas de la mesada y dos vigas de alero. Un colgador por cada luz_N
de la base (`pieza_colgadores` + `punto_foco_N`): el foco_calido, en luz_N como hoy, queda
colgado del techo.

Medidas (relativas al anclaje `techo`): ancho = ancho de la base + 0,10; fondo = profundidad +
0,40, centrado sobre la mesada; aleros a 2,16 m (los arcos pintados bajan hasta 2,12); la flecha
del arco crece con el fondo (0,16 / 0,17 / 0,23 m): arriba a 2,35 / 2,36 / 2,42 m.

Objetos (hijos del Empty `techo_curvo_<tamaño>`): pieza_punta_izq, pieza_tramo, pieza_punta_der
(superficies 0 chapa, 1 pintura, 2 acero; el tramo es estirable en X), pieza_colgadores,
punto_foco_N y `techo_curvo_<tamaño>-colonly` (los 4 caños).
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402,F401  (antes que bmesh)
import bmesh  # noqa: E402

import comun  # noqa: E402
import _techo as t  # noqa: E402

ID = "techo_curvo"
PRESUPUESTO = 1500
ALERO = 2.16
CHAPA = 0.025
ARCO = 0.05                  # alto del arco pintado de las puntas
TRAMOS = 8                   # arco de ≈ 70°: 8 tramos ≈ 32 lados por vuelta (guía 3.2)


def construir(tam):
    b = t.base(tam)
    g = t.geometria_techo(b, extra=0.40)
    oscuro, pintura, acero = comun.cargar_materiales("M_MetalOscuro", "M_PinturaCarrito", "M_Acero")
    h = g.D / 2
    s = round(0.16 * g.D / 1.1, 3)                     # flecha del arco
    R = (h * h + s * s) / (2 * s)
    cy = ALERO + s - R
    f0 = math.asin(h / R)
    angulos = [-f0 + 2 * f0 * i / TRAMOS for i in range(TRAMOS + 1)]

    def arco(radio, angs):
        return [(cy + radio * math.cos(a), g.zc + radio * math.sin(a)) for a in angs]

    def abajo(z):
        return cy + math.sqrt(R * R - (z - g.zc) ** 2)

    bm = bmesh.new()
    perfil = arco(R, angulos) + arco(R + CHAPA, angulos[::-1])
    caras = t.prisma_x(bm, perfil, -g.W / 2, g.W / 2, bisel=t.BISEL)
    t.pintar(caras, lambda n, c: 0 if abs(n.y) > 0.75 else 1)
    # Arcos pintados debajo de las puntas.
    banda = arco(R - 0.002, angulos) + arco(R - ARCO, angulos[::-1])
    for sx in (-1, 1):
        x0, x1 = sorted((sx * (g.W / 2 - 0.035), sx * (g.W / 2 - 0.012)))
        t.prisma_x(bm, banda, x0, x1, bisel=0.005, mat=1)
    col = t.canos(bm, g, lambda z: abajo(z) - t.VIGA, 2)
    t.vigas_x(bm, g, abajo, 2)
    piezas3 = t.tres_piezas(bm, g.corte, [oscuro, pintura, acero])

    colg, puntos_foco = t.colgadores(g, abajo, acero)
    choque = t.colision(f"{ID}_{tam}", cilindros=col)
    hijos = piezas3 + [colg] + puntos_foco + [choque]
    raiz = t.raiz_modelo(ID, tam, hijos)
    dz = (R + CHAPA) * math.sin(f0)
    return {
        "raiz": raiz, "piezas": piezas3, "visibles": piezas3 + [colg],
        "exportar": [raiz] + hijos, "g": g, "b": b, "puntos_foco": puntos_foco,
        "presup": PRESUPUESTO, "tol": 0.006,      # el bisel come 4 mm del canto de los aleros
        "esperado": ((-g.W / 2, g.W / 2), (b.a, ALERO + s + CHAPA), (g.zc - dz, g.zc + dz)),
        "desc": "techo %.2f × %.2f, aleros a %.2f, flecha %.2f (radio %.2f)" % (g.W, g.D, ALERO, s, R),
    }


def hoja(revision):
    t.hoja_techo(ID, construir, "techo_curvo · chico / mediano / grande: 1,70 / 2,50 / 3,50 m de "
                 "ancho · aleros a 2,16 m, chapa en arco", revision)


if __name__ == "__main__":
    t.main(ID, construir, t.revisar_techo, hoja)
