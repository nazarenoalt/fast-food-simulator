"""Modelo: pallet del proveedor (id `pallet`, el que arma carrito.rs al costado del carrito,
del lado del vendedor, donde aparecen los paquetes que llegan: REQ-PRO-04).

Genera:
    arte/fuentes/stock/pallet.blend
    godot/modelos/stock/pallet.glb
    docs/arte/revisiones/pallet.jpg

Uso:
    blender -b -P tools/blender/modelos/pallet.py
    python tools/blender/modelos/pallet.py

Forma: pallet de madera de tacos. Abajo, 3 tablas a lo largo de Z (en x = −0,35 / 0 /
0,35, donde hoy están los 3 largueros); encima, 9 tacos de madera más oscura (3 por tabla) y,
arriba, 5 tablas a lo largo de X con 2,5 cm de luz entre una y otra. Entre los tacos quedan
los huecos para la zorra, que es lo que lo hace reconocible.

Medidas = lo que arma hoy carrito.rs: 0,80 × 0,12 × 0,60 (tabla de arriba 0,8 × 0,03 × 0,6
y 3 largueros de 0,1 × 0,09 × 0,6). Mismos colores que hoy: madera clara arriba y abajo
(M_MaderaClara) y tacos más oscuros (M_Madera).
Bisel de 5 mm (no 1 cm): las tablas tienen 2,2–3 cm de espesor y con 1 cm quedaban como
almohadones.
Origen: centro de la base, a nivel del piso (hoy el nodo `Pallet` está en
(ancho/2 + 1,35; 0; −1,0) de la base, sin giro).

Objetos (hijos del Empty `pallet`):
- `pallet_cuerpo` (M_MaderaClara, M_Madera).
- `pallet-colonly`: una caja de 0,80 × 0,12 × 0,60 (hoy, la tabla y los 3 largueros;
  arriba es igual, que es donde se apoyan los paquetes).
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
from piezas import g2b  # noqa: E402
import _etapa2 as e2  # noqa: E402

ID = "pallet"
FAMILIA = "stock"
PRESUPUESTO = 800  # mueble grande de fondo (como mobiliario urbano, guía 3.1)

ANCHO, ALTO, FONDO = 0.80, 0.12, 0.60
XS = (-0.35, 0.0, 0.35)          # largueros de hoy
ZS = (-0.25, 0.0, 0.25)          # tacos
ALTO_ABAJO, ALTO_TACO, ALTO_ARRIBA = 0.022, 0.068, 0.030
ANCHO_TABLA = 0.10
N_ARRIBA, LUZ = 5, 0.025
BISEL = 0.005
CLARA, OSCURA = 0, 1

MEDIDAS = (ANCHO, ALTO, FONDO)


def construir():
    mats = comun.cargar_materiales("M_MaderaClara", "M_Madera")
    bm = bmesh.new()
    y = 0.0
    for x in XS:  # tablas de abajo (sin cara de abajo: apoyan en el piso)
        piezas.caja(bm, (ANCHO_TABLA, ALTO_ABAJO, FONDO), (x, ALTO_ABAJO / 2, 0), mat=CLARA,
                    bisel=BISEL, sin_abajo=True)
    y = ALTO_ABAJO
    for x in XS:  # tacos (sin arriba ni abajo: quedan tapados por las tablas)
        for z in ZS:
            c = piezas.caja(bm, (ANCHO_TABLA - 0.006, ALTO_TACO + 0.002, ANCHO_TABLA - 0.004),
                            (x, y + ALTO_TACO / 2, z), mat=OSCURA, bisel=0.003)
            e2.borrar_caras(bm, c, (0, 1, 0))
            e2.borrar_caras(bm, c, (0, -1, 0))
    y += ALTO_TACO
    paso = ANCHO_TABLA + LUZ
    for i in range(N_ARRIBA):  # tablas de arriba
        z = (i - (N_ARRIBA - 1) / 2) * paso
        piezas.caja(bm, (ANCHO, ALTO_ARRIBA, ANCHO_TABLA), (0, y + ALTO_ARRIBA / 2, z), mat=CLARA,
                    bisel=BISEL)
    cuerpo = piezas.terminar(f"{ID}_cuerpo", bm, mats)
    col = piezas.colision_caja(ID, (ANCHO, ALTO, FONDO), (0, ALTO / 2, 0))
    raiz = piezas.raiz(ID, [cuerpo, col])
    return raiz, cuerpo, col


# ── Hoja de revisión ───────────────────────────────────────────────────

def hoja_revision(raiz, cuerpo, revision):
    comun.preparar_revision()
    persona = bpy.data.objects["ref_persona_1,75m"]
    persona.hide_render = False
    persona.location = (-0.75, 0.25, 0)
    solo = [cuerpo]
    # Paquetes recién llegados arriba: un pack de repuestos y una bandeja de salchichas.
    extras = []
    import pack_repuestos
    import repuesto_aderezo
    pack = pack_repuestos.construir()
    pack.location = g2b((-0.15, ALTO, 0.05))
    extras.append(pack)
    for pos in pack_repuestos.posiciones_unidades():
        r, c, resto = repuesto_aderezo.construir()
        r.location = pack.location + g2b(pos)
        extras += [c, resto]
    e2.sin_cara_de_atras(pack)
    ruta = comun.RAIZ / "godot/modelos/stock/caja_salchichas_12.glb"
    if ruta.exists():
        antes = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=str(ruta))
        nuevos = [o for o in bpy.data.objects if o not in antes and o.type == "MESH"]
        for o in nuevos:
            o.location = g2b((0.18, ALTO, -0.08))
            o.rotation_euler.z = 0.2
            e2.sin_cara_de_atras(o)
        extras += nuevos
    con = solo + extras
    cuadros = e2.sacar_fotos([
        ("Frente (cliente) · día", solo, "frente", "dia"),
        ("Costado · día", solo, "costado", "dia"),
        ("3/4 · día", solo, "tres_cuartos", "dia"),
        ("3/4 bajo: los huecos · día", solo, "bajo", "dia"),
        ("Con paquetes recién llegados · atardecer", con, "tres_cuartos", "atardecer"),
        ("Con la persona de 1,75 m · día", con + [persona], "tres_cuartos", "dia"),
    ])
    comun.componer_hoja(
        f"{ID} · 0,80 × 0,12 × 0,60 m · donde deja los paquetes el proveedor",
        cuadros, revision, comun.RAIZ / f"docs/arte/revisiones/{ID}.jpg",
    )


def main():
    comun.escena_vacia()
    raiz, cuerpo, col = construir()
    revision = comun.revisar([cuerpo], PRESUPUESTO, MEDIDAS, origen="base")
    ok = comun.imprimir_revision(ID, revision)
    comun.guardar_blend(comun.RAIZ / f"arte/fuentes/{FAMILIA}/{ID}.blend")
    comun.exportar_glb([raiz, cuerpo, col], comun.RAIZ / f"godot/modelos/{FAMILIA}/{ID}.glb")
    if "--sin-hoja" not in sys.argv:
        hoja_revision(raiz, cuerpo, revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
