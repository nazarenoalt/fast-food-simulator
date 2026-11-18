"""Modelo: bolsa de papas (id `bolsa_papas`, godot/data/bloques.ron, SPEC-026).

Genera:
    arte/fuentes/stock/bolsa_papas.blend
    godot/modelos/stock/bolsa_papas.glb
    docs/arte/revisiones/bolsa_papas.jpg

Uso:
    blender -b -P tools/blender/modelos/bolsa_papas.py
    python tools/blender/modelos/bolsa_papas.py

Forma: solo la bolsa (las 12 papas las pone el código, REQ-DEP-03). Bolsa de papel madera
(M_PapelMadera) acostada, de verdulería: el fondo adelante (+Z), los costados con el fuelle
plegado y, del lado del vendedor (−Z), la boca aplastada y doblada para arriba (como la de los
panes franceses). Para que se vean las papas, una **ventana** transparente que da toda la
vuelta en el medio (M_PlasticoClaro: deja ver el color real de las papas, guía v1.4), y
adelante una franja roja (M_RojoAcento) de etiqueta, sin marcas. Sombreado duro: se marcan
los pliegues del papel.

Grilla del dato (bloques.ron): (2, 3, 2) con separación (0,096, 0,064, 0,074) → 0,192 × 0,128
× 0,222 (papa cruda 0,095 × 0,058 × 0,068).

Medidas: 0,20 × 0,143 × 0,272 (con el doblez). El cuerpo mide 0,20 × 0,135 × 0,236 y envuelve
la grilla con aire; el doblez sobresale hacia −Z. Origen: centro de la base del cuerpo, a nivel
de apoyo (chequeo propio: el doblez corre la caja). Entra en un lugar del estante (0,22 × 0,3 ×
0,4).

Sin colisión `-colonly`: el cuerpo del bloque lo crea el código (BloqueStock::ready).
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

ID = "bolsa_papas"
FAMILIA = "stock"
PRESUPUESTO = 400  # empaques y bloques de stock (guía 3.1)
GRILLA = (2, 3, 2)
SEPARACION = (0.096, 0.064, 0.074)
PAPEL, VENTANA, ROJO = range(3)
ANCHO, ALTO = 0.20, 0.135
ML = 0.118                     # medio largo del cuerpo (sección completa)
# (z, ancho, alto, centro y, fuelle, material de la banda que arranca acá)
ESTACIONES = [
    (ML + 0.007, ANCHO - 0.008, ALTO - 0.008, (ALTO - 0.008) / 2, 0.006, PAPEL),   # fondo
    (ML, ANCHO, ALTO, ALTO / 2, 0.01, PAPEL),
    (0.085, ANCHO, ALTO, ALTO / 2, 0.011, ROJO),          # franja de la etiqueta
    (0.06, ANCHO, ALTO, ALTO / 2, 0.012, PAPEL),
    (0.05, ANCHO, ALTO, ALTO / 2, 0.012, VENTANA),        # ventana que da la vuelta
    (-0.06, ANCHO, ALTO, ALTO / 2, 0.012, PAPEL),
    (-ML, ANCHO, ALTO, ALTO / 2, 0.01, PAPEL),
    (-ML - 0.012, ANCHO - 0.004, 0.07, ALTO - 0.035, 0.004, PAPEL),     # se aplasta
    (-ML - 0.022, ANCHO - 0.01, 0.012, ALTO - 0.006, 0.0, PAPEL),       # boca aplastada
]
Z_DOBLEZ = -ML - 0.022
R_DOBLEZ = 0.0075
SOLAPA = (ANCHO - 0.01, 0.006, 0.07)
MEDIDAS = (ANCHO, ALTO + 2 * R_DOBLEZ - 0.007, ML + 0.007 + (-Z_DOBLEZ + R_DOBLEZ))


def construir():
    mats = comun.cargar_materiales("M_PapelMadera", "M_PlasticoClaro", "M_RojoAcento")
    bm = bmesh.new()
    eq.loft_papel(bm, ESTACIONES, eje="z")
    y_rollo = ALTO + R_DOBLEZ - 0.007
    piezas.cilindro(bm, R_DOBLEZ, SOLAPA[0], (0, y_rollo, Z_DOBLEZ), eje="x", lados=8, mat=ROJO)
    y_solapa = y_rollo + R_DOBLEZ - SOLAPA[1] / 2
    piezas.caja(bm, SOLAPA, (0, y_solapa, Z_DOBLEZ + SOLAPA[2] / 2), mat=PAPEL, bisel=0.0015)
    return {"obj": piezas.terminar(ID, bm, mats)}


def chequeo_origen(obj):
    vs = eq.verts_godot(obj)
    cuerpo = [v for v in vs if abs(v.z) <= ML + 1e-5]
    cx = max(v.x for v in cuerpo) + min(v.x for v in cuerpo)
    cz = max(v.z for v in cuerpo) + min(v.z for v in cuerpo)
    base = min(v.y for v in vs)
    ok = abs(cx) < 1e-4 and abs(cz) < 1e-4 and abs(base) < 1e-4
    return ok, "Origen en el centro de la base del cuerpo, a nivel de apoyo (el doblez sobresale hacia −Z)"


def chequeo_grilla():
    tam = [GRILLA[0] * SEPARACION[0], GRILLA[2] * SEPARACION[1], GRILLA[1] * SEPARACION[2]]
    ok = tam[0] < ANCHO and tam[1] < ALTO and tam[2] < 2 * ML and MEDIDAS[0] <= 0.22 and MEDIDAS[2] <= 0.4
    return ok, ("Grilla del dato %.3f × %.3f × %.3f adentro del cuerpo (%.3f × %.3f × %.3f); entra en "
                "un lugar del estante (0,22 × 0,3 × 0,4)" % (*tam, ANCHO, ALTO, 2 * ML))


def revisar(m):
    res = comun.revisar(m["obj"], PRESUPUESTO, MEDIDAS, origen="base")
    res = eq.reemplazar(res, "Origen", chequeo_origen(m["obj"]))
    res.insert(1, chequeo_grilla())
    return res


def hoja(m, revision):
    import papa_cruda
    papas = eq.unidades(lambda n: papa_cruda.construir(n), GRILLA, SEPARACION, "ref_papa")
    eq.hoja_stock(ID, f"{ID} · 0,20 × 0,143 × 0,272 m (con el doblez) · stock, papel con ventana",
                  [m["obj"]], [m["obj"]] + papas, revision)


def main():
    eq.main_modelo(ID, FAMILIA, construir, revisar, hoja, lambda m: [m["obj"]])


if __name__ == "__main__":
    main()
