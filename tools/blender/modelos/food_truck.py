"""Modelo: food truck (id `food_truck`, etapa 5; todavía sin `.ron`: medidas y anclajes
propuestos acá para la spec).

Genera:
    arte/fuentes/carritos/food_truck.blend
    godot/modelos/carritos/food_truck.glb
    docs/arte/revisiones/food_truck.jpg

Uso:
    python tools/blender/modelos/food_truck.py [--sin-hoja]

Camioncito con caja cocina, como los de las ferias: la caja (casilla) de 3,30 m con la ventana
de atención del lado del cliente (+Z) y la puerta con escalón del lado del vendedor (−Z), y la
cabina del chofer adelante, en la punta +X (más baja: arriba de la cabina se ve la pared de la
caja). La construcción común (casilla, mesadas, bahías, puerta, toldo) está en _rodante.py; acá
va la cabina (perfil estirado de lado a lado con el pasarruedas en arco y las aristas
redondeadas, parabrisas y ventanillas oscuras, faros, parrilla, paragolpes y espejos).

Presupuesto: 5.000 triángulos (la lista pide excepción al tope de 3.000 de las bases, a
confirmar en la spec). Materiales (6): M_PinturaCarrito, M_Acero, M_Goma, M_PlasticoNegro,
M_Hierro (vidrios de la cabina, opacos como en los autos), M_BlancoCrema (forro de adentro y
faros apagados).

Medidas propuestas para `food_truck.ron` (la lista dice ≈ 2,2 × 2,6 × 4,5 con el largo en Z;
acá el largo va en X, porque la ventana de atención tiene que mirar al cliente, +Z):
    ancho 4,50 (casilla 3,30 + cabina 1,20), profundidad 2,20, alto total 2,72 (techo 2,62 +
    extractor). Piso de adentro a 0,50, escalón a 0,25, mesadas a 1,45 (alto_mostrador =
    piso + 0,95, medido desde la calle), techo de adentro a 2,57 (2,07 m libres).
    Ventana de atención de x −1,75 a 0,55 (2,30 m), de 1,41 a 2,25; repisa de afuera de 25 cm.
    Puerta de x 0,10 a 0,85, hasta 2,25. 3 bahías bajo la mesada de la ventana.
    Ruedas: radio 0,38; eje de atrás en x −1,60 (adentro de la caja, con pasarruedas), eje de
    adelante en x 1,68 (bajo la cabina).
Anclajes propuestos (pos en Godot, desde el centro de la casilla a nivel de la calle):
    mostrador_izq (−1,35; 1,45; 0,75)   [Cocina, Equipamiento]
    mostrador_centro (−0,60; 1,45; 0,75) [Cocina, Equipamiento, Decoracion]
    mostrador_der (0,15; 1,45; 0,75)    [Cocina, Equipamiento, Decoracion]
    atras_izq (−1,75; 1,45; −0,775)     [Cocina, Equipamiento, Deposito]   mesada de atrás
    atras_der (−0,75; 1,45; −0,775)     [Cocina, Equipamiento, Deposito]
    frente (−0,60; 0,70; 1,11)          [Telon, Decoracion]   el telón queda bajo la ventana
    cartel (−0,60; 2,62; 0,75)          [Decoracion]          arriba del techo (cartel luminoso)
    luz_1 (−1,20; 2,57; 0,30), luz_2 (0,0; 2,57; 0,30)  [Luz]  colgadas del techo de adentro
    entrega (−0,10; 1,45; 1,22)  en la repisa de afuera
    fila (−0,60; 0,0; 1,75)      primer lugar, frente a la ventana (sigue hacia +X)
    entrada (0,475; 0,0; −1,75)  al pie del escalón (punto nuevo: donde sube el jugador)
    bahia_1..3: los punto_bahia_<n> (boca a z 0,47, piso de la bahía a 0,79).
Sin `sombra` ni `techo`: la sombrilla y los techos chocarían con la caja (el toldo ya es la
tapa de la ventana).
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402,F401  (antes que bmesh)
import bmesh  # noqa: E402

import piezas  # noqa: E402
import _plaza as plaza  # noqa: E402
import _rodante as r  # noqa: E402
from piezas import g2b  # noqa: E402

ID = "food_truck"
CAB = dict(x0=1.03, x1=2.25, zh=1.06, y_techo=2.10)
EJE_ADELANTE = 1.68
R_RUEDA = 0.38


def cabina(bm, P):
    """Cabina del chofer (punta +X). Devuelve sus cajas de colisión."""
    x0, x1, zh, yt = CAB["x0"], CAB["x1"], CAB["zh"], CAB["y_techo"]
    y0 = P["y_base"]
    # Perfil (x, y, redondear) de atrás hacia adelante por abajo, con el pasarruedas.
    pts = [(x0, y0, False)]
    ra, yc = 0.46, R_RUEDA
    dx = math.sqrt(ra ** 2 - (yc - y0) ** 2)
    a0 = math.atan2(y0 - yc, dx)
    for i in range(9):
        a = (math.pi - a0) - (math.pi - 2 * a0) * i / 8
        pts.append((EJE_ADELANTE + ra * math.cos(a), yc + ra * math.sin(a), False))
    pts += [(x1, y0, True), (x1, 1.02, True), (2.21, 1.12, True), (2.04, 1.17, True), (1.74, 2.02, True),
            (1.66, yt, True), (x0, yt, False)]
    n = len(pts)
    lados = [[bm.verts.new(g2b((x, y, s * zh))) for x, y, _ in pts] for s in (-1, 1)]
    previas = set(bm.faces)
    for k in range(n):
        k2 = (k + 1) % n
        bm.faces.new((lados[0][k], lados[0][k2], lados[1][k2], lados[1][k]))
    bm.faces.new(lados[0])
    bm.faces.new(list(reversed(lados[1])))
    nuevas = [f for f in bm.faces if f not in previas]
    bmesh.ops.recalc_face_normals(bm, faces=nuevas)
    aristas = [bm.edges.get((lado[k], lado[(k + 1) % n])) for lado in lados for k in range(n) if pts[k][2]]
    bmesh.ops.bevel(bm, geom=aristas, offset=0.06, segments=2, affect="EDGES", profile=0.5, clamp_overlap=True)
    for f in bm.faces:
        if f not in previas:
            f.material_index = r.PINT
    # Parabrisas (19,4° hacia atrás) y ventanillas (vidrio oscuro opaco, como los autos).
    ang = math.degrees(math.atan2(2.04 - 1.74, 2.02 - 1.17))
    nx, ny = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    piezas.caja(bm, (0.02, 0.80, 1.78), ((2.04 + 1.74) / 2 + 0.006 * nx, (1.17 + 2.02) / 2 + 0.006 * ny, 0),
                mat=r.EXTRA, rot=(0, 0, ang))
    for s in (-1, 1):
        piezas.caja(bm, (0.50, 0.55, 0.02), (1.40, 1.62, s * (zh + 0.005)), mat=r.EXTRA)
        piezas.caja(bm, (0.12, 0.025, 0.02), (1.22, 1.20, s * (zh + 0.008)), mat=r.NEGRO, bisel=0.005)
    # Frente: faros (apagados, crema), parrilla y paragolpes.
    for s in (-1, 1):
        piezas.caja(bm, (0.04, 0.15, 0.30), (x1 + 0.006, 0.86, s * 0.70), mat=r.CREMA, bisel=0.01)
    piezas.caja(bm, (0.03, 0.24, 0.86), (x1 + 0.006, 0.80, 0), mat=r.NEGRO, bisel=0.008)
    piezas.caja(bm, (0.12, 0.16, 2.02), (x1 + 0.04, 0.42, 0), mat=r.ACERO, bisel=0.02)
    # Espejos.
    for s in (-1, 1):
        plaza.caño(bm, (1.80, 1.80, s * (zh - 0.02)), (1.86, 1.80, s * (zh + 0.17)), 0.012, 8, mat=r.NEGRO)
        piezas.caja(bm, (0.04, 0.26, 0.14), (1.86, 1.72, s * (zh + 0.22)), mat=r.NEGRO, bisel=0.01)
    # Atrás de la caja: paragolpes. Arriba: el extractor de la cocina.
    piezas.caja(bm, (0.10, 0.14, 2.0), (P["x0"] - 0.04, 0.40, 0), mat=r.ACERO, bisel=0.02)
    piezas.caja(bm, (0.60, 0.11, 0.60), (-1.30, P["alto"] + 0.045, -0.55), mat=r.ACERO, bisel=0.02)
    return [((x1 - x0, yt - y0, 2 * zh), ((x0 + x1) / 2, (y0 + yt) / 2, 0)),
            ((0.6, 0.1, 0.6), (-1.30, P["alto"] + 0.05, -0.55))]


P = {
    "id": ID, "presupuesto": 5000,
    "materiales": ("M_PinturaCarrito", "M_Acero", "M_Goma", "M_PlasticoNegro", "M_Hierro", "M_BlancoCrema"),
    "ancho": 4.50, "prof": 2.20, "alto_total": 2.72,
    "x0": -2.25, "x1": 1.05, "zh": 1.10, "alto": 2.62, "r_techo": 0.10, "seg_techo": 2,
    "y_base": 0.30, "y_piso": 0.50, "y_puerta": 2.25, "y_escalon": 0.25,
    "ventana": (-1.75, 0.55, 1.41, 2.25), "repisa": 0.25, "puerta": (0.10, 0.85),
    "z_mueble": 0.47, "bahias_x": [(-1.12, 0.99)], "mesada_atras": (-2.198, -0.20), "fondo_atras": 0.55,
    "ejes": [
        {"x": -1.60, "r": R_RUEDA, "ancho": 0.24, "z": 0.95, "caja": True, "arco": 0.46, "y_arco": 0.82},
        {"x": EJE_ADELANTE, "r": R_RUEDA, "ancho": 0.24, "z": 0.95, "caja": False},
    ],
    "z_pasarrueda": 0.79,
    "toldo_abierto": -110.0,
    "anclajes": [
        ("mostrador_izq", (-1.35, 1.45, 0.75), 0.0),
        ("mostrador_centro", (-0.60, 1.45, 0.75), 0.0),
        ("mostrador_der", (0.15, 1.45, 0.75), 0.0),
        ("atras_izq", (-1.75, 1.45, -0.775), 0.0),
        ("atras_der", (-0.75, 1.45, -0.775), 0.0),
        ("frente", (-0.60, 0.70, 1.11), 0.0),
        ("cartel", (-0.60, 2.62, 0.75), 0.0),
        ("luz_1", (-1.20, 2.57, 0.30), 0.0),
        ("luz_2", (0.0, 2.57, 0.30), 0.0),
    ],
    "entrega": (-0.10, 1.45, 1.22), "fila": (-0.60, 0.0, 1.75), "entrada": (0.475, 0.0, -1.75),
    "extra": cabina,
}

CX = 0.0
VISTAS = [
    ("Frente (lo que ve el cliente) · día", "cerrado", "dia", ((CX, 1.4, 30), (CX, 1.4, 0), 50, 6.2), False),
    ("Lado del vendedor: puerta y escalón · día", "cerrado", "dia", ((CX, 1.4, -30), (CX, 1.4, 0), 50, 6.2), False),
    ("3/4 lado del cliente · día", "cerrado", "dia", ((5.6, 3.4, 7.0), (0.0, 1.2, 0.2), 35, None), False),
    ("3/4 lado del vendedor, puerta abierta · día", "abierto", "dia", ((-5.4, 3.0, -6.6), (0.0, 1.2, 0), 35, None),
     False),
    ("3/4 · atardecer", "cerrado", "atardecer", ((-5.2, 3.4, 7.0), (0.0, 1.2, 0.2), 35, None), False),
    ("Cliente y vendedor de 1,75 m en la ventana · día", "personas", "dia",
     ((2.6, 1.9, 5.2), (-0.7, 1.5, 0.6), 35, None), False),
    ("Adentro, a la altura de los ojos (piso + 1,65) · día", "abierto", "dia",
     ((0.75, 2.15, -0.75), (-1.2, 1.55, 0.9), 16, None), True),
    ("Adentro: mesada de atrás y puerta · día", "abierto", "dia",
     ((-0.1, 2.15, 0.35), (1.3, 1.2, -1.4), 16, None), True),
    ("Adentro: alacenas en las 3 bahías · día", "alacenas", "dia",
     ((0.7, 2.05, -0.55), (-0.55, 0.85, 0.75), 18, None), True),
]

if __name__ == "__main__":
    r.main(P, "food_truck · 4,50 × 2,72 × 2,20 m · base con interior caminable (propuesta, sin .ron)", VISTAS)
