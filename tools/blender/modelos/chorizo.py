"""Modelo: chorizo (id `chorizo`, etapa 4; sin dato todavía).

Genera:
    arte/fuentes/comida/chorizo.blend
    godot/modelos/comida/chorizo.glb
    docs/arte/revisiones/chorizo.jpg

Uso:
    blender -b -P tools/blender/modelos/chorizo.py
    python tools/blender/modelos/chorizo.py

Forma: chorizo parrillero Ø 0,03 × 0,14 (lista de modelos), 12 lados (radio de 1,5 cm, guía
3.2). Más gordo y menos parejo que la salchicha: el radio tiene lomitas fijas al azar (±3 %),
se arquea 1,5 mm hacia un costado y las puntas se cierran en el atado: el cuerpo se
redondea, se estrangula en el hilo (r 2,2 mm) y termina en un nudito (r 3,2 mm). Como en la
salchicha, las caras planas tocan el radio del dato, no las aristas. Después del ruido la
pieza se vuelve a centrar y a medir (Ø 0,03 × 0,14 justos). Sombreado suave, sin bisel.

El objeto se llama `pieza_chorizo` (guía 4.4 y 6.2): el juego le cambia el color según la
cocción, así que el material es el de la carne cruda (M_CarneCruda).
La versión abierta en mariposa (lista de modelos) queda para otra tanda.
"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402, F401
import bmesh  # noqa: E402

import comun  # noqa: E402
import _comida4 as c4  # noqa: E402
import _etapa2 as e2  # noqa: E402

ID = "chorizo"
PIEZA = "pieza_chorizo"
R, LARGO = c4.R_CHORIZO, c4.LARGO_CHORIZO
MEDIDAS = (LARGO, 2 * R, 2 * R)
PRESUPUESTO = 250
LADOS = 12
CURVA = 0.0015

# (x, radio) de la mitad +X, de la punta hacia el medio.
PERFIL = [
    (0.0672, 0.0032),   # nudito
    (0.0638, 0.0022),   # el hilo del atado
    (0.0598, 0.0098),
    (0.0505, 0.0142),
    (0.0, R),
]
ANILLOS_X = [(-x, r) for x, r in PERFIL] + [(x, r) for x, r in reversed(PERFIL[:-1])]


def desvio(x):
    return CURVA * (1 - (x / (LARGO / 2)) ** 2)


def construir(nombre=PIEZA):
    (material,) = comun.cargar_materiales("M_CarneCruda")
    rnd = random.Random(4)
    giro = math.pi / LADOS
    aj = 1 / math.cos(math.pi / LADOS)
    anillos = []
    for i, (x, r) in enumerate(ANILLOS_X):
        lomas = r > 0.005  # el atado queda parejo
        anillo = []
        for k in range(LADOS):
            f = 1 + (rnd.uniform(-0.03, 0.03) if lomas else 0.0)
            a = giro + 2 * math.pi * k / LADOS
            anillo.append((x, desvio(x) + r * aj * f * math.cos(a), r * aj * f * math.sin(a)))
        anillos.append(anillo)
    puntas = [(-LARGO / 2, desvio(-LARGO / 2), 0.0), (LARGO / 2, desvio(LARGO / 2), 0.0)]
    obj = comun.lofteo(nombre, anillos, puntas, [material])
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    c4.ajustar_caja(bm, MEDIDAS)
    bm.to_mesh(obj.data)
    bm.free()
    return obj


def hoja_revision(chorizo, revision):
    comun.preparar_revision()
    chorizo.location.z = R
    estados = c4.estados_coccion(chorizo, c4.COCCION_CHORIZO, 0.05)
    for c in estados:
        c.location.x += 0.4
    ref = c4.pan_de_escala(0.0, -0.06)
    solo = [chorizo]
    cuadros = e2.sacar_fotos([
        ("Frente · día", solo, "frente", "dia"),
        ("Costado de cerca · día", solo, "costado", "dia", solo, 1.4),
        ("3/4 · día: el atado de las puntas", solo, "tres_cuartos", "dia"),
        ("3/4 · atardecer", solo, "tres_cuartos", "atardecer"),
        ("Cocción: crudo, cocido, pasado, quemado · día", estados, "tres_cuartos", "dia"),
        ("Al lado de un pan de pancho · día", [chorizo, ref], "tres_cuartos", "dia"),
    ])
    c4.hoja(ID, f"{ID} · Ø 0,03 × 0,14 m · comida chica · pieza_chorizo (color por cocción)",
            cuadros, revision)


def main():
    comun.escena_vacia()
    chorizo = construir()
    revision = comun.revisar(chorizo, PRESUPUESTO, MEDIDAS, origen="centro")
    ok = comun.imprimir_revision(ID, revision)
    c4.guardar_y_exportar(ID, [chorizo])
    if "--sin-hoja" not in sys.argv:
        hoja_revision(chorizo, revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
