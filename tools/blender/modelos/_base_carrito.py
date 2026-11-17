"""Construcción común de las bases de carrito (`barra_chica`, `barra_mediana`, `carro_grande`).

Cada script de modelo (`<id>.py`) solo dice qué base es y llama a main(). Las medidas, los
anclajes, la entrega y la fila se leen del .ron de la base (godot/data/carritos/<id>.ron),
así el modelo no se desfasa de los datos.

Diseño (guía 5.2), igual que la base de piezas simples que arma hoy el juego
(rust/game/src/carrito.rs, construir_base), en ejes de Godot (frente/cliente = +Z):
    - Cuerpo pintado `pieza_pintura` (M_PinturaCarrito: el juego lo tiñe con el color
      elegido): ancho × profundidad del .ron, desde el zócalo hasta abajo de la mesada.
    - Zócalo de acero de 8 cm (10 cm en el carro grande) que sobresale 8 mm, a 0,18 m del piso.
    - Mesada de acero de (ancho + 0,04) × 0,04 × (profundidad + 0,06), corrida 0,02 hacia el
      cliente (sobresale 2 cm a los costados, 1 cm atrás y 5 cm adelante), con las esquinas
      redondeadas y el borde de arriba con bisel de 2 segmentos. Arriba de todo = alto_mostrador.
    - Cantoneras de acero en las 4 esquinas verticales.
    - 4 ruedas de goma con taza de acero, radio 0,15 (16 lados), en x = ±(ancho/2 − 0,3),
      afuera del cuerpo (adelante y atrás), sobre 2 ejes con su larguero (M_MetalOscuro).
    - Manija para empujar del lado −X, a alto_mostrador − 0,1, que sale 0,15 m, con puño negro.
    - Bahías (huecos para las alacenas bajo mesada, `_alacena.py`): del lado del vendedor
      (−Z), bajo la mesada, N huecos de medida estándar _alacena.BAHIA = 0,58 × 0,62 × 0,50
      (ancho × alto del piso de la bahía a la mesada × fondo desde la cara del vendedor):
      2 en la barra chica, 3 en la mediana y 4 en el carro grande, centrados y separados por
      montantes pintados de 8 cm (9 cm en el carro grande). El hueco queda prolijo: piso =
      travesaño pintado de abajo (3 cm en las barras, 6 cm en el carro grande, sobre el
      zócalo), paredes = montantes, fondo = bloque del frente, techo = la mesada. Cada bahía
      tiene un Empty `punto_bahia_<n>` (de −X a +X) en el centro de la boca, a nivel del piso
      de la bahía: ahí va el origen de la alacena.
    - Lo que tapa cada bahía cuando no hay alacena es un objeto aparte
      `pieza_tapa_bahia_<n>`, que el juego esconde al poner una alacena:
        barras: puertita pintada (M_PinturaCarrito) con tirador negro, montada sobre la cara
                del vendedor (sale 2 cm, tapa 1 cm de cada lado del hueco);
        carro grande: el estante intermedio de acero de esa bahía (el carro sigue abierto del
                lado del vendedor, como antes; con una alacena el estante se saca).
      Origen de cada tapa = su `punto_bahia_<n>`.
    - El cuerpo pintado se arma por partes para dejar los huecos: costados, bloque del frente
      (del fondo de las bahías al cliente), travesaño de abajo y montantes, encastrados 1 mm
      (en las barras, los costados son de 1,5 cm: la junta queda en el borde de la cantonera).
    - Carro grande: en la punta +X, el lugar para la garrafa (separador, piso de acero, cincha
      negra y rejilla de ventilación en el costado). Además: 2 parantes de acero en el frente
      (afuera del telón) y uno en cada costado, 4 patas niveladoras con taco de goma, zócalo de
      10 cm, ruedas de 8 cm de ancho y manija más gruesa.

Qué se mide (la caja envolvente no sirve: la manija sale solo de un lado y la mesada está
corrida hacia el cliente):
    - ancho y profundidad = el cuerpo pintado (la profundidad, en los paneles de los costados,
      sin las puertitas), igual que `ancho` y `profundidad` del .ron;
    - alto = del piso (las ruedas apoyan en Y = 0) hasta arriba de la mesada = alto_mostrador.
    - Origen = centro del cuerpo pintado en X y Z, a nivel del piso (el centro del .ron, que es
      el que usan los anclajes), no el centro de la caja envolvente.

Objetos que se exportan (bajo un Empty raíz `<id>`):
    pieza_pintura, <id>_estructura (todo lo demás, en un solo objeto),
    pieza_tapa_bahia_<n>, punto_bahia_<n>,
    <id>-colonly (cuerpo + ruedas, con las bahías libres: varias cajas en un objeto, para que la
    alacena y los paquetes puedan entrar) y <id>_manija-colonly,
    punto_<anclaje> para cada anclaje del .ron (con su rot_y), punto_entrega y punto_fila.
"""
import math
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import bpy  # noqa: E402  (antes que bmesh)
import bmesh  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import comun  # noqa: E402
import piezas  # noqa: E402
import _alacena  # noqa: E402  (la medida de las bahías)

FAMILIA = "carritos"
PRESUPUESTO = 3000  # base de carrito (guía 3.1)
MAX_MATERIALES = 6  # bases de carrito (guía 4.2)

SUELO = 0.18          # alto del piso del cuerpo con ruedas (carrito.rs)
ALTO_MESADA = 0.04
RADIO_RUEDA = 0.15
ANCHO_RUEDA = 0.06
SALIDA_MANIJA = 0.15
BISEL = 0.012         # muebles / carrito (guía 3.3)
EPS = 0.001           # encastre entre partes del cuerpo (evita vértices que coinciden)
BAHIA_W, BAHIA_H, BAHIA_D = _alacena.BAHIA
BAHIAS = {"barra_chica": 2, "barra_mediana": 3, "carro_grande": 4}

# Índices de material del objeto <id>_estructura.
ACERO, GOMA, NEGRO, OSCURO = range(4)
MATERIALES_ESTRUCTURA = ("M_Acero", "M_Goma", "M_PlasticoNegro", "M_MetalOscuro")


# ── Datos ──────────────────────────────────────────────────────────────

def _vec(texto):
    return tuple(float(x) for x in texto.split(","))


def leer_ron(id_base):
    """Lee lo que hace falta del .ron de la base (no es un parser RON completo)."""
    texto = (comun.RAIZ / f"godot/data/carritos/{id_base}.ron").read_text()
    texto = re.sub(r"//[^\n]*", "", texto)

    def num(campo):
        return float(re.search(rf"\b{campo}:\s*([-\d.]+)", texto).group(1))

    def tupla(campo):
        return _vec(re.search(rf"\b{campo}:\s*\(([^)]*)\)", texto).group(1))

    anclajes = [
        (m.group(1), _vec(m.group(2)), float(m.group(3) or 0.0))
        for m in re.finditer(
            r'\(\s*id:\s*"(\w+)",\s*pos:\s*\(([^)]*)\)(?:,\s*rot_y:\s*([-\d.]+))?', texto)
    ]
    return {
        "ancho": num("ancho"), "profundidad": num("profundidad"),
        "alto": num("alto_mostrador"), "ruedas": "ruedas: true" in texto,
        "entrega": tupla("entrega"), "fila": tupla("fila"), "anclajes": anclajes,
    }


# ── Piezas propias ─────────────────────────────────────────────────────

def losa(bm, medidas, centro, radio, seg=4, bisel_arriba=0.01, bisel_abajo=0.006, mat=0):
    """Placa (mesada) de medidas Godot (X, Y, Z) con esquinas verticales redondeadas
    (radio, seg segmentos por esquina) y biseles en el borde de arriba (2 segmentos) y abajo."""
    ancho, alto, prof = medidas
    hx, hy = ancho / 2 - radio, prof / 2 - radio  # en ejes de Blender (Y = −Z de Godot)
    contorno = []
    for cx, cy, a0 in ((hx, -hy, -90), (hx, hy, 0), (-hx, hy, 90), (-hx, -hy, 180)):
        for i in range(seg + 1):
            a = math.radians(a0 + 90 * i / seg)
            contorno.append((cx + radio * math.cos(a), cy + radio * math.sin(a)))
    previas = set(bm.faces)
    abajo = [bm.verts.new((x, y, -alto / 2)) for x, y in contorno]
    arriba = [bm.verts.new((x, y, alto / 2)) for x, y in contorno]
    n = len(contorno)
    for k in range(n):
        bm.faces.new((abajo[k], abajo[(k + 1) % n], arriba[(k + 1) % n], arriba[k]))
    tapa = bm.faces.new(arriba)
    fondo = bm.faces.new(list(reversed(abajo)))
    bmesh.ops.bevel(bm, geom=list(tapa.edges), offset=bisel_arriba, segments=2,
                    affect="EDGES", profile=0.5, clamp_overlap=True)
    bmesh.ops.bevel(bm, geom=list(fondo.edges), offset=bisel_abajo, segments=1,
                    affect="EDGES", profile=0.5, clamp_overlap=True)
    nuevas = piezas._marcar(bm, previas, mat)
    piezas.mover(bm, nuevas, centro)
    return nuevas


def torno(bm, perfil, centro, signo=1, lados=16, mats=None):
    """Pieza de revolución sobre el eje Z de Godot (ruedas). perfil = [(radio, z)] de
    adentro hacia afuera; signo = +1 si "afuera" es +Z, −1 si es −Z. mats[i] = material de la
    banda entre el punto i y el i+1 (las tapas usan el de su banda vecina). Los radios son de
    las caras planas (no de las aristas), y una cara plana queda abajo: así la rueda apoya justo
    en el piso."""
    mats = mats or [0] * (len(perfil) - 1)
    aj = 1 / math.cos(math.pi / lados)
    giro = math.pi / lados
    previas = set(bm.faces)
    anillos = []
    for r, z in perfil:
        anillos.append([bm.verts.new((r * aj * math.cos(giro + 2 * math.pi * k / lados),
                                      r * aj * math.sin(giro + 2 * math.pi * k / lados),
                                      z * signo)) for k in range(lados)])
    for i, (a, b) in enumerate(zip(anillos, anillos[1:])):
        for k in range(lados):
            f = bm.faces.new((a[k], a[(k + 1) % lados], b[(k + 1) % lados], b[k]))
            f.material_index = mats[i]
    for anillo, m in ((anillos[0], mats[0]), (anillos[-1], mats[-1])):
        f = bm.faces.new(anillo)
        f.material_index = m
    nuevas = [f for f in bm.faces if f not in previas]
    # Armado sobre Z de Blender → acostado sobre Z de Godot (como piezas.cilindro eje="z").
    bmesh.ops.rotate(bm, verts=piezas._verts(nuevas), matrix=Matrix.Rotation(math.pi / 2, 3, "X"))
    piezas.mover(bm, nuevas, centro)
    return nuevas


def borrar_cara_arriba(bm, caras, y_arriba):
    """Borra la cara de arriba de una caja (la que queda tapada por la mesada, guía 3.6)."""
    z = y_arriba  # Y de Godot = Z de Blender
    tapa = [f for f in caras if f.is_valid and f.normal.z > 0.999 and
            all(abs(v.co.z - z) < 1e-6 for v in f.verts)]
    bmesh.ops.delete(bm, geom=tapa, context="FACES_ONLY")


def rueda(bm, x, z_lado, p, ancho=ANCHO_RUEDA):
    """Rueda de goma con taza de acero. z_lado = ±1 (adelante / atrás)."""
    r = RADIO_RUEDA
    zc = z_lado * (p / 2 + 0.01 + ancho / 2)
    h = ancho / 2
    perfil = [  # (radio, z) de adentro (cuerpo) hacia afuera
        (r - 0.025, -h),
        (r, -h + 0.018),
        (r, h - 0.018),
        (r - 0.025, h),
        (0.07, h),           # flanco de la goma → empieza la taza
        (0.045, h + 0.016),  # taza abombada
    ]
    torno(bm, perfil, (x, r, zc), signo=z_lado, mats=[GOMA, GOMA, GOMA, GOMA, ACERO])


# ── Modelo ─────────────────────────────────────────────────────────────

def centros_bahias(x_izq, x_der, n, sep):
    """X de los centros de n bahías centradas entre x_izq y x_der, separadas por montantes."""
    total = n * BAHIA_W + (n - 1) * sep
    x0 = (x_izq + x_der) / 2 - total / 2 + BAHIA_W / 2
    return [x0 + i * (BAHIA_W + sep) for i in range(n)]


def macizos(x_izq, x_der, xs):
    """Tramos en X entre x_izq y x_der que no son bahías (montantes)."""
    bordes = [x_izq] + [b for x in xs for b in (x - BAHIA_W / 2, x + BAHIA_W / 2)] + [x_der]
    return [(bordes[i], bordes[i + 1]) for i in range(0, len(bordes), 2)]


def frente_vendedor(bp, x_izq, x_der, xs, z_boca, z_fondo, y0, y_piso, y1):
    """Travesaño de abajo y montantes pintados entre las bahías (del lado del vendedor).
    Se encastran 1 cm en el bloque del frente y 1 mm en los costados."""
    zc, prof = (z_boca + z_fondo + 0.01) / 2, z_fondo + 0.01 - z_boca
    piezas.caja(bp, (x_der - x_izq + 2 * EPS, y_piso - y0, prof), ((x_izq + x_der) / 2, (y0 + y_piso) / 2, zc),
                bisel=BISEL, sin_abajo=True)
    for xa, xb in macizos(x_izq - EPS, x_der + EPS, xs):
        c = piezas.caja(bp, (xb - xa, y1 - y_piso + EPS, prof), ((xa + xb) / 2, (y_piso - EPS + y1) / 2, zc),
                        bisel=BISEL)
        borrar_cara_arriba(bp, c, y1)


def objeto_en(nombre, bm, materiales, origen_godot):
    """Termina el bmesh y deja el origen del objeto en origen_godot (sin mover la malla)."""
    bmesh.ops.translate(bm, vec=-piezas.g2b(origen_godot), verts=bm.verts)
    obj = piezas.terminar(nombre, bm, materiales)
    obj.location = piezas.g2b(origen_godot)
    return obj


def colision_cajas(nombre, cajas):
    """Objeto `<nombre>-colonly` con varias cajas [(medidas, centro)] (guía 6.1)."""
    bm = bmesh.new()
    for med, centro in cajas:
        piezas.caja(bm, med, centro)
    malla = bpy.data.meshes.new(f"{nombre}-colonly")
    bm.to_mesh(malla)
    bm.free()
    obj = bpy.data.objects.new(f"{nombre}-colonly", malla)
    bpy.context.scene.collection.objects.link(obj)
    obj.display_type = "WIRE"
    obj.hide_render = True
    return obj


def construir(id_base, grande=False, bahias=None):
    """Arma la base. Devuelve un dict con los objetos."""
    d = leer_ron(id_base)
    w, p, a = d["ancho"], d["profundidad"], d["alto"]
    n_bahias = bahias or BAHIAS[id_base]
    zoc_h = 0.10 if grande else 0.08
    ancho_rueda = 0.08 if grande else ANCHO_RUEDA
    y0 = SUELO + zoc_h          # arriba del zócalo = abajo del cuerpo
    y1 = a - ALTO_MESADA        # arriba del cuerpo = abajo de la mesada
    h = y1 - y0
    y_piso = y1 - BAHIA_H       # piso de las bahías
    z_boca, z_fondo = -p / 2, -p / 2 + BAHIA_D
    pintura_m, = comun.cargar_materiales("M_PinturaCarrito")
    mats = comun.cargar_materiales(*MATERIALES_ESTRUCTURA)

    # ── Cuerpo pintado (pieza_pintura) ──
    bp = bmesh.new()
    if not grande:
        esp = 0.015  # costados finos: la junta con el bloque del frente cae en la cantonera
        for sx in (-1, 1):
            c = piezas.caja(bp, (esp, h, p), (sx * (w / 2 - esp / 2), y0 + h / 2, 0), bisel=0.006,
                            sin_abajo=True)
            borrar_cara_arriba(bp, c, y1)
        x_izq, x_der = -w / 2 + esp, w / 2 - esp
        xs_bahias = centros_bahias(-w / 2, w / 2, n_bahias, 0.08)
    else:
        # Del lado del vendedor, de punta a punta: bahías y, en la punta +X, el lugar de la
        # garrafa (abierto), cerrado en las puntas por dos paneles.
        esp = 0.04
        for sx in (-1, 1):
            c = piezas.caja(bp, (esp, h, BAHIA_D + 0.01), (sx * (w / 2 - esp / 2), y0 + h / 2,
                                                            z_boca + (BAHIA_D + 0.01) / 2),
                            bisel=BISEL, sin_abajo=True)
            borrar_cara_arriba(bp, c, y1)
        # Separador del lugar de la garrafa (punta +X).
        ancho_garrafa = 0.5
        x_sep = w / 2 - esp - ancho_garrafa - 0.015
        c = piezas.caja(bp, (0.03, h, BAHIA_D), (x_sep, y0 + h / 2, z_boca + BAHIA_D / 2 - 0.004),
                        bisel=0.01, sin_abajo=True)
        borrar_cara_arriba(bp, c, y1)
        x_izq, x_der = -w / 2 + esp, x_sep - 0.015
        xs_bahias = centros_bahias(x_izq, x_der, n_bahias, 0.09)
    # Bloque del frente: del fondo de las bahías hasta el cliente, de alto completo.
    xb = w / 2 if grande else w / 2 - esp + EPS
    c = piezas.caja(bp, (2 * xb, h, p / 2 - z_fondo), (0, y0 + h / 2, (z_fondo + p / 2) / 2),
                    bisel=BISEL, sin_abajo=True)
    borrar_cara_arriba(bp, c, y1)
    frente_vendedor(bp, x_izq, x_der, xs_bahias, z_boca, z_fondo, y0, y_piso, y1)
    pintura = piezas.terminar("pieza_pintura", bp, [pintura_m])

    # ── Tapas de las bahías (el juego las esconde cuando hay una alacena) ──
    tapas, puntos_bahia = [], []
    for i, xc in enumerate(xs_bahias):
        bt = bmesh.new()
        if not grande:
            # Puertita pintada sobre la cara del vendedor, con tirador negro arriba.
            ya, yb = y_piso - 0.012, y1 - 0.006
            piezas.caja(bt, (BAHIA_W + 0.02, yb - ya, 0.02), (xc, (ya + yb) / 2, z_boca - 0.011),
                        mat=0, bisel=0.008)
            piezas.caja(bt, (0.12, 0.022, 0.02), (xc, yb - 0.06, z_boca - 0.030), mat=1, bisel=0.005)
            tapa_mats = [pintura_m, mats[NEGRO]]
        else:
            # Estante intermedio de acero de la bahía.
            piezas.caja(bt, (BAHIA_W - 0.002, 0.02, BAHIA_D - 0.03),
                        (xc, y_piso + BAHIA_H / 2, z_boca + 0.02 + (BAHIA_D - 0.03) / 2),
                        mat=0, bisel=0.006)
            tapa_mats = [mats[ACERO]]
        tapas.append(objeto_en(f"pieza_tapa_bahia_{i + 1}", bt, tapa_mats, (xc, y_piso, z_boca)))
        puntos_bahia.append(piezas.punto(f"punto_bahia_{i + 1}", (xc, y_piso, z_boca)))

    # ── Estructura (acero, goma, negro, metal oscuro) ──
    be = bmesh.new()
    # Mesada (carrito.rs: ancho+0,04 × 0,04 × prof+0,06, corrida 0,02 hacia el cliente).
    losa(be, (w + 0.04, ALTO_MESADA, p + 0.06), (0, a - ALTO_MESADA / 2, 0.02), radio=0.035,
         mat=ACERO)
    # Zócalo.
    piezas.caja(be, (w + 0.016, zoc_h, p + 0.016), (0, SUELO + zoc_h / 2, 0), mat=ACERO,
                bisel=0.01)
    # Cantoneras en las esquinas verticales.
    for sx in (-1, 1):
        for sz in (-1, 1):
            piezas.caja(be, (0.03, h - 0.002, 0.03), (sx * w / 2, y0 + h / 2, sz * p / 2),
                        mat=ACERO, bisel=0.008)
    # Ruedas, ejes y largueros.
    xr = w / 2 - 0.3
    for sx in (-1, 1):
        for sz in (-1, 1):
            rueda(be, sx * xr, sz, p, ancho_rueda)
        piezas.cilindro(be, 0.02, p + 0.08, (sx * xr, RADIO_RUEDA, 0), eje="z", lados=12,
                        mat=OSCURO)
        piezas.caja(be, (0.07, 0.035, p - 0.06), (sx * xr, SUELO - 0.0125, 0), mat=OSCURO,
                    bisel=0.008)
    # Manija para empujar (−X).
    r_tubo = 0.02 if grande else 0.015
    ym = a - 0.1
    xm = -w / 2 - SALIDA_MANIJA
    zb = p * 0.4
    for sz in (-1, 1):
        largo = SALIDA_MANIJA + r_tubo + 0.01
        piezas.cilindro(be, r_tubo, largo, (-w / 2 + 0.01 - largo / 2, ym, sz * zb), eje="x",
                        lados=12, mat=ACERO)
        piezas.caja(be, (0.012, 0.075, 0.075), (-w / 2 - 0.006, ym, sz * zb), mat=ACERO,
                    bisel=0.004)
    piezas.cilindro(be, r_tubo, 2 * zb + 2 * r_tubo, (xm, ym, 0), eje="z", lados=12, mat=ACERO)
    piezas.cilindro(be, r_tubo + 0.008, p * 0.45, (xm, ym, 0), eje="z", lados=12, mat=NEGRO)

    if grande:
        # Lugar de la garrafa: piso de acero, cincha negra de lado a lado y rejilla en el costado.
        xg0, xg1 = x_sep + 0.015, w / 2 - esp
        piezas.caja(be, (xg1 - xg0 - 0.004, 0.02, BAHIA_D - 0.004),
                    ((xg0 + xg1) / 2, y0 + 0.01, z_boca + BAHIA_D / 2), mat=ACERO, bisel=0.006)
        piezas.caja(be, (xg1 - xg0 + 0.01, 0.04, 0.012), ((xg0 + xg1) / 2, y0 + 0.38, z_boca + 0.04),
                    mat=NEGRO, bisel=0.004)
        # Parantes de acero: uno en cada costado (tapan la unión de los paneles) y 2 en el
        # frente, afuera del telón (que mide 1,3 m).
        for sx in (-1, 1):
            piezas.caja(be, (0.016, h - 0.002, 0.04), (sx * w / 2, y0 + h / 2, z_fondo), mat=ACERO,
                        bisel=0.006)
            piezas.caja(be, (0.04, h - 0.002, 0.016), (sx * w / 4, y0 + h / 2, p / 2), mat=ACERO,
                        bisel=0.006)
        for i in range(4):
            piezas.caja(be, (0.012, 0.02, 0.3), (w / 2 + 0.002, y0 + 0.22 + i * 0.06,
                                                z_boca + BAHIA_D / 2), mat=NEGRO, bisel=0.004)
        # Patas niveladoras (bajadas) con taco de goma.
        for sx in (-1, 1):
            for sz in (-1, 1):
                x, z = sx * (w / 2 - 0.12), sz * (p / 2 - 0.12)
                piezas.cilindro(be, 0.022, SUELO - 0.03 + 0.01, (x, 0.03 + (SUELO - 0.02) / 2, z),
                                lados=12, mat=OSCURO, tapas=(False, False))
                piezas.cilindro(be, 0.05, 0.03, (x, 0.015, z), lados=16, mat=GOMA,
                                tapas=(False, True))
    estructura = piezas.terminar(f"{id_base}_estructura", be, mats)

    # ── Colisión y puntos ──
    # Cuerpo: varias cajas que dejan libres las bahías (la alacena trae su propia colisión).
    salida_z = p / 2 + 0.01 + ancho_rueda + 0.016  # hasta la taza de las ruedas
    W = w + 0.04
    cajas = [
        ((W, a, salida_z - z_fondo), (0, a / 2, (z_fondo + salida_z) / 2)),               # frente
        ((W, y_piso, z_fondo + salida_z), (0, y_piso / 2, (z_fondo - salida_z) / 2)),     # abajo
        ((W, a - y1, z_fondo - z_boca + 0.01), (0, (y1 + a) / 2, (z_boca - 0.01 + z_fondo) / 2)),
    ]
    for xa, xb_ in macizos(-W / 2, W / 2, xs_bahias):
        cajas.append(((xb_ - xa, y1 - y_piso, z_fondo - z_boca),
                      ((xa + xb_) / 2, (y_piso + y1) / 2, (z_boca + z_fondo) / 2)))
    colisiones = [
        colision_cajas(id_base, cajas),
        piezas.colision_caja(f"{id_base}_manija", (SALIDA_MANIJA + 2 * r_tubo, 0.06, 2 * zb + 0.06),
                             (-w / 2 - SALIDA_MANIJA / 2 - r_tubo, ym, 0)),
    ]
    puntos = []
    for nombre, pos, rot_y in d["anclajes"]:
        e = piezas.punto(f"punto_{nombre}", pos)
        e.rotation_euler.z = math.radians(rot_y)  # rot_y de Godot = giro sobre Z de Blender
        puntos.append(e)
    puntos.append(piezas.punto("punto_entrega", d["entrega"]))
    puntos.append(piezas.punto("punto_fila", d["fila"]))

    raiz = piezas.raiz(id_base, [pintura, estructura] + tapas + colisiones + puntos + puntos_bahia)
    return {"datos": d, "raiz": raiz, "pintura": pintura, "estructura": estructura,
            "tapas": tapas, "colisiones": colisiones, "puntos": puntos + puntos_bahia,
            "puntos_anclaje": puntos, "puntos_bahia": puntos_bahia,
            "bahias": [(xc, y_piso, z_boca) for xc in xs_bahias], "y1": y1}


# ── Revisión ───────────────────────────────────────────────────────────

def _verts_mundo(obj):
    return [obj.matrix_world @ v.co for v in obj.data.vertices]


def revisar(m, tol=0.002):
    """comun.revisar() con dos chequeos cambiados (ver docstring del módulo): las medidas y
    el origen se miden sobre el cuerpo pintado y la mesada, no sobre la caja envolvente."""
    d = m["datos"]
    w, p, a = d["ancho"], d["profundidad"], d["alto"]
    visibles = [m["pintura"], m["estructura"]] + m["tapas"]
    res = comun.revisar(visibles, PRESUPUESTO, (w, a, p), origen="base",
                        max_materiales=MAX_MATERIALES, tolerancia=tol)
    bpy.context.view_layer.update()
    vp = _verts_mundo(m["pintura"])
    todos = vp + _verts_mundo(m["estructura"])
    x0, x1 = min(v.x for v in vp), max(v.x for v in vp)
    costados = [v for v in vp if abs(v.x) > w / 2 - 0.02]  # paneles de los costados
    # Blender Y = −Z de Godot
    z0, z1 = min(-v.y for v in costados), max(-v.y for v in costados)
    piso, techo = min(v.z for v in todos), max(v.z for v in todos)
    medidas_ok = (abs((x1 - x0) - w) <= tol and abs((z1 - z0) - p) <= tol and
                  abs(piso) <= tol and abs(techo - a) <= tol)
    texto_medidas = ("Medidas: cuerpo pintado %.3f × %.3f m, piso a mesada %.3f m "
                     "(.ron: ancho %.3f, profundidad %.3f, alto_mostrador %.3f)" % (
                         x1 - x0, z1 - z0, techo - piso, w, p, a))
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    origen_ok = abs(cx) <= tol and abs(cz) <= tol and abs(piso) <= tol
    texto_origen = ("Origen en el centro del cuerpo pintado (%.3f, %.3f) y a nivel del piso "
                    "(ruedas en Y = %.3f)" % (cx, cz, piso))
    nuevos = []
    for ok, texto in res:
        if texto.startswith("Medidas"):
            nuevos.append((medidas_ok, texto_medidas))
        elif texto.startswith("Origen"):
            nuevos.append((origen_ok, texto_origen))
        else:
            nuevos.append((ok, texto))
    # Puntos de anclaje = posiciones del .ron.
    esperados = {f"punto_{n}": (pos, rot) for n, pos, rot in d["anclajes"]}
    esperados["punto_entrega"] = (d["entrega"], 0.0)
    esperados["punto_fila"] = (d["fila"], 0.0)
    por_nombre = {e.name: e for e in m["puntos_anclaje"]}
    puntos_ok = set(por_nombre) == set(esperados) and all(
        (por_nombre[n].matrix_world.translation - piezas.g2b(pos)).length < 1e-5 and
        abs(math.remainder(por_nombre[n].matrix_world.to_euler().z - math.radians(rot), 2 * math.pi)) < 1e-4
        for n, (pos, rot) in esperados.items())
    nuevos.append((puntos_ok, "Puntos: %d punto_<anclaje> + entrega + fila, en las posiciones "
                   "del .ron" % len(d["anclajes"])))
    nuevos.append(chequeo_bahias(m))
    return nuevos


def chequeo_bahias(m):
    """Cada bahía: su punto_bahia y su pieza_tapa_bahia, el hueco libre (ningún vértice del
    cuerpo ni de la estructura adentro), con piso, paredes, fondo y techo (la mesada), y la
    caja de la alacena entra."""
    d = m["datos"]
    n = BAHIAS[m["raiz"].name]
    vs = [Vector((v.x, v.z, -v.y)) for o in (m["pintura"], m["estructura"]) for v in _verts_mundo(o)]
    problemas = []
    if len(m["bahias"]) != n or len(m["tapas"]) != n:
        problemas.append("cantidad")
    for i, ((xc, yp, zb), e, t) in enumerate(zip(m["bahias"], m["puntos_bahia"], m["tapas"])):
        if e.name != f"punto_bahia_{i + 1}" or t.name != f"pieza_tapa_bahia_{i + 1}":
            problemas.append(f"nombres {i + 1}")
        if (e.matrix_world.translation - piezas.g2b((xc, yp, zb))).length > 1e-5:
            problemas.append(f"punto {i + 1}")
        x0, x1, y1, z1 = xc - BAHIA_W / 2, xc + BAHIA_W / 2, yp + BAHIA_H, zb + BAHIA_D
        adentro = [v for v in vs if x0 + 1e-3 < v.x < x1 - 1e-3 and yp + 1e-3 < v.y < y1 - 1e-3
                   and zb + 1e-3 < v.z < z1 - 1e-3]
        if adentro:
            problemas.append(f"hueco {i + 1} ocupado")

        def hay(cond):
            return any(cond(v) for v in vs)
        en_boca = lambda v: zb - 1e-3 <= v.z <= z1 + 1e-3  # noqa: E731
        paredes = [
            hay(lambda v: abs(v.y - yp) < 1e-4 and x0 - 1e-3 <= v.x <= x1 + 1e-3 and en_boca(v)),
            hay(lambda v: abs(v.y - y1) < 1e-4 and x0 <= v.x and v.x <= x1 + 0.1),  # mesada
            hay(lambda v: abs(v.x - x0) < 1e-4 and en_boca(v)),
            hay(lambda v: abs(v.x - x1) < 1e-4 and en_boca(v)),
            hay(lambda v: abs(v.z - z1) < 1e-4 and x0 - 0.02 <= v.x <= x1 + 0.02),
        ]
        if not all(paredes):
            problemas.append(f"hueco {i + 1} abierto")
    entra = all(c < b for c, b in zip(_alacena.CAJA, _alacena.BAHIA))
    texto = ("Bahías: %d de %.2f × %.2f × %.2f con punto_bahia y pieza_tapa_bahia, huecos libres y "
             "cerrados; entra la alacena (caja %.2f × %.2f × %.2f)" % (
                 n, BAHIA_W, BAHIA_H, BAHIA_D, *_alacena.CAJA))
    return not problemas and entra, texto + ("" if not problemas else " — " + ", ".join(problemas))


# ── Hoja de revisión ───────────────────────────────────────────────────

DIRECCIONES = {  # en Blender (frente = −Y)
    "frente": (Vector((0, -1, 0)), True),
    "costado": (Vector((-1, 0, 0)), True),          # del lado de la manija
    "tres_cuartos": (Vector((1, -1.3, 0.9)), False),
    "vendedor": (Vector((-1, 1.3, 0.8)), False),     # 3/4 desde atrás, lado manija
    "persona": (Vector((-1.1, -1.3, 0.55)), False),
    "abajo": (Vector((1, -1.1, 0.25)), False),       # 3/4 bajo: ruedas
    "atras": (Vector((0, 1, 0)), True),              # de atrás: lado del vendedor
    "vendedor_derecha": (Vector((1, 1.3, 0.75)), False),  # 3/4 desde atrás, lado +X
}

# Alacenas que se ponen en las bahías para la foto (de −X a +X).
ALACENAS_FOTO = {
    "barra_chica": ["puertas", "cajones"],
    "barra_mediana": ["puertas", "mixta", "cajones"],
    "carro_grande": ["puertas", "cajones", "abierta", "mixta"],
}


def encuadrar(objetos, vista, margen=1.15):
    esquinas = [o.matrix_world @ Vector(c) for o in objetos for c in o.bound_box]
    minimo = Vector(map(min, *esquinas))
    maximo = Vector(map(max, *esquinas))
    centro = (minimo + maximo) / 2
    tam = maximo - minimo
    d, orto = DIRECCIONES[vista]
    d = d.normalized()
    cam = comun._camara()
    escena = bpy.context.scene
    aspecto = escena.render.resolution_x / escena.render.resolution_y
    radio = tam.length / 2
    if orto:
        cam.data.type = "ORTHO"
        ancho_vis = abs(d.y) * tam.x + abs(d.x) * tam.y
        cam.data.ortho_scale = max(ancho_vis, tam.z * aspecto) * margen
        cam.location = centro + d * (radio * 4 + 1)
    else:
        cam.data.type = "PERSP"
        cam.data.lens = 50
        medio = math.atan(cam.data.sensor_width / aspecto / 2 / cam.data.lens)
        cam.location = centro + d * (radio * 0.85 / math.sin(medio))
    cam.data.clip_start = 0.05
    cam.data.clip_end = radio * 100 + 10
    cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()


def sacar_fotos(pedidos):
    """Como comun.sacar_fotos, con las vistas propias de DIRECCIONES."""
    tmp = Path(tempfile.mkdtemp())
    todos = {o for _, objs, *_ in pedidos for o in objs}
    cuadros = []
    for etiqueta, objs, vista, luz in pedidos:
        comun.poner_luz(luz)
        for o in todos:
            o.hide_render = o not in objs
        encuadrar(objs, vista)
        cuadros.append((etiqueta, comun.render(tmp / f"{len(cuadros)}.png")))
    return cuadros


def hoja_revision(m, revision, descripcion):
    d = m["datos"]
    comun.preparar_revision()
    persona = bpy.data.objects["ref_persona_1,75m"]
    # El vendedor, parado atrás del mostrador (lado −Z de Godot = +Y de Blender).
    persona.location = (0.25 * d["ancho"], d["profundidad"] / 2 + 0.3, 0)
    piezas_v = [m["pintura"], m["estructura"]] + m["tapas"]
    sin_tapas = [m["pintura"], m["estructura"]]
    con_alacenas = list(sin_tapas)
    for variante, punto in zip(ALACENAS_FOTO[m["raiz"].name], m["puntos_bahia"]):
        al = _alacena.construir(variante)
        al["raiz"].location = punto.matrix_world.translation
        al["colision"].hide_render = True
        con_alacenas += _alacena.visibles(al)
    bpy.context.view_layer.update()
    cuadros = sacar_fotos([
        ("Frente (lo que ve el cliente) · día", piezas_v, "frente", "dia"),
        ("Costado, lado de la manija · día", piezas_v, "costado", "dia"),
        ("3/4 · día", piezas_v, "tres_cuartos", "dia"),
        ("3/4 lado del vendedor · día", piezas_v, "vendedor", "dia"),
        ("3/4 · atardecer", piezas_v, "tres_cuartos", "atardecer"),
        ("Con el vendedor de 1,75 m · día", piezas_v + [persona], "persona", "dia"),
        ("Bahías vacías (sin tapas) · día", sin_tapas, "vendedor", "dia"),
        ("Con alacenas en las bahías · día", con_alacenas, "vendedor", "dia"),
        ("Con alacenas, de atrás · día", con_alacenas, "atras", "dia"),
    ])
    w, p, a = d["ancho"], d["profundidad"], d["alto"]
    comun.componer_hoja(
        f"{m['raiz'].name} · {w:.2f} × {a:.2f} × {p:.2f} m · {descripcion}".replace(".", ","),
        cuadros, revision, comun.RAIZ / f"docs/arte/revisiones/{m['raiz'].name}.jpg",
    )


def main(id_base, descripcion, grande=False):
    comun.escena_vacia()
    m = construir(id_base, grande=grande)
    revision = revisar(m)
    ok = comun.imprimir_revision(id_base, revision)
    comun.guardar_blend(comun.RAIZ / f"arte/fuentes/{FAMILIA}/{id_base}.blend")
    comun.exportar_glb([m["raiz"], m["pintura"], m["estructura"]] + m["tapas"] + m["colisiones"] +
                       m["puntos"],
                       comun.RAIZ / f"godot/modelos/{FAMILIA}/{id_base}.glb")
    if "--sin-hoja" not in sys.argv:
        hoja_revision(m, revision, descripcion)
    if not ok:
        sys.exit(1)
