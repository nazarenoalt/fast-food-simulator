"""Construcción común de las fachadas de la ciudad (`fachada_casa_a`, `fachada_casa_b`,
`fachada_edificio`, familia `ciudad`).

Qué dibuja hoy el juego (rust/game/src/ciudad.rs, rust/core/src/ciudad.rs, SPEC-013):
cada edificio es una caja de ancho (6 a 12 m) × alto × fondo, con planta baja de 3,6 m
(ALTO_PB) y pisos de 3,0 m (ALTO_PISO), de 2 a 7 plantas; cornisa de 0,35 m arriba (color
del muro aclarado); zócalo de 0,5 m (oscurecido) y una moldura de 0,18 m a la altura de 3,6;
una puerta de 1,1 × 2,2 a 1,2 m del borde izquierdo; si tiene local, vidriera (ancho − 3 m,
de 0,4 a 2,5 m, corrida 0,9 a la derecha) que brilla de noche y toldo inclinado 18°.
Ventanas: rectángulos de 1,1 × 1,4 en columnas de paso ancho / columnas
(columnas = piso((ancho − 1) / 2)), centrados a 1,5 m del piso de cada planta, solo en los
pisos de arriba; unas "prendibles" (35 %, se prenden de noche) y otras "oscuras".

Estas fachadas son la cara de adelante de esa caja, en el ancho de referencia de 9 m
(4 columnas de 2,25 m), y vienen en MÓDULOS que se apilan con las alturas del código:
    pieza_planta_baja   y de 0 a 3,6 (origen en el piso)
    pieza_piso_<n>      y de 3,6 + 3,0·(n−1) a 3,6 + 3,0·n (origen en su piso): todos iguales
    pieza_cornisa       0,35 m arriba del último piso (origen en su base)
El paño de cada módulo es un plano en z = 0 (el frente de la caja del edificio) con un
retorno de 0,25 m hacia atrás en los costados; arriba y abajo quedan abiertos (se apilan) y
atrás no tiene cara (lo tapa la caja del edificio). Los vanos son agujeros con jamba de
0,12 m de hondo: la sombra de la jamba es lo que hace que se lea como pared.

Vidrios (guía 4.3, objetos aparte):
    pieza_ventanas_oscuras  vidrios que no se prenden (M_Hierro: gris casi negro, apenas
                            metálico, como el VIDRIO del código, que tiene metálico 0,4)
    pieza_ventanas_luz      los que se prenden de noche (M_LuzCalida, emisión)
Cada vidrio es un rectángulo de 2 triángulos en el fondo del vano, en las mismas columnas
y alturas que las ventanas del código. Cuáles se prenden es un ejemplo fijo (≈ 35 %).

Superficies de los módulos (guía 6.2, variantes de color): la superficie 0 es siempre el
muro (el juego le pone el color del edificio con set_surface_override_material, como hoy
elige entre 8 colores); después vienen las molduras (claro), el zócalo (oscuro) y la
carpintería y el hierro.

Origen: centro de la base del plano de la fachada (x = 0, piso, z = 0). La caja envolvente
no está centrada en Z (el muro va hacia atrás y molduras, toldo y balcones hacia adelante):
el chequeo de origen se reemplaza por uno propio.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402, F401  (antes que bmesh)
import bmesh  # noqa: E402

import _ciudad as ciudad  # noqa: E402
import _plaza as plaza  # noqa: E402
import comun  # noqa: E402
import piezas  # noqa: E402

PRESUPUESTO = 2000          # edificio / fachada (guía 3.1)
ANCHO = 9.0
ALTO_PB = 3.6               # rust/core/src/ciudad.rs
ALTO_PISO = 3.0
COLUMNAS = 4                # piso((9 − 1) / 2)
PASO = ANCHO / COLUMNAS     # 2,25
VENTANA = (1.1, 1.4)        # QuadMesh de ciudad.rs
Y_VENTANA = 1.5             # centro de la ventana sobre el piso de cada planta
ESPESOR = 0.25              # retorno del muro hacia atrás
PROF = 0.12                 # hondo de las jambas
CORNISA = 0.35              # alto de la cornisa (ciudad.rs)
BISEL = ciudad.BISEL
BISEL_FINO = 0.015          # molduras de 6 a 8 cm (guía 3.3: un cuarto del grosor)

# Índices de material de todas las fachadas (cada objeto se queda con los que usa).
MURO, CLARO, OSCURO, CARPINTERIA, HIERRO = range(5)


def col_x(c):
    return -ANCHO / 2 + PASO * (c + 0.5)


def ventana_y(base=0.0):
    return base + Y_VENTANA - VENTANA[1] / 2, base + Y_VENTANA + VENTANA[1] / 2


# ── Piezas de fachada ──────────────────────────────────────────────────

def molduras_ventana(bm, x, ya, yb, ancho=VENTANA[0], jambas=True):
    """Alféizar abajo, guardapolvo arriba y dos jambas finas a los costados (claro)."""
    med = ancho / 2
    ciudad.caja_frente(bm, (ancho + 0.3, 0.07, 0.13), (x, ya - 0.035, 0.065), CLARO, BISEL_FINO)
    ciudad.caja_frente(bm, (ancho + 0.4, 0.16, 0.08), (x, yb + 0.08, 0.04), CLARO, BISEL_FINO)
    if jambas:
        for s in (-1, 1):
            ciudad.caja_frente(bm, (0.1, yb - ya, 0.04), (x + s * (med + 0.05), (ya + yb) / 2, 0.02),
                               CLARO, sin_abajo=True, sin_arriba=True)


def reja(bm, x, ya, yb, ancho=VENTANA[0], z=0.1, barrotes=5):
    """Reja saliente de hierro delante de una ventana de planta baja (apoya en el alféizar)."""
    g = 0.025
    med = ancho / 2 - 0.06
    for k in range(barrotes):
        bx = -med + 2 * med * k / (barrotes - 1)
        ciudad.barra(bm, (x + bx, ya, z), (x + bx, yb, z), g, HIERRO)
    for y in (ya + 0.15, yb - 0.12):
        ciudad.barra(bm, (x - med - g, y, z), (x + med + g, y, z), g, HIERRO)


def cornisa_casa(bm):
    """Cornisa con corona saliente y pretil, de 0,35 m (local: y de 0 a 0,35)."""
    perfil = [(-ESPESOR, 0.0), (0.04, 0.0), (0.04, 0.08), (0.14, 0.13), (0.30, 0.18),
              (0.30, 0.26), (0.06, 0.27), (0.06, CORNISA), (-ESPESOR, CORNISA)]
    ciudad.perfil_segmentado(bm, perfil, [-ANCHO / 2, ANCHO / 2], [CLARO])


def zocalo(bm, tramos, alto=0.5, sale=0.04):
    """Zócalo (oscuro) en tramos [(xa, xb)], pegado al muro."""
    for xa, xb in tramos:
        ciudad.caja_frente(bm, (xb - xa, alto, sale), ((xa + xb) / 2, alto / 2, sale / 2), OSCURO,
                           sin_abajo=True)


def moldura_pb(bm):
    """Moldura entre planta baja y pisos (ciudad.rs: 0,18 de alto, 0,12 de saliente, a 3,6)."""
    ciudad.caja_frente(bm, (ANCHO, 0.18, 0.12), (0, ALTO_PB, 0.06), CLARO, BISEL)


def puerta_madera(bm, f, x, ancho, alto, zf):
    """Puerta de madera de dos hojas con tableros y banderola, con jambas y dintel claros."""
    xa, xb = x - ancho / 2, x + ancho / 2
    hoja = 2.15
    ciudad.rectangulo(bm, xa, xb, 0, hoja, zf, CARPINTERIA)
    f.vidrio(xa, xb, hoja, alto, zf)
    ciudad.caja_frente(bm, (ancho, 0.08, 0.05), (x, hoja + 0.04, zf + 0.025), CARPINTERIA)
    ciudad.caja_frente(bm, (0.03, hoja, 0.03), (x, hoja / 2, zf + 0.015), CARPINTERIA,
                       sin_abajo=True, sin_arriba=True)
    for s in (-1, 1):
        for ya, yb in ((0.2, 0.95), (1.15, 1.95)):
            ciudad.caja_frente(bm, (0.36, yb - ya, 0.03), (x + s * ancho / 4, (ya + yb) / 2, zf + 0.015),
                               CARPINTERIA)
        ciudad.caja_frente(bm, (0.16, alto, 0.05), (x + s * (ancho / 2 + 0.08), alto / 2, 0.025), CLARO,
                           BISEL_FINO, sin_abajo=True)
    ciudad.caja_frente(bm, (ancho + 0.5, 0.2, 0.09), (x, alto + 0.1, 0.045), CLARO, BISEL_FINO)


def puerta_hierro(bm, f, x, ancho, alto, zf, jambas=True):
    """Puerta de hierro y vidrio de dos hojas (entrada a los pisos de arriba), con banderola."""
    xa, xb = x - ancho / 2, x + ancho / 2
    zb = zf + 0.02
    g = 0.05
    ciudad.rectangulo(bm, xa, xb, 0, 0.9, zf, HIERRO)
    f.vidrio(xa, xb, 0.9, alto, zf)
    for bx in (xa + g / 2, x, xb - g / 2):
        ciudad.barra(bm, (bx, 0.9, zb), (bx, alto, zb), g, HIERRO)
    for y in (0.9, 2.2):
        ciudad.barra(bm, (xa, y, zb), (xb, y, zb), g, HIERRO)
    for s in (-1, 1):  # barrotes de las hojas
        for k in (1, 2):
            bx = x + s * ancho / 2 * k / 3
            ciudad.barra(bm, (bx, 0.9, zb), (bx, 2.2, zb), 0.025, HIERRO)
        if jambas:
            ciudad.caja_frente(bm, (0.16, alto, 0.05), (x + s * (ancho / 2 + 0.08), alto / 2, 0.025), CLARO,
                               BISEL_FINO, sin_abajo=True)
    if jambas:
        ciudad.caja_frente(bm, (ancho + 0.5, 0.2, 0.09), (x, alto + 0.1, 0.045), CLARO, BISEL_FINO)


# ── Armado ─────────────────────────────────────────────────────────────

class Fachada:
    """Junta los módulos y los vidrios de una fachada y la revisa.

    p = dict con: id, materiales (nombres por índice MURO..HIERRO y extras), pisos (plantas
    contando la PB), luz (lista de bool por ventana de los pisos de arriba, de abajo hacia
    arriba y de izquierda a derecha), lista (medidas ≈ de la lista), descripcion.
    """

    def __init__(self, p):
        self.p = p
        self.mats = comun.cargar_materiales(*p["materiales"])
        self.vidrios = []          # (xa, xb, ya, yb, z, prende)
        self.objetos = []          # visibles (para la revisión y las fotos)
        self.modulos = []
        self.extras = []           # punto_, colisiones (se exportan, no se revisan)
        self.alto = ALTO_PB + (p["pisos"] - 1) * ALTO_PISO

    def objeto(self, nombre, bm, origen=(0.0, 0.0, 0.0), modulo=False):
        mats = ciudad.materiales_usados(bm, self.mats)
        o = ciudad.terminar_en(nombre, bm, mats, origen)
        self.objetos.append(o)
        if modulo:
            self.modulos.append(o)
        return o

    def vidrio(self, xa, xb, ya, yb, z, prende=False):
        self.vidrios.append((xa, xb, ya, yb, z, prende))

    def pisos(self, armar_piso):
        """armar_piso(bm, fachada, n) arma un piso en coordenadas locales (y de 0 a 3) y
        devuelve sus vanos de ventana [(xa, xb, ya, yb, z)] (locales), de izquierda a derecha."""
        luz = list(self.p["luz"])
        for n in range(1, self.p["pisos"]):
            base = ALTO_PB + (n - 1) * ALTO_PISO
            bm = bmesh.new()
            vanos = armar_piso(bm, self, n)
            bmesh.ops.translate(bm, vec=piezas.g2b((0, base, 0)), verts=bm.verts)
            self.objeto(f"pieza_piso_{n}", bm, (0, base, 0), modulo=True)
            for xa, xb, ya, yb, z in vanos:
                self.vidrio(xa, xb, ya + base, yb + base, z, luz.pop(0) if luz else False)

    def cornisa(self, armar):
        bm = bmesh.new()
        armar(bm)
        bmesh.ops.translate(bm, vec=piezas.g2b((0, self.alto, 0)), verts=bm.verts)
        self.objeto("pieza_cornisa", bm, (0, self.alto, 0), modulo=True)

    def terminar_vidrios(self):
        for nombre, prende in (("pieza_ventanas_oscuras", False), ("pieza_ventanas_luz", True)):
            bm = bmesh.new()
            for xa, xb, ya, yb, z, p in self.vidrios:
                if p == prende:
                    ciudad.rectangulo(bm, xa, xb, ya, yb, z)
            mat = self.mats[len(self.mats) - 1] if prende else self.mats[HIERRO]
            if bm.faces:
                o = ciudad.terminar(nombre, bm, [mat])
                self.objetos.append(o)
                setattr(self, "luz" if prende else "oscuras", o)

    def colision(self):
        c = piezas.colision_caja(self.p["id"], (ANCHO, self.alto, ESPESOR), (0, self.alto / 2, -ESPESOR / 2))
        self.extras.append(c)

    def raiz(self):
        self.raiz_obj = piezas.raiz(self.p["id"], self.objetos + self.extras)


def revisar(f, medidas):
    """Revisión con los chequeos propios de una fachada (origen, materiales, normales)."""
    p = f.p
    res = comun.revisar(f.objetos, PRESUPUESTO, medidas, origen="base")
    mn, mx = ciudad.limites(f.objetos)
    ok = abs(mn.x + ANCHO / 2) < 1e-4 and abs(mx.x - ANCHO / 2) < 1e-4 and abs(mn.y) < 1e-4 \
        and abs(mn.z + ESPESOR) < 1e-4
    res = ciudad.reemplazar(res, "Origen", ok,
                            "Origen en el centro de la base del plano de la fachada (x de %.2f a "
                            "%.2f, piso en %.3f, muro de z %.2f a 0; adelante sale %.2f)" % (
                                mn.x, mx.x, mn.y, mn.z, mx.z))
    ok, texto = ciudad.chequeo_normales(f.objetos)
    res = ciudad.reemplazar(res, "Normales", ok, texto)
    ok, texto = ciudad.chequeo_materiales(f.objetos, 6, max_objeto=5,
                                         por_que=": fachada armada, como una base de carrito")
    res = ciudad.reemplazar(res, "Materiales: ", ok, texto)
    # Módulos: alturas del código y origen en su piso.
    alturas = []
    for o in f.modulos:
        mn_o, mx_o = ciudad.limites([o])
        alturas.append((o.name, round(o.location.z, 3), round(mx_o.y - mn_o.y, 3)))
    pisos = [a for a in alturas if a[0].startswith("pieza_piso_")]
    ok = all(abs(z - (ALTO_PB + i * ALTO_PISO)) < 1e-4 for i, (_, z, _) in enumerate(pisos))
    res.append((ok, "Módulos que se apilan: PB 0 a %.1f, %d pisos de %.1f (desde %s m), cornisa %.2f "
                "arriba de %.2f (alturas de ciudad.rs)" % (
                    ALTO_PB, len(pisos), ALTO_PISO, ", ".join("%.1f" % z for _, z, _ in pisos) or "-",
                    CORNISA, f.alto)))
    luz = sum(1 for v in f.vidrios if v[5])
    arriba = sum(1 for v in f.vidrios if v[2] >= ALTO_PB - 1e-6)
    res.append((luz > 0 and 0.2 <= luz / max(arriba, 1) <= 0.5,
                "Ventanas: %d de los pisos de arriba, %d se prenden (pieza_ventanas_luz, %.0f %%)" % (
                    arriba, luz, 100 * luz / max(arriba, 1))))
    return res


def fotos(f, extra=()):
    c = f.objetos
    pb = [o for o in f.objetos if o.name in ("pieza_planta_baja", "pieza_vidriera", "pieza_toldo")]
    return [
        ("Frente · día", c, "frente", "dia", True),
        ("Costado · día", c, "costado", "dia", True),
        ("3/4 · día", c, "tres_cuartos_bajo", "dia", False),
        ("3/4 · atardecer", c, "tres_cuartos_bajo", "atardecer", False),
        ("Planta baja con la persona de 1,75 m · día", c + ["persona"], "tres_cuartos", "dia", False,
         pb + ["persona"]),
    ] + list(extra)


def main(f, medidas, titulo, extra_fotos=(), antes_fotos=None, entre_fotos=None):
    revision = revisar(f, medidas)
    ok = comun.imprimir_revision(f.p["id"], revision)
    ciudad.guardar_y_exportar(f.p["id"], [f.raiz_obj] + f.objetos + f.extras)
    if "--sin-hoja" not in sys.argv:
        if antes_fotos:
            antes_fotos()
        bpy.context.view_layer.update()
        ciudad.hoja(f.p["id"], titulo, fotos(f, extra_fotos), revision, persona_en=(-2.2, 0, 1.2),
                   antes=entre_fotos)
    if not ok:
        sys.exit(1)
