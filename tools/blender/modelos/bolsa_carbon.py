"""Modelo: bolsa de carbón (id `bolsa_carbon`, etapa 4; todavía sin dato en bloques.ron).

Genera:
    arte/fuentes/stock/bolsa_carbon.blend
    godot/modelos/stock/bolsa_carbon.glb
    docs/arte/revisiones/bolsa_carbon.jpg

Uso:
    blender -b -P tools/blender/modelos/bolsa_carbon.py
    python tools/blender/modelos/bolsa_carbon.py

Forma: bolsa de papel madera parada, llena (panzona en el medio), con el fuelle plegado hacia
adentro en los costados, una franja negra impresa (sin texto ni marca) y arriba la boca
aplastada y enrollada (el doblez), con una manija de plástico negro para llevarla. Sombreado
duro: los pliegues del papel se marcan.

Es un paquete cerrado: el carbón no se ve. Grilla propuesta para bloques.ron: (1, 1, 1), una
"carga de carbón" por bolsa (lo que la parrilla gasta lo decide la spec de la parrilla).

Medidas (lista: ≈ 0,35 × 0,50 × 0,15): 0,35 × 0,50 × 0,15 justos (con la manija).
Origen: centro de la base, a nivel de apoyo.

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

ID = "bolsa_carbon"
FAMILIA = "stock"
PRESUPUESTO = 300  # lista de modelos
PAPEL, NEGRO = range(2)
ANCHO, ALTO, PROF = 0.35, 0.50, 0.15
Y_BOCA = 0.455
R_ROLLO = 0.011
# (y, ancho, prof, centro z, fuelle, material de la banda que arranca acá)
ESTACIONES = [
    (0.0, ANCHO - 0.02, PROF - 0.02, 0.0, 0.004, PAPEL),
    (0.012, ANCHO - 0.006, PROF - 0.006, 0.0, 0.012, PAPEL),
    (0.15, ANCHO, PROF, 0.0, 0.022, NEGRO),     # franja negra impresa
    (0.24, ANCHO, PROF, 0.0, 0.022, PAPEL),
    (0.36, ANCHO - 0.006, PROF - 0.012, 0.0, 0.018, PAPEL),
    (0.425, ANCHO - 0.014, 0.05, 0.0, 0.006, PAPEL),       # se aplasta
    (Y_BOCA, ANCHO - 0.02, 0.012, 0.0, 0.0, PAPEL),       # boca aplastada
]
MEDIDAS = (ANCHO, ALTO, PROF)


def construir():
    papel, negro = comun.cargar_materiales("M_PapelMadera", "M_PlasticoNegro")
    bm = bmesh.new()
    eq.loft_papel(bm, ESTACIONES, eje="y", tapas=(False, True))  # abajo apoya: no se ve
    # Doblez: la boca enrollada (un rollo de papel a lo ancho).
    piezas.cilindro(bm, R_ROLLO, ANCHO - 0.02, (0, Y_BOCA, 0.0), eje="x", lados=8, mat=PAPEL)
    # Manija negra: dos patas que abrazan el rollo y el agarre arriba.
    for x in (-0.055, 0.055):
        piezas.caja(bm, (0.014, 0.04, 0.026), (x, Y_BOCA + 0.014, 0), mat=NEGRO, bisel=0.003)
    piezas.caja(bm, (0.13, 0.014, 0.018), (0, ALTO - 0.007, 0), mat=NEGRO, bisel=0.004)
    return {"obj": piezas.terminar(ID, bm, [papel, negro])}


def revisar(m):
    return comun.revisar(m["obj"], PRESUPUESTO, MEDIDAS, origen="base")


def hoja(m, revision):
    comun.preparar_revision()
    import _etapa2 as e2
    import parrilla_carbon
    bolsa = [m["obj"]]
    cuadros = e2.sacar_fotos([
        ("Frente (cliente, +Z) · día", bolsa, "frente", "dia"),
        ("Costado: el fuelle · día", bolsa, "costado", "dia"),
        ("3/4 · día", bolsa, "tres_cuartos", "dia"),
        ("Arriba: el doblez y la manija · día", bolsa, "arriba", "dia"),
        ("3/4 · atardecer", bolsa, "tres_cuartos", "atardecer"),
    ])
    p = parrilla_carbon.construir()
    p["raiz"].location = piezas.g2b((0.6, 0.0, 0.0))
    bpy.context.view_layer.update()
    cuadros += e2.sacar_fotos([
        ("Al lado de la parrilla (escala) · día", bolsa + [p["cuerpo"]], "tres_cuartos", "dia"),
    ])
    comun.componer_hoja(f"{ID} · 0,35 × 0,50 × 0,15 m · stock, papel madera", cuadros, revision,
                        comun.RAIZ / f"docs/arte/revisiones/{ID}.jpg")


def main():
    eq.main_modelo(ID, FAMILIA, construir, revisar, hoja, lambda m: [m["obj"]])


if __name__ == "__main__":
    main()
