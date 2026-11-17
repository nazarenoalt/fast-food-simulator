"""Modelo: pomo de aderezo (id `pomo_aderezo`, uno para los tres aderezos de
godot/data/aderezos.ron: mostaza, ketchup y mayonesa).

Genera:
    arte/fuentes/accesorios/pomo_aderezo.blend
    godot/modelos/accesorios/pomo_aderezo.glb
    docs/arte/revisiones/pomo_aderezo.jpg

Uso:
    blender -b -P tools/blender/modelos/pomo_aderezo.py
    python tools/blender/modelos/pomo_aderezo.py

Forma: pomo apretable de plástico translúcido (12 lados), con la base apenas redondeada, un
hombro que baja hasta el cuello, una tapa a rosca y un pico cónico (8 lados) con la punta
chata. Adentro se ve el aderezo.

Un solo modelo para los tres aderezos (guía 4.2, regla 5). aderecera.rs arma cada pomo con
el color del aderezo (aderezos.ron), le pinta el pico y la tapa de ese color y le baja el
relleno con los usos (REQ-ADE-02). Por eso:
- `pieza_tapa` (tapa + pico) y `pieza_relleno` llevan M_Amarillo en el archivo (= la
  mostaza); el juego les pone el color del aderezo (`color` de aderezos.ron).
- `pieza_relleno` tiene el origen en su base (y = 0,006): el código le cambia la escala en Y
  según el nivel (0 a 1) y lo oculta si está vacío, sin moverlo.
- `pomo_aderezo_envase` (M_BolsaPlastica, alfa 0,35, como el envase de hoy): no cambia.

Medidas = lo que arma hoy aderecera.rs: envase de radio 0,028 y alto 0,17, pico hasta
0,235 → caja 0,056 × 0,235 × 0,056. Relleno de 0,006 a 0,156 (alto − 0,02, como el código),
de radio 0,0255 (el código usa 0,85 × 0,028 = 0,0238; se agranda un poco para que se lea
mejor a través del plástico).
Origen: centro de la base, a nivel de apoyo (aderecera.rs pone cada pomo a y = 0,015, arriba
de la chapa de la aderecera).

Colisión: `pomo_aderezo-colonly`, cilindro de radio 0,028 y alto 0,17 (el envase de hoy, que
tiene colisión para que la mira lo detecte). El pomo no se agarra: no tiene física propia.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

import comun  # noqa: E402
import piezas  # noqa: E402
import _etapa2 as e2  # noqa: E402

ID = "pomo_aderezo"
FAMILIA = "accesorios"
PRESUPUESTO = 500  # utensilios y objetos chicos: "pomo de aderezo" (guía 3.1)

RADIO, ALTO = 0.028, 0.17         # envase (aderecera.rs)
PUNTA = 0.235                     # arriba del pico (ALTO + 0.055 + 0.01)
Y_RELLENO, ALTO_RELLENO = 0.006, ALTO - 0.02
R_RELLENO = 0.0255
LADOS, LADOS_PICO = 12, 8         # guía 3.2: radio 1,5–5 cm → 12; menos de 1,5 cm → 8

MEDIDAS = (2 * RADIO, PUNTA, 2 * RADIO)

# Perfiles (radio, y) de abajo hacia arriba. 0 = polo.
PERFIL_ENVASE = [
    (0.0, 0.0),
    (0.0245, 0.0),
    (RADIO, 0.0045),
    (RADIO, 0.150),
    (0.0255, 0.1585),
    (0.0195, 0.1645),
    (0.0165, 0.1665),
    (0.0165, 0.172),
    (0.0, 0.172),
]
PERFIL_TAPA = [            # tapa a rosca: arranca abajo, pegada al cuello
    (0.0165, 0.1655),
    (0.0198, 0.1665),
    (0.0198, 0.1835),
    (0.0172, 0.187),
    (0.0, 0.187),
]
PERFIL_PICO = [            # abierto abajo: apoya sobre la tapa
    (0.0108, 0.1862),
    (0.0090, 0.198),
    (0.0056, 0.2165),
    (0.0044, 0.2205),
    (0.0044, 0.2315),
    (0.0030, PUNTA),
    (0.0, PUNTA),
]
PERFIL_RELLENO = [         # relativo a su origen (y = Y_RELLENO)
    (0.0, 0.0),
    (0.0225, 0.0),
    (R_RELLENO, 0.003),
    (R_RELLENO, ALTO_RELLENO - 0.004),
    (0.0235, ALTO_RELLENO),
    (0.0, ALTO_RELLENO),
]


def construir():
    m_envase, m_color = comun.cargar_materiales("M_BolsaPlastica", "M_Amarillo")

    bm = bmesh.new()
    e2.torno(bm, PERFIL_ENVASE, LADOS)
    envase = piezas.terminar(f"{ID}_envase", bm, [m_envase])

    bm = bmesh.new()
    e2.torno(bm, PERFIL_TAPA, LADOS)
    e2.torno(bm, PERFIL_PICO, LADOS_PICO)
    tapa = piezas.terminar("pieza_tapa", bm, [m_color])

    bm = bmesh.new()
    e2.torno(bm, PERFIL_RELLENO, LADOS)
    relleno = e2.objeto_en("pieza_relleno", bm, [m_color], (0, 0, 0))
    relleno.location = piezas.g2b((0, Y_RELLENO, 0))

    col = piezas.colision_cilindro(ID, RADIO, ALTO, (0, ALTO / 2, 0), lados=LADOS)
    raiz = piezas.raiz(ID, [envase, tapa, relleno, col])
    return raiz, envase, tapa, relleno, col


def chequeo_relleno(relleno):
    vs = e2.verts_godot(relleno)
    abajo, arriba = min(v.y for v in vs), max(v.y for v in vs)
    origen = relleno.matrix_world.translation
    ok = abs(abajo - Y_RELLENO) < 1e-4 and abs(arriba - (Y_RELLENO + ALTO_RELLENO)) < 1e-4 \
        and abs(origen.z - Y_RELLENO) < 1e-6 and abs(origen.x) < 1e-6 and abs(origen.y) < 1e-6
    return ok, ("Relleno de %.3f a %.3f, con el origen en su base (el juego lo escala en Y)"
                % (abajo, arriba))


# ── Hoja de revisión ───────────────────────────────────────────────────

def hoja_revision(raiz, vis, revision):
    envase, tapa, relleno = vis
    comun.preparar_revision()
    mats = e2.materiales_aderezo()
    e2.sin_cara_de_atras(envase)  # como lo dibuja Godot (el .glb ya se exportó)
    # Los tres aderezos, con distinto nivel (lleno, a la mitad, casi vacío).
    tres = []
    for i, ((nombre, _), nivel) in enumerate(zip(e2.ADEREZOS, (1.0, 0.55, 0.15))):
        dx = (i - 1) * 0.09
        en = e2.copiar(envase, f"ref_envase_{nombre}")
        ta = e2.copiar(tapa, f"ref_tapa_{nombre}", mats[nombre])
        re = e2.copiar(relleno, f"ref_relleno_{nombre}", mats[nombre])
        for o in (en, ta, re):
            o.location.x += dx + 0.4
        re.scale.z = nivel
        tres += [en, ta, re]
    cuadros = e2.sacar_fotos([
        ("Frente · día", vis, "frente", "dia"),
        ("Costado · día", vis, "costado", "dia"),
        ("3/4 · día", vis, "tres_cuartos", "dia"),
        ("3/4 · atardecer", vis, "tres_cuartos", "atardecer"),
        ("Mostaza llena, ketchup 55 %, mayonesa 15 % · día", tres, "tres_cuartos", "dia"),
    ])
    # Al lado de un pan de pancho (escala de objeto de mano).
    import pan_pancho
    pan = pan_pancho.construir("ref_pan")
    pan.location = (0.10, -0.02, 0.0225)
    cuadros += e2.sacar_fotos([
        ("Al lado de un pan de pancho · día", vis + [pan], "tres_cuartos", "dia"),
    ])
    comun.componer_hoja(
        f"{ID} · Ø 0,056 × 0,235 m · un modelo, el juego pone el color del aderezo",
        cuadros, revision, comun.RAIZ / f"docs/arte/revisiones/{ID}.jpg",
    )


def main():
    comun.escena_vacia()
    raiz, envase, tapa, relleno, col = construir()
    vis = [envase, tapa, relleno]
    revision = comun.revisar(vis, PRESUPUESTO, MEDIDAS, origen="base")
    revision.insert(1, chequeo_relleno(relleno))
    ok = comun.imprimir_revision(ID, revision)
    comun.guardar_blend(comun.RAIZ / f"arte/fuentes/{FAMILIA}/{ID}.blend")
    comun.exportar_glb([raiz, envase, tapa, relleno, col], comun.RAIZ / f"godot/modelos/{FAMILIA}/{ID}.glb")
    if "--sin-hoja" not in sys.argv:
        hoja_revision(raiz, vis, revision)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
