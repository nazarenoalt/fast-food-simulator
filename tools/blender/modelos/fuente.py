"""Modelo: fuente central (id `fuente`, rust/core/src/plaza.rs → TipoProp::Fuente).

Genera:
    arte/fuentes/plaza/fuente.blend
    godot/modelos/plaza/fuente.glb
    docs/arte/revisiones/fuente.jpg

Uso:
    python tools/blender/modelos/fuente.py [--sin-hoja]

Forma (guía 5.4): fuente de piedra (M_Piedra) de plaza de barrio. Pileta redonda de Ø 6 m con
pared gruesa (30 cm) y borde con alero; en el medio, un pedestal que asoma del agua, una
columna con base y capitel y un plato (taza) arriba, con un remate en el centro. El agua
(M_Agua, transparente) es un objeto aparte, `pieza_agua`: el espejo de la pileta y el del
plato. Se probó una cortina de agua cayendo del plato: con el alfa 0,7 de M_Agua parecía un
tambor azul que tapaba la columna, así que no va (si se quiere, mejor con partículas en Godot).

Medidas (lista-de-modelos: Ø 6,0 × 1,6): Ø 6,00 (el alero del borde) × 1,60 (punta del
remate). Hoy el juego dibuja la pileta como un cilindro macizo de radio 3 y 0,5 m de alto, una
columna de radio 0,35 hasta 1,5 m y un plato de radio 0,9 a 1,5 m: se respetan el radio, el
alto del borde (0,51), el radio del plato (0,9) y su altura (borde a 1,47 m).
Lados (guía 3.2): pileta 32 (radio > 1 m), columna y plato 24 (de 25 cm a 1 m).
Sombreado "duro": es piedra tallada, no una roca (3.4 pide facetado para piedras sueltas).

Objetos (hijos del Empty `fuente`, origen = centro de la base, a nivel del piso):
    - fuente_piedra: pileta, pedestal, columna y plato.
    - pieza_agua: los dos espejos de agua (el código puede animarlos o cambiarlos).
    - fuente-colonly: cilindro de la pileta (r 3, alto 0,51).
    - fuente_columna-colonly: cilindro del pedestal y la columna (r 0,55 hasta 1,6 m; no
      cubre el ala del plato: nadie llega hasta ahí sin meterse en el agua).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402, F401  (antes que bmesh)
import bmesh  # noqa: E402

import _plaza as plaza  # noqa: E402
import comun  # noqa: E402
import piezas  # noqa: E402

ID = "fuente"
PRESUPUESTO = 2500  # fuente / estructuras grandes de la plaza (guía 3.1)
MEDIDAS = (6.0, 1.6, 6.0)

R_PILETA = 3.0
R_ADENTRO = 2.70
BORDE = 0.51        # arriba del borde de la pileta
FONDO = 0.12        # fondo de la pileta (adentro)
AGUA = 0.42         # espejo de la pileta
R_PLATO = 0.90
AGUA_PLATO = 1.455
BORDE_PLATO = 1.49
LADOS_PILETA, LADOS_COLUMNA = 32, 24


def construir():
    piedra, agua = comun.cargar_materiales("M_Piedra", "M_Agua")
    bm = bmesh.new()
    # Pileta: de la base de afuera, por el borde, hasta el fondo de adentro.
    plaza.torno(bm, [
        (R_PILETA - 0.06, 0.0), (R_PILETA - 0.06, 0.38),          # pared de afuera
        (R_PILETA, 0.40), (R_PILETA, 0.48), (R_PILETA - 0.03, BORDE),  # alero del borde
        (R_ADENTRO + 0.03, BORDE), (R_ADENTRO, 0.48),              # bisel de adentro
        (R_ADENTRO, FONDO), (0.0, FONDO),                          # pared de adentro y fondo
    ], lados=LADOS_PILETA)
    # Pedestal, columna, plato y remate (sale del fondo de la pileta).
    plaza.torno(bm, [
        (0.55, FONDO), (0.55, 0.52), (0.51, 0.56),                 # pedestal
        (0.34, 0.58), (0.27, 0.64), (0.22, 0.70),                  # base de la columna
        (0.19, 1.12), (0.24, 1.17), (0.24, 1.21),                  # columna y capitel
        (0.50, 1.32), (0.86, 1.40), (R_PLATO, 1.43),               # panza del plato
        (R_PLATO, 1.47), (R_PLATO - 0.04, BORDE_PLATO),                   # borde del plato
        (R_PLATO - 0.09, 1.44), (0.30, 1.40),                      # adentro del plato
        (0.11, 1.40), (0.085, 1.49), (0.12, 1.52),                 # remate
        (0.10, 1.55), (0.04, 1.585), (0.0, 1.60),
    ], lados=LADOS_COLUMNA)
    cuerpo = piezas.terminar(f"{ID}_piedra", bm, [piedra])

    # Agua: no pasa por piezas.terminar (recalcularía las normales de las caras sueltas).
    ba = bmesh.new()
    plaza.disco(ba, R_ADENTRO + 0.015, AGUA, LADOS_PILETA)
    plaza.disco(ba, R_PLATO - 0.06, AGUA_PLATO, LADOS_COLUMNA)
    agua_obj = comun.objeto_desde_bmesh("pieza_agua", ba, [agua])

    cols = [
        piezas.colision_cilindro(ID, R_PILETA, BORDE, (0, BORDE / 2, 0), lados=LADOS_PILETA),
        piezas.colision_cilindro(f"{ID}_columna", 0.55, 1.6, (0, 0.8, 0), lados=16),
    ]
    raiz = piezas.raiz(ID, [cuerpo, agua_obj] + cols)
    return {"raiz": raiz, "cuerpo": cuerpo, "agua": agua_obj, "colisiones": cols}


def revisar(mod):
    res = comun.revisar([mod["cuerpo"], mod["agua"]], PRESUPUESTO, MEDIDAS, origen="base")
    mn, mx = plaza.limites([mod["agua"]])
    res.append((FONDO < mn.y < BORDE and mx.y < BORDE_PLATO,
                "pieza_agua: de %.2f a %.2f m, adentro de la pileta (fondo %.2f, borde %.2f) y "
                "abajo del borde del plato (%.2f)" % (mn.y, mx.y, FONDO, BORDE, BORDE_PLATO)))
    return res


def main():
    comun.escena_vacia()
    mod = construir()
    revision = revisar(mod)
    ok = comun.imprimir_revision(ID, revision)
    plaza.guardar_y_exportar(ID, [mod["raiz"], mod["cuerpo"], mod["agua"]] + mod["colisiones"])
    if "--sin-hoja" not in sys.argv:
        c = [mod["cuerpo"], mod["agua"]]
        plaza.hoja(ID, "fuente · Ø 6,0 × 1,6 m · fuente / estructura grande de la plaza", [
            ("Frente · día", c, "frente", "dia", True),
            ("Costado · día", c, "costado", "dia", True),
            ("3/4 · día", c, "tres_cuartos", "dia", False),
            ("3/4 · atardecer", c, "tres_cuartos", "atardecer", False),
            ("Con la persona de 1,75 m · día", c + ["persona"], "tres_cuartos", "dia", False),
            ("Arriba · día", c, "arriba", "dia", True),
        ], revision, persona_en=(2.2, 0, 3.4))
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
