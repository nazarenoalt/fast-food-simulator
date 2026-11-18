"""Modelo: bebedero de plaza (id `bebedero`, lista-de-modelos, etapa 3 · Plaza).

Genera:
    arte/fuentes/plaza/bebedero.blend
    godot/modelos/plaza/bebedero.glb
    docs/arte/revisiones/bebedero.jpg

Uso:
    python tools/blender/modelos/bebedero.py [--sin-hoja]

Forma: bebedero de piedra (M_Piedra) de plaza: zócalo, columna cuadrada que se afina hacia
arriba y una pileta cuadrada que se abre en copa, con el fondo en pendiente hacia la
rejilla. De acero (M_Acero): el pico, que sube del fondo de la pileta y se curva hacia el
frente (+Z, el lado de quien toma agua), la rejilla del desagüe y el botón en el frente de
la columna, con su chapa.

Medidas (lista ≈ 0,4 × 1,0 × 0,4): 0,40 × 1,00 × 0,40. Borde de la pileta a 0,88 m; el pico
llega a 1,00.
Biseles: zócalo de 6 cm con bisel de 1,5 cm (un cuarto, guía 3.3); la columna y la pileta
son tornos de 4 lados (las aristas las dan los quiebres del perfil).
Lados (guía 3.2): pico (r 1,2 cm) 8; rejilla y botón (r 2–2,5 cm) 12.
Origen: centro de la base, a nivel del piso.

Objetos (hijos del Empty `bebedero`):
    - bebedero_cuerpo: piedra y acero.
    - bebedero-colonly: caja de 0,40 × 0,88 × 0,40.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402, F401  (antes que bmesh)
import bmesh  # noqa: E402

from mathutils import Vector  # noqa: E402

import _arbol  # noqa: E402  (tubo(): caño doblado de una sola malla)
import _plaza as plaza  # noqa: E402
import comun  # noqa: E402
import piezas  # noqa: E402

ID = "bebedero"
PRESUPUESTO = 400   # lista de modelos
MEDIDAS = (0.4, 1.0, 0.4)
PIEDRA, ACERO = 0, 1

BORDE = 0.88
FONDO = 0.82
R_PICO = 0.012
Z_PICO = -0.09


def construir():
    mats = comun.cargar_materiales("M_Piedra", "M_Acero")
    bm = bmesh.new()
    piezas.caja(bm, (0.34, 0.06, 0.34), (0, 0.03, 0), mat=PIEDRA, bisel=0.015, sin_abajo=True)
    # Columna y pileta en un solo torno de 4 lados (cuadrado).
    plaza.torno(bm, [
        (0.13, 0.06), (0.11, 0.76),                  # columna que se afina
        (0.13, 0.78), (0.2, 0.83), (0.2, BORDE),     # copa de la pileta
        (0.17, BORDE), (0.15, 0.86),                 # canto de adentro
        (0.05, FONDO + 0.006), (0.0, FONDO),         # fondo en pendiente hacia la rejilla
    ], lados=4)
    # Rejilla del desagüe.
    piezas.cilindro(bm, 0.025, 0.006, (0, FONDO + 0.002, 0), lados=12, mat=ACERO)
    # Pico: sube del fondo y se curva hacia el frente.
    tope = MEDIDAS[1] - R_PICO
    puntos = [Vector(p) for p in ((0, 0.835, Z_PICO), (0, 0.95, Z_PICO), (0, tope, Z_PICO + 0.035),
                                  (0, tope - 0.012, -0.02))]
    _arbol.tubo(bm, puntos, [R_PICO] * 4, 8, mat=ACERO, tapa_inicio=False)  # arranca metido en el fondo
    # Botón con su chapa, en el frente de la columna.
    z_cara = 0.13 - 0.02 * (0.70 - 0.06) / 0.70
    piezas.caja(bm, (0.07, 0.07, 0.006), (0, 0.70, z_cara + 0.001), mat=ACERO, bisel=0.002)
    piezas.cilindro(bm, 0.02, 0.02, (0, 0.70, z_cara + 0.012), eje="z", lados=12, mat=ACERO)
    plaza.borrar_apoyadas(bm)
    cuerpo = piezas.terminar(f"{ID}_cuerpo", bm, mats)
    col = piezas.colision_caja(ID, (0.4, BORDE, 0.4), (0, BORDE / 2, 0))
    raiz = piezas.raiz(ID, [cuerpo, col])
    return {"raiz": raiz, "cuerpo": cuerpo, "colisiones": [col]}


def revisar(mod):
    res = comun.revisar(mod["cuerpo"], PRESUPUESTO, MEDIDAS, origen="base")
    m = mod["cuerpo"].data
    acero = [m.vertices[i].co for p in m.polygons if p.material_index == ACERO for i in p.vertices]
    piedra = [m.vertices[i].co for p in m.polygons if p.material_index == PIEDRA for i in p.vertices]
    res.append((abs(max(v.z for v in piedra) - BORDE) < 0.002 and max(v.z for v in acero) <= 1.0 + 1e-4,
                "Borde de la pileta a %.2f m; pico de acero hasta %.2f m" % (
                    max(v.z for v in piedra), max(v.z for v in acero))))
    return res


def main():
    comun.escena_vacia()
    mod = construir()
    revision = revisar(mod)
    ok = comun.imprimir_revision(ID, revision)
    plaza.guardar_y_exportar(ID, [mod["raiz"], mod["cuerpo"]] + mod["colisiones"])
    if "--sin-hoja" not in sys.argv:
        c = [mod["cuerpo"]]
        plaza.hoja(ID, "bebedero · 0,4 × 1,0 × 0,4 m · pileta a 0,88 m · mobiliario urbano", [
            ("Frente (botón) · día", c, "frente", "dia", True),
            ("Costado · día", c, "costado", "dia", True),
            ("3/4 · día", c, "tres_cuartos", "dia", False),
            ("3/4 · atardecer", c, "tres_cuartos", "atardecer", False),
            ("Con la persona de 1,75 m · día", c + ["persona"], "tres_cuartos", "dia", False),
            ("Arriba (pileta) · día", c, "arriba", "dia", True),
        ], revision, persona_en=(0.5, 0, 0.35))
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
