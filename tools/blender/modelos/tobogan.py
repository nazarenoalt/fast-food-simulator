"""Modelo: tobogán de plaza (id `tobogan`, lista-de-modelos, etapa 3 · Plaza).

Genera:
    arte/fuentes/plaza/tobogan.blend
    godot/modelos/plaza/tobogan.glb
    docs/arte/revisiones/tobogan.jpg

Uso:
    python tools/blender/modelos/tobogan.py [--sin-hoja]

Forma: el tobogán clásico de plaza. Atrás (−Z) la escalera de caño azul (M_AzulAcento) con
peldaños de hierro (M_Hierro), apenas inclinada, que sigue como pasamanos hasta 2,0 m; una
plataforma de hierro a 1,5 m con dos postes adelante y pasamanos a los costados; y la
rampa amarilla (M_Amarillo) en U, que baja a unos 33° y termina en un tramo casi plano a
0,3 m del piso, con un par de patas al final. La salida de la rampa es el frente (+Z): el
que baja sale mirando a la plaza. Juego de chicos: colores vivos (guía 4.2, regla 2).

Medidas (lista ≈ 0,8 × 2,0 × 3,5): 0,80 de ancho (la escalera y la plataforma; la rampa mide
0,60) × 2,00 de alto (pasamanos) × 3,50 de largo (del pie de la escalera a la salida).
La rampa es una U de chapa de 3 cm con bordes de 17 cm, cortada en secciones verticales; los
quiebres de menos de 30° se ven curvos (sombreado duro, guía 3.4).
Lados (guía 3.2): caños de 2,5 cm de radio, 12; peldaños de 1,6 cm, 8.
Origen: centro de la base, a nivel del piso.

Objetos (hijos del Empty `tobogan`):
    - tobogan_cuerpo: toda la malla visible.
    - tobogan-colonly: cajas de la escalera y la plataforma, de la rampa inclinada y del
      tramo final.
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
from piezas import g2b  # noqa: E402

ID = "tobogan"
PRESUPUESTO = 1500  # lista de modelos (estructuras grandes de la plaza)
MEDIDAS = (0.8, 2.0, 3.5)
AZUL, HIERRO, AMARILLO = 0, 1, 2

R = 0.025                       # caños
X_CAÑO = 0.4 - R                # escalera, postes y pasamanos
ALTO = 2.0
PLATAFORMA = 1.5                # arriba de la plataforma
Z_PIE = -1.75 + R               # pie de la escalera
Z_TOPE = -1.17                  # la escalera a 2,0 m
Z_FRENTE = -0.82                # borde de adelante de la plataforma (postes)
# Recorrido de la rampa: (z, y) de la cara de arriba del fondo.
RAMPA = [(Z_FRENTE, PLATAFORMA), (-0.62, 1.46), (0.95, 0.42), (1.15, 0.345), (1.4, 0.31), (1.75, 0.30)]
U_ANCHO, U_BORDE, U_CHAPA = 0.30, 0.17, 0.03


def z_escalera(y):
    return Z_PIE + (Z_TOPE - Z_PIE) * y / ALTO


def rampa(bm):
    """U de chapa barrida por RAMPA con secciones verticales (z constante)."""
    a, b, e = U_ANCHO, U_ANCHO - U_CHAPA, U_CHAPA
    perfil = [(-a, -e), (-b, -e), (b, -e), (a, -e), (a, U_BORDE), (b, U_BORDE), (b, 0.0),
              (-b, 0.0), (-b, U_BORDE), (-a, U_BORDE)]
    previas = set(bm.faces)
    anillos = [[bm.verts.new(g2b((x, y + dy, z))) for x, dy in perfil] for z, y in RAMPA]
    n = len(perfil)
    for p, q in zip(anillos, anillos[1:]):
        for k in range(n):
            bm.faces.new((p[k], p[(k + 1) % n], q[(k + 1) % n], q[k]))
    for an in (anillos[0], anillos[-1]):
        for idx in ((0, 1, 7, 8, 9), (1, 2, 6, 7), (2, 3, 4, 5, 6)):
            bm.faces.new([an[i] for i in idx])
    nuevas = [f for f in bm.faces if f not in previas]
    for f in nuevas:
        f.material_index = AMARILLO
    bmesh.ops.recalc_face_normals(bm, faces=nuevas)


def construir():
    mats = comun.cargar_materiales("M_AzulAcento", "M_Hierro", "M_Amarillo")
    bm = bmesh.new()
    for sx in (-1, 1):
        x = sx * X_CAÑO
        # Largueros de la escalera (siguen como pasamanos) y postes de adelante.
        plaza.poste(bm, (x, 0, Z_PIE), (x, ALTO, Z_TOPE), R, 12, mat=AZUL)
        plaza.poste(bm, (x, 0, Z_FRENTE), (x, ALTO, Z_FRENTE), R, 12, mat=AZUL)
        # Pasamanos de la plataforma.
        y = ALTO - 0.06
        plaza.caño(bm, (x, y, z_escalera(y)), (x, y, Z_FRENTE), R, 12, mat=AZUL)
        # Patas del final de la rampa.
        y_pata = RAMPA[-1][1] - U_CHAPA
        plaza.poste(bm, (sx * 0.24, 0, 1.55), (sx * 0.24, y_pata, 1.55), R, 12, mat=AZUL)
    # Travesaño bajo la salida.
    plaza.caño(bm, (-0.24, 0.12, 1.55), (0.24, 0.12, 1.55), 0.018, 8, mat=AZUL)
    # Peldaños (la plataforma es el último).
    for y in (0.3, 0.6, 0.9, 1.2):
        z = z_escalera(y)
        plaza.caño(bm, (-X_CAÑO, y, z), (X_CAÑO, y, z), 0.016, 8, mat=HIERRO)
    # Plataforma: de la escalera a los postes.
    z0, z1 = z_escalera(PLATAFORMA) + R, Z_FRENTE
    piezas.caja(bm, (2 * X_CAÑO, 0.04, z1 - z0), (0, PLATAFORMA - 0.02, (z0 + z1) / 2), mat=HIERRO,
                bisel=0.01)
    rampa(bm)
    plaza.borrar_apoyadas(bm)
    cuerpo = piezas.terminar(f"{ID}_cuerpo", bm, mats)

    # Colisión.
    (za, ya), (zb, yb) = RAMPA[1], RAMPA[2]
    largo = math.hypot(zb - za, ya - yb)
    ang = math.degrees(math.atan2(zb - za, ya - yb))   # giro sobre X: Y hacia +Z
    cajas = [
        ((0.8, ALTO, Z_FRENTE + R + 1.75), (0, ALTO / 2, (-1.75 + Z_FRENTE + R) / 2), (0, 0, 0)),
        ((0.6, 0.12, largo), (0, (ya + yb) / 2 + 0.04, (za + zb) / 2), (90 - ang, 0, 0)),
        ((0.6, 0.47, 1.75 - zb), (0, 0.235, (1.75 + zb) / 2), (0, 0, 0)),
    ]
    col = plaza.colision_cajas(ID, cajas)
    raiz = piezas.raiz(ID, [cuerpo, col])
    return {"raiz": raiz, "cuerpo": cuerpo, "colisiones": [col]}


def revisar(mod):
    res = comun.revisar(mod["cuerpo"], PRESUPUESTO, MEDIDAS, origen="base")
    (za, ya), (zb, yb) = RAMPA[1], RAMPA[2]
    ang = math.degrees(math.atan2(ya - yb, zb - za))
    res.append((25 <= ang <= 40 and RAMPA[-1][1] <= 0.35,
                "Rampa a %.0f° (25 a 40), salida a %.2f m del piso; plataforma a %.2f m" % (
                    ang, RAMPA[-1][1], PLATAFORMA)))
    return res


def main():
    comun.escena_vacia()
    mod = construir()
    revision = revisar(mod)
    ok = comun.imprimir_revision(ID, revision)
    plaza.guardar_y_exportar(ID, [mod["raiz"], mod["cuerpo"]] + mod["colisiones"])
    if "--sin-hoja" not in sys.argv:
        c = [mod["cuerpo"]]
        plaza.hoja(ID, "tobogan · 0,8 × 2,0 × 3,5 m · plataforma a 1,5 m · juego de plaza", [
            ("Frente (salida de la rampa) · día", c, "frente", "dia", True),
            ("Costado · día", c, "costado", "dia", True),
            ("3/4 · día", c, "tres_cuartos", "dia", False),
            ("3/4 · atardecer", c, "tres_cuartos", "atardecer", False),
            ("Con la persona de 1,75 m · día", c + ["persona"], "tres_cuartos", "dia", False),
            ("3/4 de atrás (escalera) · día", c, "tres_cuartos_atras", "dia", False),
        ], revision, persona_en=(0.9, 0, 0.6))
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
