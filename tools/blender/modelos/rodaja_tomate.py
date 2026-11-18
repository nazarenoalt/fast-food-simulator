"""Modelo: rodaja de tomate (id `rodaja_tomate`, etapa 4; solo si hay ingredientes extra).

Genera:
    arte/fuentes/comida/rodaja_tomate.blend
    godot/modelos/comida/rodaja_tomate.glb
    docs/arte/revisiones/rodaja_tomate.jpg

Uso:
    blender -b -P tools/blender/modelos/rodaja_tomate.py
    python tools/blender/modelos/rodaja_tomate.py

Forma: rodaja Ø 0,07 × 0,008 (lista de modelos), M_Tomate, 12 lados (radio de 1,5 a 5 cm,
guía 3.2). Caras de arriba y de abajo planas, canto redondeado (la piel). El contorno es
apenas irregular, como un tomate de verdad. 72 triángulos (presupuesto 80). Sombreado suave.
Las semillas y la pulpa clara no van: harían falta colores nuevos (y es detalle fino).
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402, F401
import bmesh  # noqa: E402

import comun  # noqa: E402
import _comida4 as c4  # noqa: E402
import _etapa2 as e2  # noqa: E402

ID = "rodaja_tomate"
R, ALTO = 0.035, 0.008
MEDIDAS = (2 * R, ALTO, 2 * R)
PRESUPUESTO = 80
LADOS = 12
H = ALTO / 2

PERFIL = [
    (0.0, -H),
    (0.0305, -H),
    (R, 0.0),       # canto
    (0.0305, H),
    (0.0, H),
]


def construir(nombre=ID):
    (material,) = comun.cargar_materiales("M_Tomate")
    forma = c4.ruido_angular(17, [(2, 0.025), (3, 0.02)])
    bm = bmesh.new()
    c4.torno(bm, PERFIL, LADOS, radio=lambda k, i: forma(2 * math.pi * k / LADOS))
    c4.ajustar_caja(bm, MEDIDAS)
    return c4.terminar(nombre, bm, [material])


def hoja_revision(tomate, revision):
    comun.preparar_revision()
    tomate.location.z = H
    ref = c4.pan_de_escala(0.0, -0.08)
    solo = [tomate]
    import hamburguesa
    import hoja_lechuga
    raiz, piezas = hamburguesa.construir()
    piezas[1].data.materials[0] = c4.material_ref("carne_cocida", c4.COCCION_CARNE[1][1])
    raiz.location = (0.4, 0, c4.ALTO_HAMBURGUESA / 2)
    base_y = c4.ALTO_HAMBURGUESA / 2 + c4.Y_QUESO_ARRIBA
    lech = hoja_lechuga.construir("ref_lechuga")
    lech.location = (0.4, 0, base_y + 0.004)
    t1 = e2.copiar(tomate, "ref_tomate1")
    t1.location = (0.4 + 0.022, 0.012, base_y + 0.009 + H)
    t2 = e2.copiar(tomate, "ref_tomate2")
    t2.location = (0.4 - 0.024, -0.01, base_y + 0.009 + H)
    piezas[3].location.z += 0.018
    completa = piezas + [lech, t1, t2]
    cuadros = e2.sacar_fotos([
        ("Frente · día", solo, "frente", "dia", solo, 1.1),
        ("Arriba · día", solo, "arriba", "dia"),
        ("3/4 · día", solo, "tres_cuartos", "dia"),
        ("3/4 · atardecer", solo, "tres_cuartos", "atardecer"),
        ("Hamburguesa completa (prueba: lechuga y 2 rodajas, tapa +18 mm) · día", completa, "tres_cuartos", "dia"),
        ("Al lado de un pan de pancho · día", [tomate, ref], "tres_cuartos", "dia"),
    ])
    c4.hoja(ID, f"{ID} · Ø 0,07 × 0,008 m · ingrediente extra", cuadros, revision)


def main():
    comun.escena_vacia()
    tomate = construir()
    revision = comun.revisar(tomate, PRESUPUESTO, MEDIDAS, origen="centro")
    ok = comun.imprimir_revision(ID, revision)
    c4.guardar_y_exportar(ID, [tomate])
    if "--sin-hoja" not in sys.argv:
        hoja_revision(tomate, revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
