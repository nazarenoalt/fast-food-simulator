"""Modelo: tacho de basura de plaza (id `tacho_basura`, lista-de-modelos, etapa 3 · Plaza).

Genera:
    arte/fuentes/plaza/tacho_basura.blend
    godot/modelos/plaza/tacho_basura.glb
    docs/arte/revisiones/tacho_basura.jpg

Uso:
    python tools/blender/modelos/tacho_basura.py [--sin-hoja]

Forma (guía 5.4): el cesto típico de plaza porteña, colgado de un poste. Canasto cilíndrico
de chapa (M_MetalOscuro), un poco más ancho arriba, abierto, con el borde y una faja al medio
de hierro (M_Hierro); poste de caño de hierro atrás (−Z, el frente mira a la plaza), con una
brida en el piso, un remate arriba y dos grampas que lo sostienen. Las perforaciones de la
chapa no se modelan (regla de los 2 metros).

Medidas (lista ≈ Ø 0,45 × 0,9): el canasto mide Ø 0,45 (el borde) y el poste llega a 0,90;
con el poste atrás (y su brida), la profundidad total es 0,54. Fondo del canasto a 0,40, borde a 0,86.
Lados (guía 3.2): canasto 16 (radio de 5 a 25 cm), poste 12 (1,5 a 5 cm).
Origen: centro de la caja envolvente, a nivel del piso (el poste apoya en Y = 0).
Biseles: las grampas son piezas de 3–4 cm: bisel de 8 mm (un cuarto del grosor, guía 3.3).

Objetos (hijos del Empty `tacho_basura`):
    - tacho_basura_cuerpo: canasto, poste y grampas.
    - tacho_basura-colonly: cilindro del canasto, del piso al borde (no se pasa por abajo).
    - tacho_basura_poste-colonly: caja del poste.
La faja del medio es solo color (hierro sobre la chapa), sin relieve: entra en el presupuesto.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402, F401  (antes que bmesh)
import bmesh  # noqa: E402

import _plaza as plaza  # noqa: E402
import comun  # noqa: E402
import piezas  # noqa: E402

ID = "tacho_basura"
PRESUPUESTO = 500   # lista de modelos (mobiliario urbano: 800)
MEDIDAS = (0.45, 0.90, 0.54)
CHAPA, HIERRO = 0, 1

R_BORDE = 0.225
FONDO, BORDE = 0.40, 0.86
R_POSTE = 0.03
Z_POSTE = -(R_BORDE + 0.04)         # centro del poste, detrás del canasto
ALTO = 0.90


def construir():
    mats = comun.cargar_materiales("M_MetalOscuro", "M_Hierro")
    bm = bmesh.new()
    # Canasto: afuera de abajo hacia arriba, borde, y adentro hasta el fondo.
    perfil = [
        (0.0, FONDO), (0.19, FONDO),                            # fondo
        (0.197, 0.58), (0.2, 0.62),                             # faja de hierro
        (0.214, 0.83), (R_BORDE, 0.835), (R_BORDE, BORDE),      # sube abriéndose; borde
        (0.2, BORDE), (0.185, FONDO + 0.04), (0.0, FONDO + 0.04),  # adentro
    ]
    mats_bandas = [CHAPA, CHAPA, HIERRO, CHAPA, HIERRO, HIERRO, HIERRO, CHAPA, CHAPA]
    plaza.torno(bm, perfil, lados=16, mats=mats_bandas)
    # Poste con brida y remate.
    plaza.torno(bm, [(0.05, 0.0), (0.05, 0.015), (R_POSTE, 0.035),
                     (R_POSTE, ALTO - 0.03), (0.036, ALTO - 0.02), (0.0, ALTO)],
                lados=12, mats=[HIERRO] * 5, centro=(0, 0, Z_POSTE))
    # Grampas: del poste a la pared del canasto.
    for y in (0.5, 0.78):
        z0, z1 = Z_POSTE, -0.19
        piezas.caja(bm, (0.035, 0.04, z1 - z0), (0, y, (z0 + z1) / 2), mat=HIERRO, bisel=0.008)
    # Centrar la caja envolvente en Z.
    zs = [-v.co.y for v in bm.verts]
    dz = -(min(zs) + max(zs)) / 2
    bmesh.ops.translate(bm, vec=piezas.g2b((0, 0, dz)), verts=bm.verts)
    plaza.borrar_apoyadas(bm)
    cuerpo = piezas.terminar(f"{ID}_cuerpo", bm, mats)
    cols = [
        piezas.colision_cilindro(ID, R_BORDE, BORDE, (0, BORDE / 2, dz), lados=12),
        piezas.colision_caja(f"{ID}_poste", (0.07, ALTO, 0.07), (0, ALTO / 2, Z_POSTE + dz)),
    ]
    raiz = piezas.raiz(ID, [cuerpo] + cols)
    return {"raiz": raiz, "cuerpo": cuerpo, "colisiones": cols, "dz": dz}


def revisar(mod):
    res = comun.revisar(mod["cuerpo"], PRESUPUESTO, MEDIDAS, origen="base")
    vs = plaza.verts_mundo([mod["cuerpo"]])
    fondo = min(v.z for v in vs if abs(v.x) < 0.1 and abs(-v.y - mod["dz"]) < 0.1 and v.z > 0.1)
    res.append((abs(fondo - FONDO) < 0.002,
                "Canasto abierto, fondo a %.2f m y borde a %.2f m (se tira algo sin agacharse)"
                % (fondo, BORDE)))
    return res


def main():
    comun.escena_vacia()
    mod = construir()
    revision = revisar(mod)
    ok = comun.imprimir_revision(ID, revision)
    plaza.guardar_y_exportar(ID, [mod["raiz"], mod["cuerpo"]] + mod["colisiones"])
    if "--sin-hoja" not in sys.argv:
        c = [mod["cuerpo"]]
        plaza.hoja(ID, "tacho_basura · Ø 0,45 × 0,9 m (0,54 con el poste) · mobiliario urbano", [
            ("Frente · día", c, "frente", "dia", True),
            ("Costado (poste atrás) · día", c, "costado", "dia", True),
            ("3/4 · día", c, "tres_cuartos", "dia", False),
            ("3/4 · atardecer", c, "tres_cuartos", "atardecer", False),
            ("Con la persona de 1,75 m · día", c + ["persona"], "tres_cuartos", "dia", False),
            ("Arriba · día", c, "arriba", "dia", True),
        ], revision, persona_en=(0.6, 0, 0.1))
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
