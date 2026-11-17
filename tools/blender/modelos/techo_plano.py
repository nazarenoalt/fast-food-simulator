"""Modelo: techo plano de chapa sobre 4 caños (id `techo_plano`, tres tamaños).

Genera, para cada tamaño (chico = barra_chica, mediano = barra_mediana, grande = carro_grande):
    arte/fuentes/accesorios/techo_plano_<tamaño>.blend
    godot/modelos/accesorios/techo_plano_<tamaño>.glb
y una sola hoja con los tres: docs/arte/revisiones/techo_plano.jpg

Uso:
    python tools/blender/modelos/techo_plano.py [--sin-hoja]

Forma (como el carrito de la foto de referencia): chapa plana de 4 cm (M_MetalOscuro arriba y
abajo) con el borde pintado y un faldón de 16 cm al frente (M_PinturaCarrito: el juego lo puede
teñir del color del carrito), sobre 4 caños de acero parados en las esquinas de la mesada (con
brida) y dos vigas de caño cuadrado. Debajo, del lado del cliente, un tubo de luz (`pieza_luz`,
M_LuzCalida, con `punto_luz`) tapado por el faldón, y un colgador por cada luz_N de la base
(`pieza_colgadores` + `punto_foco_N`): el foco_calido, puesto en luz_N como hoy, queda colgado
del techo.

Medidas (relativas al anclaje `techo`, ver _techo.geometria_techo): ancho = ancho de la base +
0,10; fondo = profundidad + 0,34, centrado sobre la mesada; chapa de 2,24 a 2,28 m y el faldón
baja hasta 2,12 m (alero ≥ 2,10). Los caños arrancan en la mesada (y = alto_mostrador).

Objetos (hijos del Empty `techo_plano_<tamaño>`): pieza_punta_izq, pieza_tramo, pieza_punta_der
(superficies: 0 chapa, 1 borde pintado, 2 acero; el tramo es estirable en X), pieza_luz,
punto_luz, pieza_colgadores, punto_foco_N y `techo_plano_<tamaño>-colonly` (los 4 caños).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402,F401  (antes que bmesh)
import bmesh  # noqa: E402

import comun  # noqa: E402
import piezas  # noqa: E402
import _techo as t  # noqa: E402

ID = "techo_plano"
PRESUPUESTO = 1500           # lista de modelos (los tris no crecen con el ancho)
CHAPA_ABAJO, CHAPA_ARRIBA = 2.24, 2.28
FALDON_ABAJO, FALDON_ESP = 2.12, 0.02


def construir(tam):
    b = t.base(tam)
    g = t.geometria_techo(b, extra=0.34)
    oscuro, pintura, acero, luz = comun.cargar_materiales(
        "M_MetalOscuro", "M_PinturaCarrito", "M_Acero", "M_LuzCalida")
    bm = bmesh.new()
    # Chapa + faldón: un solo perfil en L extruido a lo largo de X.
    perfil = [(CHAPA_ABAJO, g.zb), (CHAPA_ARRIBA, g.zb), (CHAPA_ARRIBA, g.zf), (FALDON_ABAJO, g.zf),
              (FALDON_ABAJO, g.zf - FALDON_ESP), (CHAPA_ABAJO, g.zf - FALDON_ESP)]
    caras = t.prisma_x(bm, perfil, -g.W / 2, g.W / 2, bisel=t.BISEL)
    t.pintar(caras, lambda n, c: 0 if abs(n.y) > 0.75 and c.y > CHAPA_ABAJO - 0.005 else 1)
    # Estructura de acero.
    col = t.canos(bm, g, lambda z: CHAPA_ABAJO - t.VIGA, 2)
    t.vigas_x(bm, g, lambda z: CHAPA_ABAJO, 2)
    zt = g.zpf - 0.075                                        # tubo de luz, detrás del faldón
    piezas.caja(bm, (g.W - 0.36, 0.025, 0.05), (0, CHAPA_ABAJO - 0.0125, zt), mat=2, bisel=0.005)
    for sx in (-1, 1):
        piezas.caja(bm, (0.02, 0.03, 0.03), (sx * (g.W / 2 - 0.20), CHAPA_ABAJO - 0.04, zt), mat=2,
                    bisel=0.004)
    piezas3 = t.tres_piezas(bm, g.corte, [oscuro, pintura, acero])

    bm = bmesh.new()
    y_tubo = CHAPA_ABAJO - 0.041
    piezas.cilindro(bm, 0.014, g.W - 0.42, (0, y_tubo, zt), eje="x", lados=8)
    tubo = t.objeto("pieza_luz", bm, [luz], sombreado="suave", recalcular=True)
    p_luz = piezas.punto("punto_luz", (0, y_tubo, zt))
    colg, puntos_foco = t.colgadores(g, lambda z: CHAPA_ABAJO, acero)
    choque = t.colision(f"{ID}_{tam}", cilindros=col)

    hijos = piezas3 + [tubo, p_luz, colg] + puntos_foco + [choque]
    raiz = t.raiz_modelo(ID, tam, hijos)
    return {
        "raiz": raiz, "piezas": piezas3, "visibles": piezas3 + [tubo, colg],
        "exportar": [raiz] + hijos, "g": g, "b": b, "puntos_foco": puntos_foco,
        "presup": PRESUPUESTO,
        "esperado": ((-g.W / 2, g.W / 2), (b.a, CHAPA_ARRIBA), (g.zb, g.zf)),
        "desc": "techo %.2f × %.2f, de la mesada (%.2f) a la chapa" % (g.W, g.D, b.a),
    }


def revisar(m):
    res = t.revisar_techo(m)
    luz = m["exportar"][[o.name for o in m["exportar"]].index("punto_luz")]
    tubo = next(o for o in m["visibles"] if o.name.startswith("pieza_luz"))
    centro = sum((v for v in t.verts_g([tubo])), t.Vector()) / len(tubo.data.vertices)
    ok = (luz.matrix_world.translation - piezas.g2b(centro)).length < 1e-3
    res.append((ok, "pieza_luz (tubo, M_LuzCalida) con punto_luz en el centro, tapado por el faldón"))
    return res


def hoja(revision):
    t.hoja_techo(ID, construir, "techo_plano · chico / mediano / grande: 1,70 / 2,50 / 3,50 m de "
                 "ancho · chapa a 2,28 m, faldón hasta 2,12 m", revision)


if __name__ == "__main__":
    t.main(ID, construir, revisar, hoja)
