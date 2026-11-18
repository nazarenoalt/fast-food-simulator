"""Modelo: heladera exhibidora de bebidas (id `heladera_bebidas`, lista-de-modelos, etapa 4 ·
accesorios). ⚠ Propuesta: todavía no está en ninguna spec ni en el juego ("si se agregan
bebidas").

Genera:
    arte/fuentes/accesorios/heladera_bebidas.blend
    godot/modelos/accesorios/heladera_bebidas.glb
    docs/arte/revisiones/heladera_bebidas.jpg

Uso:
    python tools/blender/modelos/heladera_bebidas.py [--sin-hoja]

Forma: la heladera vertical de kiosco, con puerta de vidrio hacia el cliente (+Z): mueble
blanco crema hueco (paredes de 4,5 cm), zócalo con rejilla negra abajo, 3 estantes negros con
cenefa adelante (4 niveles con el piso), un tubo de luz cálida arriba, adentro, y arriba de
todo el cartel: marco negro con el panel `pieza_cartel` **en blanco** (sin marca; tiene la cara
mapeada, UV de 0 a 1, para que el juego le ponga un nombre inventado si quiere).
La puerta: marco negro de 4,5 cm con el vidrio (M_Vidrio, alfa 0,2: gris medio, no lava el
color de las bebidas, como M_PlasticoClaro en el pomo) y tirador vertical del lado +X.

Medidas (lista ≈ 0,6 × 1,8 × 0,6): 0,60 × 1,80 × 0,60 justos (del fondo a la punta del
tirador). Mueble de z = −0,30 a 0,255; puerta de 0,255 a 0,285; tirador hasta 0,30.
- Hueco: 0,51 × 1,38 (de y = 0,14 a 1,52) × 0,515 de fondo.
- Estantes arriba a 0,486; 0,826 y 1,166 (niveles de 0,33 libres: entra una botella de 2,25 l).
- Lugares (3 por nivel, en x = −0,16 / 0 / 0,16 y z = −0,03, el medio del estante), de
  arriba hacia abajo y de −X a +X: punto_lugar_1..3 a 1,166 · 4..6 a 0,826 · 7..9 a 0,486 ·
  10..12 a 0,14 (el piso del hueco).
Origen: centro de la base, a nivel del piso (la caja total queda centrada: el fondo en −0,30 y
el tirador en +0,30).

Objetos (hijos del Empty `heladera_bebidas`):
    heladera_bebidas_cuerpo  mueble, zócalo, rejilla, estantes, marco del cartel.
    pieza_puerta             marco, vidrio y tirador. **Origen en la bisagra**: canto de
                             atrás del lado −X, abajo (−0,30; 0,13; 0,255), eje vertical: abre
                             girando en Y con ángulo negativo (hacia el cliente; abierta ≈ −100°).
    pieza_luz                tubo de luz (M_LuzCalida) arriba, adentro, detrás del marco: el
                             juego lo prende (o le sube la emisión) de noche.
    pieza_cartel             panel blanco del cartel, con UV.
    punto_luz                en el medio del tubo (donde el juego pondría una luz).
    punto_lugar_1..12        lugares de las bebidas.
    heladera_bebidas-colonly paredes, techo, zócalo y estantes (cajas: los lugares quedan libres).
    heladera_bebidas_puerta-colonly  la puerta, hija de pieza_puerta (guía v1.5).
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

import _accesorios5 as ac  # noqa: E402
import _equipos as eq  # noqa: E402
import comun  # noqa: E402
import piezas  # noqa: E402
from piezas import g2b  # noqa: E402

ID = "heladera_bebidas"
PRESUPUESTO = 1500  # lista de modelos
MEDIDAS = (0.60, 1.80, 0.60)
CREMA, NEGRO, VIDRIO, LUZ = range(4)

W, H = 0.60, 1.80
Z_FONDO, Z_BOCA = -0.30, 0.255
Z_PUERTA = 0.285
PARED = 0.045
HUECO_X = W / 2 - PARED                    # 0,255
HUECO_Y = (0.14, 1.52)
FONDO_HUECO = Z_FONDO + 0.04               # pared de atrás de 4 cm
ESTANTES = (0.486, 0.826, 1.166)           # arriba de cada estante
ESP = 0.012
Z_ESTANTE = (FONDO_HUECO, 0.20)            # fondo y frente de los estantes
PUERTA_Y = (0.13, 1.53)
MARCO = 0.045
BISAGRA = (-W / 2, PUERTA_Y[0], Z_BOCA)
LUZ_POS = (0.0, 1.495, 0.215)
CARTEL = (0.53, 0.19, 1.66)                # ancho, alto, centro y del panel


def lugares():
    niveles = list(reversed(ESTANTES)) + [HUECO_Y[0]]
    return [(x, y, -0.03) for y in niveles for x in (-0.16, 0.0, 0.16)]


def mueble(bm):
    """Caja hueca de una sola malla: afuera con bisel, boca abierta hacia +Z."""
    previas = set(bm.faces)
    x0, x1, y0, y1 = -W / 2, W / 2, 0.0, H
    hx, (hy0, hy1) = HUECO_X, HUECO_Y

    def v(x, y, z):
        return bm.verts.new(g2b((x, y, z)))
    # Afuera: 8 esquinas. Boca: 4 en el frente, 4 en el fondo del hueco.
    A = {(i, j, k): v(x, y, z) for i, x in enumerate((x0, x1)) for j, y in enumerate((y0, y1))
         for k, z in enumerate((Z_FONDO, Z_BOCA))}
    Bf = {(i, j): v(x, y, Z_BOCA) for i, x in enumerate((-hx, hx)) for j, y in enumerate((hy0, hy1))}
    Bb = {(i, j): v(x, y, FONDO_HUECO) for i, x in enumerate((-hx, hx)) for j, y in enumerate((hy0, hy1))}
    f = bm.faces.new
    f((A[0, 0, 0], A[0, 1, 0], A[1, 1, 0], A[1, 0, 0]))          # atrás
    f((A[0, 0, 0], A[0, 0, 1], A[0, 1, 1], A[0, 1, 0]))          # costado −X
    f((A[1, 0, 0], A[1, 1, 0], A[1, 1, 1], A[1, 0, 1]))          # costado +X
    f((A[0, 1, 0], A[0, 1, 1], A[1, 1, 1], A[1, 1, 0]))          # techo
    # Frente con la boca (4 cuadriláteros alrededor).
    f((A[0, 0, 1], A[1, 0, 1], Bf[1, 0], Bf[0, 0]))
    f((A[1, 0, 1], A[1, 1, 1], Bf[1, 1], Bf[1, 0]))
    f((A[1, 1, 1], A[0, 1, 1], Bf[0, 1], Bf[1, 1]))
    f((A[0, 1, 1], A[0, 0, 1], Bf[0, 0], Bf[0, 1]))
    # Hueco: paredes y fondo.
    f((Bf[0, 0], Bf[1, 0], Bb[1, 0], Bb[0, 0]))
    f((Bf[1, 0], Bf[1, 1], Bb[1, 1], Bb[1, 0]))
    f((Bf[1, 1], Bf[0, 1], Bb[0, 1], Bb[1, 1]))
    f((Bf[0, 1], Bf[0, 0], Bb[0, 0], Bb[0, 1]))
    f((Bb[0, 0], Bb[1, 0], Bb[1, 1], Bb[0, 1]))
    nuevas = [x for x in bm.faces if x not in previas]
    bmesh.ops.recalc_face_normals(bm, faces=nuevas)
    # Bisel de 1 cm en las aristas de afuera (no en el piso: esa cara no existe).
    afuera = set(A.values())
    aristas = [e for e in bm.edges if all(vv in afuera for vv in e.verts) and len(e.link_faces) == 2]
    bmesh.ops.bevel(bm, geom=aristas, offset=0.01, segments=1, affect="EDGES", clamp_overlap=True)
    for x in bm.faces:
        if x not in previas:
            x.material_index = CREMA


def construir():
    mats = comun.cargar_materiales("M_BlancoCrema", "M_PlasticoNegro", "M_Vidrio", "M_LuzCalida")
    crema, negro, vidrio, luz = mats
    bm = bmesh.new()
    mueble(bm)
    # Rejilla del zócalo: marco negro con 3 listones (abajo de la puerta).
    piezas.caja(bm, (0.50, 0.085, 0.008), (0, 0.058, Z_BOCA + 0.002), mat=NEGRO)
    for i in range(3):
        piezas.caja(bm, (0.46, 0.012, 0.006), (0, 0.032 + i * 0.026, Z_BOCA + 0.008), mat=CREMA)
    # Estantes negros con cenefa adelante (metidos 2 mm en los costados del hueco).
    largo = Z_ESTANTE[1] - Z_ESTANTE[0]
    for y in ESTANTES:
        piezas.caja(bm, (2 * HUECO_X + 0.004, ESP, largo), (0, y - ESP / 2, (Z_ESTANTE[0] + Z_ESTANTE[1]) / 2),
                    mat=NEGRO, bisel=0.003)
        piezas.caja(bm, (2 * HUECO_X + 0.004, 0.035, 0.012), (0, y - 0.004, Z_ESTANTE[1] - 0.004),
                    mat=NEGRO, bisel=0.003)
    # Marco del cartel (el panel blanco va aparte).
    piezas.caja(bm, (CARTEL[0] + 0.04, CARTEL[1] + 0.04, 0.02), (0, CARTEL[2], Z_BOCA + 0.009), mat=NEGRO,
                bisel=0.005)
    cuerpo = piezas.terminar(f"{ID}_cuerpo", bm, [crema, negro])
    eq.e2.suavizar_hasta(cuerpo, 31)

    # Panel del cartel, con UV de 0 a 1 (derecho para el que lo mira de frente).
    bm = bmesh.new()
    a, h, yc = CARTEL
    z = Z_BOCA + 0.0195
    vs = [bm.verts.new(g2b(p)) for p in ((-a / 2, yc - h / 2, z), (a / 2, yc - h / 2, z),
                                          (a / 2, yc + h / 2, z), (-a / 2, yc + h / 2, z))]
    cara = bm.faces.new(vs)
    capa = bm.loops.layers.uv.new("UVMap")
    for lp in cara.loops:
        p = lp.vert.co
        lp[capa].uv = ((p.x + a / 2) / a, (p.z - (yc - h / 2)) / h)
    cartel = piezas.terminar("pieza_cartel", bm, [crema])

    # Tubo de luz.
    bm = bmesh.new()
    piezas.cilindro(bm, 0.012, 2 * HUECO_X - 0.03, (0, 0, 0), eje="x", lados=8, mat=0, radio_a_caras=True)
    for s in (-1, 1):   # soportes en las puntas
        piezas.caja(bm, (0.018, 0.03, 0.03), (s * (HUECO_X - 0.009), 0.012, -0.004), mat=1)
    bmesh.ops.translate(bm, vec=g2b(LUZ_POS), verts=bm.verts)
    luz_obj = eq.objeto_en("pieza_luz", bm, [luz, crema], LUZ_POS)

    # Puerta: marco negro, vidrio y tirador del lado +X.
    bm = bmesh.new()
    alto = PUERTA_Y[1] - PUERTA_Y[0]
    caras = ac.marco(bm, W, alto, Z_PUERTA - Z_BOCA, MARCO, mat=NEGRO, bisel=0.004)
    bmesh.ops.translate(bm, vec=g2b((0, PUERTA_Y[0], Z_PUERTA)), verts=ac.piezas._verts(caras))
    piezas.caja(bm, (W - 2 * MARCO + 0.01, alto - 2 * MARCO + 0.01, 0.01),
                (0, PUERTA_Y[0] + alto / 2, (Z_BOCA + Z_PUERTA) / 2), mat=VIDRIO)
    xt = W / 2 - 0.022
    for yt in (0.62, 1.02):
        piezas.caja(bm, (0.02, 0.024, 0.016), (xt, yt, Z_PUERTA + 0.004), mat=NEGRO)
    piezas.cilindro(bm, 0.009, 0.46, (xt, 0.82, 0.30 - 0.009), lados=8, mat=NEGRO, radio_a_caras=True)
    puerta = eq.objeto_en("pieza_puerta", bm, [crema, negro, vidrio], BISAGRA)
    # Solo los materiales que usa (negro y vidrio).
    _compactar(puerta)
    eq.e2.suavizar_hasta(puerta, 46)

    puntos = [piezas.punto(f"punto_lugar_{i + 1}", p) for i, p in enumerate(lugares())]
    p_luz = piezas.punto("punto_luz", LUZ_POS)
    prof = Z_BOCA - Z_FONDO
    zc = (Z_BOCA + Z_FONDO) / 2
    alto_h = HUECO_Y[1] - HUECO_Y[0]
    col = eq.colision_cajas(ID, [
        ((W, HUECO_Y[0], prof), (0, HUECO_Y[0] / 2, zc)),
        ((W, H - HUECO_Y[1], prof), (0, (H + HUECO_Y[1]) / 2, zc)),
        ((PARED, alto_h, prof), (-(W - PARED) / 2, sum(HUECO_Y) / 2, zc)),
        ((PARED, alto_h, prof), ((W - PARED) / 2, sum(HUECO_Y) / 2, zc)),
        ((2 * HUECO_X, alto_h, 0.04), (0, sum(HUECO_Y) / 2, Z_FONDO + 0.02)),
    ] + [((2 * HUECO_X, ESP, largo), (0, y - ESP / 2, (Z_ESTANTE[0] + Z_ESTANTE[1]) / 2)) for y in ESTANTES])
    col_puerta = eq.colision_cajas(f"{ID}_puerta", [((W, alto, Z_PUERTA - Z_BOCA),
                                                     (0, PUERTA_Y[0] + alto / 2, (Z_BOCA + Z_PUERTA) / 2))],
                                   padre=puerta)
    raiz = piezas.raiz(ID, [cuerpo, puerta, luz_obj, cartel, col, p_luz] + puntos)
    return {"raiz": raiz, "cuerpo": cuerpo, "puerta": puerta, "luz": luz_obj, "cartel": cartel,
            "col": col, "col_puerta": col_puerta, "puntos": puntos, "p_luz": p_luz}


def _compactar(obj):
    """Deja en el objeto solo los materiales que usan sus caras."""
    usados = sorted({p.material_index for p in obj.data.polygons})
    mats = [obj.data.materials[i] for i in usados]
    indices = [usados.index(p.material_index) for p in obj.data.polygons]
    obj.data.materials.clear()
    for mt in mats:
        obj.data.materials.append(mt)
    for p, i in zip(obj.data.polygons, indices):
        p.material_index = i


def visibles(m):
    return [m["cuerpo"], m["puerta"], m["luz"], m["cartel"]]


def revisar(m):
    vis = visibles(m)
    res = comun.revisar(vis, PRESUPUESTO, MEDIDAS, origen="base")
    res = ac.chequeo_normales(res, [m["cuerpo"], m["puerta"], m["luz"]])
    res = ac.reemplazar(res, "Normales", res[-1][0] and m["cartel"].data.polygons[0].normal.y < -0.99,
                        res[-1][1] + "; pieza_cartel: una cara mirando al frente")
    ok = all((p.location - g2b(l)).length < 1e-6 for p, l in zip(m["puntos"], lugares()))
    ok &= (m["puerta"].location - g2b(BISAGRA)).length < 1e-6
    ok &= (m["luz"].location - g2b(LUZ_POS)).length < 1e-6 and (m["p_luz"].location - g2b(LUZ_POS)).length < 1e-6
    res.insert(1, (ok, "punto_lugar_1..12 (3 por nivel) sobre los estantes (1,166 · 0,826 · 0,486) y el piso "
                       "(0,14); pieza_puerta con el origen en la bisagra; pieza_luz y punto_luz en el tubo"))
    capa = m["cartel"].data.uv_layers[0].data
    us = [capa[i].uv for i in m["cartel"].data.polygons[0].loop_indices]
    ok_uv = abs(min(u.x for u in us)) < 1e-5 and abs(max(u.x for u in us) - 1) < 1e-5 \
        and abs(min(u.y for u in us)) < 1e-5 and abs(max(u.y for u in us) - 1) < 1e-5
    res.insert(2, (ok_uv, "pieza_cartel en blanco (M_BlancoCrema), con la cara mapeada (UV de 0 a 1), "
                          "sin marca"))
    return res


def botellas(m):
    """Botellas de referencia (solo para las fotos) en algunos lugares."""
    rojo, amarillo, azul, verde = comun.cargar_materiales("M_RojoAcento", "M_Amarillo", "M_AzulAcento",
                                                          "M_Lechuga")
    out = []
    colores = [rojo, amarillo, azul, verde]
    for i, p in enumerate(m["puntos"]):
        if i in (1, 5, 11):
            continue
        bm = bmesh.new()
        for j, dz in enumerate((-0.12, 0.0, 0.12)):
            for dx in (-0.045, 0.045):
                piezas.cilindro(bm, 0.032, 0.20, (dx, 0.10, dz), lados=12)
                piezas.cilindro(bm, 0.012, 0.07, (dx, 0.235, dz), lados=8, radio_arriba=0.010)
        b = piezas.terminar(f"ref_botellas_{i}", bm, [colores[(i * 3 + i // 3) % 4]])
        b.location = p.location
        b.parent = m["raiz"]
        out.append(b)
    return out


def hoja(m, revision):
    comun.preparar_revision()
    vis = visibles(m)
    eq.e2.sin_cara_de_atras(m["puerta"])
    bot = botellas(m)
    abrir = lambda grados: (lambda: setattr(m["puerta"].rotation_euler, "z", math.radians(grados)))  # noqa: E731
    persona = ac.persona()
    pedidos = [
        ("Frente (lo que ve el cliente), con botellas de referencia · día", vis + bot, "frente", "dia",
         vis, abrir(0)),
        ("3/4 · día", vis + bot, "tres_cuartos", "dia", vis, abrir(0)),
        ("3/4 · atardecer", vis + bot, "tres_cuartos", "atardecer", vis, abrir(0)),
        ("Puerta abierta (−100°): estantes y lugares", vis + bot, "tres_cuartos", "dia", vis, abrir(-100)),
        ("Vacía, puerta abierta · día", vis, "bajo", "dia", vis, abrir(-100)),
    ]
    cuadros = ac.sacar_fotos(pedidos)
    carro, _b = ac.carrito("barra_chica", x=-1.3)
    persona.hide_render = False
    cuadros += ac.sacar_fotos([
        ("Al lado de la barra chica, con la silueta de 1,75 m · día", vis + bot + carro + [persona],
         "tres_cuartos", "dia", vis + carro + [persona], ac.mover_persona((0.75, 0, 0.5)), 1.0),
    ])
    abrir(0)()
    comun.componer_hoja("heladera_bebidas · 0,60 × 1,80 × 0,60 m · exhibidora, 12 lugares",
                        cuadros, revision, comun.RAIZ / f"docs/arte/revisiones/{ID}.jpg")


def main():
    comun.escena_vacia()
    m = construir()
    revision = revisar(m)
    ok = comun.imprimir_revision(ID, revision)
    ac.guardar_y_exportar(ID, [m["raiz"]] + visibles(m) + [m["col"], m["col_puerta"], m["p_luz"]] + m["puntos"],
                          uvs=True)
    if "--sin-hoja" not in sys.argv:
        hoja(m, revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
