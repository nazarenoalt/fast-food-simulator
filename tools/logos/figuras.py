"""Figuras de los logos del carrito (SPEC-028, REQ-LOG-01).

Genera godot/logos/<figura>.png (128 × 128 px, fondo transparente): pancho, hamburguesa y
estrella. Se dibujan sin suavizado y solo con colores de la paleta (guía de arte 4.5): cada
píxel es transparente o un color de tools/arte/paleta.json. Al final lo comprueba.

Uso (solo hace falta Pillow):
    python3 tools/logos/figuras.py
"""
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw

RAIZ = Path(__file__).resolve().parents[2]
SALIDA = RAIZ / "godot/logos"
LADO = 128
PALETA = {
    m["nombre"]: tuple(int(m["hex"][i:i + 2], 16) for i in (1, 3, 5))
    for g in json.loads((RAIZ / "tools/arte/paleta.json").read_text())["grupos"]
    for m in g["materiales"]
    if not m.get("solo_referencia")
}


def c(nombre):
    return PALETA[nombre] + (255,)


def lienzo():
    img = Image.new("RGBA", (LADO, LADO), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def pancho():
    img, d = lienzo()
    borde, corteza, miga = c("M_Tronco"), c("M_PanCorteza"), c("M_PanMiga")
    d.rounded_rectangle((10, 40, 118, 80), radius=18, fill=corteza, outline=borde, width=3)   # mitad de atrás
    d.rounded_rectangle((2, 50, 126, 72), radius=11, fill=c("M_Tomate"), outline=borde, width=3)  # salchicha
    zigzag = [(14 + 10 * i, 58 if i % 2 else 64) for i in range(11)]
    d.line(zigzag, fill=c("M_Amarillo"), width=4)                                            # mostaza
    d.rounded_rectangle((12, 64, 116, 100), radius=16, fill=corteza, outline=borde, width=3)  # mitad de adelante
    d.rectangle((22, 67, 106, 71), fill=miga)
    return img


def hamburguesa():
    img, d = lienzo()
    borde, corteza = c("M_PlasticoNegro"), c("M_PanCorteza")
    d.chord((8, 14, 120, 86), 180, 360, fill=corteza, outline=borde, width=3)               # pan de arriba
    for x, y in ((40, 30), (62, 24), (84, 32), (52, 42), (76, 42)):                        # sésamo
        d.rectangle((x, y, x + 4, y + 2), fill=c("M_PanMiga"))
    hojas = [(6, 56)] + [(6 + 8 * i, 62 if i % 2 else 54) for i in range(1, 15)] + [(122, 56), (122, 64), (6, 64)]
    d.polygon(hojas, fill=c("M_Lechuga"), outline=borde)                                     # lechuga
    d.rounded_rectangle((8, 62, 120, 80), radius=8, fill=c("M_Tronco"), outline=borde, width=3)  # medallón
    d.rectangle((12, 80, 116, 86), fill=c("M_Tomate"), outline=borde, width=2)               # tomate
    d.rounded_rectangle((10, 86, 118, 106), radius=9, fill=corteza, outline=borde, width=3)  # pan de abajo
    return img


def estrella():
    img, d = lienzo()
    d.ellipse((6, 6, 122, 122), fill=c("M_BlancoCrema"))
    d.ellipse((14, 14, 114, 114), fill=c("M_RojoAcento"))
    puntas = []
    for i in range(10):
        r = 44 if i % 2 == 0 else 18
        a = math.pi / 2 + i * math.pi / 5
        puntas.append((64 + r * math.cos(a), 66 - r * math.sin(a)))
    d.polygon(puntas, fill=c("M_Amarillo"))
    return img


def revisar(nombre, img):
    colores = set(PALETA.values())
    datos = img.tobytes()
    for i in range(0, len(datos), 4):
        r, g, b, a = datos[i:i + 4]
        if a == 0:
            continue
        assert a == 255 and (r, g, b) in colores, f"{nombre}: píxel fuera de la paleta {(r, g, b, a)}"


def main():
    SALIDA.mkdir(parents=True, exist_ok=True)
    for nombre, f in (("pancho", pancho), ("hamburguesa", hamburguesa), ("estrella", estrella)):
        img = f()
        revisar(nombre, img)
        ruta = SALIDA / f"{nombre}.png"
        img.save(ruta, optimize=True)
        print(f"{ruta.relative_to(RAIZ)} ({LADO} × {LADO} px), solo colores de la paleta")


if __name__ == "__main__":
    main()
