"""Modelo: repuesto de aderezo (id `repuesto_aderezo`, uno para `repuesto_mostaza`,
`repuesto_ketchup` y `repuesto_mayonesa` de godot/data/productos.ron).

Genera:
    arte/fuentes/stock/repuesto_aderezo.blend
    godot/modelos/stock/repuesto_aderezo.glb
    docs/arte/revisiones/repuesto_aderezo.jpg

Uso:
    blender -b -P tools/blender/modelos/repuesto_aderezo.py
    python tools/blender/modelos/repuesto_aderezo.py

Forma: botella petisa y ancha de medio kilo (12 lados), de plástico del color del aderezo,
con hombro redondeado, cuello corto, tapa a rosca negra y una etiqueta lisa alrededor (el
texto, con un nombre inventado, queda pendiente: guía 4.5). Se distingue del pomo por la
silueta: el pomo es flaco y con pico; el repuesto es gordo y con tapa chata.

Un solo modelo para los tres repuestos (guía 4.2, regla 5), como hoy: las tres `forma` son
iguales y solo cambia el color del cuerpo. El cuerpo es `pieza_cuerpo` (M_Amarillo en el
archivo = mostaza); el juego le pone el color del aderezo que repone (`repone` → `color` de
aderezos.ron, o el color de la `forma` de hoy, que es el mismo).

Medidas: la colisión del dato, Caja(0,08 × 0,19 × 0,08): Ø 0,078 × 0,19. La `forma` de hoy
asoma 2,5 mm arriba de la colisión (la tapa llega a 0,0975); acá la tapa termina justo en el
borde de la caja (0,095), para que lo que se ve coincida con lo que choca.
Origen: el centro (= centro de la colisión), porque se agarra con la mano (guía 2.4).

Objetos (hijos del Empty `repuesto_aderezo`), sin colisión (la pone el dato):
- `pieza_cuerpo` (M_Amarillo): el cuerpo de color.
- `repuesto_aderezo_tapa_etiqueta`: etiqueta (M_BlancoCrema) y tapa (M_PlasticoNegro).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

import comun  # noqa: E402
import piezas  # noqa: E402
import _etapa2 as e2  # noqa: E402

ID = "repuesto_aderezo"
FAMILIA = "stock"
PRESUPUESTO = 400  # empaques (guía 3.1)

ANCHO, ALTO = 0.078, 0.19          # colisión del dato (0,08 × 0,19 × 0,08), sin el 1 mm de aire
R_CUERPO = 0.0385
R_ETIQUETA = ANCHO / 2             # 0,039: la etiqueta es lo más ancho
ABAJO, ARRIBA = -ALTO / 2, ALTO / 2
LADOS = 12                         # guía 3.2: radio 1,5–5 cm

MEDIDAS = (ANCHO, ALTO, ANCHO)

# (radio, y) de abajo hacia arriba.
PERFIL_CUERPO = [
    (0.0, ABAJO),
    (0.0335, ABAJO),
    (R_CUERPO, ABAJO + 0.005),
    (R_CUERPO, 0.040),
    (0.0355, 0.054),
    (0.0285, 0.064),
    (0.0175, 0.0695),
    (0.0175, 0.075),
    (0.0, 0.075),
]
PERFIL_ETIQUETA = [      # banda apenas más gruesa que el cuerpo, con sus dos escalones
    (R_CUERPO, -0.045),
    (R_ETIQUETA, -0.0445),
    (R_ETIQUETA, 0.0245),
    (R_CUERPO, 0.025),
]
PERFIL_TAPA = [
    (0.0175, 0.068),
    (0.0198, 0.0695),
    (0.0198, 0.092),
    (0.0178, ARRIBA),
    (0.0, ARRIBA),
]


def construir():
    m_cuerpo, m_etiqueta, m_tapa = comun.cargar_materiales("M_Amarillo", "M_BlancoCrema", "M_PlasticoNegro")
    bm = bmesh.new()
    e2.torno(bm, PERFIL_CUERPO, LADOS)
    cuerpo = piezas.terminar("pieza_cuerpo", bm, [m_cuerpo])

    bm = bmesh.new()
    e2.torno(bm, PERFIL_ETIQUETA, LADOS, mats=0)
    e2.torno(bm, PERFIL_TAPA, LADOS, mats=1)
    resto = piezas.terminar(f"{ID}_tapa_etiqueta", bm, [m_etiqueta, m_tapa])

    raiz = piezas.raiz(ID, [cuerpo, resto])
    return raiz, cuerpo, resto


# ── Hoja de revisión ───────────────────────────────────────────────────

def tres_colores(cuerpo, resto, desplazamiento=Vector((0, 0, 0)), separacion=0.1):
    """Copias con los tres colores de aderezo (solo para las fotos)."""
    mats = e2.materiales_aderezo(rugosidad=0.5)
    objs = []
    for i, (nombre, _) in enumerate(e2.ADEREZOS):
        d = desplazamiento + Vector(((i - 1) * separacion, 0, 0))
        c = e2.copiar(cuerpo, f"ref_cuerpo_{nombre}", mats[nombre])
        r = e2.copiar(resto, f"ref_resto_{nombre}")
        for o in (c, r):
            o.parent = None
            o.location = d
        objs += [c, r]
    return objs


def hoja_revision(raiz, vis, revision):
    cuerpo, resto = vis
    comun.preparar_revision()
    raiz.location.z = ALTO / 2
    bpy.context.view_layer.update()
    tres = tres_colores(cuerpo, resto, Vector((0.5, 0, ALTO / 2)))
    import pomo_aderezo
    praiz, envase, tapa, relleno, col = pomo_aderezo.construir()
    bpy.data.objects.remove(col)
    e2.sin_cara_de_atras(envase)
    praiz.location = (0.5 + 0.07, 0.09, 0)
    pan_obj = __import__("pan_pancho").construir("ref_pan")
    pan_obj.location = (0.5 - 0.02, -0.09, 0.0225)
    cuadros = e2.sacar_fotos([
        ("Frente · día", vis, "frente", "dia"),
        ("Costado · día", vis, "costado", "dia"),
        ("3/4 · día", vis, "tres_cuartos", "dia"),
        ("3/4 · atardecer", vis, "tres_cuartos", "atardecer"),
        ("Mostaza, ketchup y mayonesa · día", tres, "tres_cuartos", "dia"),
        ("Con un pomo y un pan de pancho · día", tres[2:4] + [envase, tapa, relleno, pan_obj], "tres_cuartos", "dia"),
    ])
    comun.componer_hoja(
        f"{ID} · Ø 0,078 × 0,19 m · un modelo para los tres repuestos (color por código)",
        cuadros, revision, comun.RAIZ / f"docs/arte/revisiones/{ID}.jpg",
    )


def main():
    comun.escena_vacia()
    raiz, cuerpo, resto = construir()
    vis = [cuerpo, resto]
    revision = comun.revisar(vis, PRESUPUESTO, MEDIDAS, origen="centro")
    ok = comun.imprimir_revision(ID, revision)
    comun.guardar_blend(comun.RAIZ / f"arte/fuentes/{FAMILIA}/{ID}.blend")
    comun.exportar_glb([raiz, cuerpo, resto], comun.RAIZ / f"godot/modelos/{FAMILIA}/{ID}.glb")
    if "--sin-hoja" not in sys.argv:
        hoja_revision(raiz, vis, revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
