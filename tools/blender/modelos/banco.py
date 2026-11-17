"""Modelo: banco de plaza (id `banco`, rust/core/src/plaza.rs → TipoProp::Banco).

Genera:
    arte/fuentes/plaza/banco.blend
    godot/modelos/plaza/banco.glb
    docs/arte/revisiones/banco.jpg

Uso:
    python tools/blender/modelos/banco.py [--sin-hoja]

Forma (guía 5.4): banco de plaza porteño, de tablas de madera (M_Madera) sobre dos patas
laterales de fundición (M_Hierro). Cada pata lateral: pata delantera que sigue hasta el
apoyabrazos, pata trasera abierta hacia atrás que sigue como soporte del respaldo inclinado
(15°), travesaño bajo el asiento y apoyabrazos. Asiento de 4 tablas y respaldo de 3.

Medidas (lista-de-modelos: 1,6 × 0,8 × 0,6):
    - largo 1,60 (las tablas; las patas van en x = ±0,65, como hoy en el juego ±0,7);
    - arriba del asiento a 0,45 m (guía 2.1, "asiento a 0,45"). Hoy el juego dibuja la tabla
      del asiento CENTRADA en 0,45 (arriba en 0,475): acá 0,45 es la superficie donde uno se
      sienta;
    - arriba del respaldo a 0,80 (hoy 0,895);
    - profundidad total 0,60 (de la punta de la pata delantera a la de la trasera); hoy 0,435.
Frente (+Z de Godot, −Y de Blender) = el lado donde uno se sienta, con el respaldo hacia −Z,
igual que en el juego (plaza.rs gira los bancos con rot_y para que +Z mire al camino;
test req_mun_02_bancos_miran_al_camino).
Origen: centro de la caja envolvente, a nivel del piso (las patas apoyan en Y = 0). El
asiento (de z = −0,15 a +0,28) queda corrido 7 cm hacia adelante del origen (hoy está
centrado), porque el respaldo inclinado ocupa lugar atrás. Las patas inclinadas se hunden 2 mm
en el piso (mejor eso que flotar).

Biseles: la guía pide 2–3 cm en mobiliario urbano, pero las tablas tienen 4 cm de grueso y
las barras de fundición 4–5 cm: un bisel de 2 cm las dejaría redondas. Se usa 1 cm en las
tablas y 8 mm en el hierro (un cuarto del grosor), que se lee igual de terminado.
Grosor mínimo (2,2): todo mide 3,5 cm o más.

Objetos (hijos del Empty `banco`):
    - banco_cuerpo: toda la malla visible (madera + hierro).
    - banco-colonly: caja del asiento, del piso a 0,45 (1,6 × 0,45 × 0,42).
    - banco_respaldo-colonly: caja inclinada del respaldo.
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

ID = "banco"
PRESUPUESTO = 800  # mobiliario urbano (guía 3.1)
MEDIDAS = (1.6, 0.8, 0.6)
MADERA, HIERRO = 0, 1

LARGO = 1.6
X_PATA = 0.65
ASIENTO = 0.45              # arriba de las tablas del asiento
TABLA = (0.09, 0.04)        # ancho (z), grueso (y) de las tablas del asiento
LUZ = 0.022                 # separación entre tablas
TABLA_R = (0.085, 0.035)    # tablas del respaldo
INCLINACION = 15.0          # respaldo, grados desde la vertical
ARRIBA = 0.80               # arriba del respaldo
GROSOR_PATA = 0.04          # fundición, en X
BARRA = 0.05                # ancho de las barras de la pata
BISEL_MADERA = 0.01
BISEL_HIERRO = 0.008
Z_PIE = 0.245  # puntas de las patas, adelante y atrás
Z_RESPALDO = 0.005  # cuánto arranca el respaldo detrás del borde del asiento


def construir():
    mats = comun.cargar_materiales("M_Madera", "M_Hierro")
    bm = bmesh.new()

    # ── Asiento: 4 tablas, la de adelante en z_frente ──
    z_frente = 0.25
    y_tabla = ASIENTO - TABLA[1] / 2
    zs = [z_frente - TABLA[0] / 2 - i * (TABLA[0] + LUZ) for i in range(4)]
    for z in zs:
        piezas.caja(bm, (LARGO, TABLA[1], TABLA[0]), (0, y_tabla, z), mat=MADERA, bisel=BISEL_MADERA)
    z_atras = zs[-1] - TABLA[0] / 2   # borde de atrás del asiento

    # ── Respaldo: 3 tablas sobre una línea inclinada que sube hacia atrás ──
    # linea(s, d) = punto (y, z) a una distancia s a lo largo de la cara de adelante del
    # soporte de hierro, corrido d hacia el que se sienta (d < 0: hacia atrás).
    t = math.radians(INCLINACION)
    eje = (math.cos(t), -math.sin(t))     # (dy, dz) a lo largo del respaldo
    normal = (math.sin(t), math.cos(t))   # hacia el que se sienta
    y_rail = y_tabla - TABLA[1] / 2 - 0.02          # travesaño bajo las tablas
    y0, z0 = y_rail, z_atras - Z_RESPALDO

    def linea(s, d=0.0):
        return (y0 + s * eje[0] + d * normal[0], z0 + s * eje[1] + d * normal[1])

    def s_de(y, d=0.0):
        return (y - y0 - d * normal[0]) / eje[0]

    h, g = TABLA_R
    paso = h + LUZ
    # La tabla de arriba toca justo ARRIBA con su arista de adelante-arriba.
    cy_tope = ARRIBA - (h / 2) * eje[0] - (g / 2) * normal[0]
    for i in range(3):
        s = s_de(cy_tope, g / 2) - i * paso
        piezas.caja(bm, (LARGO, h, g), (0, *linea(s, g / 2)), mat=MADERA, bisel=BISEL_MADERA,
                    rot=(-INCLINACION, 0, 0))

    # ── Patas laterales de fundición ──
    def pata(x):
        b = BARRA
        brazo = 0.62  # centro del apoyabrazos
        # Pata delantera: del piso hasta el apoyabrazos, apenas inclinada.
        plaza.barra(bm, x, (0.0, Z_PIE), (brazo, Z_PIE - 0.04), b, GROSOR_PATA, HIERRO, BISEL_HIERRO)
        # Apoyabrazos: de la pata delantera al soporte del respaldo.
        plaza.barra(bm, x, (brazo + 0.01, Z_PIE - 0.02), linea(s_de(brazo + 0.01, -b / 2), -b / 2),
                    0.045, GROSOR_PATA + 0.02, HIERRO, BISEL_HIERRO)
        # Travesaño bajo el asiento.
        plaza.barra(bm, x, (y_rail, z_frente - 0.01), linea(0.0, -b / 2), 0.04,
                    GROSOR_PATA, HIERRO, BISEL_HIERRO)
        # Pata trasera, abierta hacia atrás, hasta el arranque del respaldo.
        plaza.barra(bm, x, (0.0, -Z_PIE), linea(0.0, -b / 2), b, GROSOR_PATA, HIERRO, BISEL_HIERRO)
        # Soporte del respaldo: sigue la línea inclinada, detrás de las tablas.
        plaza.barra(bm, x, linea(0.0, -b / 2), linea(s_de(ARRIBA - 0.035, -b / 2), -b / 2), b,
                    GROSOR_PATA, HIERRO, BISEL_HIERRO)

    for sx in (-1, 1):
        pata(sx * X_PATA)

    # Centrar la caja envolvente en Z (el origen va en el centro de la base).
    zs_todos = [-v.co.y for v in bm.verts]
    dz = -(min(zs_todos) + max(zs_todos)) / 2
    bmesh.ops.translate(bm, vec=piezas.g2b((0, 0, dz)), verts=bm.verts)
    plaza.borrar_apoyadas(bm)
    cuerpo = piezas.terminar(f"{ID}_cuerpo", bm, mats)

    # ── Colisión ──
    z_asiento = (z_frente + z_atras) / 2 + dz
    col_asiento = piezas.colision_caja(ID, (LARGO, ASIENTO, z_frente - z_atras),
                                       (0, ASIENTO / 2, z_asiento))
    yc = (ARRIBA + ASIENTO) / 2
    yc, zc = linea(s_de(yc), 0.0)
    col_respaldo = piezas.colision_caja(f"{ID}_respaldo", (LARGO, (ARRIBA - ASIENTO) / eje[0], 0.08),
                                        (0, yc, zc + dz), rot=(-INCLINACION, 0, 0))
    raiz = piezas.raiz(ID, [cuerpo, col_asiento, col_respaldo])
    return {"raiz": raiz, "cuerpo": cuerpo, "colisiones": [col_asiento, col_respaldo],
            "z_asiento": (z_atras + dz, z_frente + dz)}


def revisar(mod):
    res = comun.revisar(mod["cuerpo"], PRESUPUESTO, MEDIDAS, origen="base")
    # Altura del asiento: lo más alto de las tablas del asiento (entre sus bordes en Z, sin
    # contar las patas: solo las puntas de las tablas, afuera de las patas).
    z0, z1 = mod["z_asiento"]
    vs = [v for v in plaza.verts_mundo([mod["cuerpo"]])
          if z0 + 0.03 < -v.y < z1 - 0.03 and abs(v.x) > X_PATA + 0.05]
    alto = max(v.z for v in vs)
    res.append((abs(alto - ASIENTO) < 0.002, "Asiento a %.3f m del piso (guía 2.1: 0,45)" % alto))
    return res


def main():
    comun.escena_vacia()
    mod = construir()
    revision = revisar(mod)
    ok = comun.imprimir_revision(ID, revision)
    plaza.guardar_y_exportar(ID, [mod["raiz"], mod["cuerpo"]] + mod["colisiones"])
    if "--sin-hoja" not in sys.argv:
        c = [mod["cuerpo"]]
        plaza.hoja(ID, "banco · 1,6 × 0,8 × 0,6 m · asiento a 0,45 m · mobiliario urbano", [
            ("Frente (donde uno se sienta) · día", c, "frente", "dia", True),
            ("Costado · día", c, "costado", "dia", True),
            ("3/4 · día", c, "tres_cuartos", "dia", False),
            ("3/4 · atardecer", c, "tres_cuartos", "atardecer", False),
            ("Con la persona de 1,75 m · día", c + ["persona"], "tres_cuartos", "dia", False),
            ("Arriba · día", c, "arriba", "dia", True),
        ], revision, persona_en=(1.2, 0, 0.3))
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
