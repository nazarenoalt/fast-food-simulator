"""Modelo: tráiler de comida (id `trailer`, etapa 5; "remolque" en SPEC-006, fuera de
alcance; todavía sin `.ron`: medidas y anclajes propuestos acá para la spec).

Genera:
    arte/fuentes/carritos/trailer.blend
    godot/modelos/carritos/trailer.glb
    docs/arte/revisiones/trailer.jpg

Uso:
    python tools/blender/modelos/trailer.py [--sin-hoja]

Casilla rodante de un eje, estilo de época: techo con las esquinas bien redondeadas (radio
0,35), ventana de atención del lado del cliente (+Z) con la tapa abierta de toldo, puerta con
escalón del lado del vendedor (−Z). En la punta −X (del mismo lado que la manija de las bases
chicas), la lanza de enganche en A con el acople y la rueda de apoyo; atrás, dos patas de
apoyo con taco de goma (como las patas niveladoras del carro grande). La construcción común
(casilla, mesadas, bahías, puerta, toldo) está en _rodante.py; acá va la lanza y las patas.

Presupuesto: 4.000 triángulos (lista). Materiales (6): M_PinturaCarrito, M_Acero, M_Goma,
M_PlasticoNegro, M_MetalOscuro (lanza, acople y patas), M_BlancoCrema (forro de adentro).

Medidas propuestas para `trailer.ron` (la lista dice ≈ 2,0 × 2,3 × 3,0 con el largo en Z; acá
el largo va en X, porque la ventana tiene que mirar al cliente):
    ancho 3,00, profundidad 2,00, alto 2,55 (la lista dice ≈ 2,3, pero con el piso a 0,50
    adentro quedarían 1,75 m de techo: el vendedor no entra parado; con 2,55 quedan 2,00).
    Piso de adentro a 0,50, escalón a 0,25, mesadas a 1,45 (alto_mostrador = piso + 0,95),
    techo de adentro a 2,50. Ventana de x −1,20 a 0,90 (2,10 m), de 1,41 a 2,10; repisa de
    25 cm. Puerta de x 0,55 a 1,30, hasta 2,15. Eje en x −0,20 (ruedas de radio 0,32 con
    pasarruedas adentro): 2 bahías bajo la mesada, una a cada lado del pasarruedas.
    Con la lanza mide 3,94 de largo (la lanza sale 0,94 en −X).
Anclajes propuestos (pos en Godot, desde el centro de la casilla a nivel de la calle):
    mostrador_izq (−0,85; 1,45; 0,66)   [Cocina, Equipamiento]
    mostrador_centro (−0,15; 1,45; 0,66) [Cocina, Equipamiento, Decoracion]
    mostrador_der (0,55; 1,45; 0,66)    [Cocina, Equipamiento, Decoracion]
    atras_izq (−0,95; 1,45; −0,70)      [Cocina, Equipamiento, Deposito]   mesada de atrás
    atras_der (−0,20; 1,45; −0,70)      [Cocina, Equipamiento, Deposito]
    frente (−0,15; 0,70; 1,01)          [Telon, Decoracion]
    cartel (−0,15; 2,55; 0,0)           [Decoracion]   arriba del techo
    luz_1 (−0,60; 2,50; 0,0), luz_2 (0,60; 2,50; 0,0)  [Luz]  techo de adentro
    entrega (0,45; 1,45; 1,12)   en la repisa de afuera
    fila (−0,15; 0,0; 1,65)      primer lugar, frente a la ventana (sigue hacia +X)
    entrada (0,925; 0,0; −1,65)  al pie del escalón
    bahia_1..2: los punto_bahia_<n> (boca a z 0,37, piso de la bahía a 0,79).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402,F401  (antes que bmesh)
import bmesh  # noqa: E402,F401

import piezas  # noqa: E402
import _plaza as plaza  # noqa: E402
import _rodante as r  # noqa: E402

ID = "trailer"
X_ACOPLE = -2.44


def lanza(bm, P):
    """Lanza en A, acople, rueda de apoyo y patas de atrás. Devuelve sus cajas de colisión."""
    x0 = P["x0"]
    y = 0.40
    for s in (-1, 1):
        plaza.caño(bm, (x0 + 0.05, y, s * 0.62), (X_ACOPLE + 0.16, y, s * 0.03), 0.035, 8, mat=r.EXTRA)
    plaza.caño(bm, (x0 + 0.02, y, -0.68), (x0 + 0.02, y, 0.68), 0.035, 8, mat=r.EXTRA)
    # Acople (cabeza y manija) sobre la punta.
    piezas.caja(bm, (0.24, 0.09, 0.11), (X_ACOPLE + 0.12, y + 0.01, 0), mat=r.EXTRA, bisel=0.015)
    piezas.cilindro(bm, 0.045, 0.06, (X_ACOPLE + 0.05, y + 0.06, 0), lados=12, mat=r.EXTRA, radio_a_caras=True)
    piezas.caja(bm, (0.12, 0.025, 0.03), (X_ACOPLE + 0.17, y + 0.07, 0), mat=r.NEGRO, bisel=0.008)
    # Rueda de apoyo: caño vertical con manivela y ruedita de goma.
    xr = x0 - 0.42
    piezas.cilindro(bm, 0.03, 0.62, (xr, 0.43, 0.20), lados=12, mat=r.EXTRA, radio_a_caras=True)
    piezas.cilindro(bm, 0.008, 0.10, (xr + 0.04, 0.77, 0.20), eje="x", lados=8, mat=r.NEGRO)
    piezas.cilindro(bm, 0.015, 0.05, (xr + 0.09, 0.80, 0.20), lados=8, mat=r.NEGRO)
    piezas.cilindro(bm, 0.06, 0.05, (xr, 0.06, 0.20), eje="z", lados=12, mat=r.GOMA, radio_a_caras=True)
    piezas.caja(bm, (0.03, 0.09, 0.08), (xr, 0.10, 0.20), mat=r.EXTRA)
    # Patas de apoyo de atrás.
    for s in (-1, 1):
        x, z = P["x1"] - 0.18, s * 0.62
        piezas.cilindro(bm, 0.022, P["y_base"] - 0.02, (x, 0.03 + (P["y_base"] - 0.02) / 2, z), lados=12,
                        mat=r.EXTRA)
        piezas.cilindro(bm, 0.05, 0.03, (x, 0.015, z), lados=16, mat=r.GOMA)
    # Paragolpes de atrás (acero) y guardabarros: nada (las ruedas van adentro).
    piezas.caja(bm, (0.08, 0.12, 1.7), (P["x1"] + 0.03, 0.38, 0), mat=r.ACERO, bisel=0.02)
    return [((x0 - X_ACOPLE, 0.2, 1.3), ((x0 + X_ACOPLE) / 2, y, 0))]


P = {
    "id": ID, "presupuesto": 4000,
    "materiales": ("M_PinturaCarrito", "M_Acero", "M_Goma", "M_PlasticoNegro", "M_MetalOscuro", "M_BlancoCrema"),
    "ancho": 3.00, "prof": 2.00, "alto_total": 2.55,
    "x0": -1.50, "x1": 1.50, "zh": 1.00, "alto": 2.55, "r_techo": 0.35, "seg_techo": 4,
    "y_base": 0.30, "y_piso": 0.50, "y_puerta": 2.15, "y_escalon": 0.25,
    "ventana": (-1.20, 0.90, 1.41, 2.10), "repisa": 0.25, "puerta": (0.55, 1.30),
    "z_mueble": 0.37, "bahias_x": [(-1.43, -0.62), (0.22, 1.43)], "mesada_atras": (-1.448, 0.35),
    "fondo_atras": 0.50,
    "ejes": [{"x": -0.20, "r": 0.32, "ancho": 0.20, "z": 0.86, "caja": True, "arco": 0.40, "y_arco": 0.70}],
    "z_pasarrueda": 0.72,
    "toldo_abierto": -110.0,
    "anclajes": [
        ("mostrador_izq", (-0.85, 1.45, 0.66), 0.0),
        ("mostrador_centro", (-0.15, 1.45, 0.66), 0.0),
        ("mostrador_der", (0.55, 1.45, 0.66), 0.0),
        ("atras_izq", (-0.95, 1.45, -0.70), 0.0),
        ("atras_der", (-0.20, 1.45, -0.70), 0.0),
        ("frente", (-0.15, 0.70, 1.01), 0.0),
        ("cartel", (-0.15, 2.55, 0.0), 0.0),
        ("luz_1", (-0.60, 2.50, 0.0), 0.0),
        ("luz_2", (0.60, 2.50, 0.0), 0.0),
    ],
    "entrega": (0.45, 1.45, 1.12), "fila": (-0.15, 0.0, 1.65), "entrada": (0.925, 0.0, -1.65),
    "extra": lanza,
}

VISTAS = [
    ("Frente (lo que ve el cliente) · día", "cerrado", "dia", ((-0.4, 1.3, 30), (-0.4, 1.3, 0), 50, 4.9), False),
    ("Lado del vendedor: puerta y escalón · día", "cerrado", "dia", ((-0.4, 1.3, -30), (-0.4, 1.3, 0), 50, 4.9),
     False),
    ("3/4 lado del cliente · día", "cerrado", "dia", ((4.4, 3.0, 5.6), (-0.3, 1.1, 0.2), 35, None), False),
    ("3/4 lado del vendedor, puerta abierta · día", "abierto", "dia", ((-4.6, 2.7, -5.2), (-0.3, 1.1, 0), 35, None),
     False),
    ("3/4 · atardecer", "cerrado", "atardecer", ((-4.6, 3.0, 5.6), (-0.3, 1.1, 0.2), 35, None), False),
    ("Cliente y vendedor de 1,75 m en la ventana · día", "personas", "dia",
     ((2.4, 1.9, 4.6), (-0.4, 1.5, 0.5), 35, None), False),
    ("Adentro, a la altura de los ojos (piso + 1,65) · día", "abierto", "dia",
     ((1.15, 2.15, -0.55), (-0.9, 1.5, 0.8), 16, None), True),
    ("Adentro: mesada de atrás y puerta · día", "abierto", "dia",
     ((-1.1, 2.15, 0.2), (1.0, 1.2, -1.3), 16, None), True),
    ("Adentro: alacenas en las 2 bahías · día", "alacenas", "dia",
     ((1.15, 2.05, -0.55), (-0.3, 0.85, 0.6), 18, None), True),
]

if __name__ == "__main__":
    r.main(P, "trailer · 3,00 × 2,55 × 2,00 m (3,94 con la lanza) · base con interior caminable "
              "(propuesta, sin .ron)", VISTAS)
