"""Modelo: pancho armado (id `pancho`, godot/data/productos.ron).

Genera:
    arte/fuentes/comida/pancho.blend
    godot/modelos/comida/pancho.glb
    docs/arte/revisiones/pancho.jpg

Uso:
    blender -b -P tools/blender/modelos/pancho.py
    python tools/blender/modelos/pancho.py

No es un modelo nuevo (guía 5.1): son las mismas piezas que `pan_pancho` y `salchicha`,
combinadas bajo un objeto vacío `pancho`. La salchicha va hundida entre las dos mitades del
pan, con su centro a pan_pancho.SALCHICHA_Z del centro del pan, y sigue siendo la pieza
`pieza_salchicha` para que el juego le ponga el color de la cocción.

Como la salchicha queda adentro del pan, el pancho mide lo mismo que el pan:
0,17 × 0,045 × 0,055 m (hoy la colisión del dato es 0,17 × 0,06 × 0,055, porque la
salchicha va apoyada arriba; se ajusta cuando el juego cargue los .glb).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402

import comun  # noqa: E402
import pan_pancho  # noqa: E402
import salchicha as mod_salchicha  # noqa: E402

ID = "pancho"
MEDIDAS = pan_pancho.MEDIDAS
PRESUPUESTO = 600  # comida armada (guía 3.1)


def construir():
    raiz = bpy.data.objects.new(ID, None)
    raiz.empty_display_size = 0.05
    bpy.context.scene.collection.objects.link(raiz)
    pan = pan_pancho.construir()
    salchicha = mod_salchicha.construir()
    salchicha.location.z = pan_pancho.SALCHICHA_Z
    for pieza in (pan, salchicha):
        pieza.parent = raiz
    return raiz, pan, salchicha


def hoja_revision(raiz, pan, salchicha, revision):
    comun.preparar_revision()
    raiz.location.z = pan_pancho.MEDIO_ALTO
    # En el juego la salchicha del pancho siempre está cocida: la foto la muestra así.
    salchicha.data.materials[0] = comun.crear_material("ref_cocida", "#B84C33", rugosidad=0.6)
    piezas = [pan, salchicha]
    cuadros = comun.sacar_fotos([
        ("Frente (lo que ve el cliente) · día", piezas, "frente", "dia", False),
        ("Costado de cerca: salchicha hundida · día", piezas, "costado", "dia", True),
        ("3/4 · día", piezas, "tres_cuartos", "dia", False),
        ("Arriba · día", piezas, "arriba", "dia", False),
        ("3/4 · atardecer", piezas, "tres_cuartos", "atardecer", False),
    ])
    # Última foto: con el material real del archivo, para ver qué recibe el juego.
    salchicha.data.materials[0] = bpy.data.materials["M_SalchichaCruda"]
    cuadros += comun.sacar_fotos([
        ("Con el color del archivo (cruda; el juego la tiñe) · día", piezas, "tres_cuartos", "dia", False),
    ])
    comun.componer_hoja(
        "pancho · 0,17 × 0,045 × 0,055 m · comida armada (pan_pancho + salchicha)",
        cuadros, revision, comun.RAIZ / f"docs/arte/revisiones/{ID}.jpg",
    )


def main():
    comun.escena_vacia()
    raiz, pan, salchicha = construir()
    revision = comun.revisar([pan, salchicha], PRESUPUESTO, MEDIDAS, origen="centro")
    ok = comun.imprimir_revision(ID, revision)
    comun.guardar_blend(comun.RAIZ / f"arte/fuentes/comida/{ID}.blend")
    comun.exportar_glb([raiz, pan, salchicha], comun.RAIZ / f"godot/modelos/comida/{ID}.glb")
    if "--sin-hoja" not in sys.argv:
        hoja_revision(raiz, pan, salchicha, revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
