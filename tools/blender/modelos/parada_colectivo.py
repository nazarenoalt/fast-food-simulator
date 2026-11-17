"""Modelo: parada de colectivo (id `parada_colectivo`, familia `ciudad`).

Genera:
    arte/fuentes/ciudad/parada_colectivo.blend
    godot/modelos/ciudad/parada_colectivo.glb
    docs/arte/revisiones/parada_colectivo.jpg

Uso:
    python tools/blender/modelos/parada_colectivo.py [--sin-hoja]

Refugio de parada porteño: dos parantes de hierro atrás que sostienen un techo en voladizo,
paño trasero y paño lateral de vidrio con marcos de hierro, un banco de madera y la cenefa
del techo en azul (donde iría el número de la línea: sin texto, lo pondría un cartel aparte
si hiciera falta). Hoy el juego no tiene colectivos ni parada: es ambientación para la
vereda de enfrente.

Frente (+Z de Godot) = el lado abierto, hacia la calle. Origen = centro de la base, a nivel
del piso.

Materiales: M_Hierro (parantes, techo, marcos, patas del banco), M_Vidrio (paños,
transparente: acá sí se tiene que ver a través), M_Madera (banco), M_AzulAcento (cenefa).

Medidas: 2,50 × 2,50 × 1,20 (las de la lista).
Colisión: parada_colectivo-colonly (parantes, paño trasero, paño lateral y banco).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402, F401  (antes que bmesh)
import bmesh  # noqa: E402

import _ciudad as ciudad  # noqa: E402
import _plaza as plaza  # noqa: E402
import comun  # noqa: E402
import piezas  # noqa: E402

ID = "parada_colectivo"
PRESUPUESTO = 800      # lista de modelos (mobiliario urbano)
MEDIDAS = (2.5, 2.5, 1.2)
ALTO, ANCHO, FONDO = 2.5, 2.5, 1.2
TECHO = 0.07
X_PARANTE, Z_ATRAS = 1.15, -0.45
PANO = (0.40, 2.05)    # de y a y
Z_LATERAL = 0.25       # adonde llega el paño lateral
HIERRO, VIDRIO, MADERA, AZUL = range(4)


def construir():
    mats = comun.cargar_materiales("M_Hierro", "M_Vidrio", "M_Madera", "M_AzulAcento")
    bm = bmesh.new()
    y_techo = ALTO - TECHO
    # Parantes (caño cuadrado de 8 cm) y el del frente del paño lateral (5 cm).
    for s in (-1, 1):
        piezas.caja(bm, (0.08, y_techo, 0.08), (s * X_PARANTE, y_techo / 2, Z_ATRAS), HIERRO, bisel=0.02)
    piezas.caja(bm, (0.05, y_techo, 0.05), (-X_PARANTE, y_techo / 2, Z_LATERAL), HIERRO, bisel=0.012)
    plaza.borrar_apoyadas(bm)
    # Techo en voladizo, con la cenefa azul adelante.
    piezas.caja(bm, (ANCHO, TECHO, FONDO), (0, ALTO - TECHO / 2, 0), HIERRO, bisel=0.02)
    piezas.caja(bm, (ANCHO, 0.18, 0.04), (0, ALTO - TECHO - 0.08, FONDO / 2 - 0.02), AZUL, bisel=0.01)
    # Marcos de los paños.
    largo = 2 * X_PARANTE - 0.08
    for y in PANO:
        piezas.caja(bm, (largo, 0.05, 0.05), (0, y, Z_ATRAS), HIERRO, bisel=0.012)
        lado = Z_LATERAL - Z_ATRAS - 0.065
        piezas.caja(bm, (0.05, 0.05, lado), (-X_PARANTE, y, (Z_LATERAL + Z_ATRAS) / 2), HIERRO, bisel=0.012)
    # Vidrios (2 cm).
    alto_pano = PANO[1] - PANO[0] - 0.05
    piezas.caja(bm, (largo, alto_pano, 0.02), (0, sum(PANO) / 2, Z_ATRAS), VIDRIO)
    piezas.caja(bm, (0.02, alto_pano, Z_LATERAL - Z_ATRAS - 0.065),
                (-X_PARANTE, sum(PANO) / 2, (Z_LATERAL + Z_ATRAS) / 2), VIDRIO)
    # Banco: asiento de madera sobre dos patas de hierro.
    piezas.caja(bm, (1.6, 0.05, 0.34), (0.2, 0.465, Z_ATRAS + 0.21), MADERA, bisel=0.012)
    for x in (-0.4, 0.8):
        piezas.caja(bm, (0.05, 0.44, 0.26), (x, 0.22, Z_ATRAS + 0.17), HIERRO, bisel=0.012)
    plaza.borrar_apoyadas(bm)
    cuerpo = piezas.terminar(ID, bm, mats)
    col = plaza.colision_cajas(ID, [
        ((0.08, y_techo, 0.08), (X_PARANTE, y_techo / 2, Z_ATRAS), (0, 0, 0)),
        ((0.08, y_techo, 0.08), (-X_PARANTE, y_techo / 2, Z_ATRAS), (0, 0, 0)),
        ((largo, PANO[1], 0.06), (0, PANO[1] / 2, Z_ATRAS), (0, 0, 0)),
        ((0.06, PANO[1], Z_LATERAL - Z_ATRAS), (-X_PARANTE, PANO[1] / 2, (Z_LATERAL + Z_ATRAS) / 2), (0, 0, 0)),
        ((1.6, 0.49, 0.34), (0.2, 0.245, Z_ATRAS + 0.21), (0, 0, 0)),
        ((ANCHO, TECHO, FONDO), (0, ALTO - TECHO / 2, 0), (0, 0, 0)),
    ])
    raiz = piezas.raiz(ID, [cuerpo, col])
    return {"raiz": raiz, "cuerpo": cuerpo, "col": col}


def main():
    comun.escena_vacia()
    m = construir()
    revision = comun.revisar(m["cuerpo"], PRESUPUESTO, MEDIDAS, origen="base")
    ok = comun.imprimir_revision(ID, revision)
    ciudad.guardar_y_exportar(ID, [m["raiz"], m["cuerpo"], m["col"]])
    if "--sin-hoja" not in sys.argv:
        c = [m["cuerpo"]]
        ciudad.hoja(ID, "parada_colectivo · 2,5 × 2,5 × 1,2 m · mobiliario urbano", [
            ("Frente · día", c, "frente", "dia", True),
            ("Costado · día", c, "costado", "dia", True),
            ("3/4 · día", c, "tres_cuartos", "dia", False),
            ("3/4 · atardecer", c, "tres_cuartos", "atardecer", False),
            ("Con la persona de 1,75 m · día", c + ["persona"], "tres_cuartos", "dia", False),
            ("Atrás · día", c, "tres_cuartos_atras", "dia", False),
        ], revision, persona_en=(0.6, 0, 0.1))
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
