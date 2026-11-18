"""Modelo: pan de hamburguesa, la base (id `pan_hamburguesa_abajo`, etapa 4; sin dato todavía).

Genera:
    arte/fuentes/comida/pan_hamburguesa_abajo.blend
    godot/modelos/comida/pan_hamburguesa_abajo.glb
    docs/arte/revisiones/pan_hamburguesa_abajo.jpg

Uso:
    blender -b -P tools/blender/modelos/pan_hamburguesa_abajo.py
    python tools/blender/modelos/pan_hamburguesa_abajo.py

Forma: la mitad de abajo de un pan de hamburguesa, Ø 0,11 × 0,03 (lista de modelos), 16 lados
(guía 3.2). Abajo es plano con el canto redondeado; el costado se infla un poco (guía 5.1:
un pan levemente inflado se lee mejor) y arriba está el corte: un disco de miga (M_PanMiga)
casi plano, apenas más alto en el centro, para que el medallón apoye en el medio. La corteza
(M_PanCorteza) termina en el borde del corte. Radio con una ondulación muy chica, para que
no parezca torneado. Sombreado suave (comida), con borde marcado solo entre corteza y miga.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402, F401
import bmesh  # noqa: E402

import comun  # noqa: E402
import _comida4 as c4  # noqa: E402
import _etapa2 as e2  # noqa: E402

ID = "pan_hamburguesa_abajo"
R, ALTO = c4.R_PAN, c4.ALTO_BASE
MEDIDAS = (2 * R, ALTO, 2 * R)
PRESUPUESTO = 200
LADOS = 16
H = ALTO / 2

# (radio, y) de abajo hacia arriba. Las bandas hasta el borde del corte son corteza.
PERFIL = [
    (0.0, -H),
    (0.043, -H),          # abajo plano
    (0.0522, -0.0108),
    (R, -0.0015),         # lo más ancho
    (0.0536, 0.0092),
    (0.0492, 0.0141),     # borde del corte (corteza → miga)
    (0.0, H),             # miga, apenas abombada en el centro
]
MATS = [0, 0, 0, 0, 0, 1]


def construir(nombre=ID):
    materiales = comun.cargar_materiales("M_PanCorteza", "M_PanMiga")
    ond = c4.ruido_angular(3, [(3, 0.008), (4, 0.006)])
    bm = bmesh.new()
    c4.torno(bm, PERFIL, LADOS, mats=MATS, radio=lambda k, i: ond(2 * math.pi * k / LADOS))
    c4.ajustar_caja(bm, MEDIDAS)
    return c4.terminar(nombre, bm, materiales)


def hoja_revision(pan, revision):
    comun.preparar_revision()
    pan.location.z = H
    import medallon
    carne = medallon.construir("ref_medallon")
    carne.data.materials[0] = c4.material_ref("carne_cocida", c4.COCCION_CARNE[1][1])
    carne.location = (0.3, 0, ALTO + c4.ALTO_CARNE / 2)
    base2 = e2.copiar(pan, "ref_base2")
    base2.location = (0.3, 0, H)
    ref = c4.pan_de_escala(0.0, -0.11)
    solo = [pan]
    cuadros = e2.sacar_fotos([
        ("Frente · día", solo, "frente", "dia"),
        ("Costado · día", solo, "costado", "dia"),
        ("3/4 · día: corte de miga arriba", solo, "tres_cuartos", "dia"),
        ("3/4 · atardecer", solo, "tres_cuartos", "atardecer"),
        ("Con el medallón (cocido) arriba · día", [base2, carne], "tres_cuartos", "dia"),
        ("Al lado de un pan de pancho · día", [pan, ref], "tres_cuartos", "dia"),
    ])
    c4.hoja(ID, f"{ID} · Ø 0,11 × 0,03 m · comida chica", cuadros, revision)


def main():
    comun.escena_vacia()
    pan = construir()
    revision = comun.revisar(pan, PRESUPUESTO, MEDIDAS, origen="centro")
    ok = comun.imprimir_revision(ID, revision)
    c4.guardar_y_exportar(ID, [pan])
    if "--sin-hoja" not in sys.argv:
        hoja_revision(pan, revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
