"""Piezas y fotos compartidas por la comida de la etapa 4 (hamburguesa y choripán).

Lo usan: medallon, pan_hamburguesa_abajo, pan_hamburguesa_arriba, feta_queso, hamburguesa,
chorizo, pan_frances, choripan, hoja_lechuga, rodaja_tomate y chimichurri. Complementa a
comun.py, piezas.py y _etapa2.py (que no se tocan).

Todo en ejes de Godot (X derecha, Y arriba, Z hacia el cliente), como piezas.py.
"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402  (antes que bmesh)
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

import comun  # noqa: E402
import piezas  # noqa: E402
from piezas import g2b  # noqa: E402
import _etapa2 as e2  # noqa: E402

FAMILIA = "comida"

# ── Hamburguesa: alturas de la pila (Godot, desde el centro de la hamburguesa armada) ──
# base 0,03 + medallón 0,012 + queso 0,003 + tapa 0,045 = 0,09 (lista de modelos).
R_PAN = 0.055                      # Ø 0,11: panes y medallón
ALTO_BASE, ALTO_CARNE, ALTO_QUESO, ALTO_TAPA = 0.03, 0.012, 0.003, 0.045
ALTO_HAMBURGUESA = ALTO_BASE + ALTO_CARNE + ALTO_QUESO + ALTO_TAPA
Y_BASE = -ALTO_HAMBURGUESA / 2 + ALTO_BASE / 2               # centro de cada pieza
Y_CARNE = -ALTO_HAMBURGUESA / 2 + ALTO_BASE + ALTO_CARNE / 2
Y_QUESO_ARRIBA = Y_CARNE + ALTO_CARNE / 2 + ALTO_QUESO       # cara de arriba del queso
Y_TAPA = ALTO_HAMBURGUESA / 2 - ALTO_TAPA / 2

# ── Choripán ──
R_CHORIZO, LARGO_CHORIZO = 0.015, 0.14
PAN_FRANCES = (0.16, 0.06, 0.08)   # ancho X, alto Y, profundidad Z
# Centro del chorizo medido desde el centro del pan francés: queda hundido en la U del
# corte, con la parte de arriba 2 mm por encima del lomo de las mitades.
CHORIZO_Y = 0.017

# Colores de cocción propuestos (solo para las hojas: los pone el juego, como la salchicha).
COCCION_CARNE = [
    ("cruda", "#B5474A"),     # = M_CarneCruda
    ("cocida", "#6E3417"),
    ("pasada", "#4B2815"),
    ("quemada", "#1C1411"),
]
COCCION_CHORIZO = [
    ("crudo", "#B5474A"),     # = M_CarneCruda
    ("cocido", "#8E3D27"),
    ("pasado", "#5A2A1B"),
    ("quemado", "#1E1410"),
]


def rgb(hexa):
    """'#RRGGBB' → (r, g, b) de 0 a 1 en sRGB, como los colores de productos.ron."""
    return tuple(round(int(hexa[i:i + 2], 16) / 255, 2) for i in (1, 3, 5))


# ── Geometría ──────────────────────────────────────────────────────────

def torno(bm, perfil, lados, mats=0, radio=lambda k, i: 1.0, alto=lambda k, i: 0.0, fase=0.0):
    """Superficie de revolución sobre Y (Godot), como e2.torno pero con deformación:
    radio(k, i) multiplica el radio del punto k (alrededor) del anillo i del perfil;
    alto(k, i) suma a su altura. perfil = [(radio, y)], radio 0 = polo. mats = índice o
    uno por banda. Devuelve las caras nuevas."""
    anillos = []
    for i, (r, y) in enumerate(perfil):
        if r <= 1e-9:
            anillos.append([bm.verts.new(g2b((0.0, y, 0.0)))])
            continue
        anillo = []
        for k in range(lados):
            a = fase + 2 * math.pi * k / lados
            rr = r * radio(k, i)
            anillo.append(bm.verts.new(g2b((rr * math.cos(a), y + alto(k, i), rr * math.sin(a)))))
        anillos.append(anillo)
    return e2._unir(bm, anillos, mats, False, False)


def ajustar_caja(bm, medidas):
    """Centra el bmesh en su caja envolvente y la estira a `medidas` (Godot) exactas.
    Para piezas con borde irregular: el ruido corre la caja unos milímetros."""
    vs = bm.verts
    mn = Vector([min(v.co[i] for v in vs) for i in range(3)])
    mx = Vector([max(v.co[i] for v in vs) for i in range(3)])
    centro, tam = (mn + mx) / 2, mx - mn
    obj = piezas.medidas_g2b(medidas)
    for v in vs:
        for i in range(3):
            v.co[i] = (v.co[i] - centro[i]) * obj[i] / tam[i]


def ruido_angular(semilla, armonicos):
    """f(θ) = 1 + Σ amp·sin(n·θ + fase), con fases al azar fijas (semilla)."""
    rnd = random.Random(semilla)
    terms = [(n, amp, rnd.uniform(0, 2 * math.pi)) for n, amp in armonicos]
    return lambda a: 1 + sum(amp * math.sin(n * a + f) for n, amp, f in terms)


def terminar(nombre, bm, materiales, origen=(0.0, 0.0, 0.0)):
    """Comida: sombreado suave completo, borde marcado solo donde cambia el material."""
    return e2.objeto_en(nombre, bm, materiales, origen, sombreado="suave")


# ── Fotos ──────────────────────────────────────────────────────────────

def estados_coccion(obj, estados, paso, eje="y"):
    """Copias de `obj` con los colores de cocción (solo para la foto), en fila."""
    copias = []
    for i, (nombre, hexa) in enumerate(estados):
        c = e2.copiar(obj, f"ref_{obj.name}_{nombre}",
                      comun.crear_material(f"ref_{nombre}_{obj.name}", hexa, rugosidad=0.65))
        d = (i - (len(estados) - 1) / 2) * paso
        if eje == "y":
            c.location.y += d
        else:
            c.location.x += d
        copias.append(c)
    return copias


def pan_de_escala(x, y, z=0.0225):
    """Un pan de pancho (escala de objeto de mano, guía 8.1), solo para las fotos."""
    import pan_pancho
    pan = pan_pancho.construir("ref_pan_pancho")
    pan.location = (x, y, z)
    pan.hide_render = True  # solo aparece en las fotos que lo piden
    return pan


def material_ref(nombre, hexa):
    return comun.crear_material(f"ref_{nombre}", hexa, rugosidad=0.65)


def hoja(id_, titulo, cuadros, revision):
    comun.componer_hoja(titulo, cuadros, revision, comun.RAIZ / f"docs/arte/revisiones/{id_}.jpg")


def guardar_y_exportar(id_, objetos):
    comun.guardar_blend(comun.RAIZ / f"arte/fuentes/{FAMILIA}/{id_}.blend")
    comun.exportar_glb(objetos, comun.RAIZ / f"godot/modelos/{FAMILIA}/{id_}.glb")
