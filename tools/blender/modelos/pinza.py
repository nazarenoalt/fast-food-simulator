"""Modelo: pinza de parrilla (id `pinza`, etapa 4; objeto de mano con física).

Genera:
    arte/fuentes/cocina/pinza.blend
    godot/modelos/cocina/pinza.glb
    docs/arte/revisiones/pinza.jpg

Uso:
    blender -b -P tools/blender/modelos/pinza.py
    python tools/blender/modelos/pinza.py

Forma: pinza de acero acostada a lo largo de X, con los dos brazos de fleje (3 mm × 16 mm, de
canto) que salen juntos de la cabeza (+X, el resorte: un bloque de acero) y se abren hacia
las puntas (−X), donde cada brazo termina en una paleta más alta (3 cm) para agarrar el
chorizo. Mangos negros sobre la mitad de atrás de cada brazo.

Medidas (lista: 0,30 × 0,03 × 0,05): 0,30 × 0,03 × 0,05 justos, abierta (en reposo).

Objeto único `pinza` (Acero, PlasticoNegro), con el origen en el centro (guía 2.4). Sin
colisión: la define el dato (guía 6.1). Fleje y paletas (3 mm) sin bisel; mangos y cabeza con
bisel de 2–3 mm. Si el juego quiere que se cierre al agarrar, los
brazos tendrían que ir como piezas aparte (no hace falta por ahora).
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

ID = "pinza"
FAMILIA = "cocina"
PRESUPUESTO = 200  # lista de modelos
ACERO, NEGRO = range(2)
MEDIDAS = (0.30, 0.03, 0.05)
ESP, ALTO_FLEJE = 0.003, 0.016
X_CABEZA, X_PALETA = 0.13, -0.10    # donde arrancan los brazos / las paletas
Z_CABEZA, Z_PUNTA = 0.006, 0.0235   # centro del fleje de cada brazo (a cada lado)
PALETA = (0.05, 0.03, ESP)
Y = 0.015                            # centro en alto


def construir():
    acero, negro = comun.cargar_materiales("M_Acero", "M_PlasticoNegro")
    bm = bmesh.new()
    largo = math.hypot(X_CABEZA - X_PALETA, Z_PUNTA - Z_CABEZA)
    ang = math.degrees(math.atan2(Z_PUNTA - Z_CABEZA, X_CABEZA - X_PALETA))
    for lado in (-1, 1):
        zc = lado * (Z_CABEZA + Z_PUNTA) / 2
        piezas.caja(bm, (largo + 0.004, ALTO_FLEJE, ESP), ((X_CABEZA + X_PALETA) / 2, Y, zc), mat=ACERO,
                    rot=(0, lado * ang, 0))
        # Paleta de la punta, derecha (paralela a X), un poco más afuera que el fleje.
        piezas.caja(bm, PALETA, (X_PALETA - PALETA[0] / 2, Y, lado * Z_PUNTA), mat=ACERO)
        # Mango negro sobre el fleje, en la mitad de atrás.
        t = 0.32                       # de la cabeza hacia la punta, dónde queda el centro del mango
        xm = X_CABEZA - t * (X_CABEZA - X_PALETA)
        zm = lado * (Z_CABEZA + t * (Z_PUNTA - Z_CABEZA))
        piezas.caja(bm, (0.11, ALTO_FLEJE + 0.004, ESP + 0.005), (xm, Y, zm), mat=NEGRO, bisel=0.002,
                    rot=(0, lado * ang, 0))
    # Cabeza (resorte): bloque de acero que junta los brazos.
    piezas.caja(bm, (0.02, ALTO_FLEJE + 0.002, 2 * Z_CABEZA + ESP + 0.004), (0.15 - 0.01, Y, 0), mat=ACERO,
                bisel=0.003)
    eq.centrar(bm)
    return {"obj": piezas.terminar(ID, bm, [acero, negro])}


def revisar(m):
    return comun.revisar(m["obj"], PRESUPUESTO, MEDIDAS, origen="centro")


def hoja(m, revision):
    def en_parrilla(obj):
        import parrilla_carbon
        import carbon_brasa
        import _etapa2 as e2
        barra = e2.barra_chica()
        p = parrilla_carbon.construir()
        c = carbon_brasa.construir()
        p["raiz"].location = g2b((-0.4, 0.95, 0.0))
        c["raiz"].location = g2b((-0.4, 0.95 + 0.09, 0.0))
        obj.location = g2b((-0.4 + 0.1, 0.95 + 0.30 + 0.015, -0.1))
        obj.rotation_euler.z = math.radians(15)
        bpy.context.view_layer.update()
        return ("Sobre la parrilla (en mostrador_izq) · día",
                [obj, p["cuerpo"], c["trozos"], c["brasa"]] + barra, [p["cuerpo"]], 1.6)
    eq.hoja_mano(ID, "pinza · 0,30 × 0,03 × 0,05 m · utensilio (origen en el centro)", m["obj"], revision,
                 escena=en_parrilla)


def main():
    eq.main_modelo(ID, FAMILIA, construir, revisar, hoja, lambda m: [m["obj"]])


if __name__ == "__main__":
    main()
