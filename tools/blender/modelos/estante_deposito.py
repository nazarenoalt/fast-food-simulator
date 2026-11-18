"""Modelo: estante de depósito (id `estante_deposito`, godot/data/accesorios.ron).

Genera:
    arte/fuentes/accesorios/estante_deposito.blend
    godot/modelos/accesorios/estante_deposito.glb
    docs/arte/revisiones/estante_deposito.jpg

Uso:
    blender -b -P tools/blender/modelos/estante_deposito.py
    python tools/blender/modelos/estante_deposito.py

Forma: estante de ángulo ranurado. 4 parantes de ángulo (perfil en L, MetalOscuro) en las
esquinas, 3 tablas de madera (MaderaClara) y un ángulo debajo del frente y de atrás de cada
tabla, más un travesaño abajo (frente y atrás) que ata las patas. Regatones de goma de
2 cm al pie de cada parante.

Respeta la `forma` de accesorios.ron: parantes de 0,03 × 1,0 en (±0,25, ±0,19), tablas
centradas a 0,35, 0,75 y 1,0 m (la de arriba asoma 1 cm sobre los parantes) y caja total
0,53 × 1,01 × 0,41. Las tablas miden 0,51 × 0,39 (1 cm menos por lado que la caja del
dato) para quedar adentro de los ángulos sin atravesarlos; arriba quedan a la misma altura
(0,36 y 0,76), así que los lugares no cambian.

Objetos (hijos del Empty `estante_deposito`, origen = centro de la base, a nivel del piso):
- `estante_deposito_cuerpo`: toda la malla visible.
- `punto_lugar_1..4`: Empties en los `lugares` de accesorios.ron (en ese orden).
- `estante_deposito-colonly`: colisión con las mismas 7 cajas de la `forma` del dato
  (tablas y parantes), para que los bloques del depósito se apoyen en las tablas.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import bpy  # noqa: E402
import bmesh  # noqa: E402

import comun  # noqa: E402
import piezas  # noqa: E402

ID = "estante_deposito"
FAMILIA = "accesorios"
PRESUPUESTO = 1000  # accesorios medianos (guía 3.1)
MEDIDAS = (0.53, 1.01, 0.41)

PARANTE_X, PARANTE_Z, ALA, ESP = 0.25, 0.19, 0.03, 0.01   # ángulo de 3 cm × 1 cm
ALTO_PARANTE = 1.0
REGATON = 0.02
TABLAS_Y = (0.35, 0.75, 1.0)
TABLA = (0.51, 0.02, 0.39)
LUGARES = [(-0.12, 0.76, 0), (0.12, 0.76, 0), (-0.12, 0.36, 0), (0.12, 0.36, 0)]
X_AFUERA, Z_AFUERA = PARANTE_X + ALA / 2, PARANTE_Z + ALA / 2   # 0,265 y 0,205


def construir():
    metal, madera, goma = comun.cargar_materiales("M_MetalOscuro", "M_MaderaClara", "M_Goma")
    bm = bmesh.new()
    largo_x = 2 * (X_AFUERA - ALA)           # entre parantes, de frente
    for sx in (-1, 1):
        for sz in (-1, 1):
            # Parante: ángulo en L con las alas hacia afuera (una en cada cara).
            # (arranca arriba del regatón; la cara de abajo queda tapada por él)
            alto, yc = ALTO_PARANTE - REGATON, (ALTO_PARANTE + REGATON) / 2
            piezas.caja(bm, (ALA, alto, ESP), (sx * PARANTE_X, yc, sz * (Z_AFUERA - ESP / 2)),
                        mat=0, bisel=0.003, sin_abajo=True)
            piezas.caja(bm, (ESP, alto, ALA), (sx * (X_AFUERA - ESP / 2), yc, sz * PARANTE_Z),
                        mat=0, bisel=0.003, sin_abajo=True)
            # Regatón de goma: el pie del parante, del mismo ancho que el ángulo.
            piezas.caja(bm, (ALA, REGATON, ALA), (sx * PARANTE_X, REGATON / 2, sz * PARANTE_Z),
                        mat=2, bisel=0.003, sin_abajo=True)
    for y in TABLAS_Y:
        piezas.caja(bm, TABLA, (0, y, 0), mat=1, bisel=0.006)
        # Ángulos de apoyo debajo del frente y de atrás de la tabla.
        for sz in (-1, 1):
            piezas.caja(bm, (largo_x, 0.03, ESP), (0, y - TABLA[1] / 2 - 0.015, sz * (Z_AFUERA - ESP / 2)),
                        mat=0, bisel=0.003)
    # Travesaños de abajo (frente y atrás) que atan las patas.
    for sz in (-1, 1):
        piezas.caja(bm, (largo_x, 0.03, ESP), (0, 0.07, sz * (Z_AFUERA - ESP / 2)), mat=0, bisel=0.003)
    cuerpo = piezas.terminar(f"{ID}_cuerpo", bm, [metal, madera, goma])

    # Colisión: las 7 cajas de la forma del dato, en un solo objeto.
    bm = bmesh.new()
    for sx in (-1, 1):
        for sz in (-1, 1):
            piezas.caja(bm, (0.03, 1.0, 0.03), (sx * PARANTE_X, 0.5, sz * PARANTE_Z))
    for y in TABLAS_Y:
        piezas.caja(bm, (0.53, 0.02, 0.41), (0, y, 0))
    col = colision(bm)

    puntos = [piezas.punto(f"punto_lugar_{i + 1}", p) for i, p in enumerate(LUGARES)]
    raiz = piezas.raiz(ID, [cuerpo, col] + puntos)
    return raiz, cuerpo, col, puntos


def colision(bm):
    """Objeto `<id>-colonly` con varias cajas (piezas.colision_caja hace una sola por
    objeto, y repetir el nombre le agregaría '.001')."""
    malla = bpy.data.meshes.new(f"{ID}-colonly")
    bm.to_mesh(malla)
    bm.free()
    obj = bpy.data.objects.new(f"{ID}-colonly", malla)
    bpy.context.scene.collection.objects.link(obj)
    obj.display_type = "WIRE"
    obj.hide_render = True
    return obj


def chequeo_lugares(puntos):
    ok = all((p.location - piezas.g2b(l)).length < 1e-6 for p, l in zip(puntos, LUGARES))
    arriba = {round(y + TABLA[1] / 2, 4) for y in TABLAS_Y[:2]}
    ok = ok and arriba == {l[1] for l in LUGARES}
    return ok, "punto_lugar_1..4 en los lugares de accesorios.ron, sobre las tablas de 0,35 y 0,75"


def hoja_revision(raiz, cuerpo, revision):
    comun.preparar_revision()
    persona = bpy.data.objects["ref_persona_1,75m"]
    persona.location = (0.7, 0.15, 0)
    solo = [cuerpo]
    cuadros = comun.sacar_fotos([
        ("Frente · día", solo, "frente", "dia", True),
        ("Costado · día", solo, "costado", "dia", True),
        ("3/4 · día", solo, "tres_cuartos", "dia", False),
        ("Al lado de la persona de 1,75 m · día", solo + [persona], "frente", "dia", True),
        ("3/4 · atardecer", solo, "tres_cuartos", "atardecer", False),
        ("Arriba · día", solo, "arriba", "dia", True),
    ])
    comun.componer_hoja(
        "estante_deposito · 0,53 × 1,01 × 0,41 m · accesorio mediano",
        cuadros, revision, comun.RAIZ / f"docs/arte/revisiones/{ID}.jpg",
    )


def main():
    comun.escena_vacia()
    raiz, cuerpo, col, puntos = construir()
    revision = comun.revisar(cuerpo, PRESUPUESTO, MEDIDAS, origen="base")
    revision.insert(1, chequeo_lugares(puntos))
    ok = comun.imprimir_revision(ID, revision)
    comun.guardar_blend(comun.RAIZ / f"arte/fuentes/{FAMILIA}/{ID}.blend")
    comun.exportar_glb([raiz, cuerpo, col] + puntos, comun.RAIZ / f"godot/modelos/{FAMILIA}/{ID}.glb")
    if "--sin-hoja" not in sys.argv:
        hoja_revision(raiz, cuerpo, revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
