"""Modelo: toldito fijo de frente (id `toldo_frente`, tres tamaños).

Genera, para cada tamaño (chico = barra_chica, mediano = barra_mediana, grande = carro_grande):
    arte/fuentes/accesorios/toldo_frente_<tamaño>.blend
    godot/modelos/accesorios/toldo_frente_<tamaño>.glb
y una sola hoja con los tres: docs/arte/revisiones/toldo_frente.jpg

Uso:
    python tools/blender/modelos/toldo_frente.py [--sin-hoja]

Forma: alerito rayado colgado de la mesada, del lado del cliente, sin parantes: una planchuela
de acero atornillada a la cara del frente justo debajo de la mesada, la lona que sale 0,34 m
hacia el cliente bajando 14° y un faldón con un festón por raya; dos tornapuntas de acero (en
las puntas) la sostienen desde la cara del carrito. Decora el frente como en los carritos de
plaza y no tapa nada: queda abajo del mostrador y arriba del telón (que va de 0,31 a 0,73 m
en el mismo anclaje, pegado a la cara: la lona está 0,34 m adelante y más arriba).

Medidas (relativas al anclaje `frente`): ancho de la base; de y = alto_mostrador − 0,30
(tornapuntas) a alto_mostrador − 0,05 (planchuela); fondo de la cara del carrito a 0,35.

Colores (guía 4.2, regla 5): superficie 0 = rayas pares (la primera desde −X), 1 = impares, en
las tres piezas. El .glb trae rojo y crema; liso = el mismo material en las dos.

Objetos (hijos del Empty `toldo_frente_<tamaño>`): pieza_punta_izq, pieza_tramo, pieza_punta_der
(superficies 0 raya A, 1 raya B, 2 acero; el tramo es un número entero de módulos de 2 rayas:
se repite). Sin colisión: es lona y está pegado al carrito (la base ya tiene la suya).
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

ID = "toldo_frente"
PRESUPUESTO = 400            # lista (el chico); mediano y grande, proporcional al ancho
SALE = 0.34                  # hasta la cara de adentro del faldón
PENDIENTE = 0.25
FALDON, FESTON = 0.08, 0.025
BARRA = (0.03, 0.035)        # planchuela: alto, fondo


def construir(tam):
    b = t.base(tam)
    r = t.rayas(b)
    rojo, crema, acero = comun.cargar_materiales("M_RojoAcento", "M_BlancoCrema", "M_Acero")
    # En el carro grande, los parantes de acero del frente sobresalen 8 mm de la cara.
    z0 = -0.01 + (0.008 if b.grande else 0.0)
    yb = b.a - 0.065                                   # mitad de la planchuela
    zb = z0 + BARRA[1]
    yf = yb - PENDIENTE * (SALE - zb)
    bm = bmesh.new()
    t.lona_rayada(bm, r, (yb - t.LONA / 2, zb), (yf, SALE), FALDON, FESTON, canto_atras=False)
    piezas.caja(bm, (b.w - 0.02, BARRA[0], BARRA[1]), (0, yb, z0 + BARRA[1] / 2), mat=2, bisel=0.006)
    y_pie = b.a - 0.30
    for sx in (-1, 1):
        x = sx * (b.w / 2 - 0.07)
        t.varilla(bm, (x, y_pie, z0 + 0.004), (x, yf - 0.01, SALE - 0.04), 0.008, lados=8, mat=2)
        piezas.caja(bm, (0.035, 0.05, 0.008), (x, y_pie + 0.005, z0 + 0.004), mat=2)   # plaquita
    piezas3 = t.tres_piezas(bm, r.corte, [rojo, crema, acero])
    raiz = t.raiz_modelo(ID, tam, piezas3)
    return {
        "raiz": raiz, "piezas": piezas3, "visibles": piezas3, "exportar": [raiz] + piezas3,
        "b": b, "r": r, "presup": t.presupuesto(PRESUPUESTO, b, tope=1000),
        "esperado": ((-b.w / 2, b.w / 2), (y_pie - 0.02, yb + BARRA[0] / 2), (z0, SALE + t.LONA)),
        "desc": "alero %.2f × %.2f (%d rayas de %.3f), colgado de la mesada" % (b.w, SALE, r.n, r.s),
        "apoyo_z": z0, "origen_txt": "la planchuela apoya en la cara del carrito (z = %.3f)" % z0,
        "lona_min": 0.70, "lona_txt": "abajo de la mesada y arriba del telón: no tapa el mostrador",
        "con_techo": False,
    }


def revisar(m):
    return t.revisar_toldo(m)


def hoja(revision):
    rojo, crema, azul = comun.cargar_materiales("M_RojoAcento", "M_BlancoCrema", "M_AzulAcento")
    t.hoja_toldo(ID, construir, "toldo_frente · chico / mediano / grande: 1,6 / 2,4 / 3,4 m · "
                 "colgado de la mesada, sale 0,35 m", revision,
                 [("rojo y crema (el .glb)", rojo, crema), ("azul y crema", azul, crema),
                  ("liso rojo", rojo, rojo)], telon=True)


if __name__ == "__main__":
    t.main(ID, construir, revisar, hoja)
