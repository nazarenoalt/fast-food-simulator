"""Modelo: chorizo en mariposa (id `chorizo_mariposa`, etapa 4; sin dato todavía).

Genera:
    arte/fuentes/comida/chorizo_mariposa.blend
    godot/modelos/comida/chorizo_mariposa.glb
    docs/arte/revisiones/chorizo_mariposa.jpg

Uso:
    python tools/blender/modelos/chorizo_mariposa.py [--sin-hoja]

Forma: la segunda versión del `chorizo` (chorizo.py), abierto a lo largo como se hace a la
parrilla: el corte va por arriba hasta casi la piel de abajo y las dos mitades se abren hacia
los costados, como un libro. Queda la cara cortada hacia arriba (plana, con una canaletita en
el medio donde se unen las mitades) y abajo dos medialunas de piel unidas en el centro por la
piel que no se cortó (la bisagra), con una V entre las dos panzas.
Medidas: 0,14 × 0,015 × 0,05 (mismo largo que el chorizo; alto = medio chorizo; ancho un
poco menos que dos chorizos abiertos: se achica al abrirse sobre la parrilla).
Corte transversal: anillo de 18 puntos (8 por mitad + la canaleta de arriba y la bisagra de
abajo); cada panza es media superelipse (llena, con la base un poco aplastada). A lo largo, 6 cortes: las puntas se achican como las del
chorizo (bajando hacia el centro de la pieza) y se cierran en abanico. Lomitas fijas al azar
(±4 % en la panza, ±0,4 mm en la cara cortada). Después del ruido la pieza se vuelve a
centrar y a medir. Sombreado suave, con el borde marcado entre la cara cortada y la piel
(así se lee el interior sin un segundo material).

El objeto se llama `pieza_chorizo` (guía 4.4 y 6.2), con un solo material, M_CarneCruda: el
juego le cambia el color según la cocción, igual que al chorizo entero (si el interior fuera
otro material, no se cocinaría).
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

ID = "chorizo_mariposa"
PIEZA = "pieza_chorizo"
LARGO, ALTO, ANCHO = c4.LARGO_CHORIZO, 0.015, 0.05
MEDIDAS = (LARGO, ALTO, ANCHO)
PRESUPUESTO = 250

YT = ALTO / 2                 # cara cortada (arriba)
ZC, A, B = ANCHO / 4, ANCHO / 4, ALTO   # cada panza: media superelipse centrada en (ZC, YT)
# Media sección (z, y) de la mitad +Z, de la canaleta hacia afuera y por la panza hasta la
# bisagra. Los índices 1 y 2 son la cara cortada.
SUPER = 2.8   # superelipse: panza llena, con la base un poco aplastada contra la parrilla


def _panza(t):
    c, s = math.cos(math.radians(t)), math.sin(math.radians(t))
    return (ZC + A * math.copysign(abs(c) ** (2 / SUPER), c), YT - B * abs(s) ** (2 / SUPER))


MEDIA = [(0.0015, YT - 0.0002), (ANCHO / 2 - 0.0025, YT)] + [_panza(t) for t in (12, 40, 68, 96, 126, 158)]
CANALETA = (0.0, YT - 0.001)
BISAGRA = (0.0, YT - 0.004)
# Cortes a lo largo (x, escala) y centro hacia donde se achican las puntas.
CORTES = [(0.02, 1.0), (0.05, 0.93), (0.062, 0.62)]
CENTRO_ESCALA = (0.0, 0.0015)
PUNTA = LARGO / 2

# En el pan francés (solo foto): centro de la mariposa medido desde el centro del pan.
# Las panzas apoyan en los bordes de la miga (z ≈ ±0,022, y = 0,026) y la bisagra cuelga
# en la U del corte; se hunde 2,5 mm en la miga.
Y_EN_PAN = 0.0245


def seccion():
    """Anillo completo (z, y, es_corte) de 18 puntos."""
    pts = [(CANALETA[0], CANALETA[1], True)]
    pts += [(z, y, i in (0, 1)) for i, (z, y) in enumerate(MEDIA)]
    pts += [(BISAGRA[0], BISAGRA[1], False)]
    pts += [(-z, y, i in (0, 1)) for i, (z, y) in reversed(list(enumerate(MEDIA)))]
    return pts


SECCION = seccion()
N = len(SECCION)
# Bandas de la cara cortada: canaleta → borde de afuera, en las dos mitades.
BANDAS_CORTE = {k for k in range(N) if SECCION[k][2] and SECCION[(k + 1) % N][2]}


def construir(nombre=PIEZA):
    (material,) = comun.cargar_materiales("M_CarneCruda")
    rnd = random.Random(7)
    estaciones = [(-x, s) for x, s in reversed(CORTES)] + CORTES
    cz, cy = CENTRO_ESCALA
    anillos = []
    for x, s in estaciones:
        anillo = []
        for z, y, corte in SECCION:
            if corte:
                y += rnd.uniform(-0.0004, 0.0004) if abs(z) > 0.001 else 0.0
            elif abs(z) > 0.001:   # panza: lomitas respecto del centro de su media elipse
                f = 1 + rnd.uniform(-0.04, 0.04)
                zc = math.copysign(ZC, z)
                z, y = zc + (z - zc) * f, YT + (y - YT) * f
            z, y = cz + (z - cz) * s, cy + (y - cy) * s
            anillo.append((x, -z, y))           # Godot (x, y, z) → Blender (x, −z, y)
        anillos.append(anillo)
    puntas = [(-PUNTA, 0.0, cy), (PUNTA, 0.0, cy)]
    # Material 1 solo para que lofteo marque el borde entre la cara cortada y la piel;
    # después todo vuelve a M_CarneCruda (un solo material: lo tiñe la cocción).
    obj = comun.lofteo(nombre, anillos, puntas, [material, material],
                       lambda banda, k: 1 if k in BANDAS_CORTE else 0)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    for f in bm.faces:
        f.material_index = 0
    c4.ajustar_caja(bm, MEDIDAS)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.materials.pop(index=1)
    return obj


def hoja_revision(mariposa, revision):
    comun.preparar_revision()
    mariposa.location.z = ALTO / 2
    estados = c4.estados_coccion(mariposa, c4.COCCION_CHORIZO, 0.07)
    for c in estados:
        c.location.x += 0.4
    import chorizo as mod_chorizo
    entero = mod_chorizo.construir("ref_chorizo_entero")
    entero.location = (0.0, 0.06, c4.R_CHORIZO)
    ref = c4.pan_de_escala(0.0, -0.07)
    # Choripán con el chorizo mariposa (copias solo para la foto), corrido en X.
    import pan_frances
    pan = pan_frances.construir("ref_pan_frances")
    pan.location = (-0.4, 0.0, pan_frances.MEDIO_ALTO)
    en_pan = e2.copiar(mariposa, "ref_mariposa_en_pan",
                       c4.material_ref("mariposa_cocido", c4.COCCION_CHORIZO[1][1]))
    en_pan.location = (-0.4, 0.0, pan_frances.MEDIO_ALTO + Y_EN_PAN)
    solo, chori = [mariposa], [pan, en_pan]
    cuadros = e2.sacar_fotos([
        ("Frente · día", solo, "frente", "dia"),
        ("Costado de cerca: las dos mitades y la bisagra · día", solo, "costado", "dia", solo, 1.4),
        ("3/4 · día: la cara cortada", solo, "tres_cuartos", "dia"),
        ("Arriba · día", solo, "arriba", "dia"),
        ("Cocción: crudo, cocido, pasado, quemado · día", estados, "tres_cuartos", "dia"),
        ("3/4 · atardecer", solo, "tres_cuartos", "atardecer"),
        ("Con el chorizo entero y un pan de pancho · día", [mariposa, entero, ref], "tres_cuartos", "dia"),
        ("Choripán mariposa (pan_frances, copia) · día", chori, "tres_cuartos", "dia"),
        ("Choripán mariposa · costado de cerca · día", chori, "costado", "dia", chori, 1.1),
    ])
    c4.hoja(ID, f"{ID} · 0,14 × 0,015 × 0,05 m · comida chica · pieza_chorizo (color por cocción)",
            cuadros, revision)


def main():
    comun.escena_vacia()
    mariposa = construir()
    revision = comun.revisar(mariposa, PRESUPUESTO, MEDIDAS, origen="centro")
    ok = comun.imprimir_revision(ID, revision)
    c4.guardar_y_exportar(ID, [mariposa])
    if "--sin-hoja" not in sys.argv:
        hoja_revision(mariposa, revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
