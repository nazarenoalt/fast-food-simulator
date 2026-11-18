"""Modelo: tabla de picar (id `tabla_picar`, etapa 4; objeto de mano con física).

Genera:
    arte/fuentes/cocina/tabla_picar.blend
    godot/modelos/cocina/tabla_picar.glb
    docs/arte/revisiones/tabla_picar.jpg

Uso:
    blender -b -P tools/blender/modelos/tabla_picar.py
    python tools/blender/modelos/tabla_picar.py

Forma: tabla de madera clara de esquinas redondeadas (radio 3 cm), con los bordes de arriba y
de abajo biselados (5 mm, un cuarto del grosor: guía 3.3, piezas finas).

Medidas (lista: 0,35 × 0,02 × 0,25): 0,35 × 0,02 × 0,25 justos.

Objeto único `tabla_picar` (MaderaClara), con el origen en el centro (guía 2.4). Sin
colisión: la define el dato (guía 6.1). Arriba es una cara plana: si el juego la usa como
superficie de trabajo, está a 0,01 del origen.
"""
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

ID = "tabla_picar"
FAMILIA = "cocina"
PRESUPUESTO = 100  # lista de modelos
MEDIDAS = (0.35, 0.02, 0.25)
RADIO, BISEL = 0.03, 0.005
H = MEDIDAS[1]
PERFIL = [(BISEL, -H / 2), (0.0, -H / 2 + BISEL), (0.0, H / 2 - BISEL), (BISEL, H / 2)]


def construir():
    madera, = comun.cargar_materiales("M_MaderaClara")
    bm = bmesh.new()
    eq.e2.torno_rr(bm, PERFIL, MEDIDAS[0] / 2, MEDIDAS[2] / 2, RADIO, segs=2, tapa_ini=True, tapa_fin=True)
    return {"obj": piezas.terminar(ID, bm, [madera])}


def revisar(m):
    return comun.revisar(m["obj"], PRESUPUESTO, MEDIDAS, origen="centro")


def hoja(m, revision):
    def en_barra(obj):
        import _etapa2 as e2
        barra = e2.barra_chica()
        ref = eq.ref_pan_frances("ref_pan_frances")
        obj.location = g2b((-0.35, 0.95 + H / 2, -0.12))
        ref.location = g2b((-0.35, 0.95 + H + 0.03, -0.12))
        bpy.context.view_layer.update()
        return ("Sobre la barra chica, con un pan francés de referencia · día", [obj, ref] + barra, [obj], 3.0)
    eq.hoja_mano(ID, "tabla_picar · 0,35 × 0,02 × 0,25 m · utensilio (origen en el centro)", m["obj"],
                 revision, escena=en_barra)


def main():
    eq.main_modelo(ID, FAMILIA, construir, revisar, hoja, lambda m: [m["obj"]])


if __name__ == "__main__":
    main()
