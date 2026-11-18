"""Modelo: bolsa de 12 panes (id `bolsa_panes_12`, godot/data/bloques.ron).

Genera:
    arte/fuentes/stock/bolsa_panes_12.blend
    godot/modelos/stock/bolsa_panes_12.glb
    docs/arte/revisiones/bolsa_panes_12.jpg

Uso:
    blender -b -P tools/blender/modelos/bolsa_panes_12.py
    python tools/blender/modelos/bolsa_panes_12.py

Forma: solo la bolsa (los 12 panes los pone el código, REQ-DEP-03). Una bolsa de plástico
blanda, de sección rectangular con las esquinas redondeadas (más redondeadas arriba), con la
punta de adelante (+Z) cerrada y redondeada, y del lado del vendedor (−Z) la boca juntada en
un cuello, el precinto, el nudo y el "copete" de plástico que sobra. Arriba, una etiqueta
chica de papel. Material transparente (M_BolsaPlastica, alfa 0,35) salvo precinto y etiqueta.

Medidas: el cuerpo envuelve la grilla del dato (1 × 6 × 2 panes, separación 0,18 × 0,047 ×
0,058 → 0,18 × 0,094 × 0,348) con un poco de aire: 0,19 × 0,105 × 0,366. El nudo sobresale
hacia −Z, como hoy en bloque_stock.rs. Origen: centro de la base del cuerpo (donde el código
pone los panes), a nivel de apoyo; el nudo queda afuera de ese centro (chequeo propio).

Sin colisión `-colonly`: el cuerpo del bloque lo crea el código (BloqueStock::ready, caja del
tamaño de la grilla), igual que la colisión de la comida sale de los datos (guía 6.1).
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

ID = "bolsa_panes_12"
FAMILIA = "stock"
PRESUPUESTO = 400  # empaques y bloques de stock (guía 3.1)

# Grilla del dato (bloques.ron): columnas X, filas Z, capas Y.
GRILLA = (1, 6, 2)
SEPARACION = (0.18, 0.047, 0.058)

ANCHO, ALTO = 0.19, 0.105          # sección del cuerpo
R_ABAJO, R_ARRIBA = 0.018, 0.034   # radios de las esquinas de la sección
MEDIO_LARGO = 0.183                # el cuerpo va de −0.183 a +0.183 en Z (Godot)
SEGS_ESQUINA = 2

# Estaciones a lo largo de Z (Godot): (z, escala x, escala y, centro y de la sección, material)
# El material es el de la banda que arranca en esa estación (0 bolsa, 1 papel).
R_CUELLO, R_PRECINTO, R_NUDO = 0.013, 0.0165, 0.02
Y_NUDO = 0.05
ESTACIONES = [
    (0.178, 0.86, 0.86, ALTO * 0.86 / 2, 0),   # punta de adelante, apoyada (centro bajado)
    (0.165, 1.0, 1.0, ALTO / 2, 0),
    (-0.165, 1.0, 1.0, ALTO / 2, 0),
    (-0.178, 0.86, 0.84, ALTO / 2, 0),          # la bolsa se empieza a juntar
    (-0.188, 0.45, 0.50, 0.054, 0),
    (-0.195, None, R_CUELLO, Y_NUDO, 0),        # cuello
    (-0.197, None, R_PRECINTO, Y_NUDO, 1),      # precinto de papel
    (-0.203, None, R_PRECINTO, Y_NUDO, 0),
    (-0.205, None, R_CUELLO, Y_NUDO, 0),
    (-0.210, None, R_NUDO, Y_NUDO, 0),          # nudo
    (-0.222, None, R_NUDO, Y_NUDO, 0),
    (-0.229, None, 0.010, Y_NUDO, 0),
    (-0.236, None, 0.020, Y_NUDO, 0),           # copete que sobra, abierto en abanico
    (-0.246, None, 0.027, Y_NUDO, 0),
]
PUNTA_ADELANTE = (0.0, ALTO * 0.80 / 2, MEDIO_LARGO)
PUNTA_ATRAS = (0.0, Y_NUDO, -0.240)  # el copete termina hundido hacia adentro
LARGO_ATRAS = 0.246

ETIQUETA = (0.085, 0.003, 0.065)  # papel apoyado arriba, hacia adelante
ETIQUETA_Z = 0.06

MEDIDAS = (ANCHO, ALTO + ETIQUETA[1], MEDIO_LARGO + LARGO_ATRAS)  # con el nudo


def seccion():
    """Rectángulo redondeado (x, y) de ANCHO × ALTO apoyado en y = 0, sentido antihorario
    visto desde +Z. Mismo número de puntos en todas las estaciones."""
    puntos = []
    esquinas = [  # (centro x, centro y, radio, ángulo inicial)
        (ANCHO / 2 - R_ABAJO, R_ABAJO, R_ABAJO, -90),
        (ANCHO / 2 - R_ARRIBA, ALTO - R_ARRIBA, R_ARRIBA, 0),
        (-ANCHO / 2 + R_ARRIBA, ALTO - R_ARRIBA, R_ARRIBA, 90),
        (-ANCHO / 2 + R_ABAJO, R_ABAJO, R_ABAJO, 180),
    ]
    for cx, cy, r, a0 in esquinas:
        for i in range(SEGS_ESQUINA + 1):
            a = math.radians(a0 + 90 * i / SEGS_ESQUINA)
            puntos.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return puntos


def anillo(z, sx, sy, cy):
    """Estación del cuerpo (escalas sobre la sección) o del nudo (sx=None: casi redondo)."""
    base = seccion()
    if sx is None:  # sección redonda de radio sy, a partir de la misma cantidad de puntos
        angulos = [math.atan2(y - ALTO / 2, x) for x, y in base]  # sin torcer las caras
        return [(sy * math.cos(a), cy + sy * math.sin(a), z) for a in angulos]
    return [(x * sx, cy + (y - ALTO / 2) * sy, z) for x, y in base]


def construir():
    m_bolsa, m_papel = comun.cargar_materiales("M_BolsaPlastica", "M_BlancoCrema")
    bm = bmesh.new()
    anillos = [[bm.verts.new(piezas.g2b(p)) for p in anillo(z, sx, sy, cy)]
               for z, sx, sy, cy, _ in ESTACIONES]
    n = len(anillos[0])
    for (a, b), (*_, mat) in zip(zip(anillos, anillos[1:]), ESTACIONES):
        for k in range(n):
            f = bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]))
            f.material_index = mat
    for punta, a in ((PUNTA_ADELANTE, anillos[0]), (PUNTA_ATRAS, anillos[-1])):
        v = bm.verts.new(piezas.g2b(punta))
        for k in range(n):
            bm.faces.new((a[k], a[(k + 1) % n], v))
    # Etiqueta de papel: pegada arriba, en la parte plana.
    piezas.caja(bm, ETIQUETA, (0, ALTO + ETIQUETA[1] / 2 - 0.0005, ETIQUETA_Z), mat=1,
                sin_abajo=True)
    return piezas.terminar(ID, bm, [m_bolsa, m_papel], sombreado="suave")


def chequeo_origen(obj):
    """El origen va en el centro de la base del cuerpo, no del total (el nudo sobresale)."""
    zs = [-v.co.y for v in obj.data.vertices]          # Z de Godot
    xs = [v.co.x for v in obj.data.vertices]
    cuerpo = [z for z in zs if abs(z) <= MEDIO_LARGO - 0.004]  # sección completa, sin puntas
    centro_z = (max(cuerpo) + min(cuerpo)) / 2
    centro_x = (max(xs) + min(xs)) / 2
    piso = min(v.co.z for v in obj.data.vertices)
    ok = abs(centro_z) < 0.002 and abs(centro_x) < 0.002 and abs(piso) < 0.002
    return ok, ("Origen en el centro de la base del cuerpo, a nivel de apoyo "
                "(el nudo sobresale %.3f m hacia −Z)" % (-min(zs) - MEDIO_LARGO))


def cambiar_chequeo(res, prefijo, nuevo):
    return [nuevo if texto.startswith(prefijo) else (ok, texto) for ok, texto in res]


def posiciones_panes():
    """Lo mismo que DefBloque::posicion_unidad (rust/core/src/deposito.rs), en Godot."""
    cols, filas, capas = GRILLA
    sx, sy, sz = SEPARACION
    for i in range(cols * filas * capas):
        capa, resto = divmod(i, cols * filas)
        fila, col = divmod(resto, cols)
        yield ((col - (cols - 1) / 2) * sx, capa * sy + sy / 2, ((filas - 1) / 2 - fila) * sz)


def hoja_revision(bolsa, revision):
    import pan_pancho
    comun.preparar_revision()
    panes = []
    for i, pos in enumerate(posiciones_panes()):
        pan = pan_pancho.construir(f"ref_pan_{i}")
        pan.location = piezas.g2b(pos)
        panes.append(pan)
    llena = [bolsa] + panes
    sola = [bolsa]
    cuadros = comun.sacar_fotos([
        ("Frente (cliente, +Z) con los 12 panes · día", llena, "frente", "dia", True),
        ("Costado: nudo hacia el vendedor (−Z) · día", llena, "costado", "dia", True),
        ("3/4 con los panes · día", llena, "tres_cuartos", "dia", False),
        ("Arriba: etiqueta y nudo · día", llena, "arriba", "dia", False),
        ("3/4 con los panes · atardecer", llena, "tres_cuartos", "atardecer", False),
        ("Sola (lo que exporta el .glb) · día", sola, "tres_cuartos", "dia", False),
    ])
    comun.componer_hoja(
        f"{ID} · {MEDIDAS[0]:.2f} × {MEDIDAS[1]:.3f} × {MEDIDAS[2]:.3f} m (con nudo) · stock",
        cuadros, revision, comun.RAIZ / f"docs/arte/revisiones/{ID}.jpg",
    )


def main():
    comun.escena_vacia()
    bolsa = construir()
    revision = comun.revisar(bolsa, PRESUPUESTO, MEDIDAS, origen="base")
    revision = cambiar_chequeo(revision, "Origen", chequeo_origen(bolsa))
    ok = comun.imprimir_revision(ID, revision)
    comun.guardar_blend(comun.RAIZ / f"arte/fuentes/{FAMILIA}/{ID}.blend")
    comun.exportar_glb([bolsa], comun.RAIZ / f"godot/modelos/{FAMILIA}/{ID}.glb")
    if "--sin-hoja" not in sys.argv:
        hoja_revision(bolsa, revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
