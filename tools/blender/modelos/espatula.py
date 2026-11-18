"""Modelo: espátula de plancha (id `espatula`, etapa 4; objeto de mano con física).

Genera:
    arte/fuentes/cocina/espatula.blend
    godot/modelos/cocina/espatula.glb
    docs/arte/revisiones/espatula.jpg

Uso:
    blender -b -P tools/blender/modelos/espatula.py
    python tools/blender/modelos/espatula.py

Forma: espátula de hamburguesería, acostada a lo largo de X: pala de acero ancha (0,10) y
plana de 3 mm, con las esquinas de atrás que se angostan al cuello; el cuello sube en
diagonal hasta el mango negro, que queda levantado (así se agarra sin tocar la plancha), con
una virola de acero adelante del mango.

Medidas (lista: 0,30 × 0,03 × 0,10): 0,30 × 0,03 × 0,10 justos. Pala de 0,12 de largo.

Objeto único `espatula` (Acero, PlasticoNegro), con el origen en el centro (guía 2.4: objetos
que se agarran). Sin colisión: la define el dato (guía 6.1). Biseles de 2–4 mm en mango y
virola; la pala y el cuello (3 mm) van sin bisel.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402,F401  (antes que bmesh)
import bmesh  # noqa: E402

import comun  # noqa: E402
import piezas  # noqa: E402
import _equipos as eq  # noqa: E402
from piezas import g2b  # noqa: E402

ID = "espatula"
FAMILIA = "cocina"
PRESUPUESTO = 200  # lista de modelos
ACERO, NEGRO = range(2)
MEDIDAS = (0.30, 0.03, 0.10)
ESP = 0.003                      # chapa de la pala y el cuello
PALA = [(-0.15, -0.05), (-0.15, 0.05), (-0.065, 0.05), (-0.025, 0.011), (-0.025, -0.011), (-0.065, -0.05)]
MANGO = (0.115, 0.021, 0.026)    # largo, alto, ancho
MANGO_X = 0.15 - MANGO[0] / 2
MANGO_Y = 0.03 - (MANGO[1] + 0.002) / 2   # la virola (2 mm más alta) toca 0,03


def construir():
    acero, negro = comun.cargar_materiales("M_Acero", "M_PlasticoNegro")
    bm = bmesh.new()
    eq.prisma(bm, PALA, 0.0, ESP, mat=ACERO)
    # Cuello: de la cola de la pala (apoyada) a la virola (levantada).
    x0, y0 = -0.03, ESP / 2
    x1, y1 = 0.034, MANGO_Y
    largo = math.hypot(x1 - x0, y1 - y0)
    angulo = math.degrees(math.atan2(y1 - y0, x1 - x0))
    piezas.caja(bm, (largo, ESP, 0.02), ((x0 + x1) / 2, (y0 + y1) / 2, 0), mat=ACERO, rot=(0, 0, angulo))
    # Virola y mango.
    piezas.caja(bm, (0.012, MANGO[1] + 0.002, MANGO[2] + 0.002), (MANGO_X - MANGO[0] / 2 - 0.004, MANGO_Y, 0),
                mat=ACERO, bisel=0.002)
    piezas.caja(bm, MANGO, (MANGO_X, MANGO_Y, 0), mat=NEGRO, bisel=0.004)
    eq.centrar(bm)
    return {"obj": piezas.terminar(ID, bm, [acero, negro])}


def revisar(m):
    return comun.revisar(m["obj"], PRESUPUESTO, MEDIDAS, origen="centro")


def hoja(m, revision):
    def en_plancha(obj):
        import plancha
        import _etapa2 as e2
        barra = e2.barra_chica()
        p = plancha.construir()
        p["raiz"].location = g2b((-0.4, 0.95, 0.0))
        obj.location = g2b((-0.4 + 0.05, 0.95 + 0.17 + 0.015, -0.08))
        obj.rotation_euler.z = math.radians(15)
        bpy.context.view_layer.update()
        return ("Sobre la plancha (en mostrador_izq) · día", [obj, p["cuerpo"], p["piloto"]] + barra,
                [p["cuerpo"]], 1.6)
    eq.hoja_mano(ID, "espatula · 0,30 × 0,03 × 0,10 m · utensilio (origen en el centro)", m["obj"],
                 revision, escena=en_plancha)


def main():
    eq.main_modelo(ID, FAMILIA, construir, revisar, hoja, lambda m: [m["obj"]])


if __name__ == "__main__":
    main()
