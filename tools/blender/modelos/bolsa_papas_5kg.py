"""Modelo: bolsa de papas de arpillera de 5 kg (id `bolsa_papas_5kg`, bloques.ron, REQ-PAP-03).

Genera:
    arte/fuentes/stock/bolsa_papas_5kg.blend
    godot/modelos/stock/bolsa_papas_5kg.glb
    docs/arte/revisiones/bolsa_papas_5kg.jpg

Uso:
    python tools/blender/modelos/bolsa_papas_5kg.py [--sin-hoja]

Forma: la bolsa de tela de verdulería de `_bolsa_arpillera.py` (abultada, costura adelante,
boca fruncida y atada hacia el vendedor), del tamaño de su grilla: 24 papas de 200 g en
2 × 4 × 3 (columnas X, filas Z, capas Y; separación 0,096 × 0,062 × 0,072).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _bolsa_arpillera as ba  # noqa: E402

ID = "bolsa_papas_5kg"
GRILLA = (2, 4, 3)
SEPARACION = (0.096, 0.062, 0.072)


def main():
    ba.main(ID, GRILLA, SEPARACION, 51, f"{ID} · bolsa de arpillera, 24 papas (≈ 5 kg) · stock")


if __name__ == "__main__":
    main()
