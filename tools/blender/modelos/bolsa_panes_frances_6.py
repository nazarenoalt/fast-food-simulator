"""Modelo: bolsa de papel con 6 panes franceses (id `bolsa_panes_frances_6`, etapa 4; todavía
sin dato en bloques.ron).

Genera:
    arte/fuentes/stock/bolsa_panes_frances_6.blend
    godot/modelos/stock/bolsa_panes_frances_6.glb
    docs/arte/revisiones/bolsa_panes_frances_6.jpg

Uso:
    blender -b -P tools/blender/modelos/bolsa_panes_frances_6.py
    python tools/blender/modelos/bolsa_panes_frances_6.py

Forma: solo la bolsa (los panes los pone el código, REQ-DEP-03). Bolsa de papel de panadería
(M_PapelMadera) acostada: el fondo de la bolsa adelante (+Z), los costados con el fuelle
plegado hacia adentro, y del lado del vendedor (−Z) la boca aplastada y doblada para arriba
(el doblez queda acostado sobre la bolsa, como cuando la cierra el panadero). Sombreado duro:
los pliegues del papel se marcan.

El papel no es transparente: los panes de adentro no se ven (el código los puede poner igual,
para contar, o no dibujarlos en este bloque).

Grilla propuesta para bloques.ron: (1, 3, 2) con separación (0,17, 0,062, 0,085) → 0,17 ×
0,124 × 0,255 (pan francés 0,16 × 0,06 × 0,08).

Medidas (lista: ≈ 0,20 × 0,10 × 0,35): 0,20 × 0,143 × 0,292. Más alta y más corta que la de
la lista: con la grilla del pan francés no entran 6 en una capa de 0,35 (6 × 0,08 = 0,48), así
que van en 2 capas de 3. El cuerpo mide 0,20 × 0,135 × 0,256; el doblez sobresale hacia −Z.
Origen: centro de la base del cuerpo, a nivel de apoyo (chequeo propio: el doblez corre la
caja).

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

ID = "bolsa_panes_frances_6"
FAMILIA = "stock"
PRESUPUESTO = 400  # lista de modelos
GRILLA = (1, 3, 2)
SEPARACION = (0.17, 0.062, 0.085)
ANCHO, ALTO = 0.20, 0.135
ML = 0.128                     # medio largo del cuerpo (sección completa)
# (z, ancho, alto, centro y, fuelle, material)
ESTACIONES = [
    (ML + 0.007, ANCHO - 0.006, ALTO - 0.006, (ALTO - 0.006) / 2, 0.006, 0),   # fondo de la bolsa
    (ML, ANCHO, ALTO, ALTO / 2, 0.01, 0),
    (0.0, ANCHO, ALTO, ALTO / 2, 0.012, 0),
    (-ML, ANCHO, ALTO, ALTO / 2, 0.01, 0),
    (-ML - 0.012, ANCHO - 0.004, 0.07, ALTO - 0.035, 0.004, 0),              # se aplasta (arriba queda)
    (-ML - 0.022, ANCHO - 0.01, 0.012, ALTO - 0.006, 0.0, 0),                 # boca aplastada
]
Z_DOBLEZ = -ML - 0.022
R_DOBLEZ = 0.0075
SOLAPA = (ANCHO - 0.01, 0.006, 0.075)
MEDIDAS = (ANCHO, ALTO + 2 * R_DOBLEZ - 0.007, ML + 0.007 + (-Z_DOBLEZ + R_DOBLEZ))


def construir():
    papel, = comun.cargar_materiales("M_PapelMadera")
    bm = bmesh.new()
    eq.loft_papel(bm, ESTACIONES, eje="z")
    # Doblez: el papel da la vuelta (rollo) y la solapa queda acostada arriba de la bolsa.
    y_rollo = ALTO + R_DOBLEZ - 0.007
    piezas.cilindro(bm, R_DOBLEZ, SOLAPA[0], (0, y_rollo, Z_DOBLEZ), eje="x", lados=8)
    y_solapa = y_rollo + R_DOBLEZ - SOLAPA[1] / 2
    piezas.caja(bm, SOLAPA, (0, y_solapa, Z_DOBLEZ + SOLAPA[2] / 2), bisel=0.0015)
    return {"obj": piezas.terminar(ID, bm, [papel])}


def chequeo_origen(obj):
    vs = eq.verts_godot(obj)
    cuerpo = [v for v in vs if abs(v.z) <= ML + 1e-5]
    cx = max(v.x for v in cuerpo) + min(v.x for v in cuerpo)
    cz = max(v.z for v in cuerpo) + min(v.z for v in cuerpo)
    base = min(v.y for v in vs)
    ok = abs(cx) < 1e-4 and abs(cz) < 1e-4 and abs(base) < 1e-4
    return ok, "Origen en el centro de la base del cuerpo, a nivel de apoyo (el doblez sobresale hacia −Z)"


def revisar(m):
    res = comun.revisar(m["obj"], PRESUPUESTO, MEDIDAS, origen="base")
    return eq.reemplazar(res, "Origen", chequeo_origen(m["obj"]))


def hoja(m, revision):
    comun.preparar_revision()
    import _etapa2 as e2
    bolsa = [m["obj"]]
    panes = eq.unidades(eq.ref_pan_frances, GRILLA, SEPARACION, "ref_pan_frances")
    # Para ver cómo entran los panes: una copia de la bolsa cortada al medio (solo para la foto).
    corte = e2.copiar(m["obj"], "ref_bolsa_cortada")
    bm = bmesh.new()
    bm.from_mesh(corte.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.x > 1e-4], context="VERTS")
    bm.to_mesh(corte.data)
    bm.free()
    cuadros = e2.sacar_fotos([
        ("Frente (cliente, +Z): el fondo de la bolsa · día", bolsa, "frente", "dia"),
        ("Costado: el doblez hacia el vendedor (−Z) · día", bolsa, "costado", "dia"),
        ("3/4 · día", bolsa, "tres_cuartos", "dia"),
        ("Desde el vendedor: el doblez arriba · día", bolsa, "vendedor", "dia"),
        ("3/4 · atardecer", bolsa, "tres_cuartos", "atardecer"),
        ("Cortada al medio (solo foto): los 6 panes de referencia", [corte] + panes, "costado", "dia"),
    ])
    comun.componer_hoja(f"{ID} · 0,20 × 0,143 × 0,292 m (con el doblez) · stock, papel de panadería",
                        cuadros, revision, comun.RAIZ / f"docs/arte/revisiones/{ID}.jpg")


def main():
    eq.main_modelo(ID, FAMILIA, construir, revisar, hoja, lambda m: [m["obj"]])


if __name__ == "__main__":
    main()
