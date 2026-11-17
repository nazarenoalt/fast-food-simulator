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
    - Barras: puertitas del lado del vendedor (−Z), con tirador negro.
    - Carro grande: sin puertitas; del lado del vendedor queda abierto bajo la mesada (hueco de
      0,5 m de profundidad), con un estante bajo de acero, un estante intermedio, 2 columnas de
      acero en la boca y, en la punta +X, el lugar para la garrafa (separador, cincha negra y
      rejilla de ventilación en el costado). Además: 2 parantes de acero en el frente (afuera
      del telón) y uno en cada costado, 4 patas niveladoras con taco de goma, zócalo de 10 cm,
      ruedas de 8 cm de ancho y manija más gruesa.

Qué se mide (la caja envolvente no sirve: la manija sale solo de un lado y la mesada está
corrida hacia el cliente):
    - ancho y profundidad = el cuerpo pintado (la profundidad, en los paneles de los costados,
      sin las puertitas), igual que `ancho` y `profundidad` del .ron;
    - alto = del piso (las ruedas apoyan en Y = 0) hasta arriba de la mesada = alto_mostrador.
    - Origen = centro del cuerpo pintado en X y Z, a nivel del piso (el centro del .ron, que es
      el que usan los anclajes), no el centro de la caja envolvente.

Objetos que se exportan (bajo un Empty raíz `<id>`):
    pieza_pintura, <id>_estructura (todo lo demás, en un solo objeto),
    <id>-colonly (cuerpo + ruedas) y <id>_manija-colonly,
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

FAMILIA = "carritos"
PRESUPUESTO = 3000  # base de carrito (guía 3.1)
MAX_MATERIALES = 6  # bases de carrito (guía 4.2)

SUELO = 0.18          # alto del piso del cuerpo con ruedas (carrito.rs)
ALTO_MESADA = 0.04
RADIO_RUEDA = 0.15
ANCHO_RUEDA = 0.06
SALIDA_MANIJA = 0.15
BISEL = 0.012         # muebles / carrito (guía 3.3)

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

def construir(id_base, grande=False, puertas=2):
    """Arma la base. Devuelve un dict con los objetos."""
    d = leer_ron(id_base)
    w, p, a = d["ancho"], d["profundidad"], d["alto"]
    zoc_h = 0.10 if grande else 0.08
    ancho_rueda = 0.08 if grande else ANCHO_RUEDA
    y0 = SUELO + zoc_h          # arriba del zócalo = abajo del cuerpo
    y1 = a - ALTO_MESADA        # arriba del cuerpo = abajo de la mesada
    h = y1 - y0
    pintura_m, = comun.cargar_materiales("M_PinturaCarrito")
    mats = comun.cargar_materiales(*MATERIALES_ESTRUCTURA)

    # ── Cuerpo pintado (pieza_pintura) ──
    bp = bmesh.new()
    if not grande:
        c = piezas.caja(bp, (w, h, p), (0, y0 + h / 2, 0), bisel=BISEL, sin_abajo=True)
        borrar_cara_arriba(bp, c, y1)
        # Puertitas del lado del vendedor (−Z): sobresalen 1,5 cm, el bisel dibuja el contorno.
        margen, luz = 0.09, 0.03
        ancho_p = (w - 2 * margen - (puertas - 1) * luz) / puertas
        yp0, yp1 = y0 + 0.06, y1 - 0.08
        xs_puertas = [-w / 2 + margen + ancho_p / 2 + i * (ancho_p + luz) for i in range(puertas)]
        for x in xs_puertas:
            piezas.caja(bp, (ancho_p, yp1 - yp0, 0.02), (x, (yp0 + yp1) / 2, -p / 2 - 0.005),
                        bisel=0.008)
    else:
        # Bloque del frente, de alto completo; del lado del vendedor queda un hueco abierto
        # de `hueco` de profundidad, cerrado en las puntas por dos paneles.
        hueco = 0.5
        zf0 = -p / 2 + hueco  # cara de atrás del bloque del frente
        c = piezas.caja(bp, (w, h, p / 2 + p / 2 - hueco), (0, y0 + h / 2, (zf0 + p / 2) / 2),
                        bisel=BISEL, sin_abajo=True)
        borrar_cara_arriba(bp, c, y1)
        esp = 0.04
        for sx in (-1, 1):
            c = piezas.caja(bp, (esp, h, hueco + 0.01), (sx * (w / 2 - esp / 2), y0 + h / 2,
                                                         -p / 2 + (hueco + 0.01) / 2 - 0.0),
                            bisel=BISEL, sin_abajo=True)
            borrar_cara_arriba(bp, c, y1)
        # Separador del lugar de la garrafa (punta +X).
        ancho_garrafa = 0.5
        x_sep = w / 2 - esp - ancho_garrafa - 0.015
        c = piezas.caja(bp, (0.03, h, hueco), (x_sep, y0 + h / 2, -p / 2 + hueco / 2 - 0.004),
                        bisel=0.01, sin_abajo=True)
        borrar_cara_arriba(bp, c, y1)
    pintura = piezas.terminar("pieza_pintura", bp, [pintura_m])

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

    if not grande:
        # Tiradores de las puertitas.
        for x in xs_puertas:
            piezas.caja(be, (0.12, 0.022, 0.02), (x, yp1 - 0.06, -p / 2 - 0.028), mat=NEGRO,
                        bisel=0.005)
    else:
        # Estante bajo (piso del hueco) y estante intermedio, de acero.
        xi0, xi1 = -w / 2 + esp, x_sep - 0.015
        piezas.caja(be, (w - 2 * esp - 0.004, 0.02, hueco - 0.004),
                    (0, y0 + 0.01, -p / 2 + hueco / 2), mat=ACERO, bisel=0.006)
        piezas.caja(be, (xi1 - xi0 - 0.004, 0.02, hueco - 0.024),
                    ((xi0 + xi1) / 2, y0 + h * 0.5, -p / 2 + hueco / 2 + 0.01), mat=ACERO,
                    bisel=0.006)
        # Lugar de la garrafa: cincha de acero de lado a lado y rejilla en el costado.
        xg0, xg1 = x_sep + 0.015, w / 2 - esp
        piezas.caja(be, (xg1 - xg0 + 0.01, 0.04, 0.012), ((xg0 + xg1) / 2, y0 + 0.38, -p / 2 + 0.04),
                    mat=NEGRO, bisel=0.004)
        # Parantes de acero: 2 columnas en la boca del hueco, una en cada costado (tapan la
        # unión de los paneles) y 2 en el frente, afuera del telón (que mide 1,3 m).
        for i in (1, 2):
            x = xi0 + (xi1 - xi0) * i / 3
            piezas.caja(be, (0.035, h - 0.002, 0.035), (x, y0 + h / 2, -p / 2 + 0.0175),
                        mat=ACERO, bisel=0.008)
        for sx in (-1, 1):
            piezas.caja(be, (0.016, h - 0.002, 0.04), (sx * w / 2, y0 + h / 2, zf0), mat=ACERO,
                        bisel=0.006)
            piezas.caja(be, (0.04, h - 0.002, 0.016), (sx * w / 4, y0 + h / 2, p / 2), mat=ACERO,
                        bisel=0.006)
        for i in range(4):
            piezas.caja(be, (0.012, 0.02, 0.3), (w / 2 + 0.002, y0 + 0.22 + i * 0.06,
                                                -p / 2 + hueco / 2), mat=NEGRO, bisel=0.004)
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
    salida_z = p / 2 + 0.01 + ancho_rueda + 0.016  # hasta la taza de las ruedas
    colisiones = [
        piezas.colision_caja(id_base, (w + 0.04, a, 2 * salida_z), (0, a / 2, 0)),
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

    raiz = piezas.raiz(id_base, [pintura, estructura] + colisiones + puntos)
    return {"datos": d, "raiz": raiz, "pintura": pintura, "estructura": estructura,
            "colisiones": colisiones, "puntos": puntos}


# ── Revisión ───────────────────────────────────────────────────────────

def _verts_mundo(obj):
    return [obj.matrix_world @ v.co for v in obj.data.vertices]


def revisar(m, tol=0.002):
    """comun.revisar() con dos chequeos cambiados (ver docstring del módulo): las medidas y
    el origen se miden sobre el cuerpo pintado y la mesada, no sobre la caja envolvente."""
    d = m["datos"]
    w, p, a = d["ancho"], d["profundidad"], d["alto"]
    visibles = [m["pintura"], m["estructura"]]
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
    por_nombre = {e.name: e for e in m["puntos"]}
    puntos_ok = set(por_nombre) == set(esperados) and all(
        (por_nombre[n].matrix_world.translation - piezas.g2b(pos)).length < 1e-5 and
        abs(math.remainder(por_nombre[n].matrix_world.to_euler().z - math.radians(rot), 2 * math.pi)) < 1e-4
        for n, (pos, rot) in esperados.items())
    nuevos.append((puntos_ok, "Puntos: %d punto_<anclaje> + entrega + fila, en las posiciones "
                   "del .ron" % len(d["anclajes"])))
    return nuevos


# ── Hoja de revisión ───────────────────────────────────────────────────

DIRECCIONES = {  # en Blender (frente = −Y)
    "frente": (Vector((0, -1, 0)), True),
    "costado": (Vector((-1, 0, 0)), True),          # del lado de la manija
    "tres_cuartos": (Vector((1, -1.3, 0.9)), False),
    "vendedor": (Vector((-1, 1.3, 0.8)), False),     # 3/4 desde atrás, lado manija
    "persona": (Vector((-1.1, -1.3, 0.55)), False),
    "abajo": (Vector((1, -1.1, 0.25)), False),       # 3/4 bajo: ruedas
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
    piezas_v = [m["pintura"], m["estructura"]]
    cuadros = sacar_fotos([
        ("Frente (lo que ve el cliente) · día", piezas_v, "frente", "dia"),
        ("Costado, lado de la manija · día", piezas_v, "costado", "dia"),
        ("3/4 · día", piezas_v, "tres_cuartos", "dia"),
        ("3/4 lado del vendedor · día", piezas_v, "vendedor", "dia"),
        ("3/4 · atardecer", piezas_v, "tres_cuartos", "atardecer"),
        ("Con el vendedor de 1,75 m · día", piezas_v + [persona], "persona", "dia"),
    ])
    w, p, a = d["ancho"], d["profundidad"], d["alto"]
    comun.componer_hoja(
        f"{m['raiz'].name} · {w:.2f} × {a:.2f} × {p:.2f} m · {descripcion}".replace(".", ","),
        cuadros, revision, comun.RAIZ / f"docs/arte/revisiones/{m['raiz'].name}.jpg",
    )


def main(id_base, descripcion, grande=False, puertas=2):
    comun.escena_vacia()
    m = construir(id_base, grande=grande, puertas=puertas)
    revision = revisar(m)
    ok = comun.imprimir_revision(id_base, revision)
    comun.guardar_blend(comun.RAIZ / f"arte/fuentes/{FAMILIA}/{id_base}.blend")
    comun.exportar_glb([m["raiz"], m["pintura"], m["estructura"]] + m["colisiones"] + m["puntos"],
                       comun.RAIZ / f"godot/modelos/{FAMILIA}/{id_base}.glb")
    if "--sin-hoja" not in sys.argv:
        hoja_revision(m, revision, descripcion)
    if not ok:
        sys.exit(1)
