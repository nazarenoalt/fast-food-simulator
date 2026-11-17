# Genera docs/arte/paleta.png a partir de la paleta de la guía de modelado.
# Uso: python3 tools/arte/generar_paleta.py docs/arte/paleta.png
from PIL import Image, ImageDraw, ImageFont
import sys
G = [
 ("Carrito y equipos", [
  ("M_PinturaCarrito",(0.78,0.13,0.10)),("M_Acero",(0.82,0.83,0.85)),("M_MetalOscuro",(0.35,0.35,0.38)),
  ("M_Goma",(0.12,0.12,0.12)),("M_PlasticoNegro",(0.10,0.10,0.10)),("M_MaderaClara",(0.70,0.55,0.38)),("M_PilotoApagado",(0.25,0.05,0.05))]),
 ("Comida y empaques", [
  ("M_PanCorteza",(0.86,0.60,0.32)),("M_PanMiga",(0.97,0.88,0.70)),("M_SalchichaCruda",(0.93,0.55,0.50)),
  ("(ref) Salchicha cocida",(0.72,0.30,0.20)),("M_Carton",(0.78,0.62,0.42)),("M_BolsaPlastica",(0.92,0.94,1.00))]),
 ("Plaza (fondo)", [
  ("M_Pasto",(0.24,0.40,0.17)),("M_Baldosa",(0.58,0.55,0.50)),("M_Camino",(0.64,0.56,0.44)),("M_Vereda",(0.48,0.48,0.47)),
  ("M_Asfalto",(0.17,0.17,0.18)),("M_Madera",(0.55,0.36,0.20)),("M_Hierro",(0.15,0.16,0.15)),("M_Tronco",(0.38,0.27,0.18)),
  ("M_Hojas1",(0.20,0.42,0.18)),("M_Hojas2",(0.24,0.47,0.20)),("M_Hojas3",(0.18,0.40,0.16)),("M_Piedra",(0.70,0.70,0.68)),
  ("M_Agua",(0.30,0.50,0.70))]),
 ("Acentos y luces", [
  ("M_Amarillo",(0.98,0.80,0.10)),("M_RojoAcento",(0.85,0.12,0.10)),("M_AzulAcento",(0.10,0.45,0.80)),
  ("M_BlancoCrema",(0.95,0.95,0.90)),("M_Lona",(0.95,0.95,0.95)),("M_Pizarra",(0.08,0.10,0.08)),
  ("M_LuzCalida",(1.00,0.75,0.45)),("M_LuzFarol",(1.00,0.82,0.55))]),
]
hx=lambda c:"#%02X%02X%02X"%tuple(round(v*255) for v in c)
try:
  f=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",17); fb=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",28)
except Exception: f=fb=ImageFont.load_default()
S,P,COLS=170,24,8
rows=sum(1+(len(g)+COLS-1)//COLS for _,g in G)
W=P+COLS*(S+P); H=P+sum(50+((len(g)+COLS-1)//COLS)*(S+70) for _,g in G)
im=Image.new("RGB",(W,H),(245,243,238)); d=ImageDraw.Draw(im); y=P
for t,g in G:
  d.text((P,y),t,fill=(30,30,30),font=fb); y+=50
  for i,(n,c) in enumerate(g):
    x=P+(i%COLS)*(S+P); yy=y+(i//COLS)*(S+70)
    d.rectangle([x,yy,x+S,yy+S],fill=tuple(round(v*255) for v in c),outline=(60,60,60),width=2)
    d.text((x,yy+S+6),n,fill=(30,30,30),font=f); d.text((x,yy+S+32),hx(c),fill=(90,90,90),font=f)
    print(n,hx(c))
  y+=((len(g)+COLS-1)//COLS)*(S+70)
im.save(sys.argv[1])
