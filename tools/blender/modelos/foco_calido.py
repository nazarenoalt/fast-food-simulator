"""Modelo: foco cálido colgante (id `foco_calido`, godot/data/accesorios.ron).

Genera:
    arte/fuentes/accesorios/foco_calido.blend
    godot/modelos/accesorios/foco_calido.glb
    docs/arte/revisiones/foco_calido.jpg

Uso:
    blender -b -P tools/blender/modelos/foco_calido.py
    python tools/blender/modelos/foco_calido.py

Forma: lamparita colgando de su cable, como las de los carritos de noche. Arriba un
florón chico donde se engancha, el cable negro (6 lados, 4 mm de radio: la excepción de
cables de la guía 2.2), el portalámparas de baquelita negra y la lamparita en forma de pera
(`pieza_lampara`, M_LuzCalida, objeto aparte para que el código la prenda y la apague).
El *Empty* `punto_luz` va en el centro de la lamparita: ahí el juego pone la luz.
Medidas: Ø 0,07 × 0,38 m (la lamparita tiene el radio de la de hoy, 0,035).
Origen: arriba, en el punto de donde cuelga (guía 2.4); revisar() no tiene esa opción, así
que el chequeo del origen es propio: tope en y = 0, centrado en X y Z.
Sin colisión (colision: false en accesorios.ron).
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402
import bmesh  # noqa: E402

import comun  # noqa: E402
import piezas  # noqa: E402

ID = "foco_calido"
FAMILIA = "accesorios"
PRESUPUESTO = 300
LARGO = 0.38
RADIO_LAMPARA = 0.035        # = radio_foco de LuzNocturna (rust/game/src/luz.rs)
MEDIDAS = (2 * RADIO_LAMPARA, LARGO, 2 * RADIO_LAMPARA)

FLORON = (0.012, 0.010, 8)   # radio, alto, lados: el enganche de arriba
CABLE = (0.004, 6)           # radio, lados
PORTA_ARRIBA = -0.265        # portalámparas: de acá para abajo
# Perfil del portalámparas (radio, y), de arriba hacia abajo: cuello, cuerpo y aro.
PERFIL_PORTA = [(0.009, PORTA_ARRIBA), (0.017, PORTA_ARRIBA - 0.012), (0.017, -0.303),
                (0.0155, -0.309)]
# Perfil de la lamparita (radio, y): rosca, cuello que se abre y la pera.
CENTRO_LAMPARA = -LARGO + RADIO_LAMPARA
# El radio se agranda 1/cos(15°) para que las caras planas (no las aristas) midan el radio.
AJUSTE = 1 / math.cos(math.pi / 12)
PERFIL_LAMPARA = [(0.0135, -0.307), (0.0135, -0.316), (0.022, -0.325)]
PERFIL_LAMPARA += [(RADIO_LAMPARA * AJUSTE * math.sin(a), CENTRO_LAMPARA + RADIO_LAMPARA * math.cos(a))
                   for a in (math.radians(g) for g in (55, 90, 125, 155))]
PUNTA_LAMPARA = -LARGO
LADOS = 12                   # radios de 1,5 a 5 cm (guía 3.2)


def torno(bm, perfil, lados, mat, tapa_arriba=True, punta_abajo=None):
    """Revoluciona un perfil [(radio, y)] alrededor de Y (Godot). Cierra arriba con una
    tapa plana y abajo con una tapa plana o en punta (punta_abajo = y de la punta)."""
    previas = set(bm.faces)
    giro = math.pi / lados
    anillos = [[bm.verts.new(piezas.g2b((r * math.cos(giro + 2 * math.pi * k / lados), y,
                                         r * math.sin(giro + 2 * math.pi * k / lados))))
                for k in range(lados)] for r, y in perfil]
    for a, b in zip(anillos, anillos[1:]):
        for k in range(lados):
            bm.faces.new((a[k], a[(k + 1) % lados], b[(k + 1) % lados], b[k]))
    if tapa_arriba:
        bm.faces.new(anillos[0])
    if punta_abajo is None:
        bm.faces.new(anillos[-1])
    else:
        v = bm.verts.new(piezas.g2b((0, punta_abajo, 0)))
        for k in range(lados):
            bm.faces.new((anillos[-1][k], anillos[-1][(k + 1) % lados], v))
    nuevas = [f for f in bm.faces if f not in previas]
    for f in nuevas:
        f.material_index = mat
    return nuevas


def construir():
    m_negro, m_luz = comun.cargar_materiales("M_PlasticoNegro", "M_LuzCalida")
    bm = bmesh.new()
    # Arriba no hace falta tapa: nunca se ve (el foco cuelga a más de 2 m, guía 3.6).
    piezas.cilindro(bm, FLORON[0], FLORON[1], (0, -FLORON[1] / 2, 0), lados=FLORON[2], mat=0,
                    tapas=(True, False))
    alto_cable = -PORTA_ARRIBA - FLORON[1]
    piezas.cilindro(bm, CABLE[0], alto_cable + 0.004, (0, -FLORON[1] - alto_cable / 2 + 0.002, 0),
                    lados=CABLE[1], mat=0, tapas=(False, False))
    torno(bm, PERFIL_PORTA, LADOS, 0, tapa_arriba=False)
    cuerpo = piezas.terminar(f"{ID}_cuerpo", bm, [m_negro], sombreado="duro")

    bm = bmesh.new()
    torno(bm, PERFIL_LAMPARA, LADOS, 0, tapa_arriba=True, punta_abajo=PUNTA_LAMPARA)
    lampara = piezas.terminar("pieza_lampara", bm, [m_luz], sombreado="suave")

    luz = piezas.punto("punto_luz", (0, CENTRO_LAMPARA, 0))
    raiz = piezas.raiz(ID, [cuerpo, lampara, luz])
    return raiz, cuerpo, lampara, luz


def chequeo_origen(objetos):
    """Origen arriba, en el punto de donde cuelga: tope en y = 0, centrado en X y Z."""
    vs = [o.matrix_world @ v.co for o in objetos for v in o.data.vertices]
    tope = max(v.z for v in vs)
    cx = (max(v.x for v in vs) + min(v.x for v in vs)) / 2
    cz = (max(v.y for v in vs) + min(v.y for v in vs)) / 2
    ok = abs(tope) < 0.002 and abs(cx) < 0.002 and abs(cz) < 0.002
    return ok, "Origen arriba, en el punto de donde cuelga (tope en y = %.3f)" % tope


def hoja_revision(raiz, cuerpo, lampara, revision):
    import pan_pancho
    comun.preparar_revision()
    raiz.location.z = 0.6  # colgado, solo para la foto
    bpy.context.view_layer.update()  # si no, la primera foto encuadra la posición vieja
    pan = pan_pancho.construir("ref_pan")
    pan.location = piezas.g2b((0.0, 0.6 - LARGO - 0.03, 0.0))
    pan.location.x = 0.12
    pan.location.z = pan_pancho.MEDIO_ALTO
    solo, con_pan = [cuerpo, lampara], [cuerpo, lampara, pan]
    cuadros = comun.sacar_fotos([
        ("Frente · día", solo, "frente", "dia", True),
        ("Costado · día", solo, "costado", "dia", True),
        ("3/4 · día", solo, "tres_cuartos", "dia", False),
        ("Escala: pan de pancho abajo · día", con_pan, "tres_cuartos", "dia", False),
        ("3/4 · atardecer (la lamparita brilla: M_LuzCalida)", solo, "tres_cuartos", "atardecer", False),
    ])
    comun.componer_hoja(
        f"{ID} · Ø 0,07 × 0,38 m · accesorio colgante (origen arriba)",
        cuadros, revision, comun.RAIZ / f"docs/arte/revisiones/{ID}.jpg",
    )


def main():
    comun.escena_vacia()
    raiz, cuerpo, lampara, luz = construir()
    piezas_vistas = [cuerpo, lampara]
    revision = comun.revisar(piezas_vistas, PRESUPUESTO, MEDIDAS, origen="base")
    revision = [chequeo_origen(piezas_vistas) if t.startswith("Origen") else (ok, t)
                for ok, t in revision]
    bpy.context.view_layer.update()
    d = (luz.matrix_world.translation.z - CENTRO_LAMPARA)
    revision.append((abs(d) < 1e-4, "punto_luz en el centro de la lamparita (y = %.3f)" % CENTRO_LAMPARA))
    ok = comun.imprimir_revision(ID, revision)
    comun.guardar_blend(comun.RAIZ / f"arte/fuentes/{FAMILIA}/{ID}.blend")
    comun.exportar_glb([raiz, cuerpo, lampara, luz], comun.RAIZ / f"godot/modelos/{FAMILIA}/{ID}.glb")
    if "--sin-hoja" not in sys.argv:
        hoja_revision(raiz, cuerpo, lampara, revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
