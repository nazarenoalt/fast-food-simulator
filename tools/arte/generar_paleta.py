# Genera docs/arte/paleta.png a partir de tools/arte/paleta.json.
# Uso: python3 tools/arte/generar_paleta.py [salida.png]
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parents[2]
PALETA = json.loads((RAIZ / "tools/arte/paleta.json").read_text())
SALIDA = Path(sys.argv[1]) if len(sys.argv) > 1 else RAIZ / "docs/arte/paleta.png"


def rgb(hexa):
    return tuple(int(hexa[i:i + 2], 16) for i in (1, 3, 5))


def fuente(nombre, tam):
    try:
        return ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{nombre}", tam)
    except OSError:
        return ImageFont.load_default()


f, fb = fuente("DejaVuSans.ttf", 17), fuente("DejaVuSans-Bold.ttf", 28)
S, P, COLS = 170, 24, 8
filas = lambda g: (len(g["materiales"]) + COLS - 1) // COLS
W = P + COLS * (S + P)
H = P + sum(50 + filas(g) * (S + 70) for g in PALETA["grupos"])
im = Image.new("RGB", (W, H), (245, 243, 238))
d = ImageDraw.Draw(im)
y = P
for g in PALETA["grupos"]:
    d.text((P, y), g["nombre"], fill=(30, 30, 30), font=fb)
    y += 50
    for i, m in enumerate(g["materiales"]):
        x = P + (i % COLS) * (S + P)
        yy = y + (i // COLS) * (S + 70)
        d.rectangle([x, yy, x + S, yy + S], fill=rgb(m["hex"]), outline=(60, 60, 60), width=2)
        d.text((x, yy + S + 6), m["nombre"], fill=(30, 30, 30), font=f)
        d.text((x, yy + S + 32), m["hex"], fill=(90, 90, 90), font=f)
    y += filas(g) * (S + 70)
im.save(SALIDA)
print(f"Paleta guardada en {SALIDA}")
