"""Modelo: cartel con el nombre de la plaza (id `cartel_plaza`, lista-de-modelos, etapa 3).

Genera:
    godot/modelos/plaza/texturas/cartel_plaza.png   ← el nombre de la plaza (guía 4.5)
    arte/fuentes/plaza/cartel_plaza.blend
    godot/modelos/plaza/cartel_plaza.glb
    docs/arte/revisiones/cartel_plaza.jpg

Uso:
    python tools/blender/modelos/cartel_plaza.py [--sin-hoja]

Forma: cartel de nomenclatura de plaza. Dos postes de caño de hierro (M_Hierro) con brida
en el piso y remate arriba, y entre ellos una chapa de 1,08 × 0,50 con canto de hierro. Lo
escrito no es geometría: es una imagen sobre las dos caras de la chapa (guía 4.5), opaca,
con fondo M_BlancoCrema y letras y guarda en M_Hierro, dibujada sin suavizado. La cara de
atrás lleva la misma imagen al derecho (se lee de los dos lados). El nombre es inventado:
"Plaza del Aljibe", barrio Las Golondrinas.

Medidas (lista ≈ 1,2 × 2,0 × 0,1): 1,20 × 2,00 × 0,10 (las bridas de los postes). Chapa de
1,38 a 1,88 m: se lee a la altura de los ojos (1,65 m).
Biseles: chapa de 3 cm de canto → 8 mm (un cuarto, guía 3.3).
Lados (guía 3.2): postes (r 3 cm) 12.
Origen: centro de la base, a nivel del piso.

Objetos (hijos del Empty `cartel_plaza`):
    - cartel_plaza_cuerpo: postes, chapa y las dos caras con el material T_cartel_plaza.
    - cartel_plaza-colonly: una caja de 1,2 × 2,0 × 0,1 (por abajo de la chapa no se pasa:
      está a 1,38 m).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

import _plaza as plaza  # noqa: E402
import comun  # noqa: E402
import piezas  # noqa: E402
from pizarra_precios import (color_paleta, fuente, guardar_textura, lienzo,  # noqa: E402
                             mapear_cara, material_cartel, revisar_cartel)

ID = "cartel_plaza"
PRESUPUESTO = 300   # lista de modelos
MEDIDAS = (1.2, 2.0, 0.1)
HIERRO, CARTEL = 0, 1   # el crema (M_BlancoCrema) está en la imagen del cartel

X_POSTE = 0.55
R_POSTE, R_BRIDA = 0.03, 0.05
CHAPA = (1.08, 0.50, 0.03)
Y_CHAPA = 1.63                    # centro de la chapa
NOMBRE = ("PLAZA", "DEL ALJIBE", "BARRIO LAS GOLONDRINAS")
TEXTURA = comun.RAIZ / f"godot/modelos/{plaza.FAMILIA}/texturas/{ID}.png"
TEXTURA_TAM = (528, 240)          # la proporción de la cara de la chapa (≈ 2,2 : 1)


def dibujar_textura():
    w, h = TEXTURA_TAM
    img, dib = lienzo(TEXTURA_TAM, "M_BlancoCrema")
    tinta = color_paleta("M_Hierro")
    dib.rectangle((8, 8, w - 9, h - 9), outline=tinta, width=6)       # guarda
    dib.rectangle((20, 20, w - 21, h - 21), outline=tinta, width=2)

    def texto(y, cadena, tam_max, ancho_max=w - 80):
        tam = tam_max
        while tam > 10 and dib.textlength(cadena, font=fuente(tam)) > ancho_max:
            tam -= 2
        dib.text((w / 2, y), cadena, font=fuente(tam), fill=tinta, anchor="mm")

    texto(55, NOMBRE[0], 34)
    texto(118, NOMBRE[1], 72)
    dib.line((90, 165, w - 90, 165), fill=tinta, width=3)
    texto(193, NOMBRE[2], 24)
    guardar_textura(img, TEXTURA)


def construir():
    dibujar_textura()
    hierro, = comun.cargar_materiales("M_Hierro")
    m_cartel = material_cartel(f"T_{ID}", TEXTURA, rugosidad=0.7)
    bm = bmesh.new()
    for sx in (-1, 1):
        plaza.torno(bm, [(R_BRIDA, 0.0), (R_BRIDA, 0.012), (R_POSTE, 0.03),
                         (R_POSTE, 1.97), (0.038, 1.978), (0.0, 2.0)],
                    lados=12, centro=(sx * X_POSTE, 0, 0), mats=[HIERRO] * 5)
    caras = piezas.caja(bm, CHAPA, (0, Y_CHAPA, 0), mat=HIERRO, bisel=0.008)
    # Las dos caras grandes (adelante −Y y atrás +Y de Blender) llevan el cartel.
    adelante = max(caras, key=lambda f: -f.calc_center_median().y)
    atras = max(caras, key=lambda f: f.calc_center_median().y)
    for f in (adelante, atras):
        f.material_index = CARTEL
    mapear_cara(bm, adelante, Vector((1, 0, 0)), Vector((0, 0, 1)))
    mapear_cara(bm, atras, Vector((-1, 0, 0)), Vector((0, 0, 1)))   # al derecho desde atrás
    plaza.borrar_apoyadas(bm)
    cuerpo = piezas.terminar(f"{ID}_cuerpo", bm, [hierro, m_cartel])
    col = piezas.colision_caja(ID, MEDIDAS, (0, MEDIDAS[1] / 2, 0))
    raiz = piezas.raiz(ID, [cuerpo, col])
    return {"raiz": raiz, "cuerpo": cuerpo, "colisiones": [col], "cartel": m_cartel}


def revisar(mod):
    res = comun.revisar(mod["cuerpo"], PRESUPUESTO, MEDIDAS, origen="base")
    res = revisar_cartel(res, [mod["cartel"]])
    caras = [p for p in mod["cuerpo"].data.polygons if p.material_index == CARTEL]
    alto = [mod["cuerpo"].data.vertices[i].co.z for p in caras for i in p.vertices]
    res.append((len(caras) == 2 and min(alto) < 1.65 < max(alto),
                "Cartel en las 2 caras de la chapa, de %.2f a %.2f m (los ojos, a 1,65)" % (
                    min(alto), max(alto))))
    return res


def main():
    comun.escena_vacia()
    mod = construir()
    revision = revisar(mod)
    ok = comun.imprimir_revision(ID, revision)
    comun.guardar_blend(comun.RAIZ / f"arte/fuentes/{plaza.FAMILIA}/{ID}.blend")
    comun.exportar_glb([mod["raiz"], mod["cuerpo"]] + mod["colisiones"],
                       comun.RAIZ / f"godot/modelos/{plaza.FAMILIA}/{ID}.glb", uvs=True)
    if "--sin-hoja" not in sys.argv:
        c = [mod["cuerpo"]]
        plaza.hoja(ID, "cartel_plaza · 1,2 × 2,0 × 0,1 m · \"Plaza del Aljibe\" · mobiliario urbano", [
            ("Frente · día", c, "frente", "dia", True),
            ("Costado · día", c, "costado", "dia", True),
            ("3/4 · día", c, "tres_cuartos", "dia", False),
            ("3/4 · atardecer", c, "tres_cuartos", "atardecer", False),
            ("Con la persona de 1,75 m · día", c + ["persona"], "tres_cuartos", "dia", False),
            ("De atrás (se lee igual) · día", c, "tres_cuartos_atras", "dia", False),
        ], revision, persona_en=(0.9, 0, 0.3))
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
