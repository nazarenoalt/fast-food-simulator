"""Construcción común de las alacenas bajo mesada (`alacena_puertas`, `alacena_cajones`,
`alacena_abierta`, `alacena_mixta`).

Pedido: un depósito de metal que se **encastra** debajo de la mesada de los carritos, del lado
del vendedor, y forma parte del carrito (como los muebles bajo mesada de acero de los food
trucks). Cada base de carrito tiene huecos de medida estándar, las **bahías**
(`_base_carrito.py`), y todas las alacenas miden lo mismo: cualquier alacena entra en
cualquier bahía de cualquier carrito (guía 5.2).

Medidas (ejes de Godot: X ancho, Y alto, Z profundidad; la boca de la bahía mira al vendedor,
−Z, y el hueco se mete hacia el cliente, +Z):

    BAHIA (hueco del carrito)  0,58 × 0,62 × 0,50   (alto = del piso de la bahía a la mesada)
    CAJA de la alacena         0,57 × 0,61 × 0,49   (5 mm de juego a los costados, 1 cm
                                                      arriba y 1 cm atrás: no se pelea con
                                                      las paredes del hueco)
    MARCO de acero             0,62 × 0,615 × 0,015 (afuera de la cara del vendedor: tapa
                                                      2 cm de cada lado del hueco, así no se
                                                      ven las juntas)

    La profundidad (0,49 + marco) entra en la barra chica, que mide 0,70 de fondo.

Origen (= `punto_bahia_<n>` del carrito): **centro de la boca, a nivel del piso de la
bahía**, en el plano de la cara del vendedor. La caja va de Z = 0 a Z = +0,49 (hacia adentro
del carrito) y el marco, las puertas y los tiradores quedan en Z < 0 (afuera). Se eligió la
boca y no el centro de la caja porque los carritos tienen profundidades distintas (0,7 / 0,8
/ 1,2 m) pero la boca siempre está en la cara del vendedor: así el anclaje se mide igual en
todos. La alacena se modela ya mirando al vendedor (puertas hacia −Z, como los controles de
los equipos, guía 5.3): el anclaje `bahia_<n>` no necesita giro.

Diseño: caja de acero (por fuera, acero con bisel; por dentro, forro de acero con el fondo en
M_MetalOscuro, que da profundidad), marco de acero soldado (4 barras, la junta se ve) y lo
que cambia en cada variante:

    puertas  2 puertas batientes con tirador vertical y un estante con pestaña adelante.
    cajones  3 cajones con tirador corrido.
    abierta  sin puertas: 2 estantes con pestaña a la vista.
    mixta    1 puerta (con estante) y una columna de 3 cajones, separadas por un montante y
             un tabique.

Objetos (hijos del Empty raíz `<id>`):
    <id>_cuerpo         caja, forro, marco, estantes y tabique (Acero, MetalOscuro).
    pieza_puerta_<n>    cada puerta, con su tirador (Acero, PlasticoNegro). Origen en la
                        bisagra: canto de afuera, cara de adelante, abajo. Abre girando sobre
                        Y: la de bisagra en −X con ángulo positivo, la de bisagra en +X con
                        ángulo negativo (hasta ~100°).
    pieza_cajon_<n>     cada cajón (frente, caja abierta arriba y tirador). Origen en el centro
                        del frente (cara de afuera). Abre deslizando hacia −Z (hasta 0,32 m).
                        Numerados de arriba hacia abajo.
    punto_lugar_<n>     lugares de depósito, apoyados en el piso, en los estantes o en el piso
                        de cada cajón (los de los cajones son hijos del cajón: se mueven con
                        él). Una bolsa de 12 panes (0,19 × 0,11 × 0,43 con el nudo) entra en
                        cada uno, con el nudo hacia la puerta.
    <id>-colonly        caja, estantes y tabique como cajas simples (no un bloque macizo: los
                        lugares quedan libres para que entren los paquetes). Puertas y cajones
                        sin colisión (se mueven; si hace falta, la arma el código).
"""
import math
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402  (antes que bmesh)
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

import comun  # noqa: E402
import piezas  # noqa: E402
from piezas import g2b  # noqa: E402

FAMILIA = "accesorios"
PRESUPUESTO = 1000  # accesorios medianos (guía 3.1)
MATERIALES = ("M_Acero", "M_PlasticoNegro", "M_MetalOscuro")
ACERO, NEGRO, OSCURO = range(3)

# ── Medida estándar (la usa también _base_carrito.py) ──────────────────
BAHIA = (0.58, 0.62, 0.50)          # hueco del carrito: ancho, alto (piso → mesada), fondo
CAJA = (0.57, 0.61, 0.49)           # caja de la alacena
MARCO = (0.62, 0.615, 0.015)        # marco de afuera (ancho, alto, espesor)
PARED = 0.012                       # paredes de la caja
LUZ_X = 0.27                        # mitad del ancho de la abertura del marco
LUZ_Y = (0.035, 0.58)               # abajo / arriba de la abertura
JUEGO = 0.003                       # entre puertas / cajones y el marco
FRENTE = 0.02                       # espesor de puertas y frentes de cajón
Z_FRENTE = -0.018                   # cara de afuera de puertas y frentes (3 mm delante del marco)
SALE_TIRADOR = 0.03                 # cuánto sale el tirador de las puertas
SALE_CORRIDO = 0.022                # cuánto sale el tirador corrido de los cajones
EPS = 0.001                         # encastre entre piezas (evita vértices que coinciden)

# Interior de la caja (Godot).
IN_X = CAJA[0] / 2 - PARED          # 0,273
IN_Y = (PARED, CAJA[1] - PARED)     # 0,012 … 0,598
IN_Z = CAJA[2] - PARED              # 0,478 (cara de adentro del fondo)

# Estantes de chapa (con pestaña adelante).
ESTANTE_ESP = 0.015
ESTANTE_Z = (0.025, 0.475)

# Cajones.
CAJON_PARED = 0.008
CAJON_Z = (FRENTE + Z_FRENTE, 0.462)    # de la cara de atrás del frente al fondo de la caja
SALIDA_CAJON = 0.32

# Bloques de godot/data/bloques.ron (con el origen en el centro de la base del cuerpo).
BOLSA = {"x": 0.19, "y": 0.108, "z": (-0.246, 0.183)}       # bolsa de 12 panes, nudo hacia −Z
BANDEJA = {"x": 0.172, "y": 0.06, "z": (-0.084, 0.084)}     # bandeja de 12 salchichas
Z_LUGAR = 0.27          # centro de los lugares sobre piso y estantes
Z_LUGAR_CAJON = 0.265   # centro de los lugares en los cajones

VARIANTES = {
    "puertas": "2 puertas y estante",
    "cajones": "3 cajones",
    "abierta": "abierta, 2 estantes",
    "mixta": "puerta + 3 cajones",
}


# ── Armado ─────────────────────────────────────────────────────────────

class Armado:
    """Junta las cajas sólidas (en Godot, alacena cerrada) para los chequeos de lugares."""

    def __init__(self):
        self.solidos = []   # (mín, máx, etiqueta)

    def caja(self, bm, medidas, centro, mat, bisel, etiqueta="fijo", solido=True, **kw):
        caras = piezas.caja(bm, medidas, centro, mat=mat, bisel=bisel, **kw)
        if solido:
            c, m = Vector(centro), Vector(medidas) / 2
            self.solidos.append((c - m, c + m, etiqueta))
        return caras


def borrar_cara(bm, caras, normal_godot):
    """Borra la cara principal de una caja recién hecha que mira hacia normal_godot (queda
    tapada por otra pieza y nunca se ve, guía 3.6)."""
    n = g2b(normal_godot)
    fuera = []
    for f in caras:
        if f.is_valid:
            f.normal_update()
            if f.normal.dot(n) > 0.999:
                fuera.append(f)
    bmesh.ops.delete(bm, geom=fuera, context="FACES_ONLY")


def objeto_en(nombre, bm, materiales, origen_godot):
    """Termina el bmesh y deja el origen del objeto en origen_godot (sin mover la malla)."""
    bmesh.ops.translate(bm, vec=-g2b(origen_godot), verts=bm.verts)
    obj = piezas.terminar(nombre, bm, materiales)
    obj.location = g2b(origen_godot)
    return obj


def caja_hueca(bm, medidas, centro, pared, abierta, mat, bisel, mat_fondo=None):
    """Caja de chapa abierta de un lado (Godot): por fuera con bisel, por dentro sin bisel,
    unidas por un borde plano en la boca. Queda cerrada (sin bordes sueltos), así las normales
    del forro miran solas hacia adentro. abierta = "-z" (la caja de la alacena) o "+y" (los
    cajones). mat_fondo = material de la cara de adentro opuesta a la boca."""
    eje, signo = {"-z": (2, -1), "+y": (1, 1)}[abierta]
    normal = [0, 0, 0]
    normal[eje] = signo
    afuera = piezas.caja(bm, medidas, centro, mat=mat, bisel=bisel)
    # Adentro: `pared` menos por lado, salvo en la boca (llega al mismo plano que afuera).
    med_in = [m - 2 * pared for m in medidas]
    cen_in = list(centro)
    med_in[eje] = medidas[eje] - pared
    cen_in[eje] = centro[eje] + signo * pared / 2
    adentro = piezas.caja(bm, tuple(med_in), tuple(cen_in), mat=mat)
    n = g2b(normal)
    bocas = []
    for caras in (afuera, adentro):
        for f in caras:
            f.normal_update()
        boca = next(f for f in caras if f.normal.dot(n) > 0.999)
        bocas.append(list(boca.verts))
        if mat_fondo is not None and caras is adentro:
            fondo = next(f for f in caras if f.normal.dot(n) < -0.999)
            fondo.material_index = mat_fondo
        bmesh.ops.delete(bm, geom=[boca], context="FACES_ONLY")
    # Borde plano de la boca: cada esquina de afuera con la de adentro del mismo lado, en orden
    # alrededor del centro (bridge_loops las cruza).
    c = g2b(centro)
    ejes = [i for i in range(3) if abs(n[i]) < 0.5]

    def angulo(v):
        return math.atan2(v.co[ejes[1]] - c[ejes[1]], v.co[ejes[0]] - c[ejes[0]])
    fuera, dentro = (sorted(vs, key=angulo) for vs in bocas)
    for k in range(4):
        f = bm.faces.new((fuera[k], fuera[(k + 1) % 4], dentro[(k + 1) % 4], dentro[k]))
        f.material_index = mat


def caja_y_marco(a, bm, montante=False):
    """La caja (chapa de acero por fuera y por dentro, fondo oscuro) y el marco de afuera."""
    w, h, d = CAJA
    caja_hueca(bm, CAJA, (0, h / 2, d / 2), PARED, "-z", ACERO, 0.005, mat_fondo=OSCURO)
    # Paredes como sólidos (para los chequeos y la colisión).
    a.solidos += [
        (Vector((-w / 2, 0, 0)), Vector((w / 2, IN_Y[0], d)), "fijo"),
        (Vector((-w / 2, IN_Y[1], 0)), Vector((w / 2, h, d)), "fijo"),
        (Vector((-w / 2, 0, 0)), Vector((-IN_X, h, d)), "fijo"),
        (Vector((IN_X, 0, 0)), Vector((w / 2, h, d)), "fijo"),
        (Vector((-w / 2, 0, IN_Z)), Vector((w / 2, h, d)), "fijo"),
    ]
    # Marco de afuera: travesaños arriba y abajo, parantes entre ellos (encastrados 1 mm).
    mw, mh, me = MARCO
    zc = -me / 2
    a.caja(bm, (mw, LUZ_Y[0], me), (0, LUZ_Y[0] / 2, zc), ACERO, 0.004, sin_abajo=True)
    a.caja(bm, (mw, mh - LUZ_Y[1], me), (0, (mh + LUZ_Y[1]) / 2, zc), ACERO, 0.004)
    alto = LUZ_Y[1] - LUZ_Y[0] + 2 * EPS
    yc = (LUZ_Y[0] + LUZ_Y[1]) / 2
    for sx in (-1, 1):
        a.caja(bm, (mw / 2 - LUZ_X, alto, me), (sx * (mw / 2 + LUZ_X) / 2, yc, zc), ACERO, 0.0035)
    if montante:  # mixta: montante al medio (puerta | cajones) y tabique adentro
        a.caja(bm, (0.02, alto, me), (0, yc, zc), ACERO, 0.0035)
        # El tabique toca piso, techo y fondo, y su canto de adelante queda detrás del
        # montante: ninguna arista se ve, va sin bisel.
        a.caja(bm, (PARED, IN_Y[1] - IN_Y[0] + 2 * EPS, IN_Z + EPS),
               (0, (IN_Y[0] + IN_Y[1]) / 2, (IN_Z - EPS) / 2), ACERO, 0.0)


def estante(a, bm, x0, x1, y_arriba):
    """Estante de chapa de acero con pestaña doblada adelante. y_arriba = cara de apoyo."""
    xc, ancho = (x0 + x1) / 2, x1 - x0
    zc = (ESTANTE_Z[0] + ESTANTE_Z[1]) / 2
    a.caja(bm, (ancho, ESTANTE_ESP, ESTANTE_Z[1] - ESTANTE_Z[0]),
           (xc, y_arriba - ESTANTE_ESP / 2, zc), ACERO, 0.004)
    a.caja(bm, (ancho - 0.004, 0.03, 0.012), (xc, y_arriba - 0.015 - EPS, ESTANTE_Z[0] + 0.006),
           ACERO, 0.003)


def tirador(bm, centro, largo, vertical):
    """Tirador de barra negra sobre dos patitas (Godot). centro = centro de la barra en X/Y,
    sobre la cara de la puerta."""
    x, y = centro
    pata = SALE_TIRADOR - 0.012
    barra = (0.014, largo, 0.012) if vertical else (largo, 0.016, 0.012)
    piezas.caja(bm, barra, (x, y, Z_FRENTE - pata - 0.006), mat=NEGRO, bisel=0.003)
    sep = largo / 2 - 0.02
    for s in (-1, 1):
        px, py = (x, y + s * sep) if vertical else (x + s * sep, y)
        piezas.caja(bm, (0.01, 0.01, pata + EPS), (px, py, Z_FRENTE - pata / 2), mat=NEGRO)


def puerta(a, nombre, x0, x1, bisagra, mats):
    """Puerta batiente (x0 < x1 en Godot). bisagra = −1 (en x0) o +1 (en x1)."""
    bm = bmesh.new()
    y0, y1 = LUZ_Y[0] + JUEGO, LUZ_Y[1] - JUEGO
    a.caja(bm, (x1 - x0, y1 - y0, FRENTE), ((x0 + x1) / 2, (y0 + y1) / 2, Z_FRENTE + FRENTE / 2),
           ACERO, 0.005, etiqueta=nombre)
    xt = x1 - 0.045 if bisagra < 0 else x0 + 0.045
    tirador(bm, (xt, y1 - 0.13), 0.16, vertical=True)
    xb = x0 if bisagra < 0 else x1
    return objeto_en(nombre, bm, mats, (xb, y0, Z_FRENTE))


def cajon(a, nombre, x0, x1, y0, y1, mats):
    """Cajón: frente (x0..x1, y0..y1) con tirador corrido y caja abierta arriba detrás."""
    bm = bmesh.new()
    xc = (x0 + x1) / 2
    a.caja(bm, (x1 - x0, y1 - y0, FRENTE), (xc, (y0 + y1) / 2, Z_FRENTE + FRENTE / 2),
           ACERO, 0.005, etiqueta=nombre)
    # Tirador corrido: una barra negra a lo largo del canto de arriba del frente.
    largo = min(0.40, (x1 - x0) - 0.06)
    piezas.caja(bm, (largo, 0.022, SALE_CORRIDO + EPS),
                (xc, y1 - 0.011 - 0.006, Z_FRENTE - (SALE_CORRIDO - EPS) / 2), mat=NEGRO,
                bisel=0.004)
    # Caja de chapa abierta arriba, detrás del frente.
    e = CAJON_PARED
    bx0, bx1 = x0 + 0.012, x1 - 0.012
    yb, hb = y0 + 0.012, (y1 - y0) - 0.03
    z0, z1 = CAJON_Z
    caja_hueca(bm, (bx1 - bx0, hb, z1 - z0), ((bx0 + bx1) / 2, yb + hb / 2, (z0 + z1) / 2), e, "+y",
               ACERO, 0.002)
    for p0, p1 in (((bx0, yb, z0), (bx0 + e, yb + hb, z1)), ((bx1 - e, yb, z0), (bx1, yb + hb, z1)),
                   ((bx0, yb, z0), (bx1, yb + hb, z0 + e)), ((bx0, yb, z1 - e), (bx1, yb + hb, z1)),
                   ((bx0, yb, z0), (bx1, yb + e, z1))):
        a.solidos.append((Vector(p0), Vector(p1), nombre))
    obj = objeto_en(nombre, bm, mats, (xc, (y0 + y1) / 2, Z_FRENTE))
    return obj, (bx0 + e, bx1 - e), yb + e


def frentes_cajones(n, y0=LUZ_Y[0], y1=LUZ_Y[1]):
    """Alturas (abajo, arriba) de n frentes en la abertura, de arriba hacia abajo."""
    h = (y1 - y0 - (n + 1) * JUEGO) / n
    return [(y0 + JUEGO + k * (h + JUEGO), y0 + JUEGO + k * (h + JUEGO) + h)
            for k in reversed(range(n))]


def construir(variante, id_alacena=None):
    """Arma la alacena. Devuelve un dict con objetos, lugares y sólidos."""
    id_alacena = id_alacena or f"alacena_{variante}"
    mats = comun.cargar_materiales(*MATERIALES)
    m_piezas = mats[:2]  # puertas y cajones: acero y plástico negro
    a = Armado()
    bm = bmesh.new()
    caja_y_marco(a, bm, montante=variante == "mixta")
    puertas, cajones, lugares = [], [], []   # lugares = (pos Godot, cajón o None)
    xl = (-IN_X + EPS, IN_X - EPS)
    if variante == "puertas":
        y_est = 0.3175
        estante(a, bm, *xl, y_est)
        puertas.append(puerta(a, "pieza_puerta_1", -LUZ_X + JUEGO, -JUEGO / 2, -1, m_piezas))
        puertas.append(puerta(a, "pieza_puerta_2", JUEGO / 2, LUZ_X - JUEGO, 1, m_piezas))
        for y in (y_est, IN_Y[0]):
            lugares += [((-0.13, y, Z_LUGAR), None), ((0.13, y, Z_LUGAR), None)]
    elif variante == "abierta":
        libre = (IN_Y[1] - IN_Y[0] - 2 * ESTANTE_ESP) / 3
        ys = [IN_Y[0] + k * (libre + ESTANTE_ESP) for k in (2, 1)]
        for y in ys:
            estante(a, bm, *xl, y)
        for y in ys + [IN_Y[0]]:
            lugares += [((-0.13, y, Z_LUGAR), None), ((0.13, y, Z_LUGAR), None)]
    elif variante == "cajones":
        for i, (y0, y1) in enumerate(frentes_cajones(3)):
            c, (bx0, bx1), piso = cajon(a, f"pieza_cajon_{i + 1}", -LUZ_X + JUEGO, LUZ_X - JUEGO,
                                        y0, y1, m_piezas)
            cajones.append(c)
            lugares += [((-0.125, piso, Z_LUGAR_CAJON), c), ((0.125, piso, Z_LUGAR_CAJON), c)]
    elif variante == "mixta":
        y_est = 0.3175
        estante(a, bm, -IN_X + EPS, -PARED / 2 - EPS, y_est)
        puertas.append(puerta(a, "pieza_puerta_1", -LUZ_X + JUEGO, -0.01 - JUEGO, -1, m_piezas))
        for y in (y_est, IN_Y[0]):
            lugares.append(((-0.14, y, Z_LUGAR), None))
        for i, (y0, y1) in enumerate(frentes_cajones(3)):
            c, (bx0, bx1), piso = cajon(a, f"pieza_cajon_{i + 1}", 0.01 + JUEGO, LUZ_X - JUEGO,
                                        y0, y1, m_piezas)
            cajones.append(c)
            lugares.append((((bx0 + bx1) / 2, piso, Z_LUGAR_CAJON), c))
    else:
        raise ValueError(variante)
    # El cuerpo no lleva plástico negro: solo acero (0) y metal oscuro (1).
    for f in bm.faces:
        if f.material_index == OSCURO:
            f.material_index = 1
    cuerpo = piezas.terminar(f"{id_alacena}_cuerpo", bm, [mats[ACERO], mats[OSCURO]])

    # Puntos de los lugares (los de los cajones, hijos del cajón).
    puntos = []
    for i, (pos, c) in enumerate(lugares):
        e = piezas.punto(f"punto_lugar_{i + 1}", pos)
        if c is not None:
            e.location = g2b(pos) - c.location
            e.parent = c
        puntos.append(e)

    col = colision(id_alacena, [s for s in a.solidos if s[2] == "fijo"])
    hijos = [cuerpo] + puertas + cajones + [col] + [p for p in puntos if p.parent is None]
    raiz = piezas.raiz(id_alacena, hijos)
    return {"id": id_alacena, "variante": variante, "raiz": raiz, "cuerpo": cuerpo,
            "puertas": puertas, "cajones": cajones, "puntos": puntos, "lugares": lugares,
            "colision": col, "solidos": a.solidos}


def colision(id_alacena, solidos):
    """`<id>-colonly` con las cajas fijas (paredes, estantes, tabique, marco) en un objeto."""
    bm = bmesh.new()
    for mn, mx, _ in solidos:
        piezas.caja(bm, tuple(mx - mn), tuple((mn + mx) / 2))
    nombre = f"{id_alacena}-colonly"
    malla = bpy.data.meshes.new(nombre)
    bm.to_mesh(malla)
    bm.free()
    obj = bpy.data.objects.new(nombre, malla)
    bpy.context.scene.collection.objects.link(obj)
    obj.display_type = "WIRE"
    obj.hide_render = True
    return obj


def visibles(m):
    return [m["cuerpo"]] + m["puertas"] + m["cajones"]


def exportables(m):
    return [m["raiz"]] + visibles(m) + [m["colision"]] + m["puntos"]


# ── Revisión ───────────────────────────────────────────────────────────

def medidas(variante):
    """Medida total (Godot) con marco, puertas y tiradores."""
    afuera = {"abierta": MARCO[2], "cajones": -Z_FRENTE + SALE_CORRIDO}.get(
        variante, -Z_FRENTE + SALE_TIRADOR)
    return (MARCO[0], MARCO[1], CAJA[2] + afuera)


def _verts_godot(objs):
    out = []
    for o in objs:
        m = o.matrix_world
        for v in o.data.vertices:
            p = m @ v.co
            out.append(Vector((p.x, p.z, -p.y)))
    return out


def chequeo_origen(m):
    """El origen va en el centro de la boca (cara del vendedor), a nivel del piso: la caja
    envolvente se corre hacia el vendedor por el marco, las puertas y los tiradores."""
    vs = _verts_godot([m["cuerpo"]])
    por_fuera = [v for v in vs if IN_X + 0.001 < abs(v.x) <= CAJA[0] / 2 + 1e-4 and v.z > -0.0015]
    marco = [v for v in vs if abs(v.x) > CAJA[0] / 2 + 0.001]  # lo que sale de la caja
    cx = (max(v.x for v in marco) + min(v.x for v in marco)) / 2
    piso = min(v.y for v in vs)
    boca = min(v.z for v in por_fuera)
    atras_marco = max(v.z for v in marco)
    ok = abs(cx) < 1e-4 and abs(piso) < 1e-4 and abs(boca) < 1e-4 and abs(atras_marco) < 1e-4
    return ok, ("Origen en el centro de la boca, a nivel del piso de la bahía (marco centrado "
                "en X = %.3f, base en Y = %.3f, la caja arranca en Z = %.3f)" % (cx, piso, boca))


def chequeo_bahia(m):
    """La caja entra en la bahía con juego y el marco tapa las juntas del hueco."""
    vs = _verts_godot([m["cuerpo"]])
    caja = [v for v in vs if v.z > 0.002]
    marco = [v for v in vs if v.z < -0.001]
    cw = max(v.x for v in caja) - min(v.x for v in caja)
    ch = max(v.y for v in caja) - min(v.y for v in caja)
    cd = max(v.z for v in caja)
    mw = max(v.x for v in marco) - min(v.x for v in marco)
    mh = max(v.y for v in marco)
    juegos = (BAHIA[0] - cw, BAHIA[1] - ch, BAHIA[2] - cd)
    ok = all(0.004 <= j <= 0.02 for j in juegos) and mw > BAHIA[0] + 0.02 and mh < BAHIA[1]
    return ok, ("Entra en la bahía %.2f × %.2f × %.2f: caja %.3f × %.3f × %.3f (juego %.0f / %.0f / "
                "%.0f mm), marco %.3f × %.3f tapa el hueco" % (
                    *BAHIA, cw, ch, cd, *(j * 1000 for j in juegos), mw, mh))


def _cruza(a0, a1, b0, b1, tol=1e-4):
    return all(a0[i] < b1[i] - tol and b0[i] < a1[i] - tol for i in range(3))


def chequeo_lugares(m):
    """Cada punto_lugar está donde dice, apoyado en algo, y una bolsa de 12 panes (la caja
    que la envuelve, con el nudo) entra sin tocar paredes, estantes ni otros cajones."""
    problemas = []
    for i, ((pos, c), e) in enumerate(zip(m["lugares"], m["puntos"])):
        p = Vector(pos)
        if (e.matrix_world.translation - g2b(pos)).length > 1e-5:
            problemas.append(f"{e.name} fuera de lugar")
        b0 = p + Vector((-BOLSA["x"] / 2, 0, BOLSA["z"][0]))
        b1 = p + Vector((BOLSA["x"] / 2, BOLSA["y"], BOLSA["z"][1]))
        if any(_cruza(b0, b1, s0, s1) for s0, s1, _ in m["solidos"]):
            problemas.append(f"la bolsa de {e.name} choca")
        if b0.z < 0.0 or b1.z > IN_Z or abs(b0.x) > IN_X or abs(b1.x) > IN_X or b1.y > IN_Y[1]:
            problemas.append(f"la bolsa de {e.name} sale de la caja")
        apoyo = any(abs(s1.y - p.y) < 1e-4 and s0.x <= p.x <= s1.x and s0.z <= p.z <= s1.z
                    for s0, s1, _ in m["solidos"])
        if not apoyo:
            problemas.append(f"{e.name} no apoya")
        if c is not None and e.parent is not c:
            problemas.append(f"{e.name} no es hijo de {c.name}")
    texto = "%d punto_lugar: entra una bolsa de 12 panes (%.2f × %.3f × %.3f con nudo) en cada uno" % (
        len(m["puntos"]), BOLSA["x"], BOLSA["y"], BOLSA["z"][1] - BOLSA["z"][0])
    return not problemas, texto + ("" if not problemas else " — " + ", ".join(problemas))


def chequeo_piezas(m):
    """Puertas con el origen en la bisagra, cajones con el origen en el centro del frente."""
    ok = True
    for p in m["puertas"]:
        xs = [v.co.x for v in p.data.vertices]
        ys = [-v.co.y for v in p.data.vertices]  # Z Godot local
        canto = min(abs(min(xs)), abs(max(xs)))
        ok &= canto < 1e-4 and abs(max(ys)) < SALE_TIRADOR + 1e-3 and min(v.co.z for v in p.data.vertices) > -1e-4
    for c in m["cajones"]:
        frente = [v for v in c.data.vertices if abs(v.co.y) < 1e-4]  # cara de afuera (Z local 0)
        if not frente:
            ok = False
            continue
        cx = (max(v.co.x for v in frente) + min(v.co.x for v in frente)) / 2
        cz = (max(v.co.z for v in frente) + min(v.co.z for v in frente)) / 2
        ok &= abs(cx) < 1e-4 and abs(cz) < 1e-4
    partes = []
    if m["puertas"]:
        partes.append(f"{len(m['puertas'])} pieza_puerta (origen en la bisagra)")
    if m["cajones"]:
        partes.append(f"{len(m['cajones'])} pieza_cajon (origen en el centro del frente)")
    return ok, "Piezas que se mueven: " + (", ".join(partes) if partes else "ninguna (abierta)")


def revisar(m):
    res = comun.revisar(visibles(m), PRESUPUESTO, medidas(m["variante"]), origen="base")
    res = [chequeo_origen(m) if t.startswith("Origen") else (ok, t) for ok, t in res]
    res.insert(1, chequeo_bahia(m))
    res.append(chequeo_piezas(m))
    res.append(chequeo_lugares(m))
    return res


# ── Hoja de revisión ───────────────────────────────────────────────────

def copia(obj, nombre=None):
    c = obj.copy()
    c.name = nombre or f"ref_{obj.name}"
    c.parent = None
    c.matrix_world = obj.matrix_world.copy()
    bpy.context.scene.collection.objects.link(c)
    return c


def abrir(m):
    """Copias (solo para la foto) con las puertas y los cajones abiertos. Devuelve
    (objetos, desplazamiento de cada cajón en Godot)."""
    objs, salida = [m["cuerpo"]], {}
    for p in m["puertas"]:
        c = copia(p)
        # Bisagra en −X (la puerta se extiende hacia +X): abre con ángulo positivo.
        c.rotation_euler.z = math.radians(110 if max(v.co.x for v in p.data.vertices) > 0.01 else -110)
        objs.append(c)
    for i, k in enumerate(m["cajones"]):
        c = copia(k)
        d = SALIDA_CAJON - 0.1 * i
        c.location = k.matrix_world.translation + g2b((0, 0, -d))
        salida[k.name] = d
        objs.append(c)
    return objs, salida


def stock(m, salida, desplazamiento=Vector()):
    """Bolsas de panes (con los panes cerrados adentro) y bandejas de salchichas en los
    lugares, para la foto."""
    import bolsa_panes_12
    import caja_salchichas_12
    import pan_pancho_cerrado
    import salchicha
    objs = []
    for i, ((pos, c), e) in enumerate(zip(m["lugares"], m["puntos"])):
        p = Vector(pos)
        if c is not None:
            p += Vector((0, 0, -salida.get(c.name, 0.0)))
        base = g2b(p) + desplazamiento
        if i % 3 == 2:
            b = caja_salchichas_12.construir()
            b.location = base
            objs.append(b)
            for j, q in enumerate(caja_salchichas_12.posiciones_unidades()):
                s = salchicha.construir(f"ref_salchicha_{i}_{j}")
                s.location = base + g2b(q)
                objs.append(s)
        else:
            b = bolsa_panes_12.construir()
            b.location = base
            objs.append(b)
            for j, q in enumerate(bolsa_panes_12.posiciones_panes()):
                pan = pan_pancho_cerrado.construir(f"ref_pan_{i}_{j}")
                pan.location = base + g2b(q)
                objs.append(pan)
    return objs


def hoja_revision(m, revision):
    import _base_carrito as base
    comun.preparar_revision()
    v = visibles(m)
    abiertos, salida = abrir(m)
    lleno = abiertos + stock(m, salida)
    # Puesta en la bahía 1 de la barra chica (otra copia de la alacena, armada de nuevo).
    carro = base.construir("barra_chica")
    otra = construir(m["variante"])
    bpy.context.view_layer.update()
    bahia = next(e for e in carro["puntos"] if e.name == "punto_bahia_1")
    otra["raiz"].location = bahia.matrix_world.translation
    bpy.context.view_layer.update()
    en_carro = [carro["pintura"], carro["estructura"]] + carro["tapas"][1:] + visibles(otra)
    for o in [carro["tapas"][0], otra["colision"]] + carro["colisiones"]:
        o.hide_render = True
    cuadros = base.sacar_fotos([
        ("Frente: lado del vendedor (el que se ve) · día", v, "atras", "dia"),
        ("3/4 lado del vendedor · día", v, "vendedor_derecha", "dia"),
        ("Abierta (copias solo para la foto) · día", abiertos, "vendedor_derecha", "dia")
        if m["puertas"] or m["cajones"] else
        ("Adentro: piso y 2 estantes · día", v, "vendedor_frente", "dia"),
        ("Con stock: bolsas de 12 panes y bandejas · día", lleno,
         "vendedor_alto" if m["cajones"] else "vendedor_frente", "dia"),
        ("En la bahía 1 de la barra chica · día", en_carro, "vendedor", "dia"),
        ("3/4 lado del vendedor · atardecer", v, "vendedor_derecha", "atardecer"),
    ])
    mw, mh, md = medidas(m["variante"])
    comun.componer_hoja(
        f"{m['id']} · {mw:.2f} × {mh:.3f} × {md:.3f} m · {VARIANTES[m['variante']]} · "
        f"bahía {BAHIA[0]:.2f} × {BAHIA[1]:.2f} × {BAHIA[2]:.2f}".replace(".", ","),
        cuadros, revision, comun.RAIZ / f"docs/arte/revisiones/{m['id']}.jpg",
    )


def main(variante):
    comun.escena_vacia()
    m = construir(variante)
    revision = revisar(m)
    ok = comun.imprimir_revision(m["id"], revision)
    comun.guardar_blend(comun.RAIZ / f"arte/fuentes/{FAMILIA}/{m['id']}.blend")
    comun.exportar_glb(exportables(m), comun.RAIZ / f"godot/modelos/{FAMILIA}/{m['id']}.glb")
    if "--sin-hoja" not in sys.argv:
        hoja_revision(m, revision)
    if not ok:
        sys.exit(1)
