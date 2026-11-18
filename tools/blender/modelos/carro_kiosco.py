"""Modelo: carro kiosco (id `carro_kiosco`, familia `carritos`; todavía sin `.ron`: medidas y
anclajes propuestos acá para la spec).

Genera:
    godot/modelos/carritos/texturas/carro_kiosco.png   ← el cartel corrido (guía 4.5)
    arte/fuentes/carritos/carro_kiosco.blend
    godot/modelos/carritos/carro_kiosco.glb
    docs/arte/revisiones/carro_kiosco.jpg

Uso:
    python tools/blender/modelos/carro_kiosco.py [--sin-hoja]

El carro de chorizos y panchos de esquina rioplatense: un kiosco de acero inoxidable sobre un
chasis bajo con ruedas chicas y lanza de enganche. En ejes de Godot (cliente = +Z):
    - Abajo, una pollera pintada (`pieza_pintura`, 0,10 a 0,40 m) con los pasarruedas de un
      tándem de ruedas chicas (radio 0,15), y arriba la chapa abollonada: paneles capitoné de
      acero (almohadones con las aristas en cruz) en una grilla de 2 filas, en los cuatro lados
      (atrás, cortada por la puerta).
    - Del lado del cliente, el mostrador de acero a 1,05 m que sale 0,23 m afuera (la repisa
      donde se entrega) y, encima, la vitrina vidriada de punta a punta (hasta 2,15 m), con
      marco de acero: dos vitrinas de exhibición en las puntas (vidrio adelante y del lado de
      la ventana, dos estantes de acero, `punto_lugar_1..12` para el stock que pone el juego) y
      en el medio la ventana de atención abierta (1,67 × 0,88 m) con un paño fijo arriba. Los
      dos costados también son vidriados arriba del mostrador.
    - Techo plano de acero que sobresale 0,20 m alrededor y, encima, el cartel luminoso
      corrido todo alrededor (`pieza_cartel`, 0,42 m de alto, de 2,20 a 2,62 m): banda amarilla
      con letras rojas ("CHORIZOS / PANCHOS / HAMBURGUESAS", "WELCOME", "CHORIPÁN") y paneles
      plateados con el logo del puesto inventado, "Lo de Tito" (óvalo rojo con letras
      amarillas). Es una sola imagen `T_carro_kiosco` (1024 × 512, colores de la paleta) con un
      renglón por lado. De noche el juego le suma emisión a `pieza_cartel` (la imagen es
      opaca, como un cartel de caja de luz); `punto_luz` adelante, bajo el alero.
    - Tubos de luz (`pieza_luces`, M_LuzCalida): uno bajo el alero, sobre la repisa, y otro
      en el techo de adentro, sobre el pasillo.
    - Lanza de enganche en A (pintada) por −X, con el acople y la rueda de apoyo; largueros
      del chasis bajo el piso.

Piso del vendedor: a 0,15 m de la calle (casi a nivel, como un kiosco). Se eligió así para que
el mostrador del cliente quede a 1,05 m (lo que pide la foto: la repisa a la altura de la
cintura) y el vendedor trabaje a 0,90 m del piso, alto de mesada de cocina; con el piso
elevado del food truck (0,50) el mostrador quedaría a 1,45, como una ventanilla. Por eso las
ruedas son chicas y van en pasarruedas (bajo los muebles de los dos lados) y no hace falta
escalón: se sube los 15 cm por la puerta de atrás.

Adentro: mesada de la vitrina (de z 0,24 a la repisa de afuera) con 4 bahías para las
alacenas debajo (_alacena.BAHIA, boca hacia el vendedor a z 0,27), pasillo de 0,74 m y mesada
de atrás (mueble con puertas) contra la pared del vendedor, hasta la puerta (`pieza_puerta`,
de acero, en la punta +X de la pared de atrás). Techo de adentro a 2,15 (2,00 m libres).

Presupuesto: 5.000 triángulos, como el food truck (base grande con interior). Materiales (6 +
cartel): M_PinturaCarrito (pollera, chasis y lanza), M_Acero, M_Vidrio, M_Goma (ruedas, piso,
pasarruedas), M_PlasticoNegro (tiradores, acople), M_LuzCalida (tubos) y T_carro_kiosco.

Medidas propuestas para `carro_kiosco.ron` (el largo en X, la vitrina mirando al cliente):
    ancho 3,20, profundidad 1,70 (la pollera pintada), alto total 2,62 (arriba del cartel).
    alto_mostrador 1,05 (mesada y repisa de afuera; piso de adentro a 0,15).
    Techo y cartel: 3,60 × 2,10 (sobresalen 0,20). De punta a punta, 4,23 (la lanza sale 0,83 por −X).
    Ventana de atención de x −0,835 a 0,835, de 1,05 a 1,93. Puerta de x 0,82 a 1,52, hasta 2,05.
Anclajes propuestos (pos en Godot, desde el centro de la pollera a nivel de la calle):
    mostrador_izq (−0,57; 1,05; 0,55)    [Cocina, Equipamiento]          frente a la ventana
    mostrador_centro (0,0; 1,05; 0,55)   [Cocina, Equipamiento, Decoracion]
    mostrador_der (0,57; 1,05; 0,55)     [Cocina, Equipamiento, Decoracion]
    atras_izq (−1,05; 1,05; −0,64)       [Cocina, Equipamiento, Deposito]  mesada de atrás
    atras_der (0,15; 1,05; −0,64)        [Cocina, Equipamiento, Deposito]
    frente (0,0; 0,25; 0,89)             [Telon, Decoracion]  el telón queda bajo la repisa
    lateral_der (1,60; 0,0; 0,0)         [Porche]  el `porche_nylon` (accesorio aparte)
    luz_1 (−1,20; 2,15; 0,97), luz_2 (1,20; 2,15; 0,97)  [Luz]  bajo el alero de adelante
    entrega (0,0; 1,05; 0,97)    en la repisa de afuera, en el medio de la ventana
    fila (0,0; 0,0; 1,50)        primer lugar, frente a la ventana (sigue hacia +X)
    entrada (1,17; 0,0; −1,35)   afuera, frente a la puerta
    bahia_1..4: los punto_bahia_<n> (boca a z 0,27, piso de la bahía a 0,39).
    lugar_1..12: punto_lugar_<n> en las vitrinas (3 niveles × 2 lugares × 2 vitrinas, de −X a
    +X y de abajo hacia arriba: mesada 1,05, estantes 1,44 y 1,78; z 0,665).
Sin `sombra`, `techo` ni `cartel`: ya tiene techo y cartel.

Objetos (bajo el Empty raíz `carro_kiosco`):
    pieza_pintura, carro_kiosco_estructura, pieza_cartel (T_ + M_Acero en los cantos),
    pieza_luces, pieza_tapa_bahia_<n> + punto_bahia_<n>, pieza_puerta (origen en la bisagra,
    gira en Y: positivo abre hacia afuera, ≈ 100°) con su carro_kiosco_puerta-colonly,
    carro_kiosco-colonly (cajas: piso, paredes con la ventana y la puerta libres, vitrinas,
    estantes, mesadas y muebles con las bahías libres, techo con el cartel y la lanza),
    punto_<anclaje>, punto_entrega, punto_fila, punto_entrada, punto_luz y punto_lugar_<n>.
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
from mathutils.bvhtree import BVHTree  # noqa: E402

import comun  # noqa: E402
import piezas  # noqa: E402
import _alacena  # noqa: E402
import _base_carrito as base  # noqa: E402
import _plaza as plaza  # noqa: E402
import _rodante as r  # noqa: E402
from piezas import g2b  # noqa: E402
from pizarra_precios import (color_paleta, fuente, guardar_textura, lienzo,  # noqa: E402
                             material_cartel, revisar_cartel)

ID = "carro_kiosco"
FAMILIA = "carritos"
PRESUPUESTO = 5000
MATERIALES = ("M_PinturaCarrito", "M_Acero", "M_Vidrio", "M_Goma", "M_PlasticoNegro", "M_LuzCalida")
PINT, ACERO, VIDRIO, GOMA, NEGRO, LUZ = range(6)
EPS = 0.001
BAHIA_W, BAHIA_H, BAHIA_D = _alacena.BAHIA

# Cuerpo (Godot): pollera de x ±1,60 y z ±0,85; paredes de arriba 3 mm adentro.
XH, ZH = 1.60, 0.85
XI, ZI = 1.56, 0.81                 # cara de adentro de las paredes
XA, ZA = 1.597, 0.847               # cara de afuera de la chapa de arriba (la pollera sobresale)
Y_CAJA, Y_POLLERA = 0.10, 0.40      # abajo de la caja / arriba de la pollera pintada
YP = 0.15                           # piso de adentro
YM, ALTO_MESADA = 1.05, 0.04        # mostrador
Y1 = YM - ALTO_MESADA               # abajo de la mesada
Y_BAHIA = Y1 - BAHIA_H              # piso de las bahías (0,39)
Y_TECHO, Y_LOSA, Y_CARTEL = 2.15, 2.20, 2.62
VUELO = 0.20
Z_BOCA, Z_FONDO = 0.27, 0.27 + BAHIA_D
Z_RUEDA_ADENTRO = 0.62              # cara de adentro de los pasarruedas
ARCO_X, ARCO_Y = 0.40, 0.34
EJES_X, R_RUEDA, ANCHO_RUEDA, Z_RUEDA = (-0.20, 0.20), 0.15, 0.09, 0.745
VX = 0.86                           # parantes de la ventana (centro)
Y_VENTANA = 1.93                    # arriba de la ventana de atención
VITRINAS = ((-1.555, -0.885), (0.885, 1.555))
Z_VITRINA = 0.52                    # fondo de las vitrinas (del lado del vendedor)
ESTANTES = (1.44, 1.78)             # arriba de los estantes
MESADA_ATRAS = (-1.56 + EPS, 0.72)
Z_ATRAS = -0.47                     # cara de la mesada de atrás
PUERTA = (0.82, 1.52, 2.05)
FILAS_PANELES = ((0.42, 0.70), (0.72, 1.00))
X_ACOPLE = -2.43

ANCLAJES = [
    ("mostrador_izq", (-0.57, YM, 0.55), 0.0),
    ("mostrador_centro", (0.0, YM, 0.55), 0.0),
    ("mostrador_der", (0.57, YM, 0.55), 0.0),
    ("atras_izq", (-1.05, YM, -0.64), 0.0),
    ("atras_der", (0.15, YM, -0.64), 0.0),
    ("frente", (0.0, 0.25, 0.89), 0.0),
    ("lateral_der", (XH, 0.0, 0.0), 0.0),
    ("luz_1", (-1.20, Y_TECHO, 0.97), 0.0),
    ("luz_2", (1.20, Y_TECHO, 0.97), 0.0),
]
ENTREGA, FILA, ENTRADA = (0.0, YM, 0.97), (0.0, 0.0, 1.50), (1.17, 0.0, -1.35)
LUZ_PUNTO = (0.0, Y_TECHO - 0.05, 0.97)
TEXTURA = comun.RAIZ / f"godot/modelos/{FAMILIA}/texturas/{ID}.png"


def lugares():
    """punto_lugar_<n>: 2 por nivel en cada vitrina (de −X a +X, de abajo hacia arriba)."""
    pts = []
    for xa, xb in VITRINAS:
        w = (xb - xa) / 2
        for y in (YM,) + ESTANTES:
            for k in range(2):
                pts.append((round(xa + w * (k + 0.5), 4), y, round((Z_VITRINA + ZI) / 2 + 0.0, 4)))
    return pts


# ── Cartel (guía 4.5) ──────────────────────────────────────────────────

ATLAS = (1024, 512)
PX_M = ATLAS[0] / (2 * (XH + VUELO))            # 284,4 px por metro
ALTO_PX = round((Y_CARTEL - Y_LOSA) * PX_M)     # 119 px
# Renglón de cada cara del cartel: (x0, y0, x1, y1) en píxeles de la imagen.
RENGLONES = {
    "frente": (0, 0, ATLAS[0], ALTO_PX),
    "atras": (0, 128, ATLAS[0], 128 + ALTO_PX),
    "izq": (0, 256, round(2 * (ZH + VUELO) * PX_M), 256 + ALTO_PX),
    "der": (0, 384, round(2 * (ZH + VUELO) * PX_M), 384 + ALTO_PX),
}


def _letras(dib, centro, texto, tam, rojo, crema, sombra=2):
    f = fuente(tam)
    for dx, dy, color in ((sombra, sombra, crema), (0, 0, rojo)):
        dib.text((centro[0] + dx, centro[1] + dy), texto, font=f, fill=color, anchor="mm")


def _panel_amarillo(dib, caja, lineas, tam):
    x0, y0, x1, y1 = caja
    dib.rectangle(caja, fill=color_paleta("M_Amarillo"))
    rojo, crema = color_paleta("M_RojoAcento"), color_paleta("M_BlancoCrema")
    dib.rectangle((x0 + 4, y0 + 4, x1 - 5, y1 - 5), outline=rojo, width=2)
    paso = (y1 - y0) / len(lineas)
    tam = min(tam, round(paso * 0.82))
    while max(dib.textlength(t, font=fuente(tam)) for t in lineas) > (x1 - x0) * 0.86:
        tam -= 1                                     # que entre la palabra más larga
    for i, t in enumerate(lineas):
        _letras(dib, ((x0 + x1) / 2, y0 + paso * (i + 0.5) + 1), t, tam, rojo, crema)


def _panel_logo(dib, caja):
    """Panel plateado con el óvalo rojo del puesto inventado ("Lo de Tito")."""
    x0, y0, x1, y1 = caja
    dib.rectangle(caja, fill=color_paleta("M_Acero"))
    azul, crema = color_paleta("M_AzulAcento"), color_paleta("M_BlancoCrema")
    rojo, amarillo = color_paleta("M_RojoAcento"), color_paleta("M_Amarillo")
    m = 10
    dib.ellipse((x0 + m, y0 + m, x1 - m, y1 - m), fill=azul)
    dib.ellipse((x0 + m + 4, y0 + m + 4, x1 - m - 4, y1 - m - 4), fill=crema)
    dib.ellipse((x0 + m + 8, y0 + m + 8, x1 - m - 8, y1 - m - 8), fill=rojo)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    alto = y1 - y0
    f1, f2 = fuente(round(alto * 0.20)), fuente(round(alto * 0.36))
    dib.text((cx, cy - alto * 0.17), "Lo de", font=f1, fill=crema, anchor="mm")
    dib.text((cx + 2, cy + alto * 0.12 + 2), "TITO", font=f2, fill=azul, anchor="mm")
    dib.text((cx, cy + alto * 0.12), "TITO", font=f2, fill=amarillo, anchor="mm")


def dibujar_textura():
    img, dib = lienzo(ATLAS, "M_Acero")
    acero = color_paleta("M_Acero")

    def partes(renglon, anchos, contenidos):
        x0, y0, x1, y1 = RENGLONES[renglon]
        total = sum(anchos)
        x = x0
        for a, c in zip(anchos, contenidos):
            xb = x + (x1 - x0) * a / total
            caja = (round(x), y0, round(xb) - 1, y1 - 1)
            if c == "logo":
                _panel_logo(dib, caja)
            else:
                _panel_amarillo(dib, caja, *c)
            dib.line((round(xb) - 1, y0, round(xb) - 1, y1), fill=acero, width=3)
            x = xb

    partes("frente", (0.9, 1.8, 0.9), ("logo", (("CHORIZOS", "PANCHOS", "HAMBURGUESAS"), 33), "logo"))
    partes("atras", (1.35, 0.9, 1.35), ((("PANCHOS", "CHORIZOS"), 44), "logo", (("HAMBURGUESAS",), 50)))
    partes("izq", (0.85, 1.25), ("logo", (("CHORIPÁN",), 62)))
    partes("der", (1.45, 0.65), ((("WELCOME",), 72), "logo"))
    guardar_textura(img, TEXTURA)


def mapear_rect(bm, cara, eje_u, eje_v, rect):
    """UV de una cara plana al rectángulo `rect` (píxeles de la imagen) del atlas."""
    uv = bm.loops.layers.uv.verify()
    W, H = ATLAS
    x0, y0, x1, y1 = rect
    u0, u1, v0, v1 = x0 / W, x1 / W, 1 - y1 / H, 1 - y0 / H
    us = [v.co.dot(eje_u) for v in cara.verts]
    vs = [v.co.dot(eje_v) for v in cara.verts]
    for b in cara.loops:
        tu = (b.vert.co.dot(eje_u) - min(us)) / (max(us) - min(us))
        tv = (b.vert.co.dot(eje_v) - min(vs)) / (max(vs) - min(vs))
        b[uv].uv = (u0 + (u1 - u0) * tu, v0 + (v1 - v0) * tv)


def cartel(m_cartel, m_acero):
    """Caja de luz corrida alrededor del techo: anillo de 12 cm con la imagen afuera."""
    bm = bmesh.new()
    ex, ez = XH + VUELO, ZH + VUELO
    ix, iz = ex - 0.12, ez - 0.12
    y0, y1 = Y_LOSA - 0.002, Y_CARTEL
    afuera = [(ex, ez), (-ex, ez), (-ex, -ez), (ex, -ez)]
    adentro = [(ix, iz), (-ix, iz), (-ix, -iz), (ix, -iz)]
    V = {}
    for nombre, pts in (("o", afuera), ("i", adentro)):
        for y in (y0, y1):
            V[nombre, y] = [bm.verts.new(g2b((x, y, z))) for x, z in pts]
    for k in range(4):
        j = (k + 1) % 4
        bm.faces.new((V["o", y1][k], V["o", y1][j], V["i", y1][j], V["i", y1][k]))
        bm.faces.new((V["o", y0][k], V["i", y0][k], V["i", y0][j], V["o", y0][j]))
        bm.faces.new((V["o", y0][k], V["o", y0][j], V["o", y1][j], V["o", y1][k]))
        bm.faces.new((V["i", y0][k], V["i", y1][k], V["i", y1][j], V["i", y0][j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=0.008, segments=1, affect="EDGES", clamp_overlap=True)
    caras = {  # normal en Blender, eje u (derecha vista de afuera) y renglón
        "frente": (Vector((0, -1, 0)), Vector((1, 0, 0))),
        "atras": (Vector((0, 1, 0)), Vector((-1, 0, 0))),
        "der": (Vector((1, 0, 0)), Vector((0, 1, 0))),
        "izq": (Vector((-1, 0, 0)), Vector((0, -1, 0))),
    }
    for f in bm.faces:
        f.material_index = 1
    for renglon, (n, eje_u) in caras.items():
        f = max(bm.faces, key=lambda f: f.calc_center_median().dot(n) + 10 * (f.normal.dot(n) > 0.999))
        f.material_index = 0
        mapear_rect(bm, f, eje_u, Vector((0, 0, 1)), RENGLONES[renglon])
    return piezas.terminar("pieza_cartel", bm, [m_cartel, m_acero])


# ── Piezas ─────────────────────────────────────────────────────────────

def almohadon(bm, centro, U, V, N, w, h, mat=ACERO):
    """Panel capitoné: rectángulo apoyado en la pared que sube en pendiente y termina en una
    punta en el medio (las aristas en cruz dan el brillo de la chapa abollonada). Cerrado."""
    O, U, V, N = Vector(centro), Vector(U), Vector(V), Vector(N)

    def P(u, v, n):
        return bm.verts.new(g2b(O + U * u + V * v + N * n))
    a, b, m = w / 2, h / 2, 0.035
    atras = [P(-a, -b, -0.003), P(a, -b, -0.003), P(a, b, -0.003), P(-a, b, -0.003)]
    alto = [P(-a + m, -b + m, 0.016), P(a - m, -b + m, 0.016), P(a - m, b - m, 0.016), P(-a + m, b - m, 0.016)]
    c = P(0, 0, 0.026)
    previas = set(bm.faces)
    bm.faces.new(list(reversed(atras)))
    for k in range(4):
        j = (k + 1) % 4
        bm.faces.new((atras[k], atras[j], alto[j], alto[k]))
        bm.faces.new((alto[k], alto[j], c))
    for f in bm.faces:
        if f not in previas:
            f.material_index = mat


def paneles(bm, eje, plano, u0, u1, n_col, signo):
    """Grilla de 2 filas de almohadones en una pared (eje "z": pared z = plano, u = x; eje "x":
    pared x = plano, u = z). signo = hacia dónde mira la pared (+1 / −1)."""
    gap = 0.02
    w = (u1 - u0 - gap * (n_col + 1)) / n_col
    for ya, yb in FILAS_PANELES:
        for i in range(n_col):
            u = u0 + gap + w / 2 + i * (w + gap)
            if eje == "z":
                c, U, N = (u, (ya + yb) / 2, plano), (signo, 0, 0), (0, 0, signo)
            else:
                c, U, N = (plano, (ya + yb) / 2, u), (0, 0, -signo), (signo, 0, 0)
            almohadon(bm, c, U, (0, 1, 0), N, w, yb - ya)


def paredes(bm):
    """Pollera pintada (con los pasarruedas y la puerta), chapa de abajo y pared de atrás."""
    arcos = [(-ARCO_X, ARCO_X, Y_CAJA, ARCO_Y)]
    pa, pb, pt = PUERTA
    # Pollera: adelante y atrás (con los arcos) y las puntas; pintada por fuera, acero por dentro.
    r.pared_con_vanos(bm, "z", -XH + 0.05 - EPS, XH - 0.05 + EPS, Y_CAJA, Y_POLLERA, ZH, ZH - 0.05,
                      arcos, PINT, ACERO, PINT, ACERO)
    r.pared_con_vanos(bm, "z", -XH + 0.05 - EPS, XH - 0.05 + EPS, Y_CAJA, Y_POLLERA, -ZH, -ZH + 0.05,
                      arcos + [(pa, pb, Y_CAJA, Y_POLLERA)], PINT, ACERO, PINT, ACERO)
    for s in (-1, 1):
        r.pared_con_vanos(bm, "x", -ZH, ZH, Y_CAJA, Y_POLLERA, s * XH, s * (XH - 0.05), [], PINT, ACERO, PINT, ACERO)
    # Chapa de arriba (acero): adelante hasta la mesada; puntas hasta 1,05; atrás hasta el techo.
    y0 = Y_POLLERA - 0.005
    r.pared_con_vanos(bm, "z", -XI - EPS, XI + EPS, y0, Y1 + 0.002, ZA, ZI, [], ACERO, ACERO, ACERO, ACERO)
    r.pared_con_vanos(bm, "z", -XI - EPS, XI + EPS, y0, Y_TECHO + EPS, -ZA, -ZI, [(pa, pb, y0, pt)],
                      ACERO, ACERO, ACERO, ACERO)
    for s in (-1, 1):
        r.pared_con_vanos(bm, "x", -ZA, ZA, y0, YM, s * XA, s * XI, [], ACERO, ACERO, ACERO, ACERO)
    # Paneles capitoné.
    paneles(bm, "z", ZA, -XI, XI, 6, 1)
    paneles(bm, "z", -ZA, -XI, pa - 0.02, 4, -1)
    for s in (-1, 1):
        paneles(bm, "x", s * XA, -ZA + 0.01, ZA - 0.01, 3, s)
    # Marco de la puerta (acero) por fuera.
    for x in (pa - 0.015, pb + 0.015):
        piezas.caja(bm, (0.03, pt - Y_CAJA, 0.02), (x, (Y_CAJA + pt) / 2, -ZH - 0.008), mat=ACERO, bisel=0.006)
    piezas.caja(bm, (pb - pa + 0.06, 0.03, 0.02), ((pa + pb) / 2, pt + 0.014, -ZH - 0.008), mat=ACERO, bisel=0.006)


def piso_y_ruedas(bm):
    """Piso de goma (con la muesca de los pasarruedas), pasarruedas, ruedas y chasis."""
    for xa, xb, zz in ((-XI, -ARCO_X, ZI), (-ARCO_X - EPS, ARCO_X + EPS, Z_RUEDA_ADENTRO - EPS), (ARCO_X, XI, ZI)):
        piezas.caja(bm, (xb - xa, 0.04, 2 * zz), ((xa + xb) / 2, YP - 0.02, 0), mat=GOMA)
    for s in (-1, 1):
        # Forro de goma del pasarruedas: techo, cara de adentro y las dos puntas.
        zc = s * (Z_RUEDA_ADENTRO + ZH - 0.05) / 2
        prof = ZH - 0.05 - Z_RUEDA_ADENTRO + 0.004
        piezas.caja(bm, (2 * ARCO_X, 0.012, prof), (0, ARCO_Y + 0.006, zc), mat=GOMA)
        piezas.caja(bm, (2 * ARCO_X, ARCO_Y + 0.012 - (YP - 0.04), 0.012),
                    (0, (ARCO_Y + 0.012 + YP - 0.04) / 2, s * (Z_RUEDA_ADENTRO + 0.006)), mat=GOMA)
        for x in (-ARCO_X + 0.006, ARCO_X - 0.006):
            piezas.caja(bm, (0.012, ARCO_Y - YP + 0.04 - 0.002, prof - 0.004), (x, (ARCO_Y + YP - 0.04) / 2, zc),
                        mat=GOMA)
        for x in EJES_X:
            zr = s * Z_RUEDA
            piezas.cilindro(bm, R_RUEDA, ANCHO_RUEDA, (x, R_RUEDA, zr), eje="z", lados=16, mat=GOMA,
                            radio_a_caras=True)
            piezas.cilindro(bm, 0.075, 0.02, (x, R_RUEDA, zr + s * (ANCHO_RUEDA / 2 + 0.009)), eje="z", lados=16,
                            mat=ACERO, radio_a_caras=True,
                            radio_arriba=0.06 if s > 0 else None)
    # Largueros del chasis (pintados) bajo el piso.
    for s in (-1, 1):
        piezas.caja(bm, (2 * XH - 0.2, 0.06, 0.07), (0, YP - 0.04 - 0.03 - EPS, s * 0.45), mat=PINT, bisel=0.01)


def lanza(bm):
    """Lanza en A, acople y rueda de apoyo (por −X)."""
    y = 0.075
    for s in (-1, 1):
        plaza.caño(bm, (-XH + 0.20, y, s * 0.45), (X_ACOPLE + 0.16, y, s * 0.035), 0.032, 8, mat=PINT)
    plaza.caño(bm, (-XH - 0.01, y, -0.50), (-XH - 0.01, y, 0.50), 0.03, 8, mat=PINT)
    piezas.caja(bm, (0.24, 0.08, 0.11), (X_ACOPLE + 0.12, y + 0.005, 0), mat=NEGRO, bisel=0.015)
    piezas.cilindro(bm, 0.04, 0.05, (X_ACOPLE + 0.05, y + 0.055, 0), lados=12, mat=NEGRO, radio_a_caras=True)
    piezas.caja(bm, (0.12, 0.025, 0.03), (X_ACOPLE + 0.17, y + 0.06, 0), mat=NEGRO, bisel=0.008)
    xr = -XH - 0.40
    piezas.cilindro(bm, 0.025, 0.40, (xr, 0.29, 0.20), lados=12, mat=ACERO, radio_a_caras=True)
    piezas.cilindro(bm, 0.008, 0.10, (xr + 0.04, 0.47, 0.20), eje="x", lados=8, mat=NEGRO)
    piezas.cilindro(bm, 0.05, 0.04, (xr, 0.05, 0.20), eje="z", lados=12, mat=GOMA, radio_a_caras=True)
    piezas.caja(bm, (0.03, 0.06, 0.07), (xr, 0.10, 0.20), mat=ACERO)


def muebles(bm, tapas_mats):
    """Mesada de la vitrina con las bahías y mesada de atrás. Devuelve (tapas, puntos, bahías)."""
    # Mesada de adentro + repisa de afuera, una sola losa.
    base.losa(bm, (2 * XI, ALTO_MESADA, 1.08 - 0.24), (0, YM - ALTO_MESADA / 2, (1.08 + 0.24) / 2),
              radio=0.02, seg=2, mat=ACERO)
    xs = base.centros_bahias(-XI, XI, 4, 0.08)
    # Zócalo bajo las bahías (hasta la cara de adentro de los pasarruedas) y la placa de atrás.
    piezas.caja(bm, (2 * XI, Y_BAHIA - YP + 0.04, Z_RUEDA_ADENTRO - Z_BOCA),
                (0, (YP - 0.04 + Y_BAHIA) / 2, (Z_BOCA + Z_RUEDA_ADENTRO) / 2), mat=ACERO, bisel=0.006)
    piezas.caja(bm, (2 * XI, Y_BAHIA - ARCO_Y - 0.012, ZI - Z_RUEDA_ADENTRO + 0.002),
                (0, (Y_BAHIA + ARCO_Y + 0.012) / 2, (ZI + Z_RUEDA_ADENTRO - 0.002) / 2), mat=ACERO)
    # Fondo de las bahías y montantes.
    piezas.caja(bm, (2 * XI, Y1 - Y_BAHIA + 2 * EPS, ZI - Z_FONDO), (0, (Y_BAHIA + Y1) / 2, (ZI + Z_FONDO) / 2),
                mat=ACERO)
    for ma, mb in base.macizos(-XI + EPS, XI - EPS, xs):
        piezas.caja(bm, (mb - ma, Y1 - Y_BAHIA + 2 * EPS, Z_FONDO - Z_BOCA + EPS),
                    ((ma + mb) / 2, (Y_BAHIA + Y1) / 2, (Z_BOCA + Z_FONDO + EPS) / 2), mat=ACERO, bisel=0.006)
    tapas, puntos, bahias = [], [], []
    for i, xc in enumerate(xs):
        bt = bmesh.new()
        ya, yb = Y_BAHIA - 0.012, Y1 - 0.006
        piezas.caja(bt, (BAHIA_W + 0.02, yb - ya, 0.02), (xc, (ya + yb) / 2, Z_BOCA - 0.011), mat=0, bisel=0.008)
        piezas.caja(bt, (0.12, 0.022, 0.02), (xc, yb - 0.06, Z_BOCA - 0.030), mat=1, bisel=0.005)
        tapas.append(base.objeto_en(f"pieza_tapa_bahia_{i + 1}", bt, tapas_mats, (xc, Y_BAHIA, Z_BOCA)))
        puntos.append(piezas.punto(f"punto_bahia_{i + 1}", (xc, Y_BAHIA, Z_BOCA)))
        bahias.append((xc, Y_BAHIA, Z_BOCA))
    # Mesada de atrás: losa, mueble con puertas sobre un zócalo (el pasarruedas queda abajo).
    xa, xb = MESADA_ATRAS
    zw = -ZI
    base.losa(bm, (xb - xa, ALTO_MESADA, Z_ATRAS - zw + 0.03), ((xa + xb) / 2, YM - ALTO_MESADA / 2,
              (zw + Z_ATRAS + 0.03) / 2), radio=0.02, seg=2, mat=ACERO)
    piezas.caja(bm, (xb - xa - 0.02, Y1 - Y_BAHIA + EPS, Z_ATRAS - zw), ((xa + xb) / 2, (Y_BAHIA + Y1 + EPS) / 2,
                (zw + Z_ATRAS) / 2), mat=ACERO, bisel=0.008)
    piezas.caja(bm, (xb - xa - 0.02, Y_BAHIA - YP + 0.04 + EPS, Z_ATRAS + Z_RUEDA_ADENTRO),
                ((xa + xb) / 2, (YP - 0.04 + Y_BAHIA + EPS) / 2, (Z_ATRAS - Z_RUEDA_ADENTRO) / 2), mat=ACERO,
                bisel=0.006)
    piezas.caja(bm, (xb - xa - 0.02, Y_BAHIA - ARCO_Y - 0.012, Z_RUEDA_ADENTRO - ZI + 0.002),
                ((xa + xb) / 2, (Y_BAHIA + ARCO_Y + 0.012) / 2, -(ZI + Z_RUEDA_ADENTRO - 0.002) / 2), mat=ACERO)
    n = 3
    w = (xb - xa - 0.04) / n
    for k in range(n):
        xc = xa + 0.02 + w * (k + 0.5)
        piezas.caja(bm, (w - 0.012, Y1 - Y_BAHIA - 0.05, 0.016), (xc, (Y_BAHIA + Y1) / 2, Z_ATRAS + 0.006),
                    mat=ACERO, bisel=0.005)
        piezas.caja(bm, (0.10, 0.02, 0.018), (xc, Y1 - 0.08, Z_ATRAS + 0.022), mat=NEGRO, bisel=0.004)
    return tapas, puntos, bahias


def vitrina(bm):
    """Marco de acero, vidrios, ventana de atención, vitrinas con estantes y techo."""
    yv0, yv1 = YM, Y_TECHO
    zv = ZA - 0.025                                  # plano de los vidrios de adelante
    # Parantes de las esquinas y de la ventana.
    for sx in (-1, 1):
        for sz in (-1, 1):
            piezas.caja(bm, (0.05, yv1 - yv0, 0.05), (sx * (XA - 0.025), (yv0 + yv1) / 2, sz * (ZA - 0.025)),
                        mat=ACERO, bisel=0.008)
        piezas.caja(bm, (0.05, yv1 - yv0, 0.05), (sx * VX, (yv0 + yv1) / 2, zv), mat=ACERO, bisel=0.008)
    # Travesaños: arriba de punta a punta, abajo de cada vitrina, arriba de la ventana.
    piezas.caja(bm, (2 * XA - 0.1, 0.04, 0.05), (0, yv1 - 0.021, zv), mat=ACERO, bisel=0.008)
    piezas.caja(bm, (2 * VX - 0.05, 0.04, 0.05), (0, Y_VENTANA + 0.02, zv), mat=ACERO, bisel=0.008)
    for xa, xb in VITRINAS:
        piezas.caja(bm, (xb - xa, 0.03, 0.05), ((xa + xb) / 2, yv0 + 0.015, zv), mat=ACERO, bisel=0.006)
    for sx in (-1, 1):
        x = sx * (XA - 0.025)
        piezas.caja(bm, (0.05, 0.03, 2 * ZA - 0.1), (x, yv0 + 0.015, 0), mat=ACERO, bisel=0.006)
        piezas.caja(bm, (0.05, 0.04, 2 * ZA - 0.1), (x, yv1 - 0.021, 0), mat=ACERO, bisel=0.008)
        piezas.caja(bm, (0.04, yv1 - yv0 - 0.07, 0.04), (x, (yv0 + 0.03 + yv1 - 0.04) / 2, 0), mat=ACERO,
                    bisel=0.006)
    # Vidrios (1 cm): vitrinas de adelante, paño fijo sobre la ventana, costados.
    for xa, xb in VITRINAS:
        piezas.caja(bm, (xb - xa - 0.02, yv1 - yv0 - 0.07 + 0.01, 0.01), ((xa + xb) / 2, (yv0 + 0.03 + yv1 - 0.04) / 2,
                    zv), mat=VIDRIO)
    piezas.caja(bm, (2 * VX - 0.06, yv1 - 0.04 - Y_VENTANA - 0.04 + 0.01, 0.01),
                (0, (Y_VENTANA + 0.04 + yv1 - 0.04) / 2, zv), mat=VIDRIO)
    for sx in (-1, 1):
        for sz in (-1, 1):
            za, zb = (0.02, ZA - 0.05) if sz > 0 else (-ZA + 0.05, -0.02)
            piezas.caja(bm, (0.01, yv1 - yv0 - 0.07 + 0.01, zb - za), (sx * (XA - 0.025), (yv0 + 0.03 + yv1 - 0.04) / 2,
                        (za + zb) / 2), mat=VIDRIO)
    # Vitrinas de exhibición: vidrio del lado de la ventana, parantes finos y estantes.
    for xa, xb in VITRINAS:
        xv = xb if xa < 0 else xa                    # lado de la ventana
        xp = xa if xa < 0 else xb                    # lado de la punta
        piezas.caja(bm, (0.01, yv1 - yv0 - 0.04, zv - 0.025 - Z_VITRINA), (xv, (yv0 + yv1 - 0.04) / 2,
                    (Z_VITRINA + zv - 0.025) / 2), mat=VIDRIO)
        for x in (xv, xp):
            piezas.caja(bm, (0.02, yv1 - yv0 - 0.04 + EPS, 0.02), (x + (0.0 if x == xv else 0.0), (yv0 + yv1 - 0.04) / 2,
                        Z_VITRINA - 0.01), mat=ACERO, bisel=0.005)
        for ye in ESTANTES:
            piezas.caja(bm, (xb - xa - 0.012, 0.02, zv - 0.03 - Z_VITRINA + 0.02), ((xa + xb) / 2, ye - 0.01,
                        (Z_VITRINA - 0.02 + zv - 0.03) / 2), mat=ACERO, bisel=0.006)
    # Techo: chapa de 5 cm que sobresale 0,20 alrededor.
    piezas.caja(bm, (2 * (XH + VUELO), Y_LOSA - Y_TECHO, 2 * (ZH + VUELO)), (0, (Y_TECHO + Y_LOSA) / 2, 0),
                mat=ACERO, bisel=0.012)


def puerta(mats):
    pa, pb, pt = PUERTA
    bm = bmesh.new()
    w, h = pb - pa - 0.01, pt - YP - 0.01
    piezas.caja(bm, (w, h, 0.03), ((pa + pb) / 2, YP + 0.005 + h / 2, -ZI - 0.02), mat=0, bisel=0.008)
    piezas.caja(bm, (w - 0.16, 0.5, 0.008), ((pa + pb) / 2, YP + 0.5, -ZI - 0.038), mat=0, bisel=0.003)
    piezas.caja(bm, (0.03, 0.14, 0.03), (pb - 0.08, YP + 0.95, -ZI - 0.05), mat=1, bisel=0.006)
    obj = base.objeto_en("pieza_puerta", bm, mats, (pa + 0.005, YP, -ZA))
    col = piezas.colision_caja(f"{ID}_puerta", (w, h, 0.03), ((pa + pb) / 2, YP + 0.005 + h / 2, -ZI - 0.02))
    col.parent = obj
    col.location = -obj.location
    return obj, col


def luces(m_luz):
    bm = bmesh.new()
    y = Y_TECHO - 0.017
    plaza.caño(bm, (-0.70, y, 0.97), (0.70, y, 0.97), 0.016, 8, mat=0)
    plaza.caño(bm, (-0.60, y, -0.10), (0.60, y, -0.10), 0.016, 8, mat=0)
    return piezas.terminar("pieza_luces", bm, [m_luz])


def colision(xs):
    pa, pb, pt = PUERTA
    yv0, yv1 = YM, Y_TECHO
    cajas = [
        ((2 * XH, YP - Y_CAJA, 2 * ZH), (0, (Y_CAJA + YP) / 2, 0)),                         # piso
        ((2 * XH, Y1 - Y_CAJA, 0.05), (0, (Y_CAJA + Y1) / 2, ZH - 0.025)),                  # frente bajo
        ((0.05, Y_TECHO - Y_CAJA, 2 * ZH), (-XH + 0.025, (Y_CAJA + Y_TECHO) / 2, 0)),       # puntas
        ((0.05, Y_TECHO - Y_CAJA, 2 * ZH), (XH - 0.025, (Y_CAJA + Y_TECHO) / 2, 0)),
        ((pa + XH, Y_TECHO - Y_CAJA, 0.05), ((pa - XH) / 2, (Y_CAJA + Y_TECHO) / 2, -ZH + 0.025)),  # atrás
        ((XH - pb, Y_TECHO - Y_CAJA, 0.05), ((pb + XH) / 2, (Y_CAJA + Y_TECHO) / 2, -ZH + 0.025)),
        ((pb - pa, Y_TECHO - pt, 0.05), ((pa + pb) / 2, (pt + Y_TECHO) / 2, -ZH + 0.025)),
        ((2 * (XH + VUELO), Y_CARTEL - Y_TECHO, 2 * (ZH + VUELO)), (0, (Y_TECHO + Y_CARTEL) / 2, 0)),  # techo
        ((2 * XI, ALTO_MESADA, 1.08 - 0.24), (0, YM - ALTO_MESADA / 2, (1.08 + 0.24) / 2)),  # mesada + repisa
        ((2 * VX, yv1 - Y_VENTANA, 0.05), (0, (Y_VENTANA + yv1) / 2, ZA - 0.025)),          # paño fijo
        ((2 * XI, Y_BAHIA - YP, ZI - Z_BOCA), (0, (YP + Y_BAHIA) / 2, (ZI + Z_BOCA) / 2)),  # bajo bahías
        ((2 * XI, BAHIA_H, ZI - Z_FONDO), (0, Y_BAHIA + BAHIA_H / 2, (ZI + Z_FONDO) / 2)),
    ]
    for ma, mb in base.macizos(-XI, XI, xs):
        cajas.append(((mb - ma, BAHIA_H, BAHIA_D), ((ma + mb) / 2, Y_BAHIA + BAHIA_H / 2, Z_BOCA + BAHIA_D / 2)))
    for xa, xb in VITRINAS:
        xv = xb if xa < 0 else xa
        cajas.append(((xb - xa, yv1 - yv0, 0.05), ((xa + xb) / 2, (yv0 + yv1) / 2, ZA - 0.025)))
        cajas.append(((0.02, yv1 - yv0, ZA - Z_VITRINA), (xv, (yv0 + yv1) / 2, (ZA + Z_VITRINA) / 2)))
        for ye in ESTANTES:
            cajas.append(((xb - xa, 0.02, ZA - Z_VITRINA), ((xa + xb) / 2, ye - 0.01, (ZA + Z_VITRINA) / 2)))
    xa, xb = MESADA_ATRAS
    cajas.append(((xb - xa, YM - YP, Z_ATRAS + ZI), ((xa + xb) / 2, (YP + YM) / 2, (Z_ATRAS - ZI) / 2)))
    cajas.append(((-XH - X_ACOPLE, 0.15, 1.0), ((X_ACOPLE - XH) / 2, 0.075, 0)))
    return plaza.colision_cajas(ID, [(m, c, (0, 0, 0)) for m, c in cajas])


# ── Modelo ─────────────────────────────────────────────────────────────

def construir():
    mats = comun.cargar_materiales(*MATERIALES)
    dibujar_textura()
    m_cartel = material_cartel(f"T_{ID}", TEXTURA, rugosidad=0.5)
    bm = bmesh.new()
    paredes(bm)
    piso_y_ruedas(bm)
    lanza(bm)
    tapas, puntos_bahia, bahias = muebles(bm, [mats[ACERO], mats[NEGRO]])
    vitrina(bm)
    pintura, estructura = r.partir(bm, mats, ID)
    obj_cartel = cartel(m_cartel, mats[ACERO])
    obj_luces = luces(mats[LUZ])
    puerta_obj, col_puerta = puerta([mats[ACERO], mats[NEGRO]])
    col = colision([b[0] for b in bahias])
    puntos = []
    for nombre, pos, rot_y in ANCLAJES:
        e = piezas.punto(f"punto_{nombre}", pos)
        e.rotation_euler.z = math.radians(rot_y)
        puntos.append(e)
    for nombre, pos in (("entrega", ENTREGA), ("fila", FILA), ("entrada", ENTRADA), ("luz", LUZ_PUNTO)):
        puntos.append(piezas.punto(f"punto_{nombre}", pos))
    puntos_lugar = [piezas.punto(f"punto_lugar_{i + 1}", p) for i, p in enumerate(lugares())]
    visibles = [pintura, estructura, obj_cartel, obj_luces] + tapas + [puerta_obj]
    raiz = piezas.raiz(ID, visibles + [col] + puntos + puntos_lugar + puntos_bahia)
    return {"raiz": raiz, "pintura": pintura, "estructura": estructura, "cartel": obj_cartel, "m_cartel": m_cartel,
            "luces": obj_luces, "tapas": tapas, "puerta": puerta_obj, "colisiones": [col, col_puerta],
            "puntos": puntos, "puntos_lugar": puntos_lugar, "puntos_bahia": puntos_bahia, "bahias": bahias,
            "visibles": visibles}


# ── Revisión ───────────────────────────────────────────────────────────

def chequeo_medidas(m, tol=0.002):
    vp = r.verts_g([m["pintura"]])
    caja = [v for v in vp if abs(v.x) <= XH + 1e-4]
    todos = r.verts_g(m["visibles"])
    x0, x1 = min(v.x for v in caja), max(v.x for v in caja)
    z0, z1 = min(v.z for v in caja), max(v.z for v in caja)
    piso, techo = min(v.y for v in todos), max(v.y for v in todos)
    largo = max(v.x for v in todos) - min(v.x for v in todos)
    ok = abs(x1 - x0 - 2 * XH) <= tol and abs(z1 - z0 - 2 * ZH) <= tol and abs(piso) <= tol and \
        abs(techo - Y_CARTEL) <= tol
    t = ("Medidas: cuerpo (pollera pintada) %.3f × %.3f m, alto %.3f con el cartel; %.2f de largo con la lanza "
         "(propuesta para el .ron: ancho 3,20, profundidad 1,70, alto 2,62)" % (x1 - x0, z1 - z0, techo - piso, largo))
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    ok_o = abs(cx) <= tol and abs(cz) <= tol and abs(piso) <= tol
    t_o = "Origen en el centro del cuerpo (%.3f, %.3f), a nivel de la calle (ruedas en Y = %.3f)" % (cx, cz, piso)
    return (ok, t), (ok_o, t_o)


def _alto(arbol, x, z, desde, dir_y=-1):
    hit = arbol.ray_cast(g2b((x, desde, z)), Vector((0, 0, dir_y)))
    return desde + dir_y * hit[3] if hit[0] else None


def chequeo_interior(m):
    dg = bpy.context.evaluated_depsgraph_get()
    arbol = BVHTree.FromObject(m["estructura"], dg)
    piso = _alto(arbol, 0.0, -0.10, 1.0)
    techo = _alto(arbol, 0.0, -0.30, 1.5, dir_y=1)
    m1 = _alto(arbol, 0.0, 0.55, 1.5)
    m2 = _alto(arbol, -0.4, -0.64, 1.5)
    repisa = _alto(arbol, 0.0, 0.97, 1.5)
    vs = r.verts_g([m["pintura"], m["estructura"]])
    pasillo = [v for v in vs if -XI + 0.02 < v.x < XI - 0.02 and Z_ATRAS + 0.04 < v.z < Z_BOCA - 0.04 and
               YP + 0.005 < v.y < Y_TECHO - 0.005]
    ventana = [v for v in vs if -VX + 0.03 < v.x < VX - 0.03 and YM + 0.005 < v.y < Y_VENTANA - 0.005 and
               Z_BOCA < v.z < ZH + 0.3]
    ok = (None not in (piso, techo, m1, m2, repisa) and abs(piso - YP) < 1e-3 and abs(m1 - YM) < 1e-3 and
          abs(m2 - YM) < 1e-3 and abs(repisa - YM) < 1e-3 and techo - piso >= 2.0 - 1e-3 and not pasillo and not ventana)
    return ok, ("Interior: piso a %.2f, mesadas a %.3f / %.3f y repisa de afuera a %.3f (piso + 0,90), %.2f m de "
                "techo, pasillo de %.2f m libre, ventana de atención libre (%.2f × %.2f)" % (
                    piso or -1, m1 or -1, m2 or -1, repisa or -1, (techo or 0) - (piso or 0), Z_BOCA - Z_ATRAS,
                    2 * VX - 0.05, Y_VENTANA - YM) +
                (f" — {len(pasillo)} vértices en el pasillo" if pasillo else "") +
                (f" — {len(ventana)} vértices en la ventana" if ventana else ""))


def chequeo_lugares(m):
    dg = bpy.context.evaluated_depsgraph_get()
    arbol = BVHTree.FromObject(m["estructura"], dg)
    malos = []
    for e, p in zip(m["puntos_lugar"], lugares()):
        apoyo = _alto(arbol, p[0], p[2], p[1] + 0.05)
        libre = arbol.ray_cast(g2b((p[0], p[1] + 0.01, p[2])), Vector((0, 0, 1)))
        hueco = libre[3] if libre[0] else 9
        if apoyo is None or abs(apoyo - p[1]) > 1e-3 or hueco < 0.30 or \
                (e.matrix_world.translation - g2b(p)).length > 1e-5:
            malos.append(e.name)
    return not malos, ("Lugares de exhibición: %d punto_lugar en las vitrinas, cada uno apoyado (mesada y "
                       "estantes) con ≥ 0,30 m libres arriba" % len(m["puntos_lugar"]) +
                       (f" — MAL: {malos}" if malos else ""))


def chequeo_puntos(m):
    esperados = {f"punto_{n}": p for n, p, _ in ANCLAJES}
    esperados.update(punto_entrega=ENTREGA, punto_fila=FILA, punto_entrada=ENTRADA, punto_luz=LUZ_PUNTO)
    por_nombre = {e.name: e for e in m["puntos"]}
    ok = set(por_nombre) == set(esperados) and all(
        (por_nombre[n].matrix_world.translation - g2b(p)).length < 1e-5 for n, p in esperados.items())
    pt = m["puerta"]
    ok &= abs(pt.location.x - (PUERTA[0] + 0.005)) < 1e-6 and m["colisiones"][1].parent == pt
    return ok, ("Puntos: %d punto_<anclaje> + entrega, fila, entrada y luz en las posiciones propuestas; "
                "pieza_puerta con la bisagra en x %.3f (gira en Y)" % (len(ANCLAJES), PUERTA[0] + 0.005))


def revisar(m):
    res = comun.revisar(m["visibles"], PRESUPUESTO, (2 * XH, Y_CARTEL, 2 * ZH), origen="base", max_materiales=6)
    (ok_m, t_m), (ok_o, t_o) = chequeo_medidas(m)
    res = comun.reemplazar_linea(res, "Medidas", ok_m, t_m)
    res = comun.reemplazar_linea(res, "Origen", ok_o, t_o)
    res = revisar_cartel(res, [m["m_cartel"]])
    nombres = list(dict.fromkeys(mt.name for o in m["visibles"] for mt in o.data.materials))
    de_paleta = [n for n in nombres if not n.startswith("T_")]
    res = comun.reemplazar_linea(res, "Materiales: ", len(de_paleta) <= 6,
                                 "Materiales: %d de la paleta (máx. 6) + el cartel T_%s" % (len(de_paleta), ID))
    res = comun.reemplazar_linea(res, "Normales", *r.chequeo_normales(m["visibles"]))
    res.append(chequeo_interior(m))
    res.append(r.chequeo_bahias(m))
    res.append(chequeo_lugares(m))
    res.append(chequeo_puntos(m))
    return res


# ── Hoja de revisión ───────────────────────────────────────────────────

def cartel_prendido(m, prendido):
    """Para la foto de atardecer: una copia del material del cartel con emisión (el juego la
    prende de noche). No se exporta."""
    obj = m["cartel"]
    if prendido:
        mat = m["m_cartel"].copy()
        mat.name = "ref_cartel_prendido"
        nodos = mat.node_tree.nodes
        bsdf = next(n for n in nodos if n.type == "BSDF_PRINCIPLED")
        tex = next(n for n in nodos if n.type == "TEX_IMAGE")
        mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = 1.2
        obj.material_slots[0].material = mat
    else:
        obj.material_slots[0].material = m["m_cartel"]


VISTAS = [
    ("Frente (lo que ve el cliente) · día", "cerrado", "dia", ((-0.4, 1.35, 30), (-0.4, 1.35, 0), 50, 5.6), 0),
    ("Lado del vendedor: puerta · día", "cerrado", "dia", ((-0.4, 1.35, -30), (-0.4, 1.35, 0), 50, 5.6), 0),
    ("3/4 lado del cliente · día", "cerrado", "dia", ((4.6, 2.9, 5.6), (-0.2, 1.25, 0.2), 35, None), 0),
    ("3/4 lado del vendedor, puerta abierta · día", "abierto", "dia", ((-4.4, 2.8, -5.4), (0.0, 1.2, 0), 35, None),
     0),
    ("3/4 · atardecer, cartel prendido", "cerrado", "atardecer", ((-4.6, 2.9, 5.6), (0.0, 1.25, 0.2), 35, None), 2),
    ("Cliente y vendedor de 1,75 m · día", "personas", "dia", ((2.4, 1.9, 4.4), (-0.3, 1.35, 0.5), 35, None), 0),
    ("Adentro, a la altura de los ojos (piso + 1,65) · día", "abierto", "dia",
     ((1.25, 1.80, -0.30), (-0.4, 1.40, 0.75), 16, None), 1),
    ("Adentro: alacenas en las 4 bahías · día", "alacenas", "dia",
     ((1.30, 1.75, -0.45), (-0.3, 0.70, 0.45), 16, None), 1),
    ("Con el porche de nylon (porche_nylon) · día", "porche", "dia", ((5.4, 2.7, 5.4), (1.0, 1.15, 0.2), 30, None),
     0),
]


def hoja_revision(m, revision):
    import porche_nylon
    comun.preparar_revision()
    persona = bpy.data.objects["ref_persona_1,75m"]
    cliente = persona.copy()
    bpy.context.scene.collection.objects.link(cliente)
    cliente.location = g2b((0.30, 0, ZH + 0.50))
    cliente.rotation_euler.z = math.pi
    persona.location = g2b((-0.35, YP, (Z_BOCA + Z_ATRAS) / 2 - 0.05))
    puerta_ab = m["puerta"].copy()
    puerta_ab.data = m["puerta"].data.copy()
    bpy.context.scene.collection.objects.link(puerta_ab)
    puerta_ab.rotation_euler.z = math.radians(100)
    fijos = [m["pintura"], m["estructura"], m["cartel"], m["luces"]]
    con_alacenas = fijos + [puerta_ab]
    for variante, punto in zip(["puertas", "cajones", "abierta", "mixta"], m["puntos_bahia"]):
        al = _alacena.construir(variante, f"ref_alacena_{punto.name}")
        al["raiz"].location = punto.matrix_world.translation
        al["colision"].hide_render = True
        con_alacenas += _alacena.visibles(al)
    po = porche_nylon.construir()
    po["raiz"].location = g2b(ANCLAJES[6][1])
    for c in po["colisiones"]:
        c.hide_render = True
    persona_p = persona.copy()
    bpy.context.scene.collection.objects.link(persona_p)
    persona_p.location = g2b((XH + 0.9, 0, 0.35))
    persona_p.rotation_euler.z = math.radians(-90)
    luz = bpy.data.lights.new("ref_relleno", "POINT")
    luz.energy = 50
    luz.shadow_soft_size = 0.5
    relleno = bpy.data.objects.new("ref_relleno", luz)
    bpy.context.scene.collection.objects.link(relleno)
    relleno.location = g2b((0.3, Y_TECHO - 0.3, -0.1))
    bpy.context.view_layer.update()
    grupos = {
        "cerrado": m["visibles"],
        "abierto": fijos + m["tapas"] + [puerta_ab],
        "personas": m["visibles"] + [persona, cliente],
        "alacenas": con_alacenas,
        "porche": m["visibles"] + po["visibles"] + [cliente, persona_p],
    }
    tmp = Path(tempfile.mkdtemp())
    todos = {o for g in grupos.values() for o in g}
    cuadros = []
    for etiqueta, grupo, luz_modo, (pos, mira, lente, orto), extra in VISTAS:
        comun.poner_luz(luz_modo)
        relleno.hide_render = extra != 1
        cartel_prendido(m, extra == 2)
        for o in todos:
            o.hide_render = o not in grupos[grupo]
        r.camara(pos, mira, lente, orto)
        cuadros.append((etiqueta, comun.render(tmp / f"{len(cuadros)}.png")))
    cartel_prendido(m, False)
    comun.componer_hoja("carro_kiosco · 3,20 × 2,62 × 1,70 m · kiosco de acero con vitrina y cartel corrido "
                        "(propuesta, sin .ron)", cuadros, revision,
                        comun.RAIZ / f"docs/arte/revisiones/{ID}.jpg")


def main():
    comun.escena_vacia()
    m = construir()
    revision = revisar(m)
    ok = comun.imprimir_revision(ID, revision)
    comun.guardar_blend(comun.RAIZ / f"arte/fuentes/{FAMILIA}/{ID}.blend")
    comun.exportar_glb([m["raiz"]] + m["visibles"] + m["colisiones"] + m["puntos"] + m["puntos_lugar"] +
                       m["puntos_bahia"], comun.RAIZ / f"godot/modelos/{FAMILIA}/{ID}.glb", uvs=True)
    if "--sin-hoja" not in sys.argv:
        hoja_revision(m, revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
