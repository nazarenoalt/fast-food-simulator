"""Modelo: cerco bajo de madera (id `cerco_bajo`, godot/data/accesorios.ron).

Genera:
    arte/fuentes/accesorios/cerco_bajo.blend
    godot/modelos/accesorios/cerco_bajo.glb
    docs/arte/revisiones/cerco_bajo.jpg

Uso:
    blender -b -P tools/blender/modelos/cerco_bajo.py
    python tools/blender/modelos/cerco_bajo.py

Forma: 2 postes de 0,06 × 0,06 con la punta en bisel (cuatro caras en punta, con las
esquinas achaflanadas) y 2 travesaños de 0,06 × 0,04 a 0,25 y 0,5 m, todo en M_Madera.

Respeta la `forma` de accesorios.ron: postes en x = ±1,2 de 0,6 de alto, travesaños
centrados en z = 0, caja total 2,46 × 0,6 × 0,06. Diferencia: en el dato los travesaños
miden 2,46 y atraviesan los postes (sus puntas quedarían pegadas a la cara de afuera del
poste y parpadearían); acá van **entre** los postes (2,34 m, encastrados), así que el
largo total lo dan los postes y no cambia.

Objetos (hijos del Empty `cerco_bajo`, origen = centro de la base, a nivel del piso, como el
anclaje `frente`):
- `cerco_bajo_cuerpo`: la malla visible.
- `cerco_bajo-colonly`: una sola caja de 2,46 × 0,6 × 0,06 (el cerco no deja pasar; los
  huecos entre travesaños no hacen falta para nada).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import bpy  # noqa: E402, F401
import bmesh  # noqa: E402

import comun  # noqa: E402
import piezas  # noqa: E402
from piezas import g2b  # noqa: E402

ID = "cerco_bajo"
FAMILIA = "accesorios"
PRESUPUESTO = 600  # guía 3.1 / lista-de-modelos
MEDIDAS = (2.46, 0.6, 0.06)

POSTE_X, POSTE, ALTO = 1.2, 0.06, 0.6
ARRANQUE_PUNTA = 0.53     # donde empieza la punta
CHAFLAN = 0.01            # esquinas del poste (bisel de muebles/accesorios, guía 3.3)
TRAVESANOS_Y = (0.25, 0.5)
TRAVESANO = (0.06, 0.04)  # alto, profundidad


def anillo_poste(x, y, medio=POSTE / 2, c=CHAFLAN):
    """Cuadrado con esquinas achaflanadas (8 puntos en orden, en el plano XZ de Godot)."""
    m, k = medio, medio - c
    return [(x + px, y, pz) for px, pz in
            ((m, -k), (m, k), (k, m), (-k, m), (-m, k), (-m, -k), (-k, -m), (k, -m))]


def poste(bm, x):
    abajo = [bm.verts.new(g2b(p)) for p in anillo_poste(x, 0.0)]
    arriba = [bm.verts.new(g2b(p)) for p in anillo_poste(x, ARRANQUE_PUNTA)]
    # Un anillo un poco más arriba y más finito: la punta arranca con un quiebre suave.
    medio = [bm.verts.new(g2b(p)) for p in anillo_poste(x, ARRANQUE_PUNTA + 0.025, POSTE / 2 * 0.62, CHAFLAN * 0.62)]
    punta = bm.verts.new(g2b((x, ALTO, 0)))
    n = len(abajo)
    for a, b in ((abajo, arriba), (arriba, medio)):
        for k in range(n):
            bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]))
    for k in range(n):
        bm.faces.new((medio[k], medio[(k + 1) % n], punta))


def construir():
    (madera,) = comun.cargar_materiales("M_Madera")
    bm = bmesh.new()
    for sx in (-1, 1):
        poste(bm, sx * POSTE_X)
    largo = 2 * (POSTE_X - POSTE / 2)
    for y in TRAVESANOS_Y:
        caras = piezas.caja(bm, (largo, TRAVESANO[0], TRAVESANO[1]), (0, y, 0), bisel=0.008)
        # Las puntas quedan pegadas a los postes: nunca se ven (guía 3.6).
        tapas = []
        for f in caras:
            f.normal_update()
            if abs(f.normal.x) > 0.999:
                tapas.append(f)
        bmesh.ops.delete(bm, geom=tapas, context="FACES")
    cuerpo = piezas.terminar(f"{ID}_cuerpo", bm, [madera])
    col = piezas.colision_caja(ID, MEDIDAS, (0, ALTO / 2, 0))
    raiz = piezas.raiz(ID, [cuerpo, col])
    return raiz, cuerpo, col


def hoja_revision(cuerpo, revision):
    comun.preparar_revision()
    persona = bpy.data.objects["ref_persona_1,75m"]
    persona.location = (0.0, 0.6, 0)
    solo = [cuerpo]
    cuadros = comun.sacar_fotos([
        ("Frente · día", solo, "frente", "dia", True),
        ("Costado de cerca · día", solo, "costado", "dia", True),
        ("3/4 · día", solo, "tres_cuartos", "dia", False),
        ("Con la persona de 1,75 m · día", solo + [persona], "tres_cuartos", "dia", False),
        ("3/4 · atardecer", solo, "tres_cuartos", "atardecer", False),
        ("Arriba · día", solo, "arriba", "dia", True),
    ])
    comun.componer_hoja(
        "cerco_bajo · 2,46 × 0,6 × 0,06 m · accesorio",
        cuadros, revision, comun.RAIZ / f"docs/arte/revisiones/{ID}.jpg",
    )


def main():
    comun.escena_vacia()
    raiz, cuerpo, col = construir()
    revision = comun.revisar(cuerpo, PRESUPUESTO, MEDIDAS, origen="base")
    ok = comun.imprimir_revision(ID, revision)
    comun.guardar_blend(comun.RAIZ / f"arte/fuentes/{FAMILIA}/{ID}.blend")
    comun.exportar_glb([raiz, cuerpo, col], comun.RAIZ / f"godot/modelos/{FAMILIA}/{ID}.glb")
    if "--sin-hoja" not in sys.argv:
        hoja_revision(cuerpo, revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
