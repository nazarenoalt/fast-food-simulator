"""Modelo: cartel de cerrado colgante (id `cartel_cerrado`, accesorios.ron, REQ-PAP-07).

Genera:
    godot/modelos/accesorios/texturas/cartel_cerrado.png   ← el cartel (guía 4.5)
    arte/fuentes/accesorios/cartel_cerrado.blend
    godot/modelos/accesorios/cartel_cerrado.glb
    docs/arte/revisiones/cartel_cerrado.jpg

Uso:
    python tools/blender/modelos/cartel_cerrado.py [--sin-hoja]

Forma: cartel que se **cuelga** de una pared o de una puerta, como el de los negocios de
barrio. Un tablero de madera (M_Madera) con el cartel pintado de los dos lados: «CERRADO» en
letras crema con sombra sobre rojo, con doble filete (textura `T_cartel_cerrado`, opaca, solo
colores de la paleta; atrás la UV va espejada para que también se lea derecho). Cuelga de un
cordón negro (M_PlasticoNegro, 6 lados de 4 mm: guía 2.2, sogas) en V, que sale de dos puntos
del canto de arriba y pasa por arriba de un clavo de acero (M_Acero) con cabeza.

Medidas: 0,32 × 0,264 × 0,023 (tablero × del cordón al canto de abajo × de la pared a la cabeza
del clavo). Tablero 0,32 × 0,16 × 0,014, de −0,26 a −0,10 m.
Origen: el punto de donde cuelga (guía 2.4, como el foco): arriba del clavo, donde apoya el
cordón. La cara que se lee mira a +Z (al frente); la pared queda en z = −0,012 (el clavo entra
ahí y el tablero queda 5 mm separado). Va en el anclaje `cartel` de las bases (categoría
Cartel): adelante, centrado, con el clavo en el canto de la mesada (en el kiosco, en el de la
repisa de afuera), para que los clientes vean que está cerrado. Cuelga delante del telón.

Objeto único `cartel_cerrado_cuerpo` (Madera, Acero, PlasticoNegro, T_cartel_cerrado), hijo del
Empty `cartel_cerrado`. Sin colisión: es liviano y está pegado a la pared (como un telón).
No es `pieza_cartel`: ese nombre es de los carteles que se prenden de noche.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

import _accesorios5 as a5  # noqa: E402
import _plaza as plaza  # noqa: E402
import _equipos as eq  # noqa: E402
import comun  # noqa: E402
import piezas  # noqa: E402
from piezas import g2b  # noqa: E402
from pizarra_precios import (color_paleta, fuente, guardar_textura, lienzo,  # noqa: E402
                             mapear_cara, material_cartel, revisar_cartel)
from telon_panchos import letras  # noqa: E402

ID = "cartel_cerrado"
PRESUPUESTO = 1000  # accesorios medianos (guía 3.1)
TEXTO = "CERRADO"
MADERA, ACERO, NEGRO, CARTEL = range(4)
TABLERO = (0.32, 0.16, 0.014)
Y_TABLERO = -0.18                    # centro (de −0,26 a −0,10)
PINTADO = (0.296, 0.136)             # la parte pintada, 1 mm afuera de la madera
Z_PARED = -0.012                     # la pared (o la puerta) donde se clava
R_CORDON = 0.004                     # sogas: 6 lados, 4 mm (guía 2.2)
X_CORDON = 0.11                      # donde el cordón entra en el canto del tablero
R_CLAVO, R_CABEZA = 0.004, 0.0075
Y_CLAVO = -R_CORDON - R_CLAVO        # el cordón apoya arriba del clavo
Z_CABEZA = (0.008, 0.011)            # la cabeza del clavo, adelante del cordón
MEDIDAS = (TABLERO[0], 0.0, Z_CABEZA[1] - Z_PARED)   # el alto se mide (el cordón en V)
TEXTURA = comun.RAIZ / f"godot/modelos/{a5.FAMILIA}/texturas/{ID}.png"
TEXTURA_TAM = (512, round(512 * PINTADO[1] / PINTADO[0]))


def dibujar_textura():
    w, h = TEXTURA_TAM
    img, dib = lienzo(TEXTURA_TAM, "M_RojoAcento")
    amarillo, crema = color_paleta("M_Amarillo"), color_paleta("M_BlancoCrema")
    sombra = color_paleta("M_Hierro")
    dib.rectangle((5, 5, w - 6, h - 6), outline=amarillo, width=5)
    dib.rectangle((16, 16, w - 17, h - 17), outline=crema, width=2)
    for x in (30, w - 31):                       # puntitos del filete en las esquinas
        for y in (30, h - 31):
            dib.ellipse((x - 5, y - 5, x + 5, y + 5), fill=amarillo)
    letras(dib, img, TEXTO, (w / 2, h / 2 + 2), fuente(round(h * 0.5)), sombra, crema, w - 110)
    guardar_textura(img, TEXTURA)


def construir():
    dibujar_textura()
    madera, acero, negro = comun.cargar_materiales("M_Madera", "M_Acero", "M_PlasticoNegro")
    m_cartel = material_cartel(f"T_{ID}", TEXTURA)
    bm = bmesh.new()
    # Clavo: entra en la pared, el cordón pasa por arriba y la cabeza lo sostiene adelante.
    largo = Z_CABEZA[0] - Z_PARED
    piezas.cilindro(bm, R_CLAVO, largo, (0, Y_CLAVO, Z_PARED + largo / 2), eje="z", lados=8, mat=ACERO,
                    tapas=(False, False), radio_a_caras=True)
    alto_c = Z_CABEZA[1] - Z_CABEZA[0]
    piezas.cilindro(bm, R_CABEZA, alto_c, (0, Y_CLAVO, Z_CABEZA[0] + alto_c / 2), eje="z", lados=8,
                    mat=ACERO, tapas=(False, True), radio_a_caras=True)
    # Cordón en V: del clavo a los dos puntos del canto de arriba (entra 3 mm en la madera).
    arriba = Y_TABLERO + TABLERO[1] / 2
    for sx in (-1, 1):
        plaza.caño(bm, (0, 0, 0), (sx * X_CORDON, arriba - 0.003, 0), R_CORDON, 6, mat=NEGRO)
    # Tablero de madera y la parte pintada (sale 1 mm de cada cara).
    piezas.caja(bm, TABLERO, (0, Y_TABLERO, 0), mat=MADERA, bisel=0.003)
    caras = piezas.caja(bm, (PINTADO[0], PINTADO[1], TABLERO[2] + 0.002), (0, Y_TABLERO, 0), mat=MADERA)
    frente = max(caras, key=lambda f: -f.calc_center_median().y)   # mira a −Y de Blender
    espalda = max(caras, key=lambda f: f.calc_center_median().y)
    for cara, u in ((frente, Vector((1, 0, 0))), (espalda, Vector((-1, 0, 0)))):
        cara.material_index = CARTEL
        mapear_cara(bm, cara, u, Vector((0, 0, 1)))
    cuerpo = piezas.terminar(f"{ID}_cuerpo", bm, [madera, acero, negro, m_cartel])
    raiz = piezas.raiz(ID, [cuerpo])
    return {"raiz": raiz, "cuerpo": cuerpo, "m_cartel": m_cartel}


def medidas_reales(obj):
    vs = eq.verts_godot(obj)
    return [max(getattr(v, c) for v in vs) - min(getattr(v, c) for v in vs) for c in "xyz"], vs


def chequeo_origen(obj):
    tam, vs = medidas_reales(obj)
    tope = max(v.y for v in vs)
    abajo = min(v.y for v in vs)
    atras = min(v.z for v in vs)
    ok = (abs(tope - R_CORDON) < 0.002 and abs(abajo - (Y_TABLERO - TABLERO[1] / 2)) < 1e-4
          and abs(atras - Z_PARED) < 1e-4 and abs(max(v.x for v in vs) + min(v.x for v in vs)) < 1e-4)
    return ok, ("Origen en el punto de donde cuelga (arriba del clavo, donde apoya el cordón): centrado en X, "
                "tablero hasta %.3f m abajo, pared en z %.3f" % (abajo, atras))


def revisar(m):
    tam, _ = medidas_reales(m["cuerpo"])
    medidas = (MEDIDAS[0], tam[1], MEDIDAS[2])
    res = comun.revisar([m["cuerpo"]], PRESUPUESTO, medidas, origen="base")
    res = eq.reemplazar(res, "Origen", chequeo_origen(m["cuerpo"]))
    res = revisar_cartel(res, [m["m_cartel"]])
    res = a5.chequeo_normales(res, [m["cuerpo"]])
    res.append((True, "Texto fijo \"%s\" de los dos lados (UV de 0 a 1; atrás espejada para que se lea "
                      "derecho); cordón en V de %.0f mm sobre un clavo; la cara que se lee mira a +Z" % (TEXTO, 2000 * R_CORDON)))
    return res


def colgar_copia(m, nombre, pos, rot_y, x=0.0):
    copia = a5.e2.copiar(m["cuerpo"], nombre)
    copia.parent = None
    copia.location = Vector((x, 0, 0)) + g2b(pos)
    copia.rotation_euler.z = math.radians(rot_y)
    return copia


def hoja_revision(m, revision):
    import carro_kiosco as kio
    import telon_panchos
    comun.preparar_revision()
    a5.e2.DIRECCIONES["cliente"] = (Vector((0.55, -1.4, 0.45)), False)   # como lo ve la fila
    m["raiz"].location.z = 0.6          # solo para las fotos: el cartel cuelga por debajo del origen
    solo = [m["cuerpo"]]
    persona = a5.persona()
    # Barra chica (x = 0, con el telón), carro grande (x = 5) y kiosco (x = −6): adelante.
    barra, b = a5.carrito("barra_chica")
    telon = telon_panchos.construir()   # (vuelve a escribir su textura, igual)
    telon.location = g2b(b.anclajes["frente"])
    extras = [telon]
    cartel_b = colgar_copia(m, f"ref_{ID}_barra", b.anclajes["cartel"], 0)
    en_barra = barra + extras + [cartel_b, persona]
    grande, g = a5.carrito("carro_grande", x=5.0)
    cartel_g = colgar_copia(m, f"ref_{ID}_grande", g.anclajes["cartel"], 0, x=5.0)
    en_grande = grande + [cartel_g]
    km = kio.construir()
    km["raiz"].location.x = -6.0
    pos_k = next(p for n, p, _ in kio.ANCLAJES if n == "cartel")
    cartel_k = colgar_copia(m, f"ref_{ID}_kiosco", pos_k, 0, x=-6.0)
    kiosco = km["visibles"] + [cartel_k]
    bpy.context.view_layer.update()
    pedidos = [
        ("Frente (lo que ve el cliente) · día", solo, "frente", "dia"),
        ("Costado (la pared queda a la izquierda) · día", solo, "costado", "dia"),
        ("3/4 · día", solo, "tres_cuartos", "dia"),
        ("3/4 · atardecer", solo, "tres_cuartos", "atardecer"),
        ("Atrás (también dice CERRADO) · día", solo, "vendedor", "dia"),
        ("Barra chica: adelante, delante del telón · día", en_barra, "cliente", "dia", barra,
         a5.mover_persona((-0.3, 0, -0.65)), 1.0),
        ("Carro grande: en el canto de la mesada · día", en_grande, "cliente", "dia", grande, None, 0.85),
        ("Kiosco: en el canto de la repisa de afuera · día", kiosco, "cliente", "dia", km["visibles"], None, 0.8),
        ("Kiosco: de cerca · atardecer", kiosco, "cliente", "atardecer", [cartel_k], None, 7.0),
    ]
    alto = a5.coma("%.3f" % medidas_reales(m["cuerpo"])[0][1])
    a5.hoja(ID, f"cartel_cerrado · 0,32 × {alto} × 0,023 m · cartel colgante (adelante, en el canto del mostrador)",
            pedidos, revision)


def main():
    comun.escena_vacia()
    m = construir()
    bpy.context.view_layer.update()
    revision = revisar(m)
    ok = comun.imprimir_revision(ID, revision)
    a5.guardar_y_exportar(ID, [m["raiz"], m["cuerpo"]], uvs=True)
    if "--sin-hoja" not in sys.argv:
        hoja_revision(m, revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
