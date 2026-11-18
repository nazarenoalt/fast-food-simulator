"""Modelo: salchicha (id `salchicha`, godot/data/productos.ron).

Genera:
    arte/fuentes/comida/salchicha.blend
    godot/modelos/comida/salchicha.glb
    docs/arte/revisiones/salchicha.jpg

Uso:
    blender -b -P tools/blender/modelos/salchicha.py
    python tools/blender/modelos/salchicha.py

Forma: salchicha tipo viena, 8 lados (radio menor a 1,5 cm, guía 3.2), puntas redondeadas
que terminan en un "nudito" chico, y apenas curvada hacia un costado (1,2 mm) para que no
parezca un caño. Medidas = la colisión del dato: cápsula de radio 0,011 y largo 0,15.
El objeto se llama `pieza_salchicha` (guía 6.2): el juego le cambia el color según la
cocción, así que el material es el de la salchicha cruda.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import bpy  # noqa: E402, F401  (carga Blender)

import comun  # noqa: E402

ID = "salchicha"
PIEZA = "pieza_salchicha"
RADIO, LARGO = 0.011, 0.15
MEDIDAS = (LARGO, 2 * RADIO, 2 * RADIO)  # ancho X, alto Y, profundidad Z (Godot)
PRESUPUESTO = 200
LADOS = 8
CURVA = 0.0012  # cuánto se arquea hacia un costado, en el medio

# (x, radio) de cada anillo: puntas redondeadas con un nudito, medio recto.
PERFIL = [
    (0.0715, 0.0045),   # nudito
    (0.068, 0.0078),
    (0.0625, 0.0098),
    (0.055, 0.0108),
    (0.03, RADIO),
    (0.0, RADIO),
]
ANILLOS_X = [(-x, r) for x, r in PERFIL] + [(x, r) for x, r in reversed(PERFIL[:-1])]

# Colores de cocción de productos.ron (solo para la hoja de revisión: los pone el juego).
ESTADOS = [
    ("cruda", "#ED8C80"),
    ("cocida", "#B84C33"),
    ("pasada", "#803824"),
    ("quemada", "#1F140F"),
]


def desvio(x):
    """Curva suave hacia +Y (atrás), centrada para que la pieza quede en el origen."""
    return CURVA * (1 - (x / (LARGO / 2)) ** 2) - CURVA / 2


def construir(nombre=PIEZA):
    (material,) = comun.cargar_materiales("M_SalchichaCruda")
    giro = math.pi / LADOS  # una cara plana abajo: apoya sin rodar de más
    # Las caras planas (no las aristas) tocan el radio del dato: si no, quedaría más fina.
    aj = 1 / math.cos(math.pi / LADOS)
    anillos = [
        [(x, desvio(x) + r * aj * math.cos(giro + 2 * math.pi * k / LADOS),
          r * aj * math.sin(giro + 2 * math.pi * k / LADOS)) for k in range(LADOS)]
        for x, r in ANILLOS_X
    ]
    puntas = [(-LARGO / 2, desvio(-LARGO / 2), 0.0), (LARGO / 2, desvio(LARGO / 2), 0.0)]
    return comun.lofteo(nombre, anillos, puntas, [material])


def hoja_revision(salchicha, revision):
    comun.preparar_revision()
    salchicha.location.z = RADIO
    # Los cuatro estados de cocción, uno al lado del otro (copias solo para la foto).
    estados = []
    for i, (nombre, hexa) in enumerate(ESTADOS):
        copia = salchicha.copy()
        copia.data = salchicha.data.copy()
        copia.data.materials[0] = comun.crear_material(f"ref_{nombre}", hexa, rugosidad=0.6)
        copia.location = (0, (i - 1.5) * 0.04, RADIO)
        bpy.context.scene.collection.objects.link(copia)
        estados.append(copia)
    solo = [salchicha]
    cuadros = comun.sacar_fotos([
        ("Frente · día", solo, "frente", "dia", False),
        ("Costado de cerca · día", solo, "costado", "dia", True),
        ("3/4 · día", solo, "tres_cuartos", "dia", False),
        ("Arriba: se ve la curva · día", solo, "arriba", "dia", False),
        ("3/4 · atardecer", solo, "tres_cuartos", "atardecer", False),
        ("Cocción: cruda, cocida, pasada, quemada · día", estados, "tres_cuartos", "dia", False),
    ])
    comun.componer_hoja(
        "salchicha · Ø 0,022 × 0,15 m · comida chica",
        cuadros, revision, comun.RAIZ / f"docs/arte/revisiones/{ID}.jpg",
    )


def main():
    comun.escena_vacia()
    salchicha = construir()
    revision = comun.revisar(salchicha, PRESUPUESTO, MEDIDAS, origen="centro")
    ok = comun.imprimir_revision(ID, revision)
    comun.guardar_blend(comun.RAIZ / f"arte/fuentes/comida/{ID}.blend")
    comun.exportar_glb([salchicha], comun.RAIZ / f"godot/modelos/comida/{ID}.glb")
    if "--sin-hoja" not in sys.argv:
        hoja_revision(salchicha, revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
