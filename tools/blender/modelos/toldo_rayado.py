"""Modelo: toldo rebatible rayado (id `toldo_rayado`, tres tamaños).

Genera, para cada tamaño (chico = barra_chica, mediano = barra_mediana, grande = carro_grande):
    arte/fuentes/accesorios/toldo_rayado_<tamaño>.blend
    godot/modelos/accesorios/toldo_rayado_<tamaño>.glb
y una sola hoja con los tres: docs/arte/revisiones/toldo_rayado.jpg

Uso:
    python tools/blender/modelos/toldo_rayado.py [--sin-hoja]

Forma: toldo de brazos, como el de un kiosco. Dos mástiles de caño agarrados con dos grapas
negras a la cara del frente del carrito (abajo de la mesada, afuera del telón, arriba de las
ruedas) sostienen la barra de atrás a 2,07 m; la lona rayada baja hacia el cliente (8,5°)
hasta la barra de carga, 72 cm adelante, y termina en un faldón con un festón por raya. Dos
brazos articulados (codo negro) van de los mástiles a la barra de carga. La lona tiene dos
caras y 1,2 cm de espesor, sin bisel (guía 3.3).

Medidas (relativas al anclaje `frente`): lona del ancho de la base; de los mástiles (desde
y = 0,40) a la lona (2,10 m); fondo de z = −0,01 (cara del carrito) a 0,81. La lona más baja
(punta de los festones) queda a 1,84 m: no tapa el mostrador ni la cara del vendedor, y entra
debajo del faldón de los techos (ver _techo.revisar_toldo).

Colores (guía 4.2, regla 5): superficie 0 = rayas pares (la primera desde −X), superficie 1 =
impares, en las tres piezas. El .glb trae rojo y crema; liso = el mismo material en las dos.

Objetos (hijos del Empty `toldo_rayado_<tamaño>`): pieza_punta_izq, pieza_tramo, pieza_punta_der
(superficies 0 raya A, 1 raya B, 2 acero, 3 plástico negro; el tramo no tiene negro y es un
número entero de módulos de 2 rayas: se repite) y `toldo_rayado_<tamaño>-colonly` (mástiles).
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

ID = "toldo_rayado"
PRESUPUESTO = 800            # lista (el chico); mediano y grande, proporcional al ancho
Z_MASTIL = 0.08              # delante del borde de la mesada (z 0,04), a 9 cm de los caños de techo
Y_BARRA = 2.07               # barra de atrás
FONDO = 0.72                 # de la barra de atrás a la de carga
PENDIENTE = 0.15
FALDON, FESTON = 0.10, 0.035
R_BARRA = 0.014


def construir(tam):
    b = t.base(tam)
    r = t.rayas(b)
    xm = b.w / 2 - 0.04
    rojo, crema, acero, negro = comun.cargar_materiales(
        "M_RojoAcento", "M_BlancoCrema", "M_Acero", "M_PlasticoNegro")
    yb = Y_BARRA + R_BARRA                      # la lona apoya sobre la barra de atrás
    zf = Z_MASTIL + FONDO
    yf = yb - PENDIENTE * FONDO
    bm = bmesh.new()
    t.lona_rayada(bm, r, (yb, Z_MASTIL), (yf, zf), FALDON, FESTON)
    col = t.mastiles(bm, b, xm, Z_MASTIL, Y_BARRA, 2, 3)
    for y, z in ((Y_BARRA, Z_MASTIL), (yf - R_BARRA - 0.001, zf - R_BARRA - 0.001)):
        piezas.cilindro(bm, R_BARRA, b.w - 0.01, (0, y, z), eje="x", lados=8, mat=2)
    for sx in (-1, 1):
        x = sx * xm
        frente = (x, yf - R_BARRA - 0.001, zf - R_BARRA - 0.001)
        t.brazo(bm, (x, 1.80, Z_MASTIL), frente, 0.05, 2, 3)
    piezas3 = t.tres_piezas(bm, r.corte, [rojo, crema, acero, negro])
    choque = t.colision(f"{ID}_{tam}", cilindros=col)
    hijos = piezas3 + [choque]
    raiz = t.raiz_modelo(ID, tam, hijos)
    y_abajo = yf + t.LONA - FALDON - FESTON
    return {
        "raiz": raiz, "piezas": piezas3, "visibles": piezas3, "exportar": [raiz] + hijos,
        "b": b, "r": r, "presup": t.presupuesto(PRESUPUESTO, b),
        "esperado": ((-b.w / 2, b.w / 2), (0.40, yb + t.LONA), (-0.01, zf + t.LONA)),
        "desc": "lona %.2f × %.2f (%d rayas de %.3f), mástiles desde 0,40" % (b.w, FONDO, r.n, r.s),
        "apoyo_z": -0.01, "origen_txt": "las grapas apoyan en la cara del carrito (z = −0,01)",
        "lona_min": 1.80, "lona_txt": "no tapa el mostrador; el cliente de 1,75 m pasa por abajo",
        "mastiles": xm, "y_abajo": y_abajo,
    }


def revisar(m):
    return t.revisar_toldo(m)


def hoja(revision):
    rojo, crema, azul = comun.cargar_materiales("M_RojoAcento", "M_BlancoCrema", "M_AzulAcento")
    t.hoja_toldo(ID, construir, "toldo_rayado · chico / mediano / grande: 1,6 / 2,4 / 3,4 m · "
                 "lona de 2,10 a 1,84 m, sale 0,81 m", revision,
                 [("rojo y crema (el .glb)", rojo, crema), ("azul y crema", azul, crema),
                  ("liso rojo", rojo, rojo)])


if __name__ == "__main__":
    t.main(ID, construir, revisar, hoja)
