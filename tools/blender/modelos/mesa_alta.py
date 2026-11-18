"""Modelo: mesa alta redonda (id `mesa_alta`, lista de modelos, etapa 5).

Genera:
    arte/fuentes/accesorios/mesa_alta.blend
    godot/modelos/accesorios/mesa_alta.glb
    docs/arte/revisiones/mesa_alta.jpg

Uso:
    python tools/blender/modelos/mesa_alta.py [--sin-hoja]

Forma: mesa alta de bar para comer parado (o en banqueta) al lado del carrito. Tablero
redondo de madera clara (M_MaderaClara) de Ø 0,60 y 3 cm con el canto biselado, a 1,10 m;
debajo, un plato de acero que lo agarra; columna de caño de acero de Ø 6 cm y base de
fundición de acero, redonda y baja (Ø 0,46), que apoya en el piso.
Medidas: Ø 0,60 × 1,10 (lista). Origen: centro de la base, a nivel del piso.
Objetos (hijos del Empty `mesa_alta`): mesa_alta_cuerpo y `mesa_alta-colonly` (tablero,
columna y base: tres cilindros en un solo objeto).
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402, F401  (antes que bmesh)
import bmesh  # noqa: E402

import _accesorios5 as a5  # noqa: E402
import _plaza as plaza  # noqa: E402
import comun  # noqa: E402
import piezas  # noqa: E402

ID = "mesa_alta"
PRESUPUESTO = 500
RADIO, ALTO = 0.30, 1.10
MEDIDAS = (2 * RADIO, ALTO, 2 * RADIO)
TABLERO = 0.03
BISEL = 0.008                  # un cuarto del espesor (guía 3.3, tablas finas)
PLATO = (0.10, 0.02)           # radio, alto
COLUMNA = 0.03                 # radio (12 lados)
BASE = [(0.23, 0.0), (0.23, 0.012), (0.20, 0.026), (0.07, 0.045), (COLUMNA, 0.06)]


def construir():
    madera, acero = comun.cargar_materiales("M_MaderaClara", "M_Acero")
    bm = bmesh.new()
    y0 = ALTO - TABLERO
    # Tablero (24 lados: radio de 25 cm a 1 m, guía 3.2).
    plaza.torno(bm, [(RADIO - BISEL, y0), (RADIO, y0 + BISEL), (RADIO, ALTO - BISEL),
                     (RADIO - BISEL, ALTO)], 24, mats=[0, 0, 0], tapa_abajo=True, tapa_arriba=True)
    yp = y0 - PLATO[1]
    plaza.torno(bm, [(PLATO[0], yp), (PLATO[0], y0)], 12, mats=[1], tapa_abajo=True)
    # Columna (sin tapas: queda entre la base y el plato) y base (sin la cara apoyada).
    plaza.torno(bm, [(COLUMNA, BASE[-1][1]), (COLUMNA, yp)], 12, mats=[1])
    plaza.torno(bm, BASE, 16, mats=[1] * (len(BASE) - 1))
    cuerpo = piezas.terminar(f"{ID}_cuerpo", bm, [madera, acero])
    a5.e2.suavizar_hasta(cuerpo, 31)   # la columna de 12 lados dobla justo 30°: redonda

    col = plaza.colision_cajas(ID, [])  # objeto vacío: se llena abajo con tres cilindros
    bm = bmesh.new()
    for r, ya, yb, lados in ((RADIO, y0, ALTO, 24), (COLUMNA, 0.06, y0, 8), (0.23, 0.0, 0.06, 12)):
        piezas.cilindro(bm, r / math.cos(math.pi / lados), yb - ya,
                        (0, (ya + yb) / 2, 0), lados=lados)
    bm.to_mesh(col.data)
    bm.free()
    raiz = piezas.raiz(ID, [cuerpo, col])
    return raiz, cuerpo, col


def revisar(cuerpo, col):
    res = comun.revisar(cuerpo, PRESUPUESTO, MEDIDAS, origen="base")
    res = a5.chequeo_normales(res, [cuerpo])
    mn, mx = a5.limites([col])
    res.append((abs(mx.y - ALTO) < 0.002 and abs(mn.y) < 0.002 and abs(mx.x - RADIO) < 0.003,
                "%s: tablero, columna y base (3 cilindros), de y %.2f a %.2f, radio %.3f"
                % (col.name, mn.y, mx.y, mx.x)))
    res.append((True, "Tablero a %.2f m: se come parado o sentado en la banqueta (asiento a 0,75)" % ALTO))
    return res


def hoja_revision(cuerpo, revision):
    import banqueta
    comun.preparar_revision()
    solo = [cuerpo]
    carro, b = a5.carrito("barra_chica")
    mesa = a5.e2.copiar(cuerpo, "ref_mesa")
    mesa.location = piezas.g2b((0.35, 0, 1.0))
    _, asiento, cuerpo_b, _ = banqueta.construir()
    bpy.context.view_layer.update()
    banq = []
    for i, (x, z) in enumerate(((0.75, 0.95), (0.0, 1.15))):
        for o in (asiento, cuerpo_b):
            c = a5.e2.copiar(o, f"ref_{o.name}_{i}")
            c.parent = None
            c.location = piezas.g2b((x, 0, z))
            banq.append(c)
    for o in (asiento, cuerpo_b):
        o.hide_render = True
    persona = a5.persona()
    escena = carro + [mesa] + banq + [persona]
    pedidos = [
        ("Frente · día", solo, "frente", "dia"),
        ("Costado · día", solo, "costado", "dia"),
        ("3/4 · día", solo, "tres_cuartos", "dia"),
        ("3/4 bajo · día", solo, "bajo", "dia"),
        ("3/4 · atardecer", solo, "tres_cuartos", "atardecer"),
        ("Arriba · día", solo, "arriba", "dia"),
        ("Con la persona de 1,75 m · día", solo + [persona], "tres_cuartos", "dia", None,
         a5.mover_persona((0.55, 0, -0.05))),
        ("Al frente de la barra chica, con 2 banquetas · día", escena, "tres_cuartos", "dia", None,
         a5.mover_persona((-0.35, 0, 1.15)), 1.0),
        ("Ídem · atardecer", escena[:-1], "tres_cuartos", "atardecer", None, None, 1.0),
    ]
    a5.hoja(ID, "mesa_alta · Ø 0,60 × 1,10 m · accesorio", pedidos, revision)


def main():
    comun.escena_vacia()
    raiz, cuerpo, col = construir()
    revision = revisar(cuerpo, col)
    ok = comun.imprimir_revision(ID, revision)
    a5.guardar_y_exportar(ID, [raiz, cuerpo, col])
    if "--sin-hoja" not in sys.argv:
        hoja_revision(cuerpo, revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
