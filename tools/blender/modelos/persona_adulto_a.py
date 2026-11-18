"""Modelo: adulto A (id `persona_adulto_a`; también es `cliente_base`).

Genera:
    arte/fuentes/personajes/persona_adulto_a.blend
    godot/modelos/personajes/persona_adulto_a.glb
    docs/arte/revisiones/persona_adulto_a.jpg

Uso:
    python tools/blender/modelos/persona_adulto_a.py [--sin-hoja]

La persona "de siempre": 1,75 m, contextura media, remera de manga corta, jean y zapatillas.
Es el mismo modelo que `cliente_base` (los clientes son los peatones, peaton.rs): no hay un
archivo aparte. Construcción, esqueleto, superficies y animaciones: ver _persona.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _persona  # noqa: E402

ID = "persona_adulto_a"
PRESUPUESTO = 3000  # personaje (guía 3.1)
PARAMETROS = {
    "altura": 1.75,
    "cabeza": 1.0,
    "hombros": 1.0, "cadera": 1.0, "cintura": 1.0, "pecho": 0.0, "panza": 0.0,
    "manga": "corta", "pantalon": "largo",
    "pelo": "corto",
    "vel_caminar": 1.2, "periodo_caminar": 1.0,
    "materiales": {
        "piel": "M_Piel2", "pelo": "M_PeloCastano", "remera": "M_AzulAcento",
        "pantalon": "M_Jean", "zapatillas": "M_BlancoCrema", "detalles": "M_PlasticoNegro",
    },
}


def main():
    _persona.main(ID, PARAMETROS, PRESUPUESTO, "contextura media (= cliente_base)")


if __name__ == "__main__":
    main()
