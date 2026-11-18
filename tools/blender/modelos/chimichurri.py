"""Modelo: frasco de chimichurri (id `chimichurri`, etapa 4; sin dato todavía).

Genera:
    arte/fuentes/comida/chimichurri.blend
    godot/modelos/comida/chimichurri.glb
    docs/arte/revisiones/chimichurri.jpg

Uso:
    blender -b -P tools/blender/modelos/chimichurri.py
    python tools/blender/modelos/chimichurri.py

Forma: frasco de vidrio de conserva Ø 0,08 × 0,12 (lista de modelos), 16 lados (radio de 4
cm, guía 3.2): cuerpo recto con la base apenas redondeada, hombro corto, cuello y tapa a
rosca roja. Adentro se ve el chimichurri, a dos tercios.

Objetos (hijos del Empty `chimichurri`), sin colisión (la pone el dato, como toda la comida):
- `chimichurri_frasco` (M_Vidrio, alfa 0,2): una sola cáscara cerrada, como el envase del
  pomo. Gris medio + alfa bajo deja ver el verde del relleno con su color (guía 4.1).
- `chimichurri_tapa` (M_RojoAcento): tapa a rosca.
- `pieza_relleno` (M_Chimichurri), 12 lados: el chimichurri, con el origen en su base
  (y = −0,0565), igual que el relleno del pomo: si el juego lo va gastando, le baja la escala
  en Y y lo oculta cuando está vacío, sin moverlo.
Origen: el centro (se agarra con la mano, guía 2.4). 360 triángulos (presupuesto 400).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402
import bmesh  # noqa: E402

import comun  # noqa: E402
import piezas  # noqa: E402
import _comida4 as c4  # noqa: E402
import _etapa2 as e2  # noqa: E402

ID = "chimichurri"
R, ALTO = 0.04, 0.12
MEDIDAS = (2 * R, ALTO, 2 * R)
PRESUPUESTO = 400
LADOS, LADOS_RELLENO = 16, 12
H = ALTO / 2
Y_RELLENO, ALTO_RELLENO, R_RELLENO = -H + 0.0035, 0.07, 0.0375

PERFIL_FRASCO = [
    (0.0, -H),
    (0.036, -H),
    (R, -H + 0.004),
    (R, 0.026),
    (0.0355, 0.035),    # hombro
    (0.031, 0.039),     # cuello
    (0.031, 0.044),     # (queda adentro de la tapa)
    (0.0, 0.044),
]
PERFIL_TAPA = [
    (0.0, 0.041),
    (0.0335, 0.041),
    (0.0335, 0.057),
    (0.031, H),
    (0.0, H),
]
PERFIL_RELLENO = [      # relativo a su origen (y = Y_RELLENO)
    (0.0, 0.0),
    (0.034, 0.0),
    (R_RELLENO, 0.003),
    (R_RELLENO, ALTO_RELLENO),
    (0.0, ALTO_RELLENO),
]


def construir():
    m_vidrio, m_tapa, m_chimi = comun.cargar_materiales("M_Vidrio", "M_RojoAcento", "M_Chimichurri")
    bm = bmesh.new()
    e2.torno(bm, PERFIL_FRASCO, LADOS)
    frasco = c4.terminar(f"{ID}_frasco", bm, [m_vidrio])
    bm = bmesh.new()
    e2.torno(bm, PERFIL_TAPA, LADOS)
    tapa = e2.objeto_en(f"{ID}_tapa", bm, [m_tapa], (0, 0, 0), sombreado="duro")
    e2.suavizar_hasta(tapa, 31)
    bm = bmesh.new()
    e2.torno(bm, PERFIL_RELLENO, LADOS_RELLENO)
    relleno = e2.objeto_en("pieza_relleno", bm, [m_chimi], (0, 0, 0), sombreado="duro")
    relleno.location = piezas.g2b((0, Y_RELLENO, 0))
    e2.suavizar_hasta(relleno, 31)
    raiz = piezas.raiz(ID, [frasco, tapa, relleno])
    return raiz, frasco, tapa, relleno


def chequeo_relleno(relleno):
    vs = e2.verts_godot(relleno)
    abajo, arriba = min(v.y for v in vs), max(v.y for v in vs)
    o = relleno.matrix_world.translation
    ok = abs(abajo - Y_RELLENO) < 1e-4 and abs(o.z - Y_RELLENO) < 1e-6 and abs(o.x) + abs(o.y) < 1e-6
    return ok, "Relleno de %.4f a %.4f, con el origen en su base (el juego lo escala en Y)" % (abajo, arriba)


def hoja_revision(raiz, vis, revision):
    frasco, tapa, relleno = vis
    comun.preparar_revision()
    raiz.location.z = H
    bpy.context.view_layer.update()  # matrix_world de los hijos, para copiarlos
    e2.sin_cara_de_atras(frasco)  # como lo dibuja Godot (el .glb ya se exportó)
    # Lleno, a la mitad y casi vacío.
    tres = []
    for i, nivel in enumerate((1.0, 0.5, 0.15)):
        copia = [e2.copiar(o, f"ref_{o.name}_{i}") for o in vis]
        for o, src in zip(copia, vis):
            o.parent = None
            o.matrix_world = src.matrix_world.copy()
            o.location.x += 0.4 + (i - 1) * 0.1
        copia[2].scale.z = nivel
        tres += copia
    ref = c4.pan_de_escala(0.1, -0.03)
    import choripan
    craiz, cpan, cchor = choripan.construir()
    cchor.data.materials[0] = c4.material_ref("chorizo_cocido", c4.COCCION_CHORIZO[1][1])
    craiz.location = (-0.11, -0.04, choripan.MEDIDAS[1] / 2)
    cuadros = e2.sacar_fotos([
        ("Frente · día", vis, "frente", "dia"),
        ("Costado · día", vis, "costado", "dia"),
        ("3/4 · día", vis, "tres_cuartos", "dia"),
        ("3/4 · atardecer", vis, "tres_cuartos", "atardecer"),
        ("Lleno, a la mitad y casi vacío (escala del relleno) · día", tres, "tres_cuartos", "dia"),
        ("Con un pan de pancho y un choripán · día", vis + [ref, cpan, cchor], "tres_cuartos", "dia"),
    ])
    c4.hoja(ID, f"{ID} · Ø 0,08 × 0,12 m · frasco de vidrio con pieza_relleno", cuadros, revision)


def main():
    comun.escena_vacia()
    raiz, frasco, tapa, relleno = construir()
    vis = [frasco, tapa, relleno]
    revision = comun.revisar(vis, PRESUPUESTO, MEDIDAS, origen="centro")
    revision.insert(1, chequeo_relleno(relleno))
    ok = comun.imprimir_revision(ID, revision)
    c4.guardar_y_exportar(ID, [raiz] + vis)
    if "--sin-hoja" not in sys.argv:
        hoja_revision(raiz, vis, revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
