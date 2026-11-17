"""Modelo: bicicleta (id `bicicleta`, lista-de-modelos, etapa 3 · Plaza). ⚠ Propuesta: todavía
no está en ninguna spec ni en el juego.

Genera:
    arte/fuentes/plaza/bicicleta.blend
    godot/modelos/plaza/bicicleta.glb
    docs/arte/revisiones/bicicleta.jpg

Uso:
    python tools/blender/modelos/bicicleta.py [--sin-hoja]

Forma: bicicleta de paseo genérica (sin marca), rodado 26, estacionada derecha con la pata
bajada. Cuadro de diamante (caño superior, diagonal, de asiento, vainas y tirantes) y horquilla
del color del cuadro; manubrio de paseo curvado hacia atrás, puños y asiento de goma, cadena y
palancas de hierro. Ruedas de rayos simplificados (guía 3.5, regla de los 2 m): cubierta de
goma con aro de acero en un solo anillo, 12 rayos (6 cables que pasan por la maza) y maza.

Medidas (lista ≈ 0,6 × 1,0 × 1,7): 0,60 de ancho (el manubrio) × 1,00 de alto (los puños) ×
1,70 de largo (ruedas de 0,66 de diámetro, 1,04 entre ejes). Asiento a 0,93.
Lados (guía 3.2): ruedas 24 (radio 0,33, medido en las caras: una cara plana apoya en el
piso), caños del cuadro 12 (radio 1,8 cm), vainas, tirantes, horquilla y manubrio 8 (menos de
1,5 cm), rayos 6 (cables de 4 mm, la excepción de la guía 2.2). Grosor mínimo 1 cm en todo
lo demás (palancas, cadena, plato).
Origen: centro de la base (entre los dos puntos de apoyo de las ruedas, en el piso).

Objetos (hijos del Empty `bicicleta`):
    pieza_cuadro       cuadro, horquilla y caja pedalera, en M_AzulAcento: el juego le cambia
                       el material para variar el color (M_RojoAcento, M_Amarillo...).
    pieza_rueda_del    rueda de adelante, origen en el eje (0; 0,33; 0,52): gira en X.
    pieza_rueda_tra    rueda de atrás, origen en el eje (0; 0,33; −0,52).
    pieza_pata         pata de apoyo (lado izquierdo de la bici, +X), origen en su eje: el
                       juego la levanta (o la esconde) si la bici anda.
    bicicleta_resto    manubrio, asiento, caño del asiento, plato, palancas, pedales y cadena.
    bicicleta-colonly  una caja angosta del cuadro y las ruedas y otra del manubrio.
La hoja reusa las fotos de _animales.hoja (poses y cambios de color antes de cada foto).
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402, F401  (antes que bmesh)
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

import _accesorios5 as ac  # noqa: E402
import _animales as an  # noqa: E402
import _plaza as plaza  # noqa: E402
import comun  # noqa: E402
import piezas  # noqa: E402
from piezas import g2b  # noqa: E402

ID = "bicicleta"
PRESUPUESTO = 1500  # lista de modelos
MEDIDAS = (0.60, 1.00, 1.70)
CUADRO, GOMA, ACERO, HIERRO = range(4)

R = 0.33                              # radio de la rueda (al piso)
EJE_T, EJE_D = (0, R, -0.52), (0, R, 0.52)
PEDALERA = (0, 0.28, -0.10)
ASIENTO_T = (0, 0.78, -0.25)          # punta del caño de asiento
DIR_T = (0, 0.78, 0.33)               # arriba del caño de dirección
DIR_B = (0, 0.64, 0.37)               # abajo
R_CAÑO = 0.018
PATA = (0.035, 0.27, -0.16)           # eje de la pata de apoyo


def V(*p):
    return Vector(p)


def rueda(nombre, eje, mats):
    """Cubierta + aro (un anillo de 24 con corte de 5 puntos), 6 cables-rayo por la maza
    y la maza. Origen en el eje."""
    bm = bmesh.new()
    lados = 24
    aj = 1 / math.cos(math.pi / lados)          # radio a las caras: una cara plana abajo
    # Corte (radio, x) y material de la cara que arranca en cada punto.
    corte = [(R, 0.0, GOMA), (R - 0.012, 0.017, GOMA), (R - 0.034, 0.012, ACERO),
             (R - 0.034, -0.012, GOMA), (R - 0.012, -0.017, GOMA)]
    anillos = []
    for i in range(lados):
        t = -math.pi / 2 + math.pi / lados + 2 * math.pi * i / lados
        anillos.append([bm.verts.new(g2b((x, r * aj * math.sin(t), r * aj * math.cos(t))))
                        for r, x, _ in corte])
    n = len(corte)
    for i in range(lados):
        a, b = anillos[i], anillos[(i + 1) % lados]
        for k in range(n):
            bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k])).material_index = corte[k][2]
    r_aro = R - 0.034
    for k in range(6):                           # 12 rayos: 6 cables que cruzan por la maza
        t = math.radians(15 + 30 * k)
        d = V(0, math.sin(t), math.cos(t)) * (r_aro + 0.003)
        plaza.caño(bm, -d, d, 0.004, 6, mat=ACERO, tapas=(False, False))
    piezas.cilindro(bm, 0.024, 0.08, (0, 0, 0), eje="x", lados=8, mat=ACERO, radio_a_caras=True)
    bmesh.ops.translate(bm, vec=g2b(eje), verts=bm.verts)
    return plaza_objeto(nombre, bm, mats, eje)


def plaza_objeto(nombre, bm, mats, origen):
    """Termina con el origen en `origen` y solo con los materiales que usa."""
    usados = sorted({f.material_index for f in bm.faces})
    for f in bm.faces:
        f.material_index = usados.index(f.material_index)
    bmesh.ops.translate(bm, vec=-g2b(origen), verts=bm.verts)
    obj = piezas.terminar(nombre, bm, [mats[i] for i in usados])
    obj.location = g2b(origen)
    return obj


def cuadro(mats):
    bm = bmesh.new()
    st_union = V(0, 0.75, -0.241)
    dt = V(*DIR_T) + V(0, -0.02, 0.006)
    tubos = [  # (desde, hasta, radio, lados)
        (V(*PEDALERA), V(*ASIENTO_T), R_CAÑO, 12),           # caño de asiento
        (V(*PEDALERA), V(*DIR_B) + V(0, 0.01, -0.003), 0.020, 12),   # diagonal
        (st_union, dt, R_CAÑO, 12),                          # superior
        (V(*DIR_B) + V(0, -0.02, 0.006), V(*DIR_T) + V(0, 0.02, -0.006), 0.022, 12),  # dirección
    ]
    # Sin tapas: las puntas quedan metidas en otro caño o en la caja pedalera.
    for a, b, r, l in tubos:
        plaza.caño(bm, a, b, r, l, mat=0, tapas=(False, False))
    for s in (-1, 1):
        sin = (False, True)   # la punta de arriba entra en otro caño; la del eje queda tapada
        plaza.caño(bm, V(s * 0.025, 0.28, -0.12), V(s * 0.052, R + 0.005, -0.52), 0.011, 8, mat=0, tapas=sin)  # vainas
        plaza.caño(bm, V(s * 0.014, 0.745, -0.238), V(s * 0.052, R + 0.012, -0.515), 0.010, 8, mat=0,
                   tapas=sin)  # tirantes
        plaza.caño(bm, V(s * 0.042, 0.625, 0.378), V(s * 0.048, R + 0.008, 0.518), 0.012, 8, mat=0,
                   tapas=sin)  # horquilla
    piezas.caja(bm, (0.11, 0.035, 0.045), (0, 0.63, 0.377), mat=0, rot=(-20, 0, 0))  # corona
    piezas.cilindro(bm, 0.022, 0.08, PEDALERA, eje="x", lados=12, mat=0, radio_a_caras=True)
    return plaza_objeto("pieza_cuadro", bm, mats, (0, 0, 0))


def resto(mats):
    bm = bmesh.new()
    # Caño del asiento y asiento (lofteo de adelante a atrás, goma).
    tope = V(0, 0.895, -0.284)
    plaza.caño(bm, V(*ASIENTO_T) + V(0, -0.02, 0.006), tope, 0.012, 8, mat=ACERO)
    asiento = [
        an.anillo((0, 0.912, -0.165), (0, 0, 1), 0.016, 0.012, 8, abajo=0.012),
        an.anillo((0, 0.915, -0.230), (0, 0, 1), 0.035, 0.016, 8, abajo=0.014),
        an.anillo((0, 0.917, -0.320), (0, 0, 1), 0.080, 0.020, 8, abajo=0.016),
        an.anillo((0, 0.917, -0.375), (0, 0, 1), 0.075, 0.017, 8, abajo=0.016),
    ]
    an.lofteo(bm, asiento, GOMA, punta_ini=(0, 0.910, -0.140), punta_fin=None)
    # Potencia y manubrio de paseo (curvado hacia atrás), con puños de goma.
    plaza.caño(bm, V(*DIR_T) + V(0, -0.01, 0.003), V(0, 0.925, 0.295), 0.014, 8, mat=ACERO)
    lado = [V(0.21, 0.972, 0.222), V(0.12, 0.948, 0.282), V(0.05, 0.935, 0.297)]
    linea = [V(-p.x, p.y, p.z) for p in lado] + [V(0, 0.932, 0.30)] + list(reversed(lado))
    ac.tubo(bm, linea, 0.011, 8, mat=ACERO)
    for s in (-1, 1):
        plaza.caño(bm, V(s * 0.20, 0.971, 0.225), V(s * 0.2945, 0.983, 0.194), 0.017, 8, mat=GOMA)
    # Plato y piñón (lado derecho de la bici, −X), palancas, pedales y cadena.
    x_cad = -0.058
    piezas.cilindro(bm, 0.09, 0.01, (x_cad, PEDALERA[1], PEDALERA[2]), eje="x", lados=16, mat=HIERRO,
                    radio_a_caras=True)
    piezas.cilindro(bm, 0.04, 0.01, (x_cad, R, -0.52), eje="x", lados=12, mat=HIERRO, radio_a_caras=True)
    for y in (PEDALERA[1] + 0.088, PEDALERA[1] - 0.088):
        y2 = R + (0.038 if y > PEDALERA[1] else -0.038)
        largo = math.hypot(0.42, y2 - y)
        ang = math.degrees(math.atan2(y2 - y, 0.42))
        piezas.caja(bm, (0.01, 0.01, largo), (x_cad, (y + y2) / 2, -0.31), mat=HIERRO, rot=(ang, 0, 0))
    for s, dz in ((-1, 1), (1, -1)):                 # palanca derecha adelante, izquierda atrás
        x = s * 0.072
        piezas.caja(bm, (0.014, 0.03, 0.18), (x, PEDALERA[1], PEDALERA[2] + dz * 0.075), mat=HIERRO)
        piezas.caja(bm, (0.09, 0.022, 0.065), (s * 0.125, PEDALERA[1], PEDALERA[2] + dz * 0.16), mat=GOMA)
    return plaza_objeto(f"{ID}_resto", bm, mats, (0, 0, 0))


def pata(mats):
    bm = bmesh.new()
    pie = (0.15, 0.0, -0.27)
    plaza.poste(bm, pie, PATA, 0.011, 8, mat=HIERRO, tapa_abajo=False, tapa_arriba=True)
    piezas.cilindro(bm, 0.018, 0.03, PATA, eje="x", lados=8, mat=HIERRO, radio_a_caras=True)
    return plaza_objeto("pieza_pata", bm, mats, PATA)


def construir():
    mats = comun.cargar_materiales("M_AzulAcento", "M_Goma", "M_Acero", "M_Hierro")
    c = cuadro(mats)
    rd = rueda("pieza_rueda_del", EJE_D, mats)
    rt = rueda("pieza_rueda_tra", EJE_T, mats)
    p = pata(mats)
    r = resto(mats)
    col = plaza.colision_cajas(ID, [((0.12, 0.93, 1.70), (0, 0.465, 0), (0, 0, 0)),
                                    ((0.60, 0.08, 0.14), (0, 0.96, 0.22), (0, 0, 0))])
    raiz = piezas.raiz(ID, [c, rd, rt, p, r, col])
    return {"raiz": raiz, "cuadro": c, "ruedas": [rd, rt], "pata": p, "resto": r, "col": col,
            "mats": mats}


def visibles(m):
    return [m["cuadro"]] + m["ruedas"] + [m["pata"], m["resto"]]


def revisar(m):
    res = comun.revisar(visibles(m), PRESUPUESTO, MEDIDAS, origen="base", tolerancia=0.004)
    res = ac.chequeo_normales(res, visibles(m))
    ok = True
    for o, eje in zip(m["ruedas"], (EJE_D, EJE_T)):
        mn, mx = an.limites([o])
        ok &= (o.matrix_world.translation - g2b(eje)).length < 1e-6 and abs(mn.y) < 1e-4
    ok &= (m["pata"].matrix_world.translation - g2b(PATA)).length < 1e-6
    ok &= all(len(s.material_slots) == 1 for s in [m["cuadro"]])
    res.insert(1, (ok, "pieza_rueda_del/tra con el origen en el eje y apoyadas en el piso; "
                       "pieza_pata en su eje; pieza_cuadro de un solo material (M_AzulAcento)"))
    return res


def main():
    comun.escena_vacia()
    m = construir()
    revision = revisar(m)
    ok = comun.imprimir_revision(ID, revision)
    plaza.guardar_y_exportar(ID, [m["raiz"]] + visibles(m) + [m["col"]])
    if "--sin-hoja" not in sys.argv:
        v = visibles(m)
        rojo, = comun.cargar_materiales("M_RojoAcento")
        azul = m["mats"][CUADRO]

        def color(mat):
            def poner():
                m["cuadro"].data.materials[0] = mat
            return poner
        an.hoja(ID, "bicicleta · 0,60 × 1,00 × 1,70 m · rodado 26, estacionada", [
            ("Costado (lado de la pata) · día", v, "costado", "dia", color(azul)),
            ("Frente · día", v, "frente", "dia", None),
            ("3/4 · día", v, "tres_cuartos", "dia", None),
            ("3/4 · atardecer", v, "tres_cuartos", "atardecer", None),
            ("Otro color: pieza_cuadro con M_RojoAcento", v, "tres_cuartos_atras", "dia", color(rojo)),
            ("Con la persona de 1,75 m · día", v + ["persona"], "tres_cuartos", "dia", color(azul)),
        ], revision, persona_en=(0.7, 0.0, -0.3))
        m["cuadro"].data.materials[0] = azul
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
