"""Modelo: toldo enrollable con faldón (id `toldo_enrollable`, tres tamaños).

Genera, para cada tamaño (chico = barra_chica, mediano = barra_mediana, grande = carro_grande):
    arte/fuentes/accesorios/toldo_enrollable_<tamaño>.blend
    godot/modelos/accesorios/toldo_enrollable_<tamaño>.glb
y una sola hoja con los tres: docs/arte/revisiones/toldo_enrollable.jpg

Uso:
    python tools/blender/modelos/toldo_enrollable.py [--sin-hoja]

Forma: caja de enrollado de acero (con el frente ochavado y tapas negras en las puntas) arriba
de dos mástiles agarrados a la cara del frente del carrito (como el toldo_rayado); la lona sale
por abajo de la caja y llega casi plana hasta la barra de carga, 0,98 m adelante (hace sombra
sobre la fila), con un faldón festoneado (un festón por raya). Brazos articulados de los
mástiles a la barra de carga, y la manivela colgando de la punta derecha (varilla de acero y
manija negra), a mano del vendedor desde el costado.

Medidas (relativas al anclaje `frente`): lona del ancho de la base; de y = 0,40 (mástiles) a
2,13 (caja); fondo de z = −0,01 (cara del carrito) a 0,99. Lona más baja (festones): 1,85 m.
La caja queda debajo de la chapa de los techos y detrás de sus faldones (no choca con ellos
ni con sus caños: ver _techo.revisar_toldo y la foto con techo_plano).

Colores (guía 4.2, regla 5): superficie 0 = rayas pares (la primera desde −X), 1 = impares, en
las tres piezas. El .glb trae azul y crema; rojo y crema, o liso, con los mismos materiales.

Objetos (hijos del Empty `toldo_enrollable_<tamaño>`): pieza_punta_izq, pieza_tramo,
pieza_punta_der (superficies 0 raya A, 1 raya B, 2 acero, 3 plástico negro; el tramo no tiene
negro y es un número entero de módulos de 2 rayas: se repite) y
`toldo_enrollable_<tamaño>-colonly` (mástiles).
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

ID = "toldo_enrollable"
PRESUPUESTO = 800            # lista (el chico); mediano y grande, proporcional al ancho
Z_MASTIL = 0.08
CAJA_ABAJO, CAJA_ARRIBA = 2.02, 2.13
CAJA_Z = (0.025, 0.15)
TAPA = 0.02
LONA_ATRAS = (2.015, 0.13)   # la lona sale por abajo de la caja
Z_FRENTE, Y_FRENTE = 0.98, 1.95
FALDON, FESTON = 0.09, 0.03


def caja_enrollado(bm, w):
    z0, z1 = CAJA_Z
    perfil = [(CAJA_ABAJO, z0), (CAJA_ARRIBA, z0), (CAJA_ARRIBA, 0.10), (2.08, z1), (CAJA_ABAJO, z1)]
    t.prisma_x(bm, perfil, -w / 2 + TAPA - 0.005, w / 2 - TAPA + 0.005, bisel=0.006, mat=2)
    tapa = [(CAJA_ABAJO - 0.006, z0 - 0.006), (CAJA_ARRIBA + 0.006, z0 - 0.006),
            (CAJA_ARRIBA + 0.006, 0.10), (2.08, z1 + 0.006), (CAJA_ABAJO - 0.006, z1 + 0.006)]
    for sx in (-1, 1):
        x0, x1 = sorted((sx * (w / 2 - TAPA), sx * w / 2))
        t.prisma_x(bm, tapa, x0, x1, mat=3)        # tapa de 2 cm: sin bisel


def manivela(bm, x):
    """Caja del engranaje bajo la caja, varilla que cuelga y manija negra."""
    piezas.cilindro(bm, 0.022, 0.03, (x, CAJA_ABAJO - 0.015, 0.07), lados=8, mat=3)
    abajo = (x, 1.36, 0.11)
    t.varilla(bm, (x, CAJA_ABAJO - 0.03, 0.07), abajo, 0.006, lados=6, mat=2)
    codo = (x - 0.09, 1.36, 0.11)
    t.varilla(bm, abajo, codo, 0.006, lados=6, mat=2)
    piezas.cilindro(bm, 0.013, 0.08, (codo[0], 1.36 - 0.04, 0.11), lados=8, mat=3)


def construir(tam):
    b = t.base(tam)
    r = t.rayas(b)
    xm = b.w / 2 - 0.04
    azul, crema, acero, negro = comun.cargar_materiales(
        "M_AzulAcento", "M_BlancoCrema", "M_Acero", "M_PlasticoNegro")
    bm = bmesh.new()
    t.lona_rayada(bm, r, LONA_ATRAS, (Y_FRENTE, Z_FRENTE), FALDON, FESTON, canto_atras=False)
    caja_enrollado(bm, b.w)
    col = t.mastiles(bm, b, xm, Z_MASTIL, CAJA_ABAJO + 0.005, 2, 3)
    barra = (Y_FRENTE - 0.016, Z_FRENTE - 0.021)                        # barra de carga
    piezas.caja(bm, (b.w - 0.01, 0.03, 0.04), (0, barra[0], barra[1]), mat=2, bisel=0.006)
    for sx in (-1, 1):
        x = sx * xm
        t.brazo(bm, (x, 1.78, Z_MASTIL), (x, barra[0] - 0.015, barra[1]), 0.06, 2, 3)
    manivela(bm, b.w / 2 - 0.12)
    piezas3 = t.tres_piezas(bm, r.corte, [azul, crema, acero, negro])
    choque = t.colision(f"{ID}_{tam}", cilindros=col)
    hijos = piezas3 + [choque]
    raiz = t.raiz_modelo(ID, tam, hijos)
    return {
        "raiz": raiz, "piezas": piezas3, "visibles": piezas3, "exportar": [raiz] + hijos,
        "b": b, "r": r, "presup": t.presupuesto(PRESUPUESTO, b),
        "esperado": ((-b.w / 2, b.w / 2), (0.40, CAJA_ARRIBA + 0.006), (-0.01, Z_FRENTE + t.LONA)),
        "desc": "lona %.2f × %.2f (%d rayas de %.3f), caja a %.2f" % (b.w, Z_FRENTE, r.n, r.s, CAJA_ARRIBA),
        "apoyo_z": -0.01, "origen_txt": "las grapas apoyan en la cara del carrito (z = −0,01)",
        "lona_min": 1.80, "lona_txt": "no tapa el mostrador; hace sombra sobre la fila y el "
                                      "cliente de 1,75 m pasa por abajo",
        "mastiles": xm,
    }


def revisar(m):
    return t.revisar_toldo(m)


def hoja(revision):
    azul, crema, rojo = comun.cargar_materiales("M_AzulAcento", "M_BlancoCrema", "M_RojoAcento")
    t.hoja_toldo(ID, construir, "toldo_enrollable · chico / mediano / grande: 1,6 / 2,4 / 3,4 m · "
                 "caja a 2,13 m, lona hasta 1,85 m, sale 0,99 m", revision,
                 [("azul y crema (el .glb)", azul, crema), ("rojo y crema", rojo, crema),
                  ("liso azul", azul, azul)])


if __name__ == "__main__":
    t.main(ID, construir, revisar, hoja)
