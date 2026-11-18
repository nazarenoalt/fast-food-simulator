"""Modelo: caja de 12 medallones (id `caja_medallones_12`, etapa 4; todavía sin dato en
bloques.ron).

Genera:
    arte/fuentes/stock/caja_medallones_12.blend
    godot/modelos/stock/caja_medallones_12.glb
    docs/arte/revisiones/caja_medallones_12.jpg

Uso:
    blender -b -P tools/blender/modelos/caja_medallones_12.py
    python tools/blender/modelos/caja_medallones_12.py

Forma: solo el empaque (los 12 medallones los pone el código, REQ-DEP-03). Caja de cartón
abierta arriba, de esquinas apenas redondeadas, con la bolsa de nylon de adentro (M_BolsaPlastica)
que asoma y se dobla por afuera del borde. Entre las capas, dos hojas de papel separador
(M_BlancoCrema) como piezas aparte: `pieza_separador_1` (entre la capa 1 y la 2) y
`pieza_separador_2` (entre la 2 y la 3). El código esconde el separador N cuando la capa
N + 1 quedó vacía (si no, queda flotando arriba de la capa de abajo).

Grilla propuesta para bloques.ron: (2, 2, 3) con separación (0,115, 0,02, 0,115) → 0,23 × 0,06 ×
0,23 (medallón Ø 0,11 × 0,012). Las capas quedan centradas a 0,01 / 0,03 / 0,05 y los
separadores a 0,02 y 0,04 (en el aire entre capas, 2,5 mm de cada lado).

Medidas (lista: ≈ 0,24 × 0,08 × 0,24): 0,24 × 0,08 × 0,24 justos (con la bolsa doblada). La
caja de cartón mide 0,236 × 0,07 × 0,236, paredes de 4 mm y fondo de 3 mm; adentro, 0,228.
Origen: centro de la base, a nivel de apoyo.

Sin colisión `-colonly`: el cuerpo del bloque lo crea el código (BloqueStock::ready), como en
la bolsa de panes y la bandeja de salchichas.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402,F401  (antes que bmesh)
import bmesh  # noqa: E402

import comun  # noqa: E402
import piezas  # noqa: E402
import _equipos as eq  # noqa: E402

ID = "caja_medallones_12"
FAMILIA = "stock"
PRESUPUESTO = 300  # lista de modelos
GRILLA = (2, 2, 3)
SEPARACION = (0.115, 0.02, 0.115)
MEDIO, RADIO = 0.118, 0.008          # contorno de la caja de cartón
ALTO_CAJA = 0.07
FONDO = 0.003
PERFIL_CAJA = [                      # (meter, y): por afuera, el borde y por adentro hasta el fondo
    (0.002, 0.0),
    (0.0, 0.003),
    (0.0, ALTO_CAJA),
    (0.004, ALTO_CAJA),
    (0.004, FONDO),
]
PERFIL_BOLSA = [                     # sale de adentro, pasa por arriba del borde y baja por afuera
    (0.006, 0.048),
    (0.0055, 0.071),
    (0.003, 0.08),
    (-0.002, 0.0765),
    (-0.002, 0.058),
]
SEPARADOR = 0.226
Y_SEPARADORES = (0.02, 0.04)
MEDIDAS = (2 * (MEDIO + 0.002), 0.08, 2 * (MEDIO + 0.002))


def construir():
    carton, bolsa, papel = comun.cargar_materiales("M_Carton", "M_BolsaPlastica", "M_BlancoCrema")
    bm = bmesh.new()
    eq.e2.torno_rr(bm, PERFIL_CAJA, MEDIO, MEDIO, RADIO, segs=2, mats=0, tapa_fin=True)
    eq.e2.torno_rr(bm, PERFIL_BOLSA, MEDIO, MEDIO, RADIO, segs=2, mats=1)
    caja = piezas.terminar(ID, bm, [carton, bolsa])
    eq.e2.suavizar_hasta(caja, 31)
    separadores = []
    for i, y in enumerate(Y_SEPARADORES):
        bm = bmesh.new()
        piezas.caja(bm, (SEPARADOR, 0.003, SEPARADOR), (0, y, 0))
        s = eq.objeto_en(f"pieza_separador_{i + 1}", bm, [papel], (0, y, 0))
        separadores.append(s)
        s.parent = caja
    return {"caja": caja, "separadores": separadores}


def chequeo_separadores(m):
    capas = [c * SEPARACION[1] + SEPARACION[1] / 2 for c in range(GRILLA[2])]
    ok = all(abs(s.location.z - (a + b) / 2) < 1e-6 for s, a, b in zip(m["separadores"], capas, capas[1:]))
    return ok, "pieza_separador_1/2 a mitad de camino entre las capas (0,02 y 0,04)"


def revisar(m):
    res = comun.revisar([m["caja"]] + m["separadores"], PRESUPUESTO, MEDIDAS, origen="base")
    res.insert(1, chequeo_separadores(m))
    return res


def hoja(m, revision):
    meds = eq.unidades(eq.ref_medallon, GRILLA, SEPARACION, "ref_medallon")
    paquete = [m["caja"]] + m["separadores"]
    eq.hoja_stock(ID, f"{ID} · 0,24 × 0,08 × 0,24 m · stock (medallones de referencia)",
                  paquete, paquete + meds, revision)


def main():
    eq.main_modelo(ID, FAMILIA, construir, revisar, hoja, lambda m: [m["caja"]] + m["separadores"])


if __name__ == "__main__":
    main()
