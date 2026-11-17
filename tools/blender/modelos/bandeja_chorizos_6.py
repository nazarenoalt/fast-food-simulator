"""Modelo: bandeja de 6 chorizos (id `bandeja_chorizos_6`, etapa 4; todavía sin dato en
bloques.ron).

Genera:
    arte/fuentes/stock/bandeja_chorizos_6.blend
    godot/modelos/stock/bandeja_chorizos_6.glb
    docs/arte/revisiones/bandeja_chorizos_6.jpg

Uso:
    blender -b -P tools/blender/modelos/bandeja_chorizos_6.py
    python tools/blender/modelos/bandeja_chorizos_6.py

Forma: igual que `caja_salchichas_12`, más chica: solo el paquete (los 6 chorizos los pone el
código, REQ-DEP-03). Bandeja de cartón baja, de esquinas redondeadas, paredes un poco abiertas
y pestaña plana; arriba, el film transparente pegado a la pestaña y estirado sobre los
chorizos (abierto abajo: esa cara nunca se ve, guía 3.6). El film es M_PlasticoClaro y no
M_BolsaPlastica (la de la lista): con la bolsa blanca los chorizos se veían rosados,
desteñidos; es lo mismo que pasó con el pack de repuestos (guía v1.4).

Grilla propuesta para bloques.ron: (1, 6, 1) con separación (0,15, 0,03, 0,03) → 0,15 × 0,03 ×
0,18: los 6 chorizos (Ø 0,03 × 0,14, acostados en X como la salchicha) uno al lado del otro.
posicion_unidad no gira las unidades, así que la bandeja va con el lado largo en Z.

Medidas (lista: ≈ 0,20 × 0,05 × 0,16): 0,172 × 0,038 × 0,20. Es la de la lista girada 90° (los
chorizos van en X, uno al lado del otro en Z) y más baja: una sola capa de chorizos de 3 cm
(con 0,05 el film quedaba 2 cm en el aire). Adentro: 0,152 × 0,18 a la altura de los
chorizos. Origen: centro de la base, a nivel de apoyo.

Sin colisión `-colonly`: el cuerpo del bloque lo crea el código (BloqueStock::ready).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402,F401  (antes que bmesh)
import bmesh  # noqa: E402,F401

import comun  # noqa: E402
import piezas  # noqa: E402
import _equipos as eq  # noqa: E402
import caja_salchichas_12 as cs  # noqa: E402  (el mismo torno; no se toca ese script)

ID = "bandeja_chorizos_6"
FAMILIA = "stock"
PRESUPUESTO = 300  # lista de modelos
GRILLA = (1, 6, 1)
SEPARACION = (0.15, 0.03, 0.03)
MEDIO_X, MEDIO_Z, RADIO = 0.086, 0.10, 0.014
FONDO = 0.003
BORDE = 0.02
PERFIL_BANDEJA = [
    (0.0080, 0.0),
    (0.0055, BORDE - 0.003),
    (0.0, BORDE - 0.002),
    (0.0, BORDE + 0.001),
    (0.0075, BORDE + 0.001),
    (0.0085, BORDE - 0.004),
    (0.0085 + 0.0025, FONDO),
]
PERFIL_FILM = [
    (0.0015, BORDE + 0.0016),
    (0.0050, 0.031),
    (0.0120, 0.0365),
    (0.0240, 0.038),
]
MEDIDAS = (2 * MEDIO_X, PERFIL_FILM[-1][1], 2 * MEDIO_Z)


def construir():
    # El torno de caja_salchichas_12 usa sus constantes de contorno: se cambian mientras se
    # arma (y se vuelven a poner), así no se copia el código ni se toca ese script.
    viejo = (cs.MEDIO_X, cs.MEDIO_Z, cs.RADIO)
    cs.MEDIO_X, cs.MEDIO_Z, cs.RADIO = MEDIO_X, MEDIO_Z, RADIO
    try:
        m_carton, m_film = comun.cargar_materiales("M_Carton", "M_PlasticoClaro")
        bm = bmesh.new()
        cs.torno(bm, PERFIL_BANDEJA, 0)
        cs.torno(bm, PERFIL_FILM, 1, tapa_inicio=False)
    finally:
        cs.MEDIO_X, cs.MEDIO_Z, cs.RADIO = viejo
    obj = piezas.terminar(ID, bm, [m_carton, m_film], sombreado="duro")
    cs.suavizar_material(obj, 1)
    return {"obj": obj}


def revisar(m):
    return comun.revisar(m["obj"], PRESUPUESTO, MEDIDAS, origen="base")


def hoja(m, revision):
    unidades = eq.unidades(eq.ref_chorizo, GRILLA, SEPARACION, "ref_chorizo")
    eq.hoja_stock(ID, f"{ID} · {MEDIDAS[0]:.3f} × {MEDIDAS[1]:.3f} × {MEDIDAS[2]:.2f} m · stock "
                  "(chorizos de referencia)", [m["obj"]], [m["obj"]] + unidades, revision)


def main():
    eq.main_modelo(ID, FAMILIA, construir, revisar, hoja, lambda m: [m["obj"]])


if __name__ == "__main__":
    main()
