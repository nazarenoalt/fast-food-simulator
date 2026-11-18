"""Modelo: cajita de cartón para papas fritas (id `cajita_papas`, productos.ron, SPEC-026).

Genera:
    arte/fuentes/comida/cajita_papas.blend
    godot/modelos/comida/cajita_papas.glb
    docs/arte/revisiones/cajita_papas.jpg

Uso:
    blender -b -P tools/blender/modelos/cajita_papas.py
    python tools/blender/modelos/cajita_papas.py

Forma: cajita abierta de cartón, vacía, de 0,09 × 0,11 × 0,056 (arriba): se abre hacia arriba
(abajo mide 0,064 × 0,036) y el borde de la boca no es recto, es una curva: el frente (+Z, lo
que ve el cliente) baja 3 cm en el medio, como un cucharón, y la espalda apenas 8 mm. Planta de
rectángulo con las esquinas redondeadas (20 puntos: hacen falta en el medio de los lados
para dibujar la curva de la boca). Pared de 3 mm (guía 2.2) con canto en la
boca. Afuera `M_RojoAcento` con una franja `M_Amarillo` alrededor (sin marcas ni texto), adentro
y el canto `M_BlancoCrema`. Cartón doblado: sombreado duro (aristas a más de 30°), sin bisel.

Objeto único `cajita_papas`, origen en el centro de la caja envolvente (guía 2.4). Sin
colisión (la define el dato). La hoja la muestra también con papas fritas adentro.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402,F401  (antes que bmesh)
import bmesh  # noqa: E402

import comun  # noqa: E402
import _equipos as eq  # noqa: E402
import _etapa2 as e2  # noqa: E402
import _papas as pp  # noqa: E402
from piezas import g2b  # noqa: E402

ID = "cajita_papas"
MEDIDAS = pp.MEDIDAS[ID]
ROJO, AMARILLO, CREMA = range(3)
H = MEDIDAS[1]
ABAJO = (0.032, 0.018)               # medio ancho X, medio fondo Z en la base
ARRIBA = (MEDIDAS[0] / 2, MEDIDAS[2] / 2)
RADIO = 0.007
PARED = 0.003
BAJA_FRENTE, BAJA_ESPALDA = 0.03, 0.008
FRANJA = (0.05, 0.068)               # alto de la franja amarilla (desde abajo)
N = 20                               # puntos de la planta (ver contorno)


def contorno(y, meter=0.0):
    """Planta (N puntos) a la altura y, metida `meter` hacia adentro (la pared interior):
    las esquinas redondeadas (3 puntos cada una) y, en el medio de cada lado, puntos extra
    para que el borde curvo de la boca se pueda dibujar (3 en el frente y la espalda, 1 en
    los costados)."""
    t = y / H
    hx = ABAJO[0] + (ARRIBA[0] - ABAJO[0]) * t - meter
    hz = ABAJO[1] + (ARRIBA[1] - ABAJO[1]) * t - meter
    esq = [(p[0], p[2]) for p in e2.anillo_rr(hx, hz, RADIO, 0.0, segs=2)]
    # anillo_rr arranca en la esquina +X+Z y gira hacia +Z: esquinas de a 3 puntos.
    medios = [
        [(hx * f, hz) for f in (0.5, 0.0, -0.5)],      # frente (+Z), de +X a −X
        [(-hx, 0.0)],                                  # costado −X
        [(hx * f, -hz) for f in (-0.5, 0.0, 0.5)],     # espalda (−Z), de −X a +X
        [(hx, 0.0)],                                   # costado +X
    ]
    pts = []
    for i in range(4):
        pts += esq[3 * i:3 * i + 3] + medios[i]
    return pts


def alto_boca(x, z):
    """Altura del borde de la boca en (x, z): baja en el medio del frente y de la espalda."""
    hx, hz = ARRIBA
    medio = max(0.0, 1 - (x / hx) ** 2)
    if z > 0:
        return H - BAJA_FRENTE * medio * min(1.0, z / hz) ** 2
    return H - BAJA_ESPALDA * medio * min(1.0, -z / hz) ** 2


def anillo(bm, alturas, meter=0.0):
    """Anillo de N vértices: alturas = un número o 'boca' (sigue el borde curvo)."""
    vs = []
    for k in range(N):
        if alturas == "boca":
            # La planta a la altura justa de cada punto (la pared se abre hacia arriba).
            x0, z0 = contorno(H, meter)[k]
            y = alto_boca(x0, z0)
            x, z = contorno(y, meter)[k]
        else:
            y = alturas
            x, z = contorno(y, meter)[k]
        vs.append(bm.verts.new(g2b((x, y - H / 2, z))))
    return vs


def construir(nombre=ID):
    mats = comun.cargar_materiales("M_RojoAcento", "M_Amarillo", "M_BlancoCrema")
    bm = bmesh.new()
    afuera = [anillo(bm, 0.0), anillo(bm, FRANJA[0]), anillo(bm, FRANJA[1]), anillo(bm, "boca")]
    adentro = [anillo(bm, "boca", PARED), anillo(bm, PARED, PARED)]
    # Pared de afuera (de abajo hacia arriba), canto, pared de adentro (de arriba hacia abajo).
    e2._unir(bm, afuera + adentro, [ROJO, AMARILLO, ROJO, CREMA, CREMA], False, False)
    piso_afuera = bm.faces.new(list(reversed(afuera[0])))
    piso_afuera.material_index = ROJO
    piso_adentro = bm.faces.new(adentro[-1])
    piso_adentro.material_index = CREMA
    pp.ajustar_caja(bm, MEDIDAS)
    return e2.objeto_en(nombre, bm, mats, (0, 0, 0), sombreado="duro")


def revisar(obj):
    return comun.revisar(obj, pp.PRESUPUESTO_CHICA, MEDIDAS, origen="centro")


def escena_llena(obj):
    """Foto extra: la cajita con dos porciones de papas fritas paradas adentro."""
    import papas_fritas
    objs = [obj]
    base = obj.location.copy()
    for i, (dx, dz, giro) in enumerate([(-0.013, 0.0, 80), (0.014, 0.0, 72)]):
        f = papas_fritas.construir(f"ref_papas_fritas_{i}")
        f.rotation_euler = (math.radians(90), math.radians(giro), 0.0)
        f.location = base + g2b((dx, 0.045, dz))
        objs.append(f)
    bpy.context.view_layer.update()
    return "Con dos porciones de papas fritas adentro (solo foto) · día", objs, objs, 2.2


def main():
    pp.main_comida(ID, construir, revisar,
                   "cajita_papas · 0,09 × 0,11 × 0,056 m · cajita de cartón para papas (comida)",
                   escena=escena_llena)


if __name__ == "__main__":
    main()
