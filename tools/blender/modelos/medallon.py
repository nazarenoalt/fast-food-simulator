"""Modelo: medallón de hamburguesa (id `medallon`, etapa 4; todavía sin dato en productos.ron).

Genera:
    arte/fuentes/comida/medallon.blend
    godot/modelos/comida/medallon.glb
    docs/arte/revisiones/medallon.jpg

Uso:
    blender -b -P tools/blender/modelos/medallon.py
    python tools/blender/modelos/medallon.py

Forma: medallón de carne picada Ø 0,11 × 0,012 (lista de modelos), 16 lados (radio de 5 a
25 cm, guía 3.2). Abajo es plano (apoya sobre la plancha y sobre el pan), el canto es
redondeado y un poco abombado, y arriba tiene un domo muy bajo con lomitas. El borde es
irregular: el radio cambia alrededor (ondas suaves + un poco de azar fijo), para que no
parezca un disco torneado. Después del ruido la pieza se vuelve a centrar y a medir, así
queda justo en Ø 0,11 × 0,012. Sombreado suave (comida, guía 3.4), sin bisel.

El objeto se llama `pieza_carne` (guía 4.4 y 6.2): el juego le cambia el color según la
cocción, así que el material es el de la carne cruda (M_CarneCruda).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402, F401
import bmesh  # noqa: E402
import math  # noqa: E402
import random  # noqa: E402

import comun  # noqa: E402
import _comida4 as c4  # noqa: E402
import _etapa2 as e2  # noqa: E402

ID = "medallon"
PIEZA = "pieza_carne"
R, ALTO = c4.R_PAN, c4.ALTO_CARNE
MEDIDAS = (2 * R, ALTO, 2 * R)
PRESUPUESTO = 200
LADOS = 16
H = ALTO / 2

# (radio, y) de abajo hacia arriba.
PERFIL = [
    (0.0, -H),
    (0.0465, -H),        # abajo plano
    (0.053, -0.0038),
    (R, -0.0008),        # canto, lo más ancho
    (0.0526, 0.0036),
    (0.0465, 0.0057),
    (0.0, H),            # domo muy bajo
]


def construir(nombre=PIEZA):
    (material,) = comun.cargar_materiales("M_CarneCruda")
    borde = c4.ruido_angular(7, [(2, 0.02), (3, 0.035), (5, 0.02), (7, 0.012)])
    rnd = random.Random(11)
    azar = [rnd.uniform(-0.022, 0.022) for _ in range(LADOS)]
    lomas = [rnd.uniform(-0.0014, 0.0) for _ in range(LADOS)]

    def radio(k, i):
        a = 2 * math.pi * k / LADOS
        return borde(a) + azar[k] * (1 if i in (2, 3, 4) else 0.4)

    def alto(k, i):
        return lomas[k] if i == 5 else (lomas[k] * 0.5 if i == 4 else 0.0)

    bm = bmesh.new()
    c4.torno(bm, PERFIL, LADOS, radio=radio, alto=alto)
    c4.ajustar_caja(bm, MEDIDAS)
    return c4.terminar(nombre, bm, [material])


def hoja_revision(carne, revision):
    comun.preparar_revision()
    carne.location.z = H
    estados = c4.estados_coccion(carne, c4.COCCION_CARNE, 0.125, eje="x")
    for c in estados:
        c.location.x += 0.5
    pan = c4.pan_de_escala(0.0, -0.11)
    solo = [carne]
    cuadros = e2.sacar_fotos([
        ("Frente · día", solo, "frente", "dia"),
        ("Arriba: borde irregular · día", solo, "arriba", "dia"),
        ("3/4 · día", solo, "tres_cuartos", "dia"),
        ("3/4 · atardecer", solo, "tres_cuartos", "atardecer"),
        ("Cocción: cruda, cocida, pasada, quemada · día", estados, "tres_cuartos", "dia"),
        ("Al lado de un pan de pancho · día", [carne, pan], "tres_cuartos", "dia"),
    ])
    c4.hoja(ID, f"{ID} · Ø 0,11 × 0,012 m · comida chica · pieza_carne (color por cocción)",
            cuadros, revision)


def main():
    comun.escena_vacia()
    carne = construir()
    revision = comun.revisar(carne, PRESUPUESTO, MEDIDAS, origen="centro")
    ok = comun.imprimir_revision(ID, revision)
    c4.guardar_y_exportar(ID, [carne])
    if "--sin-hoja" not in sys.argv:
        hoja_revision(carne, revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
