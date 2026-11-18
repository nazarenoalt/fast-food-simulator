"""Modelo: subibaja de plaza (id `subibaja`, lista-de-modelos, etapa 3 · Plaza).

Genera:
    arte/fuentes/plaza/subibaja.blend
    godot/modelos/plaza/subibaja.glb
    docs/arte/revisiones/subibaja.jpg

Uso:
    python tools/blender/modelos/subibaja.py [--sin-hoja]

Forma: subibaja de una tabla. Caballete de hierro (M_Hierro) de cuatro patas que se juntan
arriba en el buje del eje (horizontal, sobre X); encima, la tabla amarilla (M_Amarillo) de
3 m con una grampa de hierro en el medio y una manija en U de hierro cerca de cada punta.
Se modela con la tabla horizontal (en el medio del recorrido): así el juego la inclina
rotándola sobre X desde su origen. Juego de chicos: colores vivos (guía 4.2, regla 2).

Medidas (lista ≈ 0,4 × 0,8 × 3,0): 0,40 de ancho (las patas del caballete) × 0,80 de alto (las
manijas, con la tabla horizontal) × 3,00 de largo (la tabla). Eje a 0,50 m; tabla de
0,24 × 0,05 con su cara de arriba a 0,585 m.
Biseles: tabla de 5 cm → 1,2 cm (un cuarto, guía 3.3).
Lados (guía 3.2): patas y buje, 12; manijas (1,5 cm de radio), 8.
Origen: centro de la base, a nivel del piso.

Objetos (hijos del Empty `subibaja`):
    - subibaja_caballete: patas y buje.
    - pieza_tabla: tabla, grampa y manijas, con el origen en el eje de giro (0; 0,50; 0).
    - subibaja-colonly: caja del caballete.
    - subibaja_tabla-colonly: caja de la tabla, hija de pieza_tabla (si el juego la inclina,
      la colisión la sigue).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402, F401  (antes que bmesh)
import bmesh  # noqa: E402

import _plaza as plaza  # noqa: E402
import comun  # noqa: E402
import piezas  # noqa: E402
from piezas import g2b  # noqa: E402

ID = "subibaja"
PRESUPUESTO = 600   # lista de modelos
MEDIDAS = (0.4, 0.8, 3.0)

Y_EJE = 0.50
R_BUJE = 0.035
TABLA = (0.24, 0.05, 3.0)
Y_TABLA = Y_EJE + R_BUJE + TABLA[1] / 2 + 0.008   # centro de la tabla (la grampa en el medio)
Z_MANIJA = 1.15
X_MANIJA = 0.085
ARRIBA = 0.8


def construir():
    hierro, amarillo = comun.cargar_materiales("M_Hierro", "M_Amarillo")
    bm = bmesh.new()
    # Caballete: cuatro patas que apoyan planas y suben hasta el buje.
    for sx in (-1, 1):
        for sz in (-1, 1):
            plaza.poste(bm, (sx * 0.175, 0, sz * 0.13), (sx * 0.085, Y_EJE, sz * 0.012), 0.025, 12,
                        tapa_arriba=False)
    piezas.cilindro(bm, R_BUJE, 0.2, (0, Y_EJE, 0), eje="x", lados=12)
    plaza.borrar_apoyadas(bm)
    caballete = piezas.terminar(f"{ID}_caballete", bm, [hierro])

    # Tabla (coordenadas relativas al eje).
    bt = bmesh.new()
    yt = Y_TABLA - Y_EJE
    piezas.caja(bt, TABLA, (0, yt, 0), mat=1, bisel=0.012)
    # Grampa que abraza el buje.
    piezas.caja(bt, (0.08, 0.055, 0.1), (0, yt - TABLA[1] / 2 - 0.02, 0), mat=0, bisel=0.008)
    # Manijas en U invertida.
    arriba_tabla = yt + TABLA[1] / 2
    y_barra = ARRIBA - 0.015 - Y_EJE
    for sz in (-1, 1):
        z = sz * Z_MANIJA
        for sx in (-1, 1):
            plaza.caño(bt, (sx * X_MANIJA, arriba_tabla - 0.005, z), (sx * X_MANIJA, y_barra, z),
                       0.015, 8, mat=0)
        plaza.caño(bt, (-X_MANIJA - 0.015, y_barra, z), (X_MANIJA + 0.015, y_barra, z), 0.015, 8, mat=0)
    tabla = piezas.terminar("pieza_tabla", bt, [hierro, amarillo])
    tabla.location = g2b((0, Y_EJE, 0))

    col = piezas.colision_caja(ID, (0.4, Y_EJE + R_BUJE, 0.3), (0, (Y_EJE + R_BUJE) / 2, 0))
    col_tabla = piezas.colision_caja(f"{ID}_tabla", TABLA, (0, Y_TABLA, 0))
    bpy.context.view_layer.update()
    col_tabla.parent = tabla
    col_tabla.matrix_parent_inverse = tabla.matrix_world.inverted()
    raiz = piezas.raiz(ID, [caballete, tabla, col])
    return {"raiz": raiz, "caballete": caballete, "tabla": tabla, "colisiones": [col, col_tabla]}


def revisar(mod):
    res = comun.revisar([mod["caballete"], mod["tabla"]], PRESUPUESTO, MEDIDAS, origen="base")
    p = mod["tabla"].matrix_world.translation
    mn, _ = plaza.limites([mod["tabla"]])
    res.append((abs(p.z - Y_EJE) < 1e-6 and abs(p.x) < 1e-6 and abs(p.y) < 1e-6 and mn.y >= Y_EJE - R_BUJE - 0.03,
                "pieza_tabla aparte con el origen en el eje de giro (%.2f m), apoyada sobre el buje"
                % p.z))
    return res


def main():
    comun.escena_vacia()
    mod = construir()
    revision = revisar(mod)
    ok = comun.imprimir_revision(ID, revision)
    plaza.guardar_y_exportar(ID, [mod["raiz"], mod["caballete"], mod["tabla"]] + mod["colisiones"])
    if "--sin-hoja" not in sys.argv:
        c = [mod["caballete"], mod["tabla"]]
        plaza.hoja(ID, "subibaja · 0,4 × 0,8 × 3,0 m · eje a 0,5 m · juego de plaza", [
            ("Frente · día", c, "frente", "dia", True),
            ("Costado · día", c, "costado", "dia", True),
            ("3/4 · día", c, "tres_cuartos", "dia", False),
            ("3/4 · atardecer", c, "tres_cuartos", "atardecer", False),
            ("Con la persona de 1,75 m · día", c + ["persona"], "tres_cuartos", "dia", False),
            ("Arriba · día", c, "arriba", "dia", True),
        ], revision, persona_en=(0.6, 0, 0.6))
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
