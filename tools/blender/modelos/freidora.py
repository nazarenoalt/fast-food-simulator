"""Modelo: freidora eléctrica de mostrador (id `freidora`, accesorios.ron, SPEC-026).

Genera:
    arte/fuentes/cocina/freidora.blend
    godot/modelos/cocina/freidora.glb
    docs/arte/revisiones/freidora.jpg

Uso:
    blender -b -P tools/blender/modelos/freidora.py
    python tools/blender/modelos/freidora.py

Forma, medidas y piezas: ver _freidora.py. Angosta y profunda: 0,26 × 0,328 × 0,474, así dos
entran en la porción de mesada más chica (0,57 m entre anclajes del carro kiosco).

Objetos (hijos del Empty `freidora`, origen = centro de la base, a nivel del mostrador):
- `freidora_cuerpo` (Acero, MetalOscuro, PlasticoNegro): cuerpo, cuba, cabezal, perilla, patas.
- `pieza_piloto` (M_PilotoApagado) y `pieza_aceite` (M_Aceite, transparente, origen en su cara
  de arriba): piezas que el juego podrá cambiar al freír.
- `punto_colador`: centro del canasto del colador apoyado en la cuba (el Surtido del dato).
- `freidora-colonly`: cuba hueca (fondo y 4 paredes) y cabezal macizo.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _equipos as eq  # noqa: E402
import _freidora as fr  # noqa: E402

ID = "freidora"
MEDIDAS = (fr.ANCHO, fr.ALTO, fr.PROFUNDIDAD)


def construir():
    return fr.construir(ID, [0.0])


def revisar(m):
    return fr.revisar(m, MEDIDAS)


def hoja(m, revision):
    segunda = fr.construir("ref_freidora_2", [0.0])
    for o in fr.visibles(segunda):
        o.hide_render = True   # solo aparece en la última foto (si no, se superpone con la primera)
    fr.hoja(ID, "freidora · 0,26 × 0,328 × 0,474 m · equipo de cocina (angosta: entran dos por porción)",
            m["raiz"], fr.visibles(m), fr.coladores(m), revision,
            segunda=fr.visibles(segunda) + [segunda["raiz"]])


def main():
    eq.main_modelo(ID, fr.FAMILIA, construir, revisar, hoja, fr.exportar)


if __name__ == "__main__":
    main()
