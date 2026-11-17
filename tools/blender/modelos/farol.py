"""Modelo: farol de plaza (id `farol`, rust/core/src/plaza.rs → TipoProp::Farol).

Genera:
    arte/fuentes/plaza/farol.blend
    godot/modelos/plaza/farol.glb
    docs/arte/revisiones/farol.jpg

Uso:
    python tools/blender/modelos/farol.py [--sin-hoja]

Forma (guía 5.4): farola porteña de hierro (M_Hierro). Base torneada (zócalo, campana y
anillo), columna apenas cónica con un collar arriba y, encima, el farol de 4 caras: bandeja,
vidrio que se abre hacia arriba con 4 parantes en las aristas, techo en pirámide con alero y
un remate.

Medidas (lista-de-modelos ≈ 0,5 × 3,9 × 0,5, se confirma): 0,50 × 3,90 × 0,50. El ancho lo da
el alero del techo (cuadrado de 0,5 m); la base mide Ø 0,34. Hoy el juego dibuja una columna de
radio 0,07 y 3,6 m con un cono de radio 0,22 arriba (hasta 3,975 m) y pone la luz a 3,62 m.
Acá la columna tiene radio 0,07 abajo y 0,055 arriba, y la luz queda en el medio del vidrio.

Objetos (hijos del Empty `farol`, origen = centro de la base, a nivel del piso):
    - farol_cuerpo: todo el hierro.
    - pieza_lampara: el vidrio del farol (M_LuzFarol, emisión), objeto aparte para que el
      juego lo prenda y apague con la luz (guía 4.3).
    - punto_luz: Empty a (0; 3,62; 0), donde el juego pone la LuzNocturna (plaza.rs).
    - farol-colonly: cilindro de la columna (r 0,08, del piso a 3,4 m).
    - farol_base-colonly: cilindro de la base (r 0,17, 0,55 m).
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

ID = "farol"
PRESUPUESTO = 800  # mobiliario urbano (guía 3.1)
MEDIDAS = (0.5, 3.9, 0.5)
LUZ_Y = 3.62       # plaza.rs: luz.set_position(0, 3.62, 0)
R2 = math.sqrt(2)

# Farol: vidrio de VIDRIO_Y0 a VIDRIO_Y1, centrado en la luz.
VIDRIO_Y0, VIDRIO_Y1 = 3.46, 3.78
VIDRIO_ABAJO, VIDRIO_ARRIBA = 0.105, 0.155   # medio lado
ALERO = 0.25                                  # medio lado del techo


def construir():
    hierro, luz = comun.cargar_materiales("M_Hierro", "M_LuzFarol")
    bm = bmesh.new()
    # Base y columna (16 lados: radios de 5 a 25 cm, guía 3.2).
    plaza.torno(bm, [
        (0.17, 0.0), (0.17, 0.05), (0.15, 0.075),    # zócalo con bisel
        (0.125, 0.09), (0.095, 0.40),                # campana
        (0.11, 0.42), (0.11, 0.47), (0.08, 0.50),    # anillo
        (0.07, 0.52), (0.055, 3.24),                 # columna, apenas cónica
        (0.08, 3.26), (0.08, 3.30), (0.055, 3.32),   # collar
        (0.05, 3.40),                                # cuello que recibe el farol
    ], lados=16)
    # Bandeja del farol (pirámide truncada invertida, 4 lados).
    plaza.torno(bm, [(0.045, 3.40), (0.13, 3.45), (0.13, 3.47), (0, 3.47)],
                lados=4, tapa_abajo=True)
    # Parantes en las 4 aristas del vidrio.
    alto = VIDRIO_Y1 - VIDRIO_Y0
    sale = VIDRIO_ARRIBA - VIDRIO_ABAJO
    beta = math.degrees(math.atan2(sale, alto))
    largo = math.hypot(alto, sale)
    medio = (VIDRIO_ABAJO + VIDRIO_ARRIBA) / 2
    for psi, (sx, sz) in ((45, (1, 1)), (135, (1, -1)), (-135, (-1, -1)), (-45, (-1, 1))):
        piezas.caja(bm, (0.025, largo, 0.025), (sx * medio, (VIDRIO_Y0 + VIDRIO_Y1) / 2, sz * medio),
                    rot=(beta, psi, 0))
    # Techo: faja, alero y pirámide, con remate.
    plaza.torno(bm, [
        (0.165, VIDRIO_Y1 - 0.01), (0.165, 3.81),
        (ALERO, 3.81), (ALERO, 3.83), (0.2, 3.845),
        (0.03, 3.875), (0, 3.875),
    ], lados=4, tapa_abajo=True)
    plaza.torno(bm, [(0.0, 3.86), (0.02, 3.87), (0.028, 3.885), (0.0, 3.90)], lados=8)
    plaza.borrar_apoyadas(bm)
    cuerpo = piezas.terminar(f"{ID}_cuerpo", bm, [hierro])

    # Vidrio (pieza_lampara).
    bl = bmesh.new()
    plaza.torno(bl, [(VIDRIO_ABAJO, VIDRIO_Y0), (VIDRIO_ARRIBA, VIDRIO_Y1)], lados=4,
                tapa_abajo=True, tapa_arriba=True)
    lampara = piezas.terminar("pieza_lampara", bl, [luz])

    punto = piezas.punto("punto_luz", (0, LUZ_Y, 0))
    cols = [
        piezas.colision_cilindro(ID, 0.08, 3.4, (0, 1.7, 0)),
        piezas.colision_cilindro(f"{ID}_base", 0.17, 0.55, (0, 0.275, 0), lados=16),
    ]
    raiz = piezas.raiz(ID, [cuerpo, lampara, punto] + cols)
    return {"raiz": raiz, "cuerpo": cuerpo, "lampara": lampara, "punto": punto, "colisiones": cols}


def revisar(mod):
    res = comun.revisar([mod["cuerpo"], mod["lampara"]], PRESUPUESTO, MEDIDAS, origen="base")
    p = mod["punto"].matrix_world.translation
    mn, mx = plaza.limites([mod["lampara"]])
    adentro = mn.y < LUZ_Y < mx.y and abs(p.x) < 1e-6 and abs(p.y) < 1e-6
    res.append((abs(p.z - LUZ_Y) < 1e-6 and adentro,
                "punto_luz a %.2f m, dentro de pieza_lampara (%.2f a %.2f m), como la luz de plaza.rs"
                % (p.z, mn.y, mx.y)))
    return res


def main():
    comun.escena_vacia()
    mod = construir()
    revision = revisar(mod)
    ok = comun.imprimir_revision(ID, revision)
    plaza.guardar_y_exportar(ID, [mod["raiz"], mod["cuerpo"], mod["lampara"], mod["punto"]]
                             + mod["colisiones"])
    if "--sin-hoja" not in sys.argv:
        c = [mod["cuerpo"], mod["lampara"]]
        plaza.hoja(ID, "farol · 0,5 × 3,9 × 0,5 m · luz a 3,62 m · mobiliario urbano", [
            ("Frente · día", c, "frente", "dia", True),
            ("Costado · día", c, "costado", "dia", True),
            ("3/4 · día", c, "tres_cuartos_bajo", "dia", False),
            ("3/4 · atardecer", c, "tres_cuartos_bajo", "atardecer", False),
            ("Con la persona de 1,75 m · día", c + ["persona"], "tres_cuartos_bajo", "dia", False),
        ], revision, persona_en=(0.6, 0, 0.2))
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
