"""Modelo: camioneta del proveedor (id `camioneta_proveedor`, familia `ciudad`). Propuesta:
hoy el proveedor no se ve en el juego (el pedido aparece en el pallet).

Genera:
    arte/fuentes/ciudad/camioneta_proveedor.blend
    godot/modelos/ciudad/camioneta_proveedor.glb
    docs/arte/revisiones/camioneta_proveedor.jpg

Uso:
    python tools/blender/modelos/camioneta_proveedor.py [--sin-hoja]

Utilitario chico de reparto, tipo furgón de carga, genérico y SIN marcas. Mismo criterio que
los autos (`_auto.py`, de donde salen el lofteo de la carrocería, el perfil y las ruedas): de
frente a +Z, capó corto y bajo, parabrisas inclinado, cabina con las ventanillas de las
puertas de adelante y todo el resto de caja de chapa ciega (techo alto y casi plano).
Atrás, un vano de carga con dos puertas de hoja que abren hacia los costados.

Objetos (hijos del Empty `camioneta_proveedor`; origen = centro de la base, a nivel del piso):
    - pieza_carroceria: toda la chapa, M_PinturaCarrito (el juego le pone el color).
    - camioneta_proveedor_detalles: vidrios opacos (M_Hierro), paragolpes y parrilla (M_Goma).
    - camioneta_proveedor_caja: el interior de la caja de carga (piso de goma, paredes y
      mampara de acero), que se ve con las puertas abiertas. Sus caras miran hacia adentro.
    - pieza_puerta_trasera_izq / _der: las dos hojas de atrás (chapa M_PinturaCarrito,
      vidrio opaco y manija), con el origen en la bisagra (borde de afuera, abajo de la
      hoja): giran en Y de Godot; +100° abre la izquierda y −100° la derecha (hacia los
      costados). El juego tiene que pintarlas con el mismo color que pieza_carroceria.
    - pieza_rueda_1..4: 1 delantera +X, 2 delantera −X, 3 trasera +X, 4 trasera −X, radio
      0,33 (como el auto_a), con el origen en el eje (giran en X).
    - pieza_faros (M_LuzFarol) y pieza_luces_traseras (M_PilotoApagado, verticales en los
      parantes de atrás, como en los furgones): el juego las prende de noche.
    Sin `-colonly`: se mueve, como los autos (la colisión la arma el código).

Medidas: 1,90 × 2,00 × 4,80 (con los espejos; la chapa mide 1,84 de ancho) (lista ≈ 1,9 ×
2,0 × 4,8). Ejes a 3,0 m, trocha 1,60.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402  (antes que bmesh)
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

import _auto as auto  # noqa: E402
import _ciudad as ciudad  # noqa: E402
import comun  # noqa: E402
import piezas  # noqa: E402
from piezas import g2b  # noqa: E402

ID = "camioneta_proveedor"
PRESUPUESTO = 3000
L = 2.35   # medio largo de la chapa (con el paragolpes de adelante y las manijas de atrás: 2,40)
P = {
    "id": ID,
    "largo": 2 * L,
    "radio": 0.33,
    "ejes": (1.50, -1.50),
    "trocha": 0.81,
    "piso_puntas": [(-L, 0.42), (-2.12, 0.34), (2.10, 0.34), (L, 0.40)],
    "techo": [(-L, 1.95), (-2.30, 1.992), (0.70, 1.992), (0.80, 1.975), (1.55, 1.22), (2.15, 1.07),
              (L, 0.99)],
    "cintura": [(-L, 1.15), (1.55, 1.13), (2.15, 1.01), (L, 0.93)],
    "ancho": [(-L, 0.90), (-2.25, 0.92), (1.90, 0.92), (2.20, 0.90), (L, 0.84)],
    "ancho_techo": [(-L, 0.84), (-2.25, 0.87), (0.75, 0.87), (1.55, 0.84), (2.15, 0.80), (L, 0.76)],
    "parabrisas": (0.80, 1.55),
    "luneta": (99.0, 99.0),          # sin luneta: atrás van las puertas
    "parante_b": (0.30, 0.38),
    "ventanillas": [(0.38, 1.55)],   # solo las puertas de adelante
    "paragolpes": (0.40, 0.38),
}
MEDIDAS = (1.90, 2.00, 4.80)

# Vano de carga y puertas de atrás (Godot).
VANO_X, VANO_PISO, VANO_TECHO = 0.70, 0.55, 1.85
CAJA_FONDO = 0.25                 # mampara detrás de los asientos (z)
PUERTA_X, PUERTA_Y0, PUERTA_Y1 = 0.80, 0.50, 1.88   # hoja: de x 0,004 a 0,80
PUERTA_E = 0.04                   # espesor de la hoja (va por fuera de la chapa)
JUNTA = 0.004                     # luz entre las dos hojas
Z_BISAGRA = -L - PUERTA_E / 2
APERTURA = 100                    # grados, para la foto de descarga


def vano(chapa, perfil):
    """Saca la tapa de atrás de la carrocería y pone un marco plano con el vano de carga.
    Devuelve el contorno del vano (10 puntos de Godot, en el orden del anillo)."""
    yb = g2b((0, 0, -L)).y
    tapa = [f for f in chapa.faces if len(f.verts) > 4 and all(abs(v.co.y - yb) < 1e-6 for v in f.verts)]
    assert len(tapa) == 1, "no encontré la tapa de atrás"
    anillo = list(tapa[0].verts)
    bmesh.ops.delete(chapa, geom=tapa, context="FACES_ONLY")
    puntos = perfil.anillo(-L)
    vs = [min(anillo, key=lambda v: (v.co - g2b(q)).length) for q in puntos]
    m = 0.08
    der = [(VANO_X, VANO_PISO), (VANO_X, VANO_PISO + 0.07), (VANO_X, 1.15), (VANO_X, VANO_TECHO),
           (VANO_X - m, VANO_TECHO)]
    contorno = [(x, y, -L) for x, y in der] + [(-x, y, -L) for x, y in reversed(der)]
    adentro = [chapa.verts.new(g2b(q)) for q in contorno]
    n = len(vs)
    for i in range(n):
        j = (i + 1) % n
        f = chapa.faces.new((vs[i], vs[j], adentro[j], adentro[i]))
        f.normal_update()
        if f.normal.dot(g2b((0, 0, -1))) < 0:
            f.normal_flip()
    return contorno


def caja_carga(contorno):
    """Interior de la caja: paredes del vano hacia adentro hasta la mampara, mirando hacia
    adentro. Piso (la banda de abajo) de goma, el resto de acero."""
    bm = bmesh.new()
    atras = [bm.verts.new(g2b(q)) for q in contorno]
    fondo = [bm.verts.new(g2b((x, y, CAJA_FONDO))) for x, y, _ in contorno]
    n = len(contorno)
    centro = g2b((0, (VANO_PISO + VANO_TECHO) / 2, (CAJA_FONDO - L) / 2))
    for i in range(n):
        j = (i + 1) % n
        f = bm.faces.new((atras[i], atras[j], fondo[j], fondo[i]))
        piso = contorno[i][1] == VANO_PISO and contorno[j][1] == VANO_PISO
        f.material_index = 1 if piso else 0
    f = bm.faces.new(fondo)
    f.material_index = 0
    for f in bm.faces:
        f.normal_update()
        if f.normal.dot(centro - f.calc_center_median()) < 0:
            f.normal_flip()
    return bm


def puerta(lado, mats):
    """Hoja de atrás. lado = +1 (der, +X) o −1 (izq). Origen en la bisagra."""
    bm = bmesh.new()
    x0, x1 = JUNTA / 2, PUERTA_X
    cx = lado * (x0 + x1) / 2
    piezas.caja(bm, (x1 - x0, PUERTA_Y1 - PUERTA_Y0, PUERTA_E), (cx, (PUERTA_Y0 + PUERTA_Y1) / 2, Z_BISAGRA),
                mat=0, bisel=0.015)
    # Vidrio opaco (arriba) y manija (del lado de la junta).
    piezas.caja(bm, (0.56, 0.42, 0.01), (lado * 0.40, 1.56, Z_BISAGRA - PUERTA_E / 2), mat=1, bisel=0.003)
    piezas.caja(bm, (0.035, 0.14, 0.016), (lado * 0.07, 1.10, -L - PUERTA_E - 0.002), mat=2,
                bisel=0.005)
    nombre = "pieza_puerta_trasera_" + ("der" if lado > 0 else "izq")
    return ciudad.terminar_en(nombre, bm, mats, origen=(lado * PUERTA_X, PUERTA_Y0, Z_BISAGRA))


def construir():
    mats = comun.cargar_materiales(*auto.MATERIALES)
    pintura, vidrio, goma, acero, faro, piloto = mats
    chapa, vidrios, perfil = auto.carroceria(P)
    contorno = vano(chapa, perfil)
    # Espejos grandes de utilitario (chapa).
    zc = P["parabrisas"][1] - 0.12
    w = auto.interp(P["ancho"], zc)
    yc = auto.interp(P["cintura"], zc)
    for s in (-1, 1):
        piezas.caja(chapa, (0.07, 0.20, 0.14), (s * (w * 0.98 + 0.0135), yc + 0.12, zc), bisel=0.015)
    # Paragolpes, parrilla y una banda de goma a los costados (protección de la caja).
    wf = auto.interp(P["ancho"], L) * 0.93
    piezas.caja(vidrios, (2 * wf, 0.14, 0.08), (0, P["paragolpes"][0], L + 0.01), mat=1, bisel=0.015)
    piezas.caja(vidrios, (2 * 0.86, 0.14, 0.08), (0, P["paragolpes"][1], -L - 0.01), mat=1, bisel=0.015)
    yf = auto.interp(P["techo"], L)
    piezas.caja(vidrios, (wf * 0.85, 0.16, 0.03), (0, yf - 0.17, L), mat=1, bisel=0.01)
    za, zb = P["ejes"][1] + 0.45, P["ejes"][0] - 0.45
    for s in (-1, 1):
        piezas.caja(vidrios, (0.03, 0.10, zb - za), (s * 0.925, 0.62, (za + zb) / 2), mat=1, bisel=0.01)
    # Faros y luces traseras (verticales, en los parantes de atrás).
    bf, bt = bmesh.new(), bmesh.new()
    for s in (-1, 1):
        piezas.caja(bf, (0.26, 0.13, 0.04), (s * (wf - 0.17), yf - 0.15, L), bisel=0.012)
        piezas.caja(bt, (0.085, 0.50, 0.04), (s * 0.85, 1.0, -L - 0.01), bisel=0.012)
    objs = {
        "carroceria": ciudad.terminar("pieza_carroceria", chapa, [pintura]),
        "detalles": ciudad.terminar(f"{ID}_detalles", vidrios, [vidrio, goma]),
        "caja": ciudad.terminar(f"{ID}_caja", caja_carga(contorno), [acero, goma]),
        "faros": ciudad.terminar("pieza_faros", bf, [faro]),
        "traseras": ciudad.terminar("pieza_luces_traseras", bt, [piloto]),
    }
    objs["puertas"] = [puerta(-1, [pintura, vidrio, goma]), puerta(1, [pintura, vidrio, goma])]
    ruedas = []
    xr = P["trocha"]
    for i, (x, z) in enumerate(((xr, P["ejes"][0]), (-xr, P["ejes"][0]), (xr, P["ejes"][1]),
                                (-xr, P["ejes"][1])), 1):
        ruedas.append(ciudad.terminar_en(f"pieza_rueda_{i}", auto.rueda(P, i, x, z), [goma, acero],
                                         origen=(x, P["radio"], z)))
    objs["ruedas"] = ruedas
    objs["visibles"] = [objs[k] for k in ("carroceria", "detalles", "caja", "faros", "traseras")] + \
        objs["puertas"] + ruedas
    objs["raiz"] = piezas.raiz(ID, objs["visibles"])
    return objs


def chequeo_caja(caja):
    """Las caras del interior de la caja miran hacia adentro (a propósito: se ve desde el vano)."""
    centro = g2b((0, (VANO_PISO + VANO_TECHO) / 2, (CAJA_FONDO - L) / 2))
    m = caja.matrix_world
    malas = sum(1 for f in caja.data.polygons
                if (m.to_3x3() @ f.normal).dot(centro - m @ f.center) <= 0)
    return malas == 0, "%s: interior de la caja de carga (%.2f m de hondo) con las caras hacia adentro " \
        "(se ve con las puertas abiertas)%s" % (caja.name, CAJA_FONDO + L, "" if not malas else f": {malas} MAL")


def chequeo_puertas(puertas):
    bien = []
    for p in puertas:
        mn, mx = ciudad.limites([p])
        o = p.location
        og = Vector((o.x, o.z, -o.y))
        borde = mx.x if og.x > 0 else mn.x
        bien.append(abs(borde - og.x) < 0.001 and abs(mn.y - og.y) < 0.001 and
                    abs((mn.z + mx.z) / 2 - og.z) < 0.02 and len(p.data.materials) == 3)
    return all(bien), "Puertas traseras (pieza_puerta_trasera_izq/der): origen en la bisagra, en el borde " \
        "de afuera (x = ±%.2f) y abajo de la hoja (y = %.2f); giran en Y y abren hacia los costados" % (
            PUERTA_X, PUERTA_Y0)


def revisar(objs):
    v = objs["visibles"]
    res = comun.revisar(v, PRESUPUESTO, MEDIDAS, origen="base")
    ok, texto = ciudad.chequeo_materiales(v, 6, por_que=": vehículo armado, como una base de carrito")
    res = ciudad.reemplazar(res, "Materiales: ", ok, texto)
    sin_caja = [o for o in v if o is not objs["caja"]]
    ok, texto = ciudad.chequeo_normales(sin_caja, frente=False, centro=(0, 0.7, 0))
    ok2, texto2 = chequeo_caja(objs["caja"])
    res = ciudad.reemplazar(res, "Normales", ok, texto + " (salvo el interior de la caja: línea aparte)")
    res.append((ok2, texto2))
    bien = []
    for r in objs["ruedas"]:
        mn, mx = ciudad.limites([r])
        eje = r.location
        bien.append(abs(mn.y) < 1e-4 and abs(eje.z - P["radio"]) < 1e-6 and abs((mn.z + mx.z) / 2 + eje.y) < 1e-4)
    res.append((all(bien), "Ruedas: radio %.2f a las caras (24 lados), origen en el eje, apoyan en el piso; "
                "trocha %.2f, ejes en z %.2f y %.2f" % (P["radio"], 2 * P["trocha"], P["ejes"][0], P["ejes"][1])))
    res.append(chequeo_puertas(objs["puertas"]))
    return res


def abrir(puertas, grados):
    def hacer():
        izq, der = puertas
        izq.rotation_euler.z = math.radians(grados)
        der.rotation_euler.z = -math.radians(grados)
        bpy.context.view_layer.update()
    return hacer


def main():
    comun.escena_vacia()
    objs = construir()
    revision = revisar(objs)
    mn, mx = ciudad.limites(objs["visibles"])
    print("Medidas reales (Godot):", tuple(round(c, 3) for c in mx - mn), "min", tuple(round(c, 3) for c in mn))
    ok = comun.imprimir_revision(ID, revision)
    ciudad.guardar_y_exportar(ID, [objs["raiz"]] + objs["visibles"])
    if "--sin-hoja" not in sys.argv:
        v = objs["visibles"]
        car = objs["carroceria"]
        puertas = objs["puertas"]
        import auto_a
        otro = auto.construir(auto_a.P)
        otro["raiz"].location = g2b((-2.4, 0, 0.3))
        for o in otro["visibles"]:
            o.data.materials[0] = o.data.materials[0]
        azul = comun.cargar_materiales("M_AzulAcento")[0]

        def otro_color():
            abrir(puertas, 0)()
            car.data.materials[0] = azul
            for p in puertas:
                p.data.materials[0] = azul

        def con_auto():
            car.data.materials[0] = bpy.data.materials["M_PinturaCarrito"]
            for p in puertas:
                p.data.materials[0] = bpy.data.materials["M_PinturaCarrito"]
            otro["carroceria"].data.materials[0] = azul
        ciudad.hoja(ID, ciudad.m("camioneta_proveedor · 1.9 × 2.0 × 4.8 m · utilitario de reparto "
                                 "(genérico, sin marca)"), [
            ("Frente · día", v, "frente", "dia", True),
            ("Costado · día", v, "costado", "dia", True),
            ("3/4 · día", v, "tres_cuartos", "dia", False),
            ("3/4 · atardecer", v, "tres_cuartos", "atardecer", False),
            ("Atrás · puertas cerradas · día", v, "tres_cuartos_atras", "dia", False),
            ("Atrás · puertas abiertas (descarga) · día", v + ["persona"], "tres_cuartos_atras", "dia", False),
            ("Otro color (lo elige el juego) · día", v, "tres_cuartos", "dia", False),
            ("Al lado del auto_a · día", v + otro["visibles"], "tres_cuartos", "dia", False),
            ("Puertas abiertas · atardecer", v, "tres_cuartos_atras", "atardecer", False),
        ], revision, persona_en=(1.2, 0, -3.1),
            antes={5: abrir(puertas, APERTURA), 6: otro_color, 7: con_auto, 8: abrir(puertas, APERTURA)})
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
