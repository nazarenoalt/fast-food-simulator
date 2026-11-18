"""Modelo: tabla para las papas (id `tabla_papas`, accesorios.ron, SPEC-026).

Genera:
    arte/fuentes/cocina/tabla_papas.blend
    godot/modelos/cocina/tabla_papas.glb
    docs/arte/revisiones/tabla_papas.jpg

Uso:
    blender -b -P tools/blender/modelos/tabla_papas.py
    python tools/blender/modelos/tabla_papas.py

La tabla de picar de `tabla_picar.py` (misma forma: 0,35 × 0,02 × 0,25, esquinas redondeadas,
madera clara) usada como **accesorio** de mostrador (Equipamiento): el origen va en el centro
de la base, a nivel del mostrador (guía 2.4), y lleva colisión `tabla_papas-colonly` (una caja),
para que el cuchillo, el pelapapas y la papa que trae su Surtido queden apoyados arriba
(REQ-PAP-06; las posiciones están en accesorios.ron y en la última foto de la hoja).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402

import comun  # noqa: E402
import piezas  # noqa: E402
import _equipos as eq  # noqa: E402
import _etapa2 as e2  # noqa: E402
import tabla_picar  # noqa: E402
from piezas import g2b  # noqa: E402

ID = "tabla_papas"
FAMILIA = "cocina"
PRESUPUESTO = 1000  # accesorios medianos (guía 3.1)
MEDIDAS = tabla_picar.MEDIDAS
# Surtido de accesorios.ron: (producto, posición, giro en Y).
SURTIDO = [("cuchillo", (0.0, 0.031, 0.065), 0), ("pelapapas", (0.07, 0.029, -0.055), -8),
           ("papa_cruda", (-0.1, 0.051, -0.06), 0)]


def construir():
    obj = tabla_picar.construir()["obj"]
    obj.name = obj.data.name = f"{ID}_cuerpo"
    obj.location = g2b((0, MEDIDAS[1] / 2, 0))
    col = piezas.colision_caja(ID, MEDIDAS, (0, MEDIDAS[1] / 2, 0))
    raiz = piezas.raiz(ID, [obj, col])
    bpy.context.view_layer.update()
    return {"raiz": raiz, "obj": obj, "col": col}


def revisar(m):
    return comun.revisar([m["obj"]], PRESUPUESTO, MEDIDAS, origen="base")


def hoja(m, revision):
    import importlib
    comun.preparar_revision()
    vis = [m["obj"]]
    cosas = []
    for prod, pos, giro in SURTIDO:
        o = importlib.import_module(prod).construir(f"ref_{prod}") if prod == "papa_cruda" else \
            importlib.import_module(prod).construir()["obj"]
        o.location = g2b(pos)
        o.rotation_euler.z = __import__("math").radians(giro)
        cosas.append(o)
    bpy.context.view_layer.update()
    cuadros = e2.sacar_fotos([
        ("Frente · día", vis, "frente", "dia"),
        ("3/4 · día", vis, "tres_cuartos", "dia"),
        ("Con su Surtido: cuchillo, pelapapas y una papa · día", vis + cosas, "tres_cuartos", "dia"),
        ("Con su Surtido · atardecer", vis + cosas, "tres_cuartos", "atardecer"),
    ])
    barra = e2.barra_chica()
    for o in [m["raiz"]] + cosas:
        o.location += g2b((0.4, 0.95, 0.0))
    bpy.context.view_layer.update()
    cuadros += e2.sacar_fotos([("Sobre la barra chica (mostrador_der) · día", vis + cosas + barra,
                                "vendedor_alto", "dia", vis + cosas, 2.4)])
    comun.componer_hoja(f"{ID} · 0,35 × 0,02 × 0,25 m · accesorio (tabla con cuchillo, pelapapas y papa)",
                        cuadros, revision, comun.RAIZ / f"docs/arte/revisiones/{ID}.jpg")


def main():
    eq.main_modelo(ID, FAMILIA, construir, revisar, hoja, lambda m: [m["raiz"], m["obj"], m["col"]])


if __name__ == "__main__":
    main()
