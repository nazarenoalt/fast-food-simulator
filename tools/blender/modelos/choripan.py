"""Modelo: choripán armado (id `choripan`, etapa 4; sin dato todavía).

Genera:
    arte/fuentes/comida/choripan.blend
    godot/modelos/comida/choripan.glb
    docs/arte/revisiones/choripan.jpg

Uso:
    blender -b -P tools/blender/modelos/choripan.py
    python tools/blender/modelos/choripan.py

No es un modelo nuevo (guía 5.1): son las mismas piezas que `pan_frances` y `chorizo`,
combinadas bajo un objeto vacío `choripan`, como el pancho. El chorizo va hundido en la U del
corte, con su centro a CHORIZO_Y = 0,017 del centro del pan (asoma 2 mm sobre el lomo de
las mitades), y sigue siendo `pieza_chorizo` para que el juego le ponga el color de la
cocción.

Medidas: 0,16 × 0,062 × 0,08 (la lista decía 0,07 de alto, con el chorizo apoyado arriba;
hundido queda 8 mm más bajo). El centro de la caja queda 1 mm por encima del centro del
pan: el pan va a y = −0,001 del origen del choripán.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402

import comun  # noqa: E402
import _comida4 as c4  # noqa: E402
import _etapa2 as e2  # noqa: E402
import chorizo as mod_chorizo  # noqa: E402
import pan_frances  # noqa: E402

ID = "choripan"
ARRIBA = max(pan_frances.MEDIO_ALTO, c4.CHORIZO_Y + c4.R_CHORIZO)   # 0,032
ABAJO = -pan_frances.MEDIO_ALTO
Y_PAN = -(ARRIBA + ABAJO) / 2                                       # −0,001
MEDIDAS = (pan_frances.MEDIDAS[0], ARRIBA - ABAJO, pan_frances.MEDIDAS[2])
PRESUPUESTO = 600


def construir():
    raiz = bpy.data.objects.new(ID, None)
    raiz.empty_display_size = 0.05
    bpy.context.scene.collection.objects.link(raiz)
    pan = pan_frances.construir()
    chorizo = mod_chorizo.construir()
    pan.location.z = Y_PAN
    chorizo.location.z = Y_PAN + c4.CHORIZO_Y
    for p in (pan, chorizo):
        p.parent = raiz
    return raiz, pan, chorizo


def hoja_revision(raiz, pan, chorizo, revision):
    comun.preparar_revision()
    raiz.location.z = MEDIDAS[1] / 2
    chorizo.data.materials[0] = c4.material_ref("chorizo_cocido", c4.COCCION_CHORIZO[1][1])
    piezas = [pan, chorizo]
    ref = c4.pan_de_escala(0.0, -0.09)
    cuadros = e2.sacar_fotos([
        ("Frente (lo que ve el cliente) · día", piezas, "frente", "dia"),
        ("Costado de cerca: chorizo hundido · día", piezas, "costado", "dia", piezas, 1.1),
        ("3/4 · día", piezas, "tres_cuartos", "dia"),
        ("Arriba · día", piezas, "arriba", "dia"),
        ("3/4 · atardecer", piezas, "tres_cuartos", "atardecer"),
        ("Al lado de un pan de pancho · día", piezas + [ref], "tres_cuartos", "dia"),
    ])
    chorizo.data.materials[0] = bpy.data.materials["M_CarneCruda"]
    ref.hide_render = True
    cuadros += e2.sacar_fotos([
        ("Con el color del archivo (crudo; el juego lo tiñe) · día", piezas, "tres_cuartos", "dia"),
    ])
    c4.hoja(ID, "choripan · 0,16 × 0,062 × 0,08 m · comida armada (pan_frances + chorizo)",
            cuadros, revision)


def main():
    comun.escena_vacia()
    raiz, pan, chorizo = construir()
    revision = comun.revisar([pan, chorizo], PRESUPUESTO, MEDIDAS, origen="centro")
    ok = comun.imprimir_revision(ID, revision)
    c4.guardar_y_exportar(ID, [raiz, pan, chorizo])
    if "--sin-hoja" not in sys.argv:
        hoja_revision(raiz, pan, chorizo, revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
