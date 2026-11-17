"""Modelo: hamburguesa armada (id `hamburguesa`, etapa 4; sin dato todavía).

Genera:
    arte/fuentes/comida/hamburguesa.blend
    godot/modelos/comida/hamburguesa.glb
    docs/arte/revisiones/hamburguesa.jpg

Uso:
    blender -b -P tools/blender/modelos/hamburguesa.py
    python tools/blender/modelos/hamburguesa.py

No es un modelo nuevo (guía 5.1): son las mismas piezas, apiladas bajo un objeto vacío
`hamburguesa`, sin atravesarse:
    pan_hamburguesa_abajo   y de −0,045 a −0,015   (base, miga arriba)
    pieza_carne             y de −0,015 a −0,003   (el medallón: el juego le pone la cocción)
    pieza_queso             cara de arriba en 0,0  (la feta, con la forma `derretida` aplicada
                                                    y girada 20°; el juego la oculta si no lleva)
    pan_hamburguesa_arriba  y de 0,0 a 0,045       (tapa)
Total: Ø 0,11 × 0,09 (lista de modelos). Sin queso, la tapa baja 3 mm (Y_TAPA − 0,003).
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402
from mathutils import Matrix  # noqa: E402

import comun  # noqa: E402
import _comida4 as c4  # noqa: E402
import _etapa2 as e2  # noqa: E402
import feta_queso  # noqa: E402
import medallon  # noqa: E402
import pan_hamburguesa_abajo as abajo  # noqa: E402
import pan_hamburguesa_arriba as arriba  # noqa: E402

ID = "hamburguesa"
MEDIDAS = (2 * c4.R_PAN, c4.ALTO_HAMBURGUESA, 2 * c4.R_PAN)
PRESUPUESTO = 600  # comida armada (guía 3.1)
GIRO_QUESO = 20    # grados: las puntas no se salen de la caja de Ø 0,11


def construir():
    raiz = bpy.data.objects.new(ID, None)
    raiz.empty_display_size = 0.05
    bpy.context.scene.collection.objects.link(raiz)
    base = abajo.construir()
    carne = medallon.construir()
    queso = feta_queso.construir("pieza_queso", derretida=1.0, forma_clave=False)
    queso.data.transform(Matrix.Rotation(math.radians(GIRO_QUESO), 4, "Z"))
    tapa = arriba.construir()
    base.location.z = c4.Y_BASE
    carne.location.z = c4.Y_CARNE
    queso.location.z = c4.Y_QUESO_ARRIBA - feta_queso.H
    tapa.location.z = c4.Y_TAPA
    piezas = [base, carne, queso, tapa]
    for p in piezas:
        p.parent = raiz
    return raiz, piezas


def chequeo_pila(piezas):
    """Cada pieza empieza donde termina la de abajo (sin atravesarse)."""
    base, carne, queso, tapa = piezas
    mn = lambda o: e2.limites_godot([o])[0].y  # noqa: E731
    mx = lambda o: e2.limites_godot([o])[1].y  # noqa: E731
    ok = (abs(mx(base) - mn(carne)) < 1e-4 and abs(mx(queso) - mn(tapa)) < 1e-4
          and mx(carne) <= mx(queso) - feta_queso.ALTO + 1e-4)
    return ok, ("Pila sin atravesarse: base hasta %.3f, carne %.3f a %.3f, queso hasta %.3f, tapa desde %.3f"
                % (mx(base), mn(carne), mx(carne), mx(queso), mn(tapa)))


def hoja_revision(raiz, piezas, revision):
    base, carne, queso, tapa = piezas
    comun.preparar_revision()
    raiz.location.z = c4.ALTO_HAMBURGUESA / 2
    bpy.context.view_layer.update()
    # En el juego la hamburguesa siempre lleva la carne cocida: la foto la muestra así.
    carne.data.materials[0] = c4.material_ref("carne_cocida", c4.COCCION_CARNE[1][1])
    # Sin queso: la tapa baja 3 mm.
    dx = 0.3
    sin = [e2.copiar(o, f"ref_sin_{o.name}") for o in (base, carne, tapa)]
    for o, src in zip(sin, (base, carne, tapa)):
        o.parent = None
        o.matrix_world = src.matrix_world.copy()
        o.location.x += dx
    sin[2].location.z -= feta_queso.ALTO
    # Abierta: la tapa al costado, para ver cómo apoya cada capa.
    ab = [e2.copiar(o, f"ref_ab_{o.name}") for o in piezas]
    for o, src in zip(ab, piezas):
        o.parent = None
        o.matrix_world = src.matrix_world.copy()
        o.location.x += 2 * dx
    ab[3].location.x += 0.13
    ab[3].location.z = c4.ALTO_TAPA / 2
    cuadros = e2.sacar_fotos([
        ("Frente (lo que ve el cliente) · día", piezas, "frente", "dia"),
        ("Costado de cerca · día", piezas, "costado", "dia", piezas, 1.05),
        ("3/4 · día", piezas, "tres_cuartos", "dia"),
        ("3/4 · atardecer", piezas, "tres_cuartos", "atardecer"),
        ("Sin queso (pieza_queso oculta, tapa −3 mm) · día", sin, "tres_cuartos", "dia"),
        ("Abierta · día", ab, "tres_cuartos", "dia"),
    ])
    carne.data.materials[0] = bpy.data.materials["M_CarneCruda"]
    for o in sin + ab:
        o.hide_render = True
    ref = c4.pan_de_escala(0.0, -0.11)
    cuadros += e2.sacar_fotos([
        ("Con el color del archivo (carne cruda; el juego la tiñe) · día", piezas, "bajo", "dia"),
        ("Al lado de un pan de pancho · día", piezas + [ref], "tres_cuartos", "dia"),
    ])
    c4.hoja(ID, f"{ID} · Ø 0,11 × 0,09 m · comida armada (base + medallón + queso + tapa)",
            cuadros, revision)


def main():
    comun.escena_vacia()
    raiz, piezas = construir()
    revision = comun.revisar(piezas, PRESUPUESTO, MEDIDAS, origen="centro")
    revision.insert(1, chequeo_pila(piezas))
    ok = comun.imprimir_revision(ID, revision)
    c4.guardar_y_exportar(ID, [raiz] + piezas)
    if "--sin-hoja" not in sys.argv:
        hoja_revision(raiz, piezas, revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
