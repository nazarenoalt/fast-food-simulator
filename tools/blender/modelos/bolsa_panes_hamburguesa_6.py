"""Modelo: bolsa de 6 panes de hamburguesa (id `bolsa_panes_hamburguesa_6`, etapa 4; todavía
sin dato en bloques.ron).

Genera:
    arte/fuentes/stock/bolsa_panes_hamburguesa_6.blend
    godot/modelos/stock/bolsa_panes_hamburguesa_6.glb
    docs/arte/revisiones/bolsa_panes_hamburguesa_6.jpg

Uso:
    blender -b -P tools/blender/modelos/bolsa_panes_hamburguesa_6.py
    python tools/blender/modelos/bolsa_panes_hamburguesa_6.py

Forma: la misma bolsa que `bolsa_panes_12` (se usa su código, con otras medidas): solo la
bolsa (los 6 panes los pone el código, REQ-DEP-03). Bolsa de plástico blanda de sección
rectangular con las esquinas redondeadas (más arriba), punta de adelante (+Z) cerrada y, del
lado del vendedor (−Z), el cuello, el precinto de papel, el nudo y el copete. Arriba, la
etiqueta chica de papel. M_BolsaPlastica (alfa 0,35) y M_BlancoCrema.

Grilla propuesta para bloques.ron: (2, 3, 1) con separación (0,115, 0,08, 0,115) → 0,23 × 0,08
× 0,345 (pan entero Ø 0,11 × 0,075: base de 0,03 + tapa de 0,045).

Medidas (lista: ≈ 0,24 × 0,10 × 0,36): el cuerpo mide 0,24 × 0,10 × 0,366; con la etiqueta y
el nudo (que sobresale hacia −Z, como en la bolsa de 12), 0,24 × 0,103 × 0,429. Origen:
centro de la base del cuerpo, a nivel de apoyo (chequeo propio: el nudo corre la caja).

Sin colisión `-colonly`: el cuerpo del bloque lo crea el código (BloqueStock::ready).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402,F401  (antes que bmesh)

import comun  # noqa: E402
import _equipos as eq  # noqa: E402
import bolsa_panes_12 as bp  # noqa: E402  (la misma bolsa; no se toca ese script)

ID = "bolsa_panes_hamburguesa_6"
FAMILIA = "stock"
PRESUPUESTO = 400  # empaques y bloques de stock (guía 3.1)
GRILLA = (2, 3, 1)
SEPARACION = (0.115, 0.08, 0.115)

ANCHO, ALTO = 0.24, 0.10
R_ABAJO, R_ARRIBA = 0.02, 0.04
ML = 0.183                                  # medio largo del cuerpo
R_CUELLO, R_PRECINTO, R_NUDO = 0.013, 0.0165, 0.02
Y_NUDO = 0.048
ESTACIONES = [  # como en bolsa_panes_12, a partir de la punta del cuerpo
    (ML - 0.005, 0.86, 0.86, ALTO * 0.86 / 2, 0),
    (ML - 0.018, 1.0, 1.0, ALTO / 2, 0),
    (-(ML - 0.018), 1.0, 1.0, ALTO / 2, 0),
    (-(ML - 0.005), 0.86, 0.84, ALTO / 2, 0),
    (-(ML + 0.005), 0.38, 0.50, 0.052, 0),
    (-(ML + 0.012), None, R_CUELLO, Y_NUDO, 0),
    (-(ML + 0.014), None, R_PRECINTO, Y_NUDO, 1),
    (-(ML + 0.020), None, R_PRECINTO, Y_NUDO, 0),
    (-(ML + 0.022), None, R_CUELLO, Y_NUDO, 0),
    (-(ML + 0.027), None, R_NUDO, Y_NUDO, 0),
    (-(ML + 0.039), None, R_NUDO, Y_NUDO, 0),
    (-(ML + 0.046), None, 0.010, Y_NUDO, 0),
    (-(ML + 0.053), None, 0.020, Y_NUDO, 0),
    (-(ML + 0.063), None, 0.027, Y_NUDO, 0),
]
LARGO_ATRAS = ML + 0.063
ETIQUETA = (0.085, 0.003, 0.065)
MEDIDAS = (ANCHO, ALTO + ETIQUETA[1], ML + LARGO_ATRAS)

_CAMBIOS = {
    "ID": ID, "ANCHO": ANCHO, "ALTO": ALTO, "R_ABAJO": R_ABAJO, "R_ARRIBA": R_ARRIBA,
    "MEDIO_LARGO": ML, "ESTACIONES": ESTACIONES, "PUNTA_ADELANTE": (0.0, ALTO * 0.80 / 2, ML),
    "PUNTA_ATRAS": (0.0, Y_NUDO, -(ML + 0.057)), "LARGO_ATRAS": LARGO_ATRAS, "ETIQUETA": ETIQUETA,
    "ETIQUETA_Z": 0.07, "MEDIDAS": MEDIDAS,
}


def construir():
    """bolsa_panes_12.construir() con estas medidas: se cambian sus constantes mientras se arma
    y se vuelven a poner."""
    viejos = {k: getattr(bp, k) for k in _CAMBIOS}
    for k, v in _CAMBIOS.items():
        setattr(bp, k, v)
    try:
        return {"obj": bp.construir()}
    finally:
        for k, v in viejos.items():
            setattr(bp, k, v)


def revisar(m):
    for k, v in _CAMBIOS.items():   # chequeo_origen de bp usa MEDIO_LARGO
        setattr(bp, k, v)
    res = comun.revisar(m["obj"], PRESUPUESTO, MEDIDAS, origen="base")
    return bp.cambiar_chequeo(res, "Origen", bp.chequeo_origen(m["obj"]))


def hoja(m, revision):
    panes = eq.unidades(eq.ref_pan_hamburguesa, GRILLA, SEPARACION, "ref_pan")
    eq.hoja_stock(ID, f"{ID} · 0,24 × 0,103 × 0,429 m (con nudo) · stock (panes de referencia)",
                  [m["obj"]], [m["obj"]] + panes, revision)


def main():
    eq.main_modelo(ID, FAMILIA, construir, revisar, hoja, lambda m: [m["obj"]])


if __name__ == "__main__":
    main()
