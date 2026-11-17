"""Modelo: hamacas de plaza (id `hamaca`, lista-de-modelos, etapa 3 · Plaza).

Genera:
    arte/fuentes/plaza/hamaca.blend
    godot/modelos/plaza/hamaca.glb
    docs/arte/revisiones/hamaca.jpg

Uso:
    python tools/blender/modelos/hamaca.py [--sin-hoja]

Forma: la hamaca doble de plaza de barrio. Estructura de caño pintado de rojo (M_RojoAcento;
los juegos pueden ser más vivos que el resto del fondo): un travesaño arriba y, en cada
punta, dos patas en A abiertas hacia adelante y atrás con un refuerzo horizontal. De cada
abrazadera de hierro (M_Hierro) bajan las cadenas (cilindros de 6 lados, guía 2.2) hasta un
asiento de tabla (M_Madera). Las cadenas no se modelan eslabón por eslabón (regla de los 2 m).

Medidas (lista ≈ 3,0 × 2,4 × 1,5): 3,00 de ancho (el travesaño) × 2,40 de alto × 1,50 de fondo
(las patas en el piso). Asientos a 0,45 m del piso, 1,30 m entre los dos.
Las hamacas se balancean hacia adelante y atrás (alrededor de X).
Lados (guía 3.2): caños de 4 cm de radio, 12; refuerzos y cadenas, 8 y 6.
Biseles: tabla del asiento de 3,5 cm → bisel de 9 mm (un cuarto, guía 3.3).
Origen: centro de la base, a nivel del piso (las patas apoyan planas en Y = 0).

Objetos (hijos del Empty `hamaca`):
    - hamaca_estructura: travesaño, patas, refuerzos y abrazaderas.
    - pieza_asiento_1 (x = −0,65) y pieza_asiento_2 (x = +0,65): asiento y cadenas de cada
      hamaca, cada uno con el origen en su eje de giro (el eje del travesaño, y = 2,343), para
      que el juego los balancee rotándolos sobre X.
    - hamaca-colonly: cuatro cajas de las patas y una del travesaño (los asientos no chocan:
      se mueven).
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402, F401  (antes que bmesh)
import bmesh  # noqa: E402

import _plaza as plaza  # noqa: E402
import comun  # noqa: E402
import piezas  # noqa: E402
from piezas import g2b  # noqa: E402

ID = "hamaca"
PRESUPUESTO = 1500  # lista de modelos (estructuras grandes de la plaza)
MEDIDAS = (3.0, 2.4, 1.5)
PINTURA, HIERRO, MADERA = 0, 1, 2

R_CAÑO = 0.045
R_ABRAZADERA = R_CAÑO + 0.012
Y_EJE = 2.4 - R_ABRAZADERA      # eje del travesaño = eje de giro de los asientos
X_PATA = 1.40
R_PATA = 0.04
Z_PIE = 0.75 - R_PATA            # centro de la pata en el piso
Y_REFUERZO = 0.9
X_ASIENTOS = (-0.65, 0.65)
CADENA = 0.2                     # media separación de las cadenas
ASIENTO = (0.46, 0.035, 0.17)
Y_ASIENTO = 0.45                 # arriba de la tabla


def construir():
    mats = comun.cargar_materiales("M_RojoAcento", "M_Hierro", "M_Madera")
    bm = bmesh.new()
    # Travesaño con tapas.
    piezas.cilindro(bm, R_CAÑO, 3.0 - 0.02, (0, Y_EJE, 0), eje="x", lados=12, mat=PINTURA)
    for sx in (-1, 1):
        piezas.cilindro(bm, R_CAÑO + 0.006, 0.02, (sx * 1.49, Y_EJE, 0), eje="x", lados=12, mat=HIERRO)
    # Patas en A y refuerzo.
    for sx in (-1, 1):
        x = sx * X_PATA
        for sz in (-1, 1):
            plaza.poste(bm, (x, 0, sz * Z_PIE), (x, Y_EJE, sz * 0.02), R_PATA, 12, mat=PINTURA,
                        tapa_arriba=False)
        z_ref = Z_PIE * (1 - Y_REFUERZO / Y_EJE) + 0.01
        plaza.caño(bm, (x, Y_REFUERZO, -z_ref), (x, Y_REFUERZO, z_ref), 0.025, 8, mat=PINTURA)
    # Abrazaderas de las cadenas.
    for xa in X_ASIENTOS:
        for sx in (-1, 1):
            piezas.cilindro(bm, R_ABRAZADERA, 0.035, (xa + sx * CADENA, Y_EJE, 0), eje="x",
                            lados=12, mat=HIERRO)
    plaza.borrar_apoyadas(bm)
    estructura = piezas.terminar(f"{ID}_estructura", bm, mats[:2])

    # Asientos (cada uno con su origen en el eje de giro).
    asientos = []
    for i, xa in enumerate(X_ASIENTOS, 1):
        ba = bmesh.new()
        y_tabla = Y_ASIENTO - ASIENTO[1] / 2
        for sx in (-1, 1):
            plaza.caño(ba, (sx * CADENA, -R_CAÑO - 0.005, 0), (sx * CADENA, y_tabla - Y_EJE, 0),
                       0.006, 6, mat=0)
            # Herraje donde la cadena toma la tabla.
            piezas.caja(ba, (0.03, 0.05, 0.05), (sx * CADENA, y_tabla - Y_EJE + 0.01, 0), mat=0,
                        bisel=0.006)
        piezas.caja(ba, ASIENTO, (0, y_tabla - Y_EJE, 0), mat=1, bisel=0.009)
        # En la pieza, los índices son propios: 0 = hierro, 1 = madera.
        obj = piezas.terminar(f"pieza_asiento_{i}", ba, [mats[HIERRO], mats[MADERA]])
        obj.location = g2b((xa, Y_EJE, 0))
        asientos.append(obj)

    # Colisión: patas y travesaño.
    largo = math.hypot(Y_EJE, Z_PIE)
    ang = math.degrees(math.atan2(Z_PIE, Y_EJE))
    cajas = [((0.09, largo, 0.09), (sx * X_PATA, Y_EJE / 2, sz * Z_PIE / 2), (-sz * ang, 0, 0))
             for sx in (-1, 1) for sz in (-1, 1)]
    cajas.append(((3.0, 0.1, 0.1), (0, Y_EJE, 0), (0, 0, 0)))
    col = plaza.colision_cajas(ID, cajas)
    raiz = piezas.raiz(ID, [estructura] + asientos + [col])
    return {"raiz": raiz, "estructura": estructura, "asientos": asientos, "colisiones": [col]}


def revisar(mod):
    visibles = [mod["estructura"]] + mod["asientos"]
    res = comun.revisar(visibles, PRESUPUESTO, MEDIDAS, origen="base")
    ok = True
    textos = []
    for a in mod["asientos"]:
        mn, mx = plaza.limites([a])
        p = a.matrix_world.translation
        tabla = mn.y + ASIENTO[1]
        ok &= abs(p.z - Y_EJE) < 1e-6 and abs(p.y) < 1e-6 and abs(tabla - Y_ASIENTO) < 0.002 \
            and mx.y < Y_EJE + 1e-3
        textos.append("%s: eje a %.3f m, tabla a %.3f m" % (a.name, p.z, tabla))
    res.append((ok, "Asientos aparte con el origen en el eje de giro (" + "; ".join(textos) + ")"))
    return res


def main():
    comun.escena_vacia()
    mod = construir()
    revision = revisar(mod)
    ok = comun.imprimir_revision(ID, revision)
    plaza.guardar_y_exportar(ID, [mod["raiz"], mod["estructura"]] + mod["asientos"] + mod["colisiones"])
    if "--sin-hoja" not in sys.argv:
        c = [mod["estructura"]] + mod["asientos"]
        plaza.hoja(ID, "hamaca · 3,0 × 2,4 × 1,5 m · asientos a 0,45 m · juego de plaza", [
            ("Frente · día", c, "frente", "dia", True),
            ("Costado (patas en A) · día", c, "costado", "dia", True),
            ("3/4 · día", c, "tres_cuartos", "dia", False),
            ("3/4 · atardecer", c, "tres_cuartos", "atardecer", False),
            ("Con la persona de 1,75 m · día", c + ["persona"], "tres_cuartos", "dia", False),
            ("Arriba · día", c, "arriba", "dia", True),
        ], revision, persona_en=(0.0, 0, 0.6))
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
