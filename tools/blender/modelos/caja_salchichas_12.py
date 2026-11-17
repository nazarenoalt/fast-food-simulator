"""Modelo: bandeja de 12 salchichas (id `caja_salchichas_12`, godot/data/bloques.ron).

Genera:
    arte/fuentes/stock/caja_salchichas_12.blend
    godot/modelos/stock/caja_salchichas_12.glb
    docs/arte/revisiones/caja_salchichas_12.jpg

Uso:
    blender -b -P tools/blender/modelos/caja_salchichas_12.py
    python tools/blender/modelos/caja_salchichas_12.py

Forma: solo el paquete (las 12 salchichas las pone el código, REQ-DEP-03). Bandeja de cartón
baja, de esquinas redondeadas, con las paredes un poco abiertas hacia arriba y una pestaña
plana alrededor del borde; arriba, el film transparente pegado a la pestaña y estirado sobre
las salchichas (abierto abajo: esa cara nunca se ve, guía 3.6).

Medidas: adentro (0,15 × 0,146 en el fondo, 0,152 × 0,149 a la altura de las salchichas de
abajo) entra la grilla del dato (1 × 6 × 2 salchichas, separación 0,16 × 0,024 × 0,025: 0,15
de largo y 0,147 de profundidad) y la pared tiene la altura de hoy (0,45 del alto de la
grilla ≈ 0,022). Afuera: 0,172 × 0,051 × 0,168. Las salchichas de abajo quedan 2 mm metidas
en el fondo de 3 mm (posicion_unidad arranca en y = 0); no se nota.
Origen: centro de la base, a nivel de apoyo.

Sin colisión `-colonly`: el cuerpo del bloque lo crea el código (BloqueStock::ready), como en
la bolsa de panes.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402
import bmesh  # noqa: E402

import comun  # noqa: E402
import piezas  # noqa: E402

ID = "caja_salchichas_12"
FAMILIA = "stock"
PRESUPUESTO = 300  # lista de modelos (tope de empaques: 400)

GRILLA = (1, 6, 2)
SEPARACION = (0.16, 0.024, 0.025)

# Contorno exterior de la pestaña (medio ancho X, media profundidad Z) y radio de esquina.
MEDIO_X, MEDIO_Z, RADIO = 0.086, 0.084, 0.014
SEGS_ESQUINA = 2

# Perfil de la bandeja: (cuánto se mete desde el contorno de la pestaña, altura y).
# Sale del borde de abajo, sube por afuera, da la vuelta por la pestaña y baja por adentro
# hasta el fondo. Pared de 3 mm, pestaña de 3 mm, paredes abiertas 2 mm.
FONDO = 0.003
BORDE = 0.022
PERFIL_BANDEJA = [
    (0.0080, 0.0),       # borde de abajo, por afuera
    (0.0055, BORDE - 0.003),
    (0.0, BORDE - 0.002),  # pestaña, abajo
    (0.0, BORDE + 0.001),  # pestaña, arriba
    (0.0075, BORDE + 0.001),
    (0.0085, BORDE - 0.004),
    (0.0085 + 0.0025, FONDO),  # fondo de adentro
]
# Film: pegado arriba de la pestaña, estirado sobre las dos capas de salchichas.
PERFIL_FILM = [
    (0.0015, BORDE + 0.0016),
    (0.0050, 0.040),
    (0.0120, 0.0485),
    (0.0240, 0.0505),
]
MEDIDAS = (2 * MEDIO_X, PERFIL_FILM[-1][1], 2 * MEDIO_Z)


def anillo(meter, y):
    """Rectángulo redondeado a `meter` del contorno, a la altura y (Godot)."""
    ax, az = MEDIO_X - meter, MEDIO_Z - meter
    r = max(RADIO - meter, 0.003)
    puntos = []
    for cx, cz, a0 in ((ax - r, az - r, 0), (-ax + r, az - r, 90),
                       (-ax + r, -az + r, 180), (ax - r, -az + r, 270)):
        for i in range(SEGS_ESQUINA + 1):
            a = math.radians(a0 + 90 * i / SEGS_ESQUINA)
            puntos.append((cx + r * math.cos(a), y, cz + r * math.sin(a)))
    return puntos


def torno(bm, perfil, mat, tapa_inicio=True, tapa_fin=True):
    """Barre el perfil alrededor de Y con anillos de rectángulo redondeado."""
    anillos = [[bm.verts.new(piezas.g2b(p)) for p in anillo(m, y)] for m, y in perfil]
    n = len(anillos[0])
    caras = []
    for a, b in zip(anillos, anillos[1:]):
        for k in range(n):
            caras.append(bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k])))
    if tapa_inicio:
        caras.append(bm.faces.new(anillos[0]))
    if tapa_fin:
        caras.append(bm.faces.new(anillos[-1]))
    for f in caras:
        f.material_index = mat
    return caras


def suavizar_material(obj, indice):
    """Sombreado suave en las caras de un material (el film es una tela, guía 3.4)."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    for e in bm.edges:
        if all(f.material_index == indice for f in e.link_faces):
            e.smooth = True
    bm.to_mesh(obj.data)
    bm.free()


def construir():
    m_carton, m_film = comun.cargar_materiales("M_Carton", "M_BolsaPlastica")
    bm = bmesh.new()
    torno(bm, PERFIL_BANDEJA, 0)
    torno(bm, PERFIL_FILM, 1, tapa_inicio=False)
    obj = piezas.terminar(ID, bm, [m_carton, m_film], sombreado="duro")
    suavizar_material(obj, 1)
    return obj


def posiciones_unidades():
    """Lo mismo que DefBloque::posicion_unidad (rust/core/src/deposito.rs), en Godot."""
    cols, filas, capas = GRILLA
    sx, sy, sz = SEPARACION
    for i in range(cols * filas * capas):
        capa, resto = divmod(i, cols * filas)
        fila, col = divmod(resto, cols)
        yield ((col - (cols - 1) / 2) * sx, capa * sy + sy / 2, ((filas - 1) / 2 - fila) * sz)


def hoja_revision(bandeja, revision):
    import salchicha
    comun.preparar_revision()
    unidades = []
    for i, pos in enumerate(posiciones_unidades()):
        s = salchicha.construir(f"ref_salchicha_{i}")
        s.location = piezas.g2b(pos)
        unidades.append(s)
    llena, sola = [bandeja] + unidades, [bandeja]
    cuadros = comun.sacar_fotos([
        ("Frente (cliente, +Z) con las 12 salchichas · día", llena, "frente", "dia", True),
        ("Costado con las salchichas · día", llena, "costado", "dia", True),
        ("3/4 con las salchichas · día", llena, "tres_cuartos", "dia", False),
        ("Arriba · día", llena, "arriba", "dia", False),
        ("3/4 con las salchichas · atardecer", llena, "tres_cuartos", "atardecer", False),
        ("Sola (lo que exporta el .glb) · día", sola, "tres_cuartos", "dia", False),
    ])
    comun.componer_hoja(
        f"{ID} · {MEDIDAS[0]:.3f} × {MEDIDAS[1]:.3f} × {MEDIDAS[2]:.3f} m · stock",
        cuadros, revision, comun.RAIZ / f"docs/arte/revisiones/{ID}.jpg",
    )


def main():
    comun.escena_vacia()
    bandeja = construir()
    revision = comun.revisar(bandeja, PRESUPUESTO, MEDIDAS, origen="base")
    ok = comun.imprimir_revision(ID, revision)
    comun.guardar_blend(comun.RAIZ / f"arte/fuentes/{FAMILIA}/{ID}.blend")
    comun.exportar_glb([bandeja], comun.RAIZ / f"godot/modelos/{FAMILIA}/{ID}.glb")
    if "--sin-hoja" not in sys.argv:
        hoja_revision(bandeja, revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
