"""Modelo: chorrito de aderezo (id `chorrito_aderezo`, el zigzag que comida.rs dibuja arriba
del pancho por cada aderezo puesto, SPEC-012).

Genera:
    arte/fuentes/comida/chorrito_aderezo.blend
    godot/modelos/comida/chorrito_aderezo.glb
    docs/arte/revisiones/chorrito_aderezo.jpg

Uso:
    blender -b -P tools/blender/modelos/chorrito_aderezo.py
    python tools/blender/modelos/chorrito_aderezo.py

Forma: un hilo de aderezo continuo que va y viene en ondas (3 idas y vueltas a lo largo del
pancho), de sección ovalada (5 mm de ancho × 4 mm de alto, como los palitos de hoy), con las
puntas redondeadas. Se curva hacia abajo en las ondas para quedar apoyado sobre la salchicha
(radio 0,011) en vez de flotar derecho. Sombreado suave (comida, guía 3.4). 6 lados en vez de
8: es un hilo, como los cables y sogas (guía 2.2); con 8 se pasaba de las 300 caras.

Un solo modelo para los tres aderezos: el objeto es `pieza_chorrito` (M_Amarillo en el
archivo = mostaza) y el juego le pone el `color` del aderezo (aderezos.ron), igual que hoy.

Medidas = el zigzag de hoy (6 palitos de 0,03 × 0,004 × 0,005 girados ±35°, de x = −0,0625
a 0,0625): 0,152 de largo y 0,021 de ancho. De alto mide 0,007 (hoy 0,004) porque baja
3 mm en las ondas, siguiendo la salchicha.
Origen: el centro de la caja. Dónde va: comida.rs lo pone a y = 0,037 del centro del pancho
(arriba de la salchicha de piezas simples). Sobre el modelo `pancho` (salchicha a y = 0,004)
va a y = Y_EN_PANCHO (0,0156), +0,003 por cada aderezo más, como hoy.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

import comun  # noqa: E402
import piezas  # noqa: E402
from piezas import g2b  # noqa: E402
import _etapa2 as e2  # noqa: E402

ID = "chorrito_aderezo"
PIEZA = "pieza_chorrito"
FAMILIA = "comida"
PRESUPUESTO = 300  # comida chica (guía 3.1)

ANCHO_HILO, ALTO_HILO = 0.005, 0.004
LADOS = 6
ONDAS = 3                      # idas y vueltas completas
PUNTOS_POR_MEDIA = 3           # segmentos por media onda
LARGO_CAMINO = 0.154           # largo de las ondas completas (las muestras empiezan medio paso adentro)
PUNTA = 0.004                  # cuánto sale cada punta redondeada más allá del eje
AMPLITUD = 0.00815
R_APOYO = 0.011 + ALTO_HILO / 2  # el eje del hilo, apoyado sobre la salchicha
SALCHICHA_Y_PANCHO = 0.004 + 0.011  # arriba de la salchicha en el modelo pancho



def caida(z):
    """Cuánto baja el eje del hilo a `z` del medio, para seguir la salchicha."""
    return R_APOYO - math.sqrt(R_APOYO ** 2 - z ** 2)


CAIDA = caida(AMPLITUD)                      # en las crestas
CAIDA_ALTA = caida(AMPLITUD / 2)             # la muestra más alta (a 30° de la onda)
MEDIDAS = (0.152, ALTO_HILO + CAIDA - CAIDA_ALTA, 2 * AMPLITUD + ANCHO_HILO)
Y_EN_PANCHO = SALCHICHA_Y_PANCHO + ALTO_HILO / 2 - CAIDA_ALTA - (CAIDA - CAIDA_ALTA) / 2  # centro de la caja


def eje(t):
    """Punto del eje (Godot) para t de 0 a 1, antes de centrar."""
    x = -LARGO_CAMINO / 2 + LARGO_CAMINO * t
    z = AMPLITUD * math.sin(2 * math.pi * ONDAS * t)
    y = math.sqrt(max(R_APOYO ** 2 - z ** 2, 0.0)) - R_APOYO
    return Vector((x, y, z))


def construir(nombre=PIEZA):
    (material,) = comun.cargar_materiales("M_Amarillo")
    # Muestras corridas medio paso: así caen justo en las crestas de las ondas.
    m = 2 * ONDAS * PUNTOS_POR_MEDIA
    ts = [(i + 0.5) / m for i in range(m)]
    centros = [eje(t) for t in ts]
    n = len(centros) - 1
    arriba = Vector((0, 1, 0))
    anillos = []
    for i, c in enumerate(centros):
        a = centros[max(i - 1, 0)]
        b = centros[min(i + 1, n)]
        tang = (b - a).normalized()
        lado = arriba.cross(tang).normalized()
        sube = tang.cross(lado).normalized()
        escala = 0.75 if i in (0, n) else 1.0   # se afina un poco en las puntas
        anillos.append([c + lado * (ANCHO_HILO / 2 * escala) * math.cos(2 * math.pi * k / LADOS) +
                        sube * (ALTO_HILO / 2 * escala) * math.sin(2 * math.pi * k / LADOS)
                        for k in range(LADOS)])
    t0 = (centros[1] - centros[0]).normalized()
    t1 = (centros[-1] - centros[-2]).normalized()
    puntas = [centros[0] - t0 * PUNTA, centros[-1] + t1 * PUNTA]
    # Centrar en la caja envolvente.
    todos = [p for a in anillos for p in a] + puntas
    mn = Vector([min(p[i] for p in todos) for i in range(3)])
    mx = Vector([max(p[i] for p in todos) for i in range(3)])
    centro = (mn + mx) / 2
    anillos = [[g2b(p - centro) for p in a] for a in anillos]
    puntas = [g2b(p - centro) for p in puntas]
    return comun.lofteo(nombre, anillos, puntas, [material])


# ── Hoja de revisión ───────────────────────────────────────────────────

def sobre_pancho(nombre_aderezos, dx, mats):
    """Un pancho (modelo pancho) con chorritos de los aderezos dados, a dx en X."""
    import pancho
    raiz, pan, salchicha = pancho.construir()
    raiz.location = (dx, 0, 0.0225)
    objs = [pan, salchicha]
    for k, nombre in enumerate(nombre_aderezos):
        ch = construir(f"ref_chorrito_{nombre}_{dx}")
        ch.data.materials[0] = mats[nombre]
        ch.location = (dx, 0, 0.0225 + Y_EN_PANCHO + 0.003 * k)
        objs.append(ch)
    return objs


def hoja_revision(chorrito, revision):
    comun.preparar_revision()
    mats = e2.materiales_aderezo(rugosidad=0.45)
    chorrito.location.z = MEDIDAS[1] / 2
    solo = [chorrito]
    mostaza = sobre_pancho(["mostaza"], 0.4, mats)
    dos = sobre_pancho(["ketchup", "mostaza"], 0.7, mats)
    tres = sobre_pancho(["mayonesa", "ketchup", "mostaza"], 1.0, mats)
    cuadros = e2.sacar_fotos([
        ("Arriba · día", solo, "arriba", "dia"),
        ("Frente · día", solo, "frente", "dia", solo, 1.1),
        ("3/4 · día", solo, "tres_cuartos", "dia"),
        ("Sobre el pancho (mostaza) · día", mostaza, "tres_cuartos", "dia"),
        ("Ketchup y mostaza (+3 mm cada uno) · día", dos, "tres_cuartos", "dia"),
        ("Los tres aderezos · atardecer", tres, "tres_cuartos", "atardecer"),
    ])
    comun.componer_hoja(
        f"{ID} · 0,152 × 0,007 × 0,021 m · el juego pone el color del aderezo",
        cuadros, revision, comun.RAIZ / f"docs/arte/revisiones/{ID}.jpg",
    )


def main():
    comun.escena_vacia()
    chorrito = construir()
    revision = comun.revisar(chorrito, PRESUPUESTO, MEDIDAS, origen="centro")
    ok = comun.imprimir_revision(ID, revision)
    comun.guardar_blend(comun.RAIZ / f"arte/fuentes/{FAMILIA}/{ID}.blend")
    comun.exportar_glb([chorrito], comun.RAIZ / f"godot/modelos/{FAMILIA}/{ID}.glb")
    if "--sin-hoja" not in sys.argv:
        hoja_revision(chorrito, revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
