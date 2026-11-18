"""Modelo: colectivo (id `colectivo`, familia `ciudad`, etapa 6). Diseño genérico: sin marca,
sin número ni recorrido de ninguna línea real.

Genera:
    arte/fuentes/ciudad/colectivo.blend
    godot/modelos/ciudad/colectivo.glb
    docs/arte/revisiones/colectivo.jpg

Uso:
    python tools/blender/modelos/colectivo.py [--sin-hoja]

Hoy el juego no tiene colectivos: es ambientación para la calle (pasa por la calle, como los
autos de transito.rs). Mismo criterio que los autos (`_auto.py`):

Forma (ejes de Godot, frente = +Z; como el auto, si el código lo arma mirando a +X hay que
girarlo +90° en Y): colectivo urbano porteño de piso bajo, una caja larga de esquinas
redondeadas.
    - Carrocería: el perfil del costado (z, y) estirado de lado a lado: piso a 0,32 con los
      dos pasarruedas en arco, frente casi vertical con el parabrisas apenas tirado hacia
      atrás, techo a 2,88 con las esquinas de adelante y de atrás redondeadas. Las aristas del
      contorno (salvo abajo) llevan un bisel de 10 cm en 2 segmentos: esquinas de colectivo.
    - Arriba, el equipo de aire acondicionado; a los costados, una franja a la altura de la
      cintura (sobre los pasarruedas).
    - Vidrios: parabrisas, cartel de recorrido (en blanco, oscuro), ventanillas corridas con
      parantes pintados, luneta y las puertas de vidrio (dos hojas). Las puertas van del lado
      de la vereda: a la derecha del sentido de marcha, que mirando a +Z es −X (adelante, junto
      al chofer, y en el medio, entre los ejes).
    - Espejos "orejas" de colectivo: brazos que salen de las esquinas de arriba del frente y
      bajan hasta el espejo, a los costados del parabrisas.
    - Paragolpes, parrilla del motor (atrás) y espejos en goma.

Vidrios: gris casi negro OPACO (M_Hierro), como los autos: de lejos se lee mejor, no deja ver
un colectivo vacío por dentro y no tiene problemas de orden de dibujo.

Objetos (hijos del Empty `colectivo`; origen = centro de la base, a nivel del piso):
    pieza_carroceria      toda la chapa, con dos superficies: 0 = color principal y 1 = franja de
                          la cintura y equipo del techo. El .glb trae M_PinturaCarrito en las
                          dos (un color); el juego pone el color de la "línea" en cada una
                          (en la hoja: rojo con franja y techo amarillos, y azul con crema).
    colectivo_detalles    vidrios (M_Hierro) y paragolpes, parrilla y espejos (M_Goma).
    pieza_rueda_1..4      1 delantera +X, 2 delantera −X, 3 trasera +X, 4 trasera −X (cubierta
                          M_Goma, llanta M_Acero; las de atrás son duales, más anchas), con el
                          origen en el eje (giran en X). Radio 0,50 a las caras (24 lados).
    pieza_faros           faros (M_LuzFarol, el juego los prende de noche).
    pieza_luces_traseras  M_PilotoApagado (el juego las enciende de noche).
Sin `-colonly`: se mueve, y el código le arma su caja (como a los autos).

Medidas: 2,86 × 3,00 × 12,0 con los espejos (la chapa mide 2,50 de ancho). Lista ≈ 2,5 × 3,0
× 12. Ejes en z = 3,55 y −2,45 (entre ejes 6,0 m).
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402  (antes que bmesh)
import bmesh  # noqa: E402

import _ciudad as ciudad  # noqa: E402
import _plaza as plaza  # noqa: E402
import comun  # noqa: E402
import piezas  # noqa: E402
from piezas import g2b  # noqa: E402

ID = "colectivo"
PRESUPUESTO = 3000
MATERIALES = ("M_PinturaCarrito", "M_Hierro", "M_Goma", "M_Acero", "M_LuzFarol", "M_PilotoApagado")
MEDIDAS = (2.86, 3.00, 12.0)

W = 2.50                     # ancho de la chapa
XS = W / 2
ZF, ZR = 5.96, -5.96         # frente y cola de la chapa (los paragolpes llegan a ±6,0)
Y0, YT = 0.32, 2.88          # piso de la carrocería y techo
R_RUEDA, R_ARCO, Y_EJE = 0.50, 0.58, 0.50
EJES = (3.55, -2.45)
BISEL = 0.10
VENT = (1.30, 2.40)          # ventanillas (y)
FRANJA = (1.12, 1.24)
PUERTAS = ((4.70, 5.62), (0.30, 1.40))    # del lado −X (vereda)
VENT_Z = (-5.55, 5.60)
PARANTES = [VENT_Z[0] + k * (VENT_Z[1] - VENT_Z[0]) / 9 for k in range(1, 9)]
CHAPA, FRANJA_M = 0, 1       # superficies de pieza_carroceria
VIDRIO, GOMA = 0, 1          # de colectivo_detalles


def perfil():
    """Contorno del costado [(z, y, redondear)]: redondear = el tramo hasta el punto
    siguiente lleva bisel en las aristas del costado."""
    pts = [(ZF, Y0, False)]
    for zc in EJES:
        dz = math.sqrt(R_ARCO ** 2 - (Y_EJE - Y0) ** 2)
        a0 = math.atan2(Y0 - Y_EJE, dz)
        n = 8
        for i in range(n + 1):
            a = a0 + (math.pi - 2 * a0) * i / n
            pts.append((zc + R_ARCO * math.cos(a), Y_EJE + R_ARCO * math.sin(a), False))
    pts += [
        (ZR, Y0, True), (ZR, 2.78, True), (ZR + 0.04, 2.85, True), (ZR + 0.11, YT, True),
        (5.74, YT, True), (5.82, 2.86, True), (5.86, 2.80, True), (5.90, 2.55, True),
        (ZF, 0.95, True),
    ]
    return pts


def carroceria(bm):
    pts = perfil()
    n = len(pts)
    lados = [[bm.verts.new(g2b((sx * XS, y, z))) for z, y, _ in pts] for sx in (-1, 1)]
    for k in range(n):
        k2 = (k + 1) % n
        bm.faces.new((lados[0][k], lados[0][k2], lados[1][k2], lados[1][k]))
    tapas = [bm.faces.new(lados[0]), bm.faces.new(list(reversed(lados[1])))]
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    aristas = []
    for lado in lados:
        for k, (_, _, r) in enumerate(pts):
            if r:
                e = bm.edges.get((lado[k], lado[(k + 1) % n]))
                aristas.append(e)
    bmesh.ops.bevel(bm, geom=aristas, offset=BISEL, segments=2, affect="EDGES", profile=0.5,
                    clamp_overlap=True)
    for f in bm.faces:
        f.material_index = CHAPA
    del tapas


def tramos_ventanilla(sx):
    """Tramos en z de las ventanillas de un costado (del lado −X, cortadas por las puertas)."""
    if sx > 0:
        return [VENT_Z]
    (p1a, _), (p2a, p2b) = PUERTAS
    return [(VENT_Z[0], p2a - 0.08), (p2b + 0.08, p1a - 0.08)]


def en_puerta(sx, z, margen=0.0):
    return sx < 0 and any(a - margen <= z <= b + margen for a, b in PUERTAS)


def construir():
    mats = comun.cargar_materiales(*MATERIALES)
    pintura, hierro, goma, acero, faro, piloto = mats
    bc = bmesh.new()
    carroceria(bc)
    bd = bmesh.new()
    for sx in (-1, 1):
        x = sx * (XS + 0.005)
        # Ventanillas y parantes.
        for za, zb in tramos_ventanilla(sx):
            piezas.caja(bd, (0.02, VENT[1] - VENT[0], zb - za), (x, sum(VENT) / 2, (za + zb) / 2), mat=VIDRIO)
        for z in PARANTES:
            if en_puerta(sx, z, 0.12):
                continue
            piezas.caja(bc, (0.03, VENT[1] - VENT[0] + 0.04, 0.10), (sx * (XS + 0.01), sum(VENT) / 2, z),
                        mat=CHAPA, bisel=0.008)
        # Franja de la cintura (superficie 1), cortada por las puertas.
        cortes = [(-5.86, 5.84)] if sx > 0 else [(-5.86, PUERTAS[1][0] - 0.04),
                                                  (PUERTAS[1][1] + 0.04, PUERTAS[0][0] - 0.04)]
        for za, zb in cortes:
            piezas.caja(bc, (0.02, FRANJA[1] - FRANJA[0], zb - za), (x, sum(FRANJA) / 2, (za + zb) / 2),
                        mat=FRANJA_M)
    # Puertas de vidrio (dos hojas) con su marco de goma.
    for za, zb in PUERTAS:
        hoja = (zb - za - 0.03) / 2
        for k in range(2):
            zc = za + hoja / 2 + k * (hoja + 0.03)
            piezas.caja(bd, (0.02, 2.02, hoja), (-(XS + 0.005), 0.40 + 1.01, zc), mat=VIDRIO)
        piezas.caja(bd, (0.016, 2.06, 0.03), (-(XS + 0.004), 1.41, (za + zb) / 2), mat=GOMA)
    # Parabrisas y cartel de recorrido (en blanco), siguiendo el frente.
    ang = math.degrees(math.atan2(ZF - 5.90, 2.55 - 0.95))
    piezas.caja(bd, (2.14, 1.52, 0.02), (0, 1.75, (ZF + 5.90) / 2 + 0.006), mat=VIDRIO, rot=(-ang, 0, 0))
    ang2 = math.degrees(math.atan2(5.90 - 5.86, 2.80 - 2.55))
    piezas.caja(bd, (1.80, 0.20, 0.02), (0, 2.675, 5.88 + 0.006), mat=VIDRIO, rot=(-ang2, 0, 0))
    # Luneta.
    piezas.caja(bd, (2.0, 0.85, 0.02), (0, 2.0, ZR - 0.005), mat=VIDRIO)
    # Paragolpes, parrilla del motor y espejos (goma).
    for z in (ZF, ZR):
        piezas.caja(bd, (W - 0.06, 0.28, 0.08), (0, 0.46, z), mat=GOMA, bisel=0.02)
    piezas.caja(bd, (1.5, 0.30, 0.03), (0, 0.86, ZR - 0.008), mat=GOMA, bisel=0.008)
    piezas.caja(bd, (0.9, 0.10, 0.03), (0, 0.66, ZF + 0.008), mat=GOMA, bisel=0.008)
    for sx in (-1, 1):
        a = (sx * 1.10, 2.72, 5.78)
        b = (sx * 1.40, 2.66, 5.88)
        c = (sx * 1.40, 2.30, 5.90)
        plaza.caño(bd, a, b, 0.022, 8, mat=GOMA)
        plaza.caño(bd, b, c, 0.022, 8, mat=GOMA)
        piezas.caja(bd, (0.06, 0.38, 0.18), (sx * 1.40, 2.12, 5.90), mat=GOMA, bisel=0.015)
    # Equipo de aire acondicionado (superficie 1).
    piezas.caja(bc, (1.50, 0.13, 2.40), (0, YT + 0.055, -0.6), mat=FRANJA_M, bisel=0.03)
    # Faros y luces traseras.
    bf, bt = bmesh.new(), bmesh.new()
    for sx in (-1, 1):
        piezas.caja(bf, (0.46, 0.14, 0.04), (sx * 0.82, 0.82, ZF), bisel=0.012)
        piezas.caja(bt, (0.18, 0.50, 0.04), (sx * 1.02, 0.95, ZR), bisel=0.012)
    objs = {
        "carroceria": ciudad.terminar("pieza_carroceria", bc, [pintura, pintura]),
        "detalles": ciudad.terminar(f"{ID}_detalles", bd, [hierro, goma]),
        "faros": ciudad.terminar("pieza_faros", bf, [faro]),
        "traseras": ciudad.terminar("pieza_luces_traseras", bt, [piloto]),
    }
    ruedas = []
    xs = {True: (XS - 0.03 - 0.15, 0.30), False: (XS - 0.03 - 0.23, 0.46)}   # (x del centro, ancho)
    i = 0
    for delantera, z in ((True, EJES[0]), (False, EJES[1])):
        xc, ancho = xs[delantera]
        for sx in (1, -1):
            i += 1
            x = sx * xc
            bm = bmesh.new()
            piezas.cilindro(bm, R_RUEDA, ancho, (x, R_RUEDA, z), eje="x", lados=24, mat=0, radio_a_caras=True)
            piezas.cilindro(bm, 0.30, 0.03, (x + sx * ancho / 2, R_RUEDA, z), eje="x", lados=16, mat=1,
                            radio_a_caras=True)
            ruedas.append(ciudad.terminar_en(f"pieza_rueda_{i}", bm, [goma, acero], origen=(x, R_RUEDA, z)))
    objs["ruedas"] = ruedas
    visibles = [objs["carroceria"], objs["detalles"], objs["faros"], objs["traseras"]] + ruedas
    objs["visibles"] = visibles
    objs["raiz"] = piezas.raiz(ID, visibles)
    return objs


def chequeo_carroceria(car):
    usados = {p.material_index for p in car.data.polygons}
    mn, mx = ciudad.limites([car])
    ok = usados == {0, 1} and abs(mx.x - mn.x - (W + 0.05)) < 0.01 and abs(mx.y - 3.0) < 1e-3
    return ok, "pieza_carroceria: 2 superficies (0 chapa, 1 franja y techo), chapa de %.2f de ancho; " \
        "techo con el aire a %.2f" % (W, mx.y)


def revisar(objs):
    v = objs["visibles"]
    res = comun.revisar(v, PRESUPUESTO, MEDIDAS, origen="base")
    ok, texto = ciudad.chequeo_materiales(v, 6, por_que=": vehículo armado, como una base de carrito")
    res = ciudad.reemplazar(res, "Materiales: ", ok, texto)
    bien = []
    for r in objs["ruedas"]:
        mn, mx = ciudad.limites([r])
        bien.append(abs(mn.y) < 1e-4 and abs(r.location.z - R_RUEDA) < 1e-6 and
                    abs((mn.z + mx.z) / 2 + r.location.y) < 1e-4)
    res.append((all(bien), "Ruedas: radio %.2f a las caras (24 lados), origen en el eje, apoyan en el piso; "
                "ejes en z %.2f y %.2f" % (R_RUEDA, *EJES)))
    res.insert(1, chequeo_carroceria(objs["carroceria"]))
    return res


def main():
    comun.escena_vacia()
    objs = construir()
    revision = revisar(objs)
    ok = comun.imprimir_revision(ID, revision)
    ciudad.guardar_y_exportar(ID, [objs["raiz"]] + objs["visibles"])
    if "--sin-hoja" not in sys.argv:
        v = objs["visibles"]
        car = objs["carroceria"]
        rojo, amarillo, azul, crema = comun.cargar_materiales(
            "M_RojoAcento", "M_Amarillo", "M_AzulAcento", "M_BlancoCrema")

        def colores(a, b):
            def f():
                car.data.materials[0] = a
                car.data.materials[1] = b
            return f
        ciudad.hoja(ID, ciudad.m("colectivo · 2.86 × 3.0 × 12.0 m · urbano genérico (sin marca ni línea)"), [
            ("Frente · día", v, "frente", "dia", True),
            ("Costado +X (chofer) · día", v, "costado", "dia", True),
            ("3/4 · día (el .glb: un color)", v, "tres_cuartos", "dia", False),
            ("Lado de la vereda (−X): puertas · rojo y amarillo · día", v, "tres_cuartos_atras", "dia", False),
            ("Azul y crema · 3/4 · atardecer", v, "tres_cuartos", "atardecer", False),
            ("Con la persona de 1,75 m (lado vereda) · día", v + ["persona"], "tres_cuartos_atras", "dia", False),
        ], revision, persona_en=(-1.9, 0, 5.2), antes={3: colores(rojo, amarillo), 4: colores(azul, crema)})
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
