"""Modelo: parrilla a carbón de mostrador (id `parrilla_carbon`, etapa 4; todavía sin dato
en accesorios.ron).

Genera:
    arte/fuentes/cocina/parrilla_carbon.blend
    godot/modelos/cocina/parrilla_carbon.glb
    docs/arte/revisiones/parrilla_carbon.jpg

Uso:
    blender -b -P tools/blender/modelos/parrilla_carbon.py
    python tools/blender/modelos/parrilla_carbon.py

Forma: batea de chapa (M_MetalOscuro) de esquinas redondeadas, con reborde, sobre 4 patas
de hierro; arriba, la parrilla de hierro (M_Hierro): un marco con 18 varillas de punta a
punta (hacia el vendedor), apoyado en el reborde con 4 patitas. Del lado del cliente (+Z),
un respaldo de chapa que lo cuida de las chispas y el calor (como el respaldo de la
plancha). Manijas laterales negras, como las del hervidor. El carbón no está acá: es el
modelo aparte `carbon_brasa`, que el código pone en `punto_carbon`.

Medidas (lista: ≈ 0,70 × 0,35 × 0,45): 0,70 (de manija a manija) × 0,35 (arriba del
respaldo) × 0,45 (reborde).
- Batea: adentro 0,60 × 0,16 × 0,406, piso a 0,09 del apoyo (entra el montón de brasas de
  0,50 × 0,08 × 0,35, que queda 13 cm debajo de las varillas).
- Superficie de trabajo (la parrilla): marco de 0,60 × 0,40 por dentro, con las varillas
  arriba a 0,30 del apoyo, centrada en el origen. Ahí va `punto_superficie`.

Objetos (hijos del Empty `parrilla_carbon`, origen = centro de la base, a nivel del mostrador):
- `parrilla_carbon_cuerpo`: todo lo que se ve (MetalOscuro, Hierro, PlasticoNegro).
- `punto_superficie`: centro de la parrilla, arriba de las varillas (0; 0,30; 0).
- `punto_carbon`: centro del piso de la batea (0; 0,09; 0): origen de `carbon_brasa`.
- `parrilla_carbon-colonly`: una caja hasta arriba de la parrilla (lo que se pone encima se
  apoya en las varillas; adentro de la batea no entra nada por física: el carbón lo pone el
  código) y el respaldo. Las manijas no chocan.

Sin pieza_piloto ni perillas: el fuego es el carbón (`pieza_brasa` de `carbon_brasa`).
El chequeo de origen de comun.revisar() sirve tal cual (el respaldo queda adentro del
reborde, así que la caja total está centrada); además se mide la batea centrada.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402,F401  (antes que bmesh)
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

import comun  # noqa: E402
import piezas  # noqa: E402
import _equipos as eq  # noqa: E402

ID = "parrilla_carbon"
FAMILIA = "cocina"
PRESUPUESTO = 1500  # equipos de cocina (guía 3.1)
OSCURO, HIERRO, NEGRO = range(3)

MX, MZ, RADIO = 0.31, 0.213, 0.02     # medio ancho / media profundidad de la batea (afuera)
PARED = 0.01
REBORDE = 0.012                       # cuánto sale el reborde
Y_BATEA, Y_FONDO, Y_BOCA = 0.08, 0.09, 0.25
SUP = (0.60, 0.40)                    # adentro del marco de la parrilla
Y_SUP = 0.30
MARCO = 0.012                         # barra cuadrada del marco
VARILLAS, R_VARILLA = 18, 0.004
Y_RESPALDO = 0.35
ESP_RESPALDO = 0.008
MANIJA_X = 0.35                       # punta de afuera de las manijas

MEDIDAS = (2 * MANIJA_X, Y_RESPALDO, 2 * (MZ + REBORDE))

# Perfil de la batea (meter, y): sube por afuera, da la vuelta por el reborde y baja por
# adentro hasta el piso. meter < 0 = hacia afuera.
PERFIL = [
    (0.004, Y_BATEA),
    (0.0, Y_BATEA + 0.004),
    (0.0, Y_BOCA - 0.014),
    (-REBORDE, Y_BOCA - 0.01),
    (-REBORDE, Y_BOCA - 0.003),
    (-REBORDE + 0.003, Y_BOCA),
    (PARED - 0.003, Y_BOCA),
    (PARED, Y_BOCA - 0.003),
    (PARED, Y_FONDO),
]


def construir():
    oscuro, hierro, negro = comun.cargar_materiales("M_MetalOscuro", "M_Hierro", "M_PlasticoNegro")
    bm = bmesh.new()
    # Batea, cerrada abajo (se ve entre las patas) y con el piso de adentro.
    eq.e2.torno_rr(bm, PERFIL, MX, MZ, RADIO, segs=3, mats=OSCURO, tapa_ini=True, tapa_fin=True)
    # Patas de hierro.
    for x in (-0.26, 0.26):
        for z in (-0.16, 0.16):
            piezas.caja(bm, (0.025, Y_BATEA + 0.004, 0.025), (x, (Y_BATEA + 0.004) / 2, z), mat=HIERRO,
                        bisel=0.004, sin_abajo=True)
    # Parrilla: marco de barra cuadrada, varillas de punta a punta (en Z) y 4 patitas.
    hx, hz = SUP[0] / 2, SUP[1] / 2
    ym = Y_SUP - MARCO / 2
    for lado in (-1, 1):
        piezas.caja(bm, (SUP[0] + 2 * MARCO, MARCO, MARCO), (0, ym, lado * (hz + MARCO / 2)),
                    mat=HIERRO, bisel=0.003)
        piezas.caja(bm, (MARCO, MARCO, SUP[1]), (lado * (hx + MARCO / 2), ym, 0), mat=HIERRO, bisel=0.003)
    paso = (SUP[0] - 0.04) / (VARILLAS - 1)
    for i in range(VARILLAS):
        x = -hx + 0.02 + i * paso
        piezas.cilindro(bm, R_VARILLA, SUP[1] + 0.006, (x, Y_SUP - R_VARILLA, 0), eje="z", lados=8,
                        mat=HIERRO, tapas=(False, False))
    for sx in (-1, 1):
        for sz in (-1, 1):
            alto = Y_SUP - MARCO - Y_BOCA + 0.002
            piezas.caja(bm, (MARCO, alto, MARCO),
                        (sx * (hx + MARCO / 2), Y_BOCA + alto / 2 - 0.002, sz * (hz + MARCO / 2)),
                        mat=HIERRO, sin_abajo=True)
    # Respaldo del lado del cliente, apoyado en el reborde.
    z_resp = MZ + REBORDE - ESP_RESPALDO / 2 - 0.002
    alto = Y_RESPALDO - Y_BOCA + 0.004
    caras = piezas.caja(bm, (2 * (MX + REBORDE) - 0.004, alto, ESP_RESPALDO),
                        (0, Y_BOCA - 0.004 + alto / 2, z_resp), mat=OSCURO, bisel=0.003)
    eq.borrar_caras(bm, caras, (0, -1, 0))
    # Manijas laterales: dos soportes de hierro y una barra negra, debajo del reborde.
    y_man = 0.19
    for lado in (-1, 1):
        for zs in (-0.06, 0.06):
            c = piezas.caja(bm, (0.026, 0.018, 0.016), (lado * (MX + 0.011), y_man, zs), mat=HIERRO,
                            bisel=0.004)
            eq.borrar_caras(bm, c, (-lado, 0, 0))
        piezas.caja(bm, (0.018, 0.024, 0.15), (lado * (MANIJA_X - 0.009), y_man, 0), mat=NEGRO, bisel=0.006)
    cuerpo = piezas.terminar(f"{ID}_cuerpo", bm, [oscuro, hierro, negro])

    sup = piezas.punto("punto_superficie", (0, Y_SUP, 0))
    carbon = piezas.punto("punto_carbon", (0, Y_FONDO, 0))
    ancho, prof = 2 * (MX + REBORDE), 2 * (MZ + REBORDE)
    col = eq.colision_cajas(ID, [
        ((ancho, Y_SUP, prof), (0, Y_SUP / 2, 0)),
        ((ancho, Y_RESPALDO - Y_SUP, ESP_RESPALDO), (0, (Y_RESPALDO + Y_SUP) / 2, z_resp)),
    ])
    raiz = piezas.raiz(ID, [cuerpo, sup, carbon, col])
    return {"raiz": raiz, "cuerpo": cuerpo, "sup": sup, "carbon": carbon, "col": col}


def chequeo_parrilla(m):
    """Batea centrada y del tamaño pedido; varillas arriba a Y_SUP; marco SUP por dentro."""
    vs = eq.verts_godot(m["cuerpo"])
    adentro = [v for v in vs if Y_FONDO - 1e-5 <= v.y <= Y_BOCA - 0.003 + 1e-5
               and abs(v.x) <= MX - PARED + 1e-5 and abs(v.z) <= MZ - PARED + 1e-5]
    bx = max(v.x for v in adentro) - min(v.x for v in adentro)
    bz = max(v.z for v in adentro) - min(v.z for v in adentro)
    cx = max(v.x for v in adentro) + min(v.x for v in adentro)
    cz = max(v.z for v in adentro) + min(v.z for v in adentro)
    grilla = [v for v in eq.caras_material(m["cuerpo"], HIERRO) if v.y > Y_SUP - MARCO - 1e-5]
    arriba = max(v.y for v in grilla)
    gx = max(v.x for v in grilla) - min(v.x for v in grilla) - 2 * MARCO
    gz = max(v.z for v in grilla) - min(v.z for v in grilla) - 2 * MARCO
    p = m["sup"].location
    ok = (abs(bx - 2 * (MX - PARED)) < 1e-4 and abs(bz - 2 * (MZ - PARED)) < 1e-4 and abs(cx) < 1e-4
          and abs(cz) < 1e-4 and abs(arriba - Y_SUP) < 1e-4 and abs(gx - SUP[0]) < 1e-4
          and abs(gz - SUP[1]) < 1e-4 and (Vector((p.x, -p.y, p.z)) - Vector((0, 0, Y_SUP))).length < 1e-4)
    return ok, ("Batea por dentro %.3f × %.3f (piso a %.2f); parrilla %.2f × %.2f por dentro del marco, "
                "varillas arriba a %.3f; punto_superficie en su centro" % (bx, bz, Y_FONDO, gx, gz, arriba))


def revisar(m):
    res = comun.revisar([m["cuerpo"]], PRESUPUESTO, MEDIDAS, origen="base", max_materiales=6)
    res.insert(1, chequeo_parrilla(m))
    return res


def hoja(m, revision):
    import carbon_brasa
    c = carbon_brasa.construir()
    c["raiz"].location = m["carbon"].location.copy()
    c["raiz"].parent = m["raiz"]
    vis = [m["cuerpo"], c["trozos"], c["brasa"]]
    eq.hoja_equipo(ID, "parrilla_carbon · parrilla 0,60 × 0,40 m a 0,30 m (con carbon_brasa) · equipo de cocina",
                   m["raiz"], vis, revision,
                   etiqueta_vendedor="Lado del vendedor (con carbon_brasa en punto_carbon) · día",
                   etiqueta_arriba="Arriba: 18 varillas y brasas · día")


def main():
    eq.main_modelo(ID, FAMILIA, construir, revisar, hoja,
                   lambda m: [m["raiz"], m["cuerpo"], m["sup"], m["carbon"], m["col"]])


if __name__ == "__main__":
    main()
