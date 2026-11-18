"""Modelo: pan de pancho cerrado, entero, sin cortar (id `pan_pancho_cerrado`).

Genera:
    arte/fuentes/comida/pan_pancho_cerrado.blend
    godot/modelos/comida/pan_pancho_cerrado.glb
    docs/arte/revisiones/pan_pancho_cerrado.jpg

Uso:
    blender -b -P tools/blender/modelos/pan_pancho_cerrado.py
    python tools/blender/modelos/pan_pancho_cerrado.py

Forma: el mismo pan que `pan_pancho` (mismo largo, mismas puntas, mismas medidas), pero
entero: un bollo con el lomo redondeado y solo corteza. Comparte con el pan abierto las
estaciones y la forma de las puntas, así los dos se ven como el mismo pan.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402, F401  (carga Blender)

import comun  # noqa: E402
import pan_pancho  # noqa: E402

ID = "pan_pancho_cerrado"
MEDIDAS = pan_pancho.MEDIDAS
PRESUPUESTO = pan_pancho.PRESUPUESTO
MEDIO_ALTO, MEDIO_ANCHO = pan_pancho.MEDIO_ALTO, pan_pancho.MEDIO_ANCHO

# Medio perfil del corte transversal (y, z), de la base al centro del lomo. Se espeja.
PERFIL = [
    (0.0, -MEDIO_ALTO),       # base, casi plana
    (0.017, -0.021),
    (0.026, -0.010),
    (MEDIO_ANCHO, 0.003),     # lo más ancho
    (0.0255, 0.0135),
    (0.019, 0.0205),
    (0.0095, 0.0223),
    (0.0, MEDIO_ALTO),        # lomo
]


def anillo(x):
    s, cz = pan_pancho.escala_punta(x), pan_pancho.CENTRO_ESCALA_Z
    completo = PERFIL + [(-y, z) for y, z in reversed(PERFIL[1:-1])]
    return [(x, y * s, cz + (z - cz) * s) for y, z in completo]


def construir(nombre=ID):
    materiales = comun.cargar_materiales("M_PanCorteza")
    anillos = [anillo(x) for x in pan_pancho.ESTACIONES]
    return comun.lofteo(nombre, anillos, pan_pancho.puntas(anillos), materiales)


def hoja_revision(pan, revision):
    comun.preparar_revision()
    pan.location.z = MEDIO_ALTO
    abierto = pan_pancho.construir("ref_pan_abierto")
    abierto.location = (0, 0.075, MEDIO_ALTO)
    solo = [pan]
    cuadros = comun.sacar_fotos([
        ("Frente · día", solo, "frente", "dia", False),
        ("Costado de cerca · día", solo, "costado", "dia", True),
        ("3/4 · día", solo, "tres_cuartos", "dia", False),
        ("Arriba · día", solo, "arriba", "dia", False),
        ("3/4 · atardecer", solo, "tres_cuartos", "atardecer", False),
        ("Junto al pan abierto · día", [pan, abierto], "tres_cuartos", "dia", False),
    ])
    comun.componer_hoja(
        "pan_pancho_cerrado · 0,17 × 0,045 × 0,055 m · comida chica",
        cuadros, revision, comun.RAIZ / f"docs/arte/revisiones/{ID}.jpg",
    )


def main():
    comun.escena_vacia()
    pan = construir()
    revision = comun.revisar(pan, PRESUPUESTO, MEDIDAS, origen="centro")
    ok = comun.imprimir_revision(ID, revision)
    comun.guardar_blend(comun.RAIZ / f"arte/fuentes/comida/{ID}.blend")
    comun.exportar_glb([pan], comun.RAIZ / f"godot/modelos/comida/{ID}.glb")
    if "--sin-hoja" not in sys.argv:
        hoja_revision(pan, revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
