"""Construcción común de los autos de la ciudad (`auto_a` sedán, `auto_b` chico; familia
`ciudad`). Diseño genérico, sin marcas.

Qué dibuja hoy el juego (rust/game/src/transito.rs): un auto armado mirando a +X con dos
cajas del color del auto (cuerpo 4,1 × 0,65 × 1,75 a 0,6 de alto y cabina 2,1 × 0,55 × 1,6
a 1,2), vidrios gris azulado oscuro opaco, faros y luces traseras que se prenden de noche
(REQ-AMB-09), cuatro ruedas de radio 0,33 y 0,22 de ancho (ejes en x ±1,3, z ±0,82) con su
pivote en el eje, que el código gira según la velocidad (rotate_z(−v·dt / 0,33)), y una
caja de colisión de 4,1 × 1,4 × 1,75 en un AnimatableBody3D que arma el propio código. El
color sale de una lista de 7 (rojo, azul, blanco, negro, gris, amarillo, verde).

Forma (en ejes de Godot, frente = +Z, como pide la guía; el código hoy arma el auto
mirando a +X: al usar el .glb hay que girarlo +90° en Y):
    - Carrocería: un "lofteo" de cortes transversales a lo largo de Z. Cada corte es un
      anillo de 10 puntos (bajo, cintura, hombro, borde del techo y canaleta, a los dos
      lados) que sale de curvas del perfil: alto del techo/capó/baúl, línea de cintura,
      ancho y piso. El piso sube en semicírculo sobre cada rueda (pasarruedas). La franja
      entre el borde del techo y la canaleta queda pintada a lo largo de todo el auto: es lo
      que dibuja los parantes del parabrisas y de la luneta.
    - Vidrios: las caras del lofteo que caen en el parabrisas, la luneta y las ventanillas
      (con el parante del medio pintado) pasan a otro objeto.
    - Espejos (cajas de la carrocería), paragolpes y parrilla de goma.

Vidrios: gris casi negro OPACO (M_Hierro, apenas metálico: refleja algo del cielo). De
lejos se lee mejor que un vidrio transparente (que dejaría ver un auto vacío por dentro),
no tiene problemas de orden de dibujo y es más barato; el código ya usa un vidrio opaco.

Objetos (hijos del Empty `<id>`; origen = centro de la base, a nivel del piso):
    - pieza_carroceria: toda la chapa, un solo material M_PinturaCarrito: el juego le pone
      el color del auto (como pieza_pintura del carrito).
    - <id>_detalles: vidrios (M_Hierro) y paragolpes y parrilla (M_Goma).
    - pieza_rueda_1..4: 1 delantera +X, 2 delantera −X, 3 trasera +X, 4 trasera −X
      (cubierta M_Goma y taza M_Acero), con el origen en su eje (gira en X).
    - pieza_faros: faros delanteros (M_LuzFarol, emisión: el juego los prende de noche).
    - pieza_luces_traseras: M_PilotoApagado (como el piloto del hervidor: el juego las
      enciende de noche).
    Sin `-colonly`: el auto se mueve y el código ya le arma su caja de colisión.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402  (antes que bmesh)
import bmesh  # noqa: E402

import _ciudad as ciudad  # noqa: E402
import comun  # noqa: E402
import piezas  # noqa: E402
from piezas import g2b  # noqa: E402

PRESUPUESTO = 2500  # lista de modelos (vehículo)
MATERIALES = ("M_PinturaCarrito", "M_Hierro", "M_Goma", "M_Acero", "M_LuzFarol", "M_PilotoApagado")
ANCHO_RUEDA = 0.2


def interp(puntos, z):
    """Interpolación lineal en una lista [(z, valor)] ordenada por z."""
    if z <= puntos[0][0]:
        return puntos[0][1]
    for (z0, v0), (z1, v1) in zip(puntos, puntos[1:]):
        if z <= z1:
            return v0 + (v1 - v0) * (z - z0) / (z1 - z0)
    return puntos[-1][1]


class Perfil:
    def __init__(self, p):
        self.p = p
        self.ra = p["radio"] + 0.05            # radio del pasarruedas

    def piso(self, z):
        p = self.p
        y = interp(p["piso_puntas"], z)
        for ze in p["ejes"]:
            dz = z - ze
            if abs(dz) < self.ra:
                y = max(y, p["radio"] + math.sqrt(self.ra ** 2 - dz ** 2))
        return y

    def anillo(self, z):
        p = self.p
        yb = self.piso(z)
        yt = interp(p["techo"], z)
        yc = interp(p["cintura"], z)
        w = interp(p["ancho"], z)
        wt = interp(p["ancho_techo"], z)
        yc = min(yc, yt - 0.04)
        y2 = min(max(0.5, yb + 0.06), yc - 0.05)
        der = [(w * 0.95, yb), (w, y2), (w * 0.98, yc), (wt, yt), (wt - 0.08, yt + 0.008)]
        izq = [(-x, y) for x, y in reversed(der)]
        return [(x, y, z) for x, y in der + izq]

    def estaciones(self):
        p = self.p
        zs = set()
        for clave in ("techo", "cintura", "ancho", "ancho_techo"):
            zs |= {z for z, _ in p[clave]}
        zs |= set(p["parante_b"])
        t0 = math.degrees(math.asin((interp(p["piso_puntas"], 0.0) - p["radio"]) / self.ra))
        for ze in p["ejes"]:
            for t in (t0, 35, 70, 110, 145, 180 - t0):
                zs.add(round(ze + self.ra * math.cos(math.radians(t)), 4))
        largo = p["largo"] / 2
        return sorted(z for z in zs if -largo - 1e-6 <= z <= largo + 1e-6)


def es_vidrio(p, banda, z0, z1):
    medio = (z0 + z1) / 2

    def dentro(a, b):
        return min(a, b) - 1e-6 <= medio <= max(a, b) + 1e-6
    if banda == 4:
        return dentro(*p["parabrisas"]) or dentro(*p["luneta"])
    if banda in (2, 6):
        return any(dentro(a, b) for a, b in p["ventanillas"])
    return False


def carroceria(p):
    """Lofteo de la carrocería. Devuelve (bm_chapa, bm_vidrios) con normales hacia afuera."""
    perfil = Perfil(p)
    zs = perfil.estaciones()
    bm = bmesh.new()
    anillos = [[bm.verts.new(g2b(q)) for q in perfil.anillo(z)] for z in zs]
    n = len(anillos[0])
    for (a, b), z0, z1 in zip(zip(anillos, anillos[1:]), zs, zs[1:]):
        for i in range(n):
            i2 = (i + 1) % n
            f = bm.faces.new((a[i], a[i2], b[i2], b[i]))
            f.material_index = 1 if es_vidrio(p, i, z0, z1) else 0
    bm.faces.new(anillos[0])
    bm.faces.new(list(reversed(anillos[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)   # cerrada: el recálculo es seguro
    vidrios = bm.copy()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index == 1], context="FACES")
    bmesh.ops.delete(vidrios, geom=[f for f in vidrios.faces if f.material_index == 0], context="FACES")
    for f in vidrios.faces:
        f.material_index = 0
    return bm, vidrios, perfil


def rueda(p, i, x, z):
    r = p["radio"]
    s = 1 if x > 0 else -1
    bm = bmesh.new()
    piezas.cilindro(bm, r, ANCHO_RUEDA, (x, r, z), eje="x", lados=24, mat=0, radio_a_caras=True)
    piezas.cilindro(bm, r * 0.62, 0.03, (x + s * ANCHO_RUEDA / 2, r, z), eje="x", lados=16, mat=1,
                    radio_a_caras=True)
    return bm


def construir(p):
    mats = comun.cargar_materiales(*MATERIALES)
    pintura, vidrio, goma, acero, faro, piloto = mats
    chapa, vidrios, perfil = carroceria(p)
    L = p["largo"] / 2
    # Espejos (chapa).
    zc = p["parabrisas"][1] - 0.12
    w = interp(p["ancho"], zc)
    yc = interp(p["cintura"], zc)
    for s in (-1, 1):
        piezas.caja(chapa, (0.09, 0.10, 0.15), (s * (w * 0.98 + 0.01), yc + 0.05, zc), bisel=0.015)
    # Paragolpes y parrilla (goma), en el mismo objeto que los vidrios.
    wf, wt = interp(p["ancho"], L) * 0.93, interp(p["ancho"], -L) * 0.93
    piezas.caja(vidrios, (2 * wf, 0.12, 0.06), (0, p["paragolpes"][0], L), mat=1, bisel=0.015)
    piezas.caja(vidrios, (2 * wt, 0.12, 0.06), (0, p["paragolpes"][1], -L), mat=1, bisel=0.015)
    yf = interp(p["techo"], L)
    piezas.caja(vidrios, (wf * 0.75, 0.11, 0.03), (0, yf - 0.15, L), mat=1, bisel=0.01)
    # Faros y luces traseras.
    bf, bt = bmesh.new(), bmesh.new()
    for s in (-1, 1):
        piezas.caja(bf, (0.30, 0.11, 0.04), (s * (wf - 0.2), yf - 0.13, L), bisel=0.012)
        yt = interp(p["techo"], -L)
        piezas.caja(bt, (0.26, 0.13, 0.04), (s * (wt - 0.17), yt - 0.13, -L), bisel=0.012)
    objs = {
        "carroceria": ciudad.terminar("pieza_carroceria", chapa, [pintura]),
        "detalles": ciudad.terminar(f"{p['id']}_detalles", vidrios, [vidrio, goma]),
        "faros": ciudad.terminar("pieza_faros", bf, [faro]),
        "traseras": ciudad.terminar("pieza_luces_traseras", bt, [piloto]),
    }
    ruedas = []
    xr = p["trocha"]
    for i, (x, z) in enumerate(((xr, p["ejes"][0]), (-xr, p["ejes"][0]), (xr, p["ejes"][1]), (-xr, p["ejes"][1])), 1):
        ruedas.append(ciudad.terminar_en(f"pieza_rueda_{i}", rueda(p, i, x, z), [goma, acero],
                                         origen=(x, p["radio"], z)))
    objs["ruedas"] = ruedas
    visibles = [objs["carroceria"], objs["detalles"], objs["faros"], objs["traseras"]] + ruedas
    objs["visibles"] = visibles
    objs["raiz"] = piezas.raiz(p["id"], visibles)
    return objs


def revisar(p, objs):
    v = objs["visibles"]
    res = comun.revisar(v, PRESUPUESTO, p["medidas"], origen="base")
    ok, texto = ciudad.chequeo_materiales(v, 6, por_que=": vehículo armado, como una base de carrito")
    res = ciudad.reemplazar(res, "Materiales: ", ok, texto)
    ok, texto = ciudad.chequeo_normales(v, frente=False, centro=(0, 0.7, 0))
    res = ciudad.reemplazar(res, "Normales", ok, texto)
    # Ruedas: origen en el eje y apoyadas en el piso.
    bien = []
    for r in objs["ruedas"]:
        mn, mx = ciudad.limites([r])
        eje = r.location
        bien.append(abs(mn.y) < 1e-4 and abs(eje.z - p["radio"]) < 1e-6 and
                    abs((mn.z + mx.z) / 2 + eje.y) < 1e-4)
    res.append((all(bien), "Ruedas: radio %.2f a las caras (24 lados), origen en el eje (a %.2f), apoyan "
                "en el piso; trocha %.2f, ejes en z %.2f y %.2f" % (
                    p["radio"], p["radio"], 2 * p["trocha"], p["ejes"][0], p["ejes"][1])))
    return res


def main(p, titulo):
    comun.escena_vacia()
    objs = construir(p)
    revision = revisar(p, objs)
    ok = comun.imprimir_revision(p["id"], revision)
    ciudad.guardar_y_exportar(p["id"], [objs["raiz"]] + objs["visibles"])
    if "--sin-hoja" not in sys.argv:
        v = objs["visibles"]
        car = objs["carroceria"]

        def otro_color():
            car.data.materials[0] = bpy.data.materials.get("M_AzulAcento") or \
                comun.cargar_materiales("M_AzulAcento")[0]
        ciudad.hoja(p["id"], titulo, [
            ("Frente · día", v, "frente", "dia", True),
            ("Costado · día", v, "costado", "dia", True),
            ("3/4 · día", v, "tres_cuartos", "dia", False),
            ("3/4 · atardecer", v, "tres_cuartos", "atardecer", False),
            ("Con la persona de 1,75 m · día", v + ["persona"], "tres_cuartos_atras", "dia", False),
            ("Otro color (lo elige el juego) · día", v, "tres_cuartos", "dia", False),
        ], revision, persona_en=(-1.5, 0, 0.9), antes={5: otro_color})
    if not ok:
        sys.exit(1)
