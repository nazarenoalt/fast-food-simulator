"""Construcción común de las bases grandes con interior caminable (etapa 5): `food_truck` y
`trailer` (familia `carritos`). Cada script (`<id>.py`) da sus medidas en un dict P y llama a
main(); lo propio de cada uno (la cabina del camión, la lanza del tráiler) lo agrega con
P["extra"].

Todavía no tienen `.ron`: las medidas y los anclajes los propone el script (están en su
docstring y en P["anclajes"]); cuando se escriba la spec, el `.ron` tiene que copiar esos
valores (o el script pasa a leerlos del `.ron`, como `_base_carrito.py`).

Mismo lenguaje que las bases chicas (`_base_carrito.py`), en ejes de Godot (frente/cliente =
+Z, vendedor = −Z, arriba = +Y):
    - Casilla de chapa pintada (`pieza_pintura`): dos paredes de punta, dos costados y el
      techo, con las esquinas de arriba redondeadas (radio P["r_techo"]: 10 cm en el camión,
      35 cm en el tráiler). Paredes de 5 cm: por fuera chapa pintada, por dentro forro
      M_BlancoCrema (paneles lavables), los marcos de la ventana y la puerta en acero.
    - Del lado del cliente (+Z), la ventana de atención con su repisa de acero afuera y el
      toldo: la tapa de la ventana abierta hacia arriba (`pieza_toldo`, pintada, con dos
      amortiguadores de acero), como los food trucks de verdad.
    - Del lado del vendedor (−Z), la puerta (`pieza_puerta`, pintada) y el escalón de acero.
    - Adentro: piso de goma a P["y_piso"], mesada de acero corrida contra la ventana a
      y_piso + 0,95 (= alto_mostrador del .ron, medido desde la calle) y, debajo, el mueble de
      acero con las **bahías** para las alacenas bajo mesada (`_alacena.py`): mismas medidas
      que en las barras (0,58 × 0,62 × 0,50), la boca mirando al vendedor (−Z), con
      `punto_bahia_<n>` y su `pieza_tapa_bahia_<n>` (puertita de acero con tirador negro, el
      juego la esconde cuando hay una alacena). Contra la pared del vendedor, una mesada de
      atrás (mueble cerrado con puertas) para más equipos.
    - Ruedas de goma con llanta de acero adentro de pasarruedas (cajas de goma); el piso tiene
      la muesca de cada rueda.
Qué se mide (como en las bases chicas): ancho × profundidad = la casilla pintada; alto = del
piso a lo más alto del techo. Origen = centro de la casilla pintada en X y Z, a nivel de la
calle. El toldo abierto, el escalón, la cabina o la lanza quedan fuera de esa medida.

Objetos (bajo el Empty raíz `<id>`):
    pieza_pintura, <id>_estructura (forro, mesadas, muebles, piso, ruedas y lo demás),
    pieza_tapa_bahia_<n>, punto_bahia_<n>, pieza_puerta (origen en la bisagra, gira en Y:
    positivo abre hacia afuera, ≈ 100°), pieza_toldo (origen en la bisagra, gira en X: el
    .glb lo trae abierto a −110°; 0 = cerrado tapando la ventana),
    <id>-colonly (piso, paredes con los huecos de la ventana y la puerta, techo, mesadas y
    muebles con las bahías libres, escalón y lo de P["extra"]), <id>_puerta-colonly (hija de
    la puerta), punto_<anclaje> de P["anclajes"], punto_entrega, punto_fila y punto_entrada
    (afuera, al pie del escalón: donde el jugador sube).
"""
import math
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402  (antes que bmesh)
import bmesh  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
from mathutils.bvhtree import BVHTree  # noqa: E402

import comun  # noqa: E402
import piezas  # noqa: E402
import _alacena  # noqa: E402
import _base_carrito as base  # noqa: E402
import _ciudad as ciudad  # noqa: E402
import _plaza as plaza  # noqa: E402
from piezas import g2b  # noqa: E402

FAMILIA = "carritos"
MAX_MATERIALES = 6
PINT, ACERO, GOMA, NEGRO, EXTRA, CREMA = range(6)
EPS = 0.001
PARED = 0.05
ALTO_MESADA = 0.04
MESADA_SOBRE_PISO = 0.95
BAHIA_W, BAHIA_H, BAHIA_D = _alacena.BAHIA
BISEL = 0.012


# ── Piezas ─────────────────────────────────────────────────────────────

def pared_con_vanos(bm, plano, u0, u1, v0, v1, n_out, n_in, vanos, m_out, m_in, m_jamba, m_borde):
    """Paño de pared grueso (cerrado) con huecos rectangulares, en el plano z = n (plano "z",
    u = x) o x = n (plano "x", u = z). vanos = [(ua, ub, va, vb)]. Cara de afuera en n_out,
    de adentro en n_in; los cantos de los huecos llevan m_jamba y los del borde, m_borde."""
    def p(u, v, n):
        return g2b((u, v, n) if plano == "z" else (n, v, u))
    us = sorted({u0, u1} | {c for a, b, *_ in vanos for c in (a, b)})
    vs = sorted({v0, v1} | {c for *_, a, b in vanos for c in (a, b)})
    us = [u for u in us if u0 - 1e-9 <= u <= u1 + 1e-9]
    vs = [v for v in vs if v0 - 1e-9 <= v <= v1 + 1e-9]
    vert = {}

    def V(i, j, k):
        if (i, j, k) not in vert:
            vert[i, j, k] = bm.verts.new(p(us[i], vs[j], (n_out, n_in)[k]))
        return vert[i, j, k]

    def lleno(i, j):
        if not (0 <= i < len(us) - 1 and 0 <= j < len(vs) - 1):
            return False
        cu, cv = (us[i] + us[i + 1]) / 2, (vs[j] + vs[j + 1]) / 2
        return not any(a < cu < b and c < cv < d for a, b, c, d in vanos)

    nuevas = []
    for i in range(len(us) - 1):
        for j in range(len(vs) - 1):
            if not lleno(i, j):
                continue
            for k, m in ((0, m_out), (1, m_in)):
                f = bm.faces.new((V(i, j, k), V(i + 1, j, k), V(i + 1, j + 1, k), V(i, j + 1, k)))
                f.material_index = m
                nuevas.append(f)
            bordes = (((i - 1, j), (i, j), (i, j + 1), i == 0),
                      ((i + 1, j), (i + 1, j), (i + 1, j + 1), i == len(us) - 2),
                      ((i, j - 1), (i, j), (i + 1, j), j == 0),
                      ((i, j + 1), (i, j + 1), (i + 1, j + 1), j == len(vs) - 2))
            for vecino, a, b, en_borde in bordes:
                if lleno(*vecino):
                    continue
                f = bm.faces.new((V(*a, 0), V(*b, 0), V(*b, 1), V(*a, 1)))
                f.material_index = m_borde if en_borde else m_jamba
                nuevas.append(f)
    return nuevas


def contorno_techo(zh, ytop, r, seg, meter=0.0):
    """Arco de arriba de la sección (z, y), de (+zh, ytop − r) a (−zh, ytop − r), metido
    `meter` hacia adentro (para el forro)."""
    pts = []
    rr = r - meter
    for cz, a0 in ((zh - r, 0), (-zh + r, 90)):
        for i in range(seg + 1):
            a = math.radians(a0 + 90 * i / seg)
            pts.append((cz + rr * math.cos(a), ytop - r + rr * math.sin(a)))
    return pts


def prisma_x(bm, perfil, x0, x1, mats_lados, mat_x0, mat_x1):
    """Perfil cerrado [(z, y)] estirado sobre X de x0 a x1. mats_lados[k] = material del
    lado entre el punto k y el k+1."""
    n = len(perfil)
    a = [bm.verts.new(g2b((x0, y, z))) for z, y in perfil]
    b = [bm.verts.new(g2b((x1, y, z))) for z, y in perfil]
    caras = []
    for k in range(n):
        f = bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]))
        f.material_index = mats_lados[k]
        caras.append(f)
    f0 = bm.faces.new(list(reversed(a)))
    f0.material_index = mat_x0
    f1 = bm.faces.new(b)
    f1.material_index = mat_x1
    return caras + [f0, f1]


def casilla(bm, P):
    """Paredes, techo y piso de la casilla."""
    x0, x1, zh, t = P["x0"], P["x1"], P["zh"], PARED
    y0, ytop, r, seg = P["y_base"], P["alto"], P["r_techo"], P["seg_techo"]
    yc = ytop - r
    # Paredes de punta (sección completa).
    seccion = [(-zh, y0), (zh, y0)] + contorno_techo(zh, ytop, r, seg)
    lados = [PINT] * len(seccion)
    prisma_x(bm, seccion, x0, x0 + t, lados, PINT, CREMA)
    prisma_x(bm, seccion, x1 - t, x1, lados, CREMA, PINT)
    # Techo: banda curva entre las paredes de punta.
    afuera = contorno_techo(zh, ytop, r, seg)
    adentro = contorno_techo(zh, ytop, r, seg, meter=t)
    anillo = afuera + list(reversed(adentro))
    m = len(afuera)
    mats = [PINT] * (m - 1) + [PINT] + [CREMA] * (m - 1) + [PINT]
    prisma_x(bm, anillo, x0 + t - EPS, x1 - t + EPS, mats, PINT, PINT)
    # Costados con la ventana (cliente, +Z) y la puerta (vendedor, −Z), y los pasarruedas.
    arcos = [(e["x"] - e["arco"], e["x"] + e["arco"], y0, e["y_arco"]) for e in P["ejes"] if e["caja"]]
    va, vb, vy0, vy1 = P["ventana"]
    pa, pb = P["puerta"]
    u0, u1 = x0 + t - EPS, x1 - t + EPS
    pared_con_vanos(bm, "z", u0, u1, y0, yc + EPS, zh, zh - t, arcos + [(va, vb, vy0, vy1)],
                    PINT, CREMA, ACERO, PINT)
    pared_con_vanos(bm, "z", u0, u1, y0, yc + EPS, -zh, -zh + t, arcos + [(pa, pb, P["y_piso"], P["y_puerta"])],
                    PINT, CREMA, ACERO, PINT)
    # Piso de goma (con la muesca de cada rueda) y pasarruedas.
    yp = P["y_piso"]
    zi = zh - t + EPS
    cortes = sorted({u0, u1} | {c for a, b, *_ in arcos for c in (a, b)})
    for xa, xb in zip(cortes, cortes[1:]):
        rueda_aca = any(a - 1e-6 <= (xa + xb) / 2 <= b + 1e-6 for a, b, *_ in arcos)
        zz = P["z_pasarrueda"] if rueda_aca else zi
        piezas.caja(bm, (xb - xa + (EPS if rueda_aca else 0), 0.08, 2 * zz), ((xa + xb) / 2, yp - 0.04, 0), mat=GOMA)
    for e in P["ejes"]:
        if not e["caja"]:
            continue
        xa, xb, ya = e["x"] - e["arco"], e["x"] + e["arco"], e["y_arco"]
        zp = P["z_pasarrueda"]
        for s in (-1, 1):
            zc = s * (zp + zh - t) / 2
            piezas.caja(bm, (xb - xa, 0.04, zh - t - zp + EPS), (e["x"], ya + 0.02, zc), mat=GOMA)
            piezas.caja(bm, (xb - xa + 0.004, ya + 0.04 - (yp - 0.09), 0.03),
                        (e["x"], (ya + 0.04 + yp - 0.09) / 2, s * (zp - 0.015)), mat=GOMA)
            for x in (xa + 0.017, xb - 0.017):
                y_a, y_b = yp - 0.08 + 0.003, ya + 0.02
                piezas.caja(bm, (0.03, y_b - y_a, zh - t - zp - 0.004), (x, (y_a + y_b) / 2, zc), mat=GOMA)


def rueda(bm, x, zc, r, ancho, s):
    """Rueda de vehículo (eje Z): cubierta de goma y llanta de acero hacia afuera (s = ±1)."""
    piezas.cilindro(bm, r, ancho, (x, r, zc), eje="z", lados=24, mat=GOMA, radio_a_caras=True)
    piezas.cilindro(bm, r * 0.6, 0.03, (x, r, zc + s * (ancho / 2 + 0.01)), eje="z", lados=16, mat=ACERO,
                    radio_a_caras=True, radio_arriba=r * 0.5 if s > 0 else None)


def mueble_frente(bm, P, tapas_mats):
    """Mesada de la ventana y su mueble con las bahías. Devuelve (tapas, puntos, bahías)."""
    x_in0, x_in1 = P["x0"] + PARED, P["x1"] - PARED
    zw = P["zh"] - PARED
    yp = P["y_piso"]
    ym = yp + MESADA_SOBRE_PISO           # arriba de la mesada
    y1 = ym - ALTO_MESADA                  # abajo de la mesada
    y_bahia = y1 - BAHIA_H                 # piso de las bahías
    z_boca = P["z_mueble"]                 # cara del mueble (vendedor)
    z_fondo = z_boca + BAHIA_D
    # Mesada de adentro (contra la pared) y repisa de afuera (por la ventana).
    base.losa(bm, (x_in1 - x_in0 - 2 * EPS, ALTO_MESADA, zw - z_boca + 0.03), (
        (x_in0 + x_in1) / 2, ym - ALTO_MESADA / 2, (zw + z_boca - 0.03) / 2), radio=0.02, seg=2, mat=ACERO)
    va, vb = P["ventana"][:2]
    base.losa(bm, (vb - va - 0.02, ALTO_MESADA, P["repisa"]), ((va + vb) / 2, ym - ALTO_MESADA / 2 - 0.002,
              zw + P["repisa"] / 2), radio=0.02, seg=2, mat=ACERO)
    # Bahías: donde entran, entre las puntas del mueble y los pasarruedas.
    xs = []
    for xa, xb in P["bahias_x"]:
        n = int((xb - xa + 0.08) // (BAHIA_W + 0.08))
        xs += base.centros_bahias(xa, xb, n, 0.08)
    # Cuerpo del mueble (acero): montantes de alto completo, travesaño bajo las bahías y fondo.
    alto = y1 - yp + EPS
    for ma, mb in base.macizos(x_in0 + EPS, x_in1 - EPS, xs):
        piezas.caja(bm, (mb - ma, alto, zw - z_boca), ((ma + mb) / 2, yp + alto / 2, (zw + z_boca) / 2),
                    mat=ACERO, bisel=0.006)
    for xc in xs:
        piezas.caja(bm, (BAHIA_W + 2 * EPS, y_bahia - yp, zw - z_boca - 0.004),
                    (xc, (yp + y_bahia) / 2, (zw + z_boca + 0.004) / 2), mat=ACERO, bisel=0.006)
        piezas.caja(bm, (BAHIA_W + 2 * EPS, BAHIA_H + EPS, zw - z_fondo),
                    (xc, y_bahia + BAHIA_H / 2, (zw + z_fondo) / 2), mat=ACERO)
    tapas, puntos, bahias = [], [], []
    for i, xc in enumerate(xs):
        bt = bmesh.new()
        ya, yb = y_bahia - 0.012, y1 - 0.006
        piezas.caja(bt, (BAHIA_W + 0.02, yb - ya, 0.02), (xc, (ya + yb) / 2, z_boca - 0.011), mat=0, bisel=0.008)
        piezas.caja(bt, (0.12, 0.022, 0.02), (xc, yb - 0.06, z_boca - 0.030), mat=1, bisel=0.005)
        tapas.append(base.objeto_en(f"pieza_tapa_bahia_{i + 1}", bt, tapas_mats, (xc, y_bahia, z_boca)))
        puntos.append(piezas.punto(f"punto_bahia_{i + 1}", (xc, y_bahia, z_boca)))
        bahias.append((xc, y_bahia, z_boca))
    return tapas, puntos, bahias, xs


def mueble_atras(bm, P):
    """Mesada de atrás (contra la pared del vendedor): mueble cerrado con puertas."""
    xa, xb = P["mesada_atras"]
    zw = -P["zh"] + PARED
    zb = zw + P["fondo_atras"]
    yp = P["y_piso"]
    ym = yp + MESADA_SOBRE_PISO
    y1 = ym - ALTO_MESADA
    base.losa(bm, (xb - xa, ALTO_MESADA, zb - zw + 0.03), ((xa + xb) / 2, ym - ALTO_MESADA / 2, (zw + zb + 0.03) / 2),
              radio=0.02, seg=2, mat=ACERO)
    piezas.caja(bm, (xb - xa - 0.02, y1 - yp + EPS, zb - zw - EPS), ((xa + xb) / 2, yp + (y1 - yp) / 2, (zw + zb) / 2),
                mat=ACERO, bisel=0.008)
    n = max(1, round((xb - xa) / 0.6))
    w = (xb - xa - 0.04) / n
    for k in range(n):
        xc = xa + 0.02 + w * (k + 0.5)
        piezas.caja(bm, (w - 0.012, y1 - yp - 0.10, 0.016), (xc, yp + (y1 - yp) / 2 + 0.02, zb + 0.006),
                    mat=ACERO, bisel=0.005)
        piezas.caja(bm, (0.10, 0.02, 0.018), (xc, y1 - 0.08, zb + 0.022), mat=NEGRO, bisel=0.004)
    return zb


def toldo(P, mats):
    """Tapa de la ventana abierta hacia arriba: pieza_toldo con el origen en la bisagra."""
    va, vb, vy0, vy1 = P["ventana"]
    zh = P["zh"]
    yb = vy1 + 0.06                         # bisagra, arriba de la ventana
    largo = yb - vy0 + 0.04                 # cerrada tapa la ventana y 4 cm más
    ancho = vb - va + 0.14
    bm = bmesh.new()
    # Armada cerrada (colgando sobre la pared, eje en (yb, zh + 0,02)) y después se abre.
    piezas.caja(bm, (ancho, largo, 0.03), ((va + vb) / 2, yb - largo / 2, zh + 0.017), mat=0, bisel=0.01)
    piezas.cilindro(bm, 0.012, ancho - 0.1, ((va + vb) / 2, yb, zh + 0.02), eje="x", lados=8, mat=1,
                    radio_a_caras=True)
    obj = base.objeto_en("pieza_toldo", bm, mats, ((va + vb) / 2, yb, zh + 0.02))
    # Se abre y se aplica el giro a la malla (guía 2.4: rotación 0): el .glb lo trae abierto y
    # el juego lo cierra girándolo en X (+P["toldo_abierto"] en valor absoluto).
    obj.data.transform(Matrix.Rotation(math.radians(P["toldo_abierto"]), 4, "X"))
    bpy.context.view_layer.update()
    # Amortiguadores (en la estructura): de la pared a 1/2 del largo de la tapa.
    puntas = []
    for x in (va - 0.035, vb + 0.035):                              # a los costados de la ventana
        a = (x, (vy0 + vy1) / 2, zh + 0.012)
        tapa = Vector(g2b((x, yb - largo * 0.55, zh + 0.002)))     # en la tapa cerrada
        b = obj.matrix_world @ (Matrix.Rotation(math.radians(P["toldo_abierto"]), 4, "X") @
                                (tapa - obj.location))              # la misma, abierta
        puntas.append((a, (b.x, b.z, -b.y)))
    return obj, puntas, (ancho, largo, yb)


def puerta(P, mats):
    pa, pb = P["puerta"]
    yp, yt = P["y_piso"], P["y_puerta"]
    zh = P["zh"]
    bm = bmesh.new()
    w, h = pb - pa - 0.01, yt - yp - 0.01
    piezas.caja(bm, (w, h, 0.04), ((pa + pb) / 2, yp + 0.005 + h / 2, -zh + 0.02), mat=0, bisel=0.008)
    piezas.caja(bm, (0.03, 0.14, 0.03), (pb - 0.08, yp + 1.0, -zh - 0.012), mat=1, bisel=0.006)
    piezas.caja(bm, (w - 0.06, 0.18, 0.006), ((pa + pb) / 2, yp + 0.14, -zh - 0.002), mat=2)
    obj = base.objeto_en("pieza_puerta", bm, mats, (pa + 0.005, yp, -zh))
    col = piezas.colision_caja(f"{P['id']}_puerta", (w, h, 0.04), ((pa + pb) / 2, yp + 0.005 + h / 2, -zh + 0.02))
    col.parent = obj
    col.location = -obj.location
    return obj, col


# ── Modelo ─────────────────────────────────────────────────────────────

def partir(bm, mats, id_):
    """Separa la chapa pintada (pieza_pintura) del resto (<id>_estructura)."""
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bp = bm.copy()
    bmesh.ops.delete(bp, geom=[f for f in bp.faces if f.material_index != PINT], context="FACES")
    be = bm.copy()
    bmesh.ops.delete(be, geom=[f for f in be.faces if f.material_index == PINT], context="FACES")
    bm.free()
    pintura = ciudad.terminar("pieza_pintura", bp, [mats[PINT]])
    usados = ciudad.materiales_usados(be, mats)
    estructura = ciudad.terminar(f"{id_}_estructura", be, usados)
    return pintura, estructura


def construir(P):
    mats = comun.cargar_materiales(*P["materiales"])
    bm = bmesh.new()
    casilla(bm, P)
    tapas, puntos_bahia, bahias, xs_bahias = mueble_frente(bm, P, [mats[ACERO], mats[NEGRO]])
    z_atras = mueble_atras(bm, P)
    # Escalón de acero (afuera, al pie de la puerta), colgado de dos soportes.
    pa, pb = P["puerta"]
    zh = P["zh"]
    ye = P["y_escalon"]
    piezas.caja(bm, (pb - pa + 0.10, 0.04, 0.32), ((pa + pb) / 2, ye - 0.02, -zh - 0.16 - 0.005), mat=ACERO, bisel=0.008)
    for x in (pa, pb):
        piezas.caja(bm, (0.04, P["y_base"] + 0.04 - ye + 0.04, 0.04), (x, (ye - 0.04 + P["y_base"] + 0.04) / 2,
                    -zh - 0.03), mat=ACERO)
    # Ruedas.
    for e in P["ejes"]:
        for s in (-1, 1):
            rueda(bm, e["x"], s * e["z"], e["r"], e["ancho"], s)
    # Lo propio de cada modelo (cabina, lanza...).
    cajas_extra = P["extra"](bm, P) if P.get("extra") else []
    toldo_obj, puntas, _ = toldo(P, [mats[PINT], mats[ACERO]])
    for a, b in puntas:
        plaza.caño(bm, a, b, 0.012, 8, mat=ACERO)
    pintura, estructura = partir(bm, mats, P["id"])
    puerta_obj, col_puerta = puerta(P, [mats[PINT], mats[NEGRO], mats[ACERO]])
    colisiones = [colision(P, xs_bahias, z_atras, cajas_extra), col_puerta]
    puntos = []
    for nombre, pos, rot_y in P["anclajes"]:
        e = piezas.punto(f"punto_{nombre}", pos)
        e.rotation_euler.z = math.radians(rot_y)
        puntos.append(e)
    for nombre in ("entrega", "fila", "entrada"):
        puntos.append(piezas.punto(f"punto_{nombre}", P[nombre]))
    piezas_mov = tapas + [puerta_obj, toldo_obj]
    hijos = [pintura, estructura] + piezas_mov + colisiones[:1] + puntos + puntos_bahia
    raiz = piezas.raiz(P["id"], hijos)
    return {"P": P, "raiz": raiz, "pintura": pintura, "estructura": estructura, "tapas": tapas,
            "puerta": puerta_obj, "toldo": toldo_obj, "colisiones": colisiones, "puntos": puntos,
            "puntos_bahia": puntos_bahia, "bahias": bahias, "z_atras": z_atras,
            "visibles": [pintura, estructura] + piezas_mov}


def colision(P, xs, z_atras, cajas_extra):
    """Cajas: piso, paredes (con la ventana y la puerta libres), techo, mesadas y muebles (con
    las bahías libres), escalón y las de P["extra"]."""
    x0, x1, zh, t = P["x0"], P["x1"], P["zh"], PARED
    W, X = x1 - x0, (x0 + x1) / 2
    yp, ytop, y0 = P["y_piso"], P["alto"], P["y_base"]
    ym = yp + MESADA_SOBRE_PISO
    va, vb, vy0, vy1 = P["ventana"]
    pa, pb = P["puerta"]
    cajas = [
        ((W, yp - y0, 2 * zh), (X, (y0 + yp) / 2, 0)),                      # piso
        ((W, 0.1, 2 * zh), (X, ytop - 0.05, 0)),                            # techo
        ((t, ytop - y0, 2 * zh), (x0 + t / 2, (y0 + ytop) / 2, 0)),         # puntas
        ((t, ytop - y0, 2 * zh), (x1 - t / 2, (y0 + ytop) / 2, 0)),
    ]
    for z, (ha, hb, hy0, hy1) in ((zh - t / 2, (va, vb, vy0, vy1)), (-zh + t / 2, (pa, pb, yp, P["y_puerta"]))):
        cajas += [
            ((ha - x0, ytop - y0, t), ((x0 + ha) / 2, (y0 + ytop) / 2, z)),
            ((x1 - hb, ytop - y0, t), ((hb + x1) / 2, (y0 + ytop) / 2, z)),
            ((hb - ha, hy0 - y0, t), ((ha + hb) / 2, (y0 + hy0) / 2, z)),
            ((hb - ha, ytop - hy1, t), ((ha + hb) / 2, (hy1 + ytop) / 2, z)),
        ]
    # Mueble de la ventana: mesada y repisa, fondo de las bahías y lo macizo entre bahías.
    zb, zw = P["z_mueble"], zh - t
    y1 = ym - ALTO_MESADA
    y_bahia = y1 - BAHIA_H
    cajas.append(((W - 2 * t, ALTO_MESADA, zw - zb + 0.03), (X, ym - ALTO_MESADA / 2, (zw + zb - 0.03) / 2)))
    cajas.append(((vb - va, ALTO_MESADA, P["repisa"] + t), ((va + vb) / 2, ym - ALTO_MESADA / 2, zw + (P["repisa"] + t) / 2)))
    cajas.append(((W - 2 * t, y_bahia - yp, zw - zb), (X, (yp + y_bahia) / 2, (zw + zb) / 2)))
    cajas.append(((W - 2 * t, BAHIA_H, zw - zb - BAHIA_D), (X, y_bahia + BAHIA_H / 2, (zw + zb + BAHIA_D) / 2)))
    for ma, mb in base.macizos(x0 + t, x1 - t, xs):
        cajas.append(((mb - ma, BAHIA_H, BAHIA_D), ((ma + mb) / 2, y_bahia + BAHIA_H / 2, zb + BAHIA_D / 2)))
    xa, xb = P["mesada_atras"]
    cajas.append(((xb - xa, ym - yp, z_atras + zh - t), ((xa + xb) / 2, (yp + ym) / 2, (z_atras - zh + t) / 2)))
    ye = P["y_escalon"]
    cajas.append(((pb - pa + 0.1, ye, 0.32), ((pa + pb) / 2, ye / 2, -zh - 0.165)))
    cajas += cajas_extra
    return plaza.colision_cajas(P["id"], [(m, c, (0, 0, 0)) for m, c in cajas])


# ── Revisión ───────────────────────────────────────────────────────────

def verts_g(objs):
    bpy.context.view_layer.update()
    return [Vector(((o.matrix_world @ v.co).x, (o.matrix_world @ v.co).z, -(o.matrix_world @ v.co).y))
            for o in objs for v in o.data.vertices]


def chequeo_normales(objs):
    """La chapa y la estructura salen de un mismo bmesh partido por material: se vuelven a
    juntar y cada parte cerrada tiene que tener volumen > 0. Las piezas que se mueven, igual."""
    bm = bmesh.new()
    for o in objs[:2]:
        m = o.data.copy()
        m.transform(o.matrix_world)
        bm.from_mesh(m)
        bpy.data.meshes.remove(m)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    malas, abiertas, vistas, islas = [], 0, set(), 0
    for f0 in bm.faces:
        if f0.index in vistas:
            continue
        isla, pila = [], [f0]
        vistas.add(f0.index)
        while pila:
            f = pila.pop()
            isla.append(f)
            for e in f.edges:
                for g in e.link_faces:
                    if g.index not in vistas:
                        vistas.add(g.index)
                        pila.append(g)
        islas += 1
        if not all(len(e.link_faces) == 2 for f in isla for e in f.edges):
            abiertas += 1
            continue
        vol = sum(f.verts[0].co.dot(f.verts[i].co.cross(f.verts[i + 1].co)) / 6
                  for f in isla for i in range(1, len(f.verts) - 1))
        if vol <= 0:
            malas.append(len(isla))
    bm.free()
    for o in objs[2:]:
        if comun._volumen_con_signo(o) <= 0:
            malas.append(o.name)
    ok = not malas and abiertas == 0
    return ok, "Normales hacia afuera (chapa + estructura juntas: %d partes cerradas, %d abiertas; " \
        "piezas que se mueven cerradas)%s" % (islas - abiertas, abiertas, f" — MAL: {malas}" if malas else "")


def chequeo_medidas(m, tol=0.002):
    P = m["P"]
    vp = verts_g([m["pintura"]])
    caja = [v for v in vp if P["x0"] - 1e-6 <= v.x <= P["x1"] + 1e-6]
    todos = verts_g([m["pintura"], m["estructura"]])
    x0, x1 = min(v.x for v in vp), max(v.x for v in vp)
    z0, z1 = min(v.z for v in caja), max(v.z for v in caja)
    piso, techo = min(v.y for v in todos), max(v.y for v in todos)
    ok = (abs(x1 - x0 - P["ancho"]) <= tol and abs(z1 - z0 - P["prof"]) <= tol and abs(piso) <= tol and
          abs(techo - P["alto_total"]) <= tol)
    texto = "Medidas: casilla pintada %.3f × %.3f m, alto %.3f (propuesta para el .ron: ancho %.2f, " \
        "profundidad %.2f; alto total %.2f)" % (x1 - x0, z1 - z0, techo - piso, P["ancho"], P["prof"], P["alto_total"])
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    ok_o = abs(cx) <= tol and abs(cz) <= tol and abs(piso) <= tol
    texto_o = "Origen en el centro de la casilla pintada (%.3f, %.3f), a nivel de la calle (ruedas en Y = %.3f)" % (
        cx, cz, piso)
    return (ok, texto), (ok_o, texto_o)


def chequeo_interior(m):
    """Piso, mesadas a 0,95 del piso, techo, pasillo libre entre los muebles y escalón."""
    P = m["P"]
    yp = P["y_piso"]
    ym = yp + MESADA_SOBRE_PISO
    vs = verts_g([m["pintura"], m["estructura"]])
    zb, za = P["z_mueble"], m["z_atras"]
    x_in0, x_in1 = P["x0"] + PARED, P["x1"] - PARED
    techo_int = P["alto"] - PARED
    pasillo = [v for v in vs if x_in0 + 0.02 < v.x < x_in1 - 0.02 and za + 0.04 < v.z < zb - 0.04 and
               yp + 0.005 < v.y < techo_int - 0.005]
    # Arriba de las mesadas (las dos a ym).
    dg = bpy.context.evaluated_depsgraph_get()
    arbol = BVHTree.FromObject(m["estructura"], dg)
    alturas = []
    for x, z in ((P["anclajes_dict"]["mostrador_centro"][0], (zb + P["zh"]) / 2),
                 (sum(P["mesada_atras"]) / 2, (za - P["zh"]) / 2)):
        hit = arbol.ray_cast(g2b((x, ym + 0.5, z)), Vector((0, 0, -1)))
        alturas.append(ym + 0.5 - hit[3] if hit[0] else -1)
    hit = arbol.ray_cast(g2b(((x_in0 + x_in1) / 2, yp + 0.5, (zb + za) / 2)), Vector((0, 0, -1)))
    piso = yp + 0.5 - hit[3] if hit[0] else -1
    ok = (not pasillo and all(abs(a - ym) < 1e-3 for a in alturas) and abs(piso - yp) < 1e-3 and
          techo_int - yp >= 2.0 and P["y_escalon"] <= yp / 2 + 0.03)
    return ok, ("Interior: piso a %.2f, mesadas a %.3f / %.3f (piso + 0,95), %.2f m de techo, pasillo de %.2f m "
                "libre, escalón a %.2f" % (piso, alturas[0], alturas[1], techo_int - yp, zb - za, P["y_escalon"]) +
                (f" — {len(pasillo)} vértices en el pasillo, por ej. {pasillo[0]}" if pasillo else ""))


def chequeo_bahias(m):
    """Como en las bases chicas: hueco libre, cerrado (piso, mesada, paredes, fondo) y la
    boca libre hacia el vendedor."""
    vs = verts_g([m["pintura"], m["estructura"]])
    dg = bpy.context.evaluated_depsgraph_get()
    arboles = [BVHTree.FromObject(o, dg) for o in (m["pintura"], m["estructura"])]
    problemas = []
    for i, ((xc, yp, zb), e, t) in enumerate(zip(m["bahias"], m["puntos_bahia"], m["tapas"])):
        if e.name != f"punto_bahia_{i + 1}" or t.name != f"pieza_tapa_bahia_{i + 1}":
            problemas.append(f"nombres {i + 1}")
        x0, x1, y1, z1 = xc - BAHIA_W / 2, xc + BAHIA_W / 2, yp + BAHIA_H, zb + BAHIA_D
        if any(x0 + 1e-3 < v.x < x1 - 1e-3 and yp + 1e-3 < v.y < y1 - 1e-3 and zb + 1e-3 < v.z < z1 - 1e-3
               for v in vs):
            problemas.append(f"hueco {i + 1} ocupado")
        centro = (xc, yp + BAHIA_H / 2, zb + BAHIA_D / 2)
        esperado = {(0, -1, 0): BAHIA_H / 2, (0, 1, 0): BAHIA_H / 2, (-1, 0, 0): BAHIA_W / 2,
                    (1, 0, 0): BAHIA_W / 2, (0, 0, 1): BAHIA_D / 2}
        for d, dist in esperado.items():
            hit = base.rayo(arboles, centro, d)
            if hit is None or abs(hit - dist) > 1e-3:
                problemas.append(f"hueco {i + 1} {d}: {hit}")
        hit = base.rayo(arboles, centro, (0, 0, -1))
        if hit is not None and hit < BAHIA_D / 2 + 0.5:
            problemas.append(f"boca {i + 1} tapada a {hit:.2f}")
    n = len(m["bahias"])
    return not problemas, ("Bahías: %d de %.2f × %.2f × %.2f bajo la mesada de la ventana, con punto_bahia y "
                           "pieza_tapa_bahia; huecos libres y cerrados, boca libre hacia el vendedor" % (
                               n, BAHIA_W, BAHIA_H, BAHIA_D) + ("" if not problemas else " — " + ", ".join(problemas)))


def chequeo_piezas(m):
    P = m["P"]
    pt, tl = m["puerta"], m["toldo"]
    pa = P["puerta"][0]
    ok = (abs(pt.location.x - (pa + 0.005)) < 1e-6 and abs(pt.location.z - P["y_piso"]) < 1e-6 and
          tl.rotation_euler.to_quaternion().angle < 1e-6 and
          m["colisiones"][1].parent == pt)
    vt = verts_g([tl])
    return ok, ("pieza_puerta (bisagra en x %.3f, gira en Y) y pieza_toldo (bisagra a %.2f, abierto en la malla; "
                "se cierra girando %.0f° en X; lo más bajo a %.2f, sale %.2f de la pared)" % (
                    pa + 0.005, tl.location.z, -P["toldo_abierto"], min(v.y for v in vt),
                    max(v.z for v in vt) - P["zh"]))


def chequeo_puntos(m):
    P = m["P"]
    esperados = {f"punto_{n}": (p, r) for n, p, r in P["anclajes"]}
    for n in ("entrega", "fila", "entrada"):
        esperados[f"punto_{n}"] = (P[n], 0.0)
    por_nombre = {e.name: e for e in m["puntos"]}
    ok = set(por_nombre) == set(esperados) and all(
        (por_nombre[n].matrix_world.translation - g2b(p)).length < 1e-5 for n, (p, _) in esperados.items())
    return ok, "Puntos: %d punto_<anclaje> + entrega, fila y entrada, en las posiciones propuestas" % len(P["anclajes"])


def revisar(m):
    P = m["P"]
    res = comun.revisar(m["visibles"], P["presupuesto"], (P["ancho"], P["alto_total"], P["prof"]), origen="base",
                        max_materiales=MAX_MATERIALES)
    (ok_m, t_m), (ok_o, t_o) = chequeo_medidas(m)
    res = plaza.reemplazar(res, "Medidas", ok_m, t_m)
    res = plaza.reemplazar(res, "Origen", ok_o, t_o)
    res = plaza.reemplazar(res, "Normales", *chequeo_normales(m["visibles"]))
    res.append(chequeo_interior(m))
    res.append(chequeo_bahias(m))
    res.append(chequeo_piezas(m))
    res.append(chequeo_puntos(m))
    return res


# ── Hoja de revisión ───────────────────────────────────────────────────

def camara(pos_g, mira_g, lente=50, orto=None):
    cam = comun._camara()
    if orto:
        cam.data.type = "ORTHO"
        cam.data.ortho_scale = orto
    else:
        cam.data.type = "PERSP"
        cam.data.lens = lente
    cam.location = g2b(pos_g)
    cam.rotation_euler = (g2b(mira_g) - g2b(pos_g)).to_track_quat("-Z", "Y").to_euler()
    cam.data.clip_start = 0.05
    cam.data.clip_end = 200


def hoja_revision(m, revision, titulo, vistas):
    """vistas = [(etiqueta, objetos o claves, luz, (pos, mira, lente, orto), relleno)]: cámaras
    fijas (ejes de Godot). relleno=True prende una luz chica adentro (solo para la foto)."""
    P = m["P"]
    comun.preparar_revision()
    persona = bpy.data.objects["ref_persona_1,75m"]
    # Dos personas: un cliente afuera, frente a la ventana, y el vendedor adentro.
    cliente = persona.copy()
    bpy.context.scene.collection.objects.link(cliente)
    vc = sum(P["ventana"][:2]) / 2
    cliente.location = g2b((vc + 0.3, 0, P["zh"] + 0.55))
    persona.location = g2b((vc - 0.3, P["y_piso"], (P["z_mueble"] + m["z_atras"]) / 2 - 0.05))
    cliente.rotation_euler.z = math.pi
    # Puerta abierta (copia) y alacenas en las bahías.
    puerta_ab = m["puerta"].copy()
    puerta_ab.data = m["puerta"].data.copy()
    bpy.context.scene.collection.objects.link(puerta_ab)
    puerta_ab.rotation_euler.z = math.radians(100)
    sin_tapas = [m["pintura"], m["estructura"], m["toldo"]]
    con_alacenas = list(sin_tapas) + [puerta_ab]
    variantes = ["puertas", "cajones", "mixta", "abierta"]
    for variante, punto in zip(variantes, m["puntos_bahia"]):
        al = _alacena.construir(variante, f"ref_alacena_{punto.name}")
        al["raiz"].location = punto.matrix_world.translation
        al["colision"].hide_render = True
        con_alacenas += _alacena.visibles(al)
    luz = bpy.data.lights.new("ref_relleno", "POINT")
    luz.energy = 250
    luz.shadow_soft_size = 0.5
    relleno = bpy.data.objects.new("ref_relleno", luz)
    bpy.context.scene.collection.objects.link(relleno)
    relleno.location = g2b(((P["x0"] + P["x1"]) / 2, P["alto"] - 0.3, 0))
    bpy.context.view_layer.update()
    grupos = {
        "cerrado": m["visibles"],
        "abierto": [m["pintura"], m["estructura"], m["toldo"]] + m["tapas"] + [puerta_ab],
        "personas": m["visibles"] + [persona, cliente],
        "personas_ab": [m["pintura"], m["estructura"], m["toldo"]] + m["tapas"] + [puerta_ab, persona, cliente],
        "alacenas": con_alacenas,
        "sin_tapas": sin_tapas + [puerta_ab],
    }
    tmp = Path(tempfile.mkdtemp())
    todos = {o for g in grupos.values() for o in g}
    cuadros = []
    for etiqueta, grupo, luz_modo, (pos, mira, lente, orto), con_relleno in vistas:
        comun.poner_luz(luz_modo)
        relleno.hide_render = not con_relleno
        for o in todos:
            o.hide_render = o not in grupos[grupo]
        camara(pos, mira, lente, orto)
        cuadros.append((etiqueta, comun.render(tmp / f"{len(cuadros)}.png")))
    comun.componer_hoja(titulo, cuadros, revision, comun.RAIZ / f"docs/arte/revisiones/{P['id']}.jpg")


def main(P, titulo, vistas):
    P["anclajes_dict"] = {n: p for n, p, _ in P["anclajes"]}
    comun.escena_vacia()
    m = construir(P)
    revision = revisar(m)
    ok = comun.imprimir_revision(P["id"], revision)
    comun.guardar_blend(comun.RAIZ / f"arte/fuentes/{FAMILIA}/{P['id']}.blend")
    comun.exportar_glb([m["raiz"]] + m["visibles"] + m["colisiones"] + m["puntos"] + m["puntos_bahia"],
                       comun.RAIZ / f"godot/modelos/{FAMILIA}/{P['id']}.glb")
    if "--sin-hoja" not in sys.argv:
        hoja_revision(m, revision, titulo, vistas)
    if not ok:
        sys.exit(1)
