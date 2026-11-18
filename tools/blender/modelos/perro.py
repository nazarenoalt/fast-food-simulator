"""Modelo: perro de plaza (id `perro`, lista-de-modelos, etapa 3 · Personajes). ⚠ Propuesta:
todavía no está en ninguna spec ni en el juego.

Genera:
    arte/fuentes/personajes/perro.blend
    godot/modelos/personajes/perro.glb
    docs/arte/revisiones/perro.jpg

Uso:
    python tools/blender/modelos/perro.py [--sin-hoja]

Forma: el perro "caramelo" mestizo de plaza, mediano, parado. Pecho hondo y cintura recogida,
cuello que sale alto del pecho, cabeza con cráneo ancho, stop marcado y hocico más angosto,
orejas semiparadas con la punta doblada hacia adelante, patas delanteras derechas y traseras
con el ángulo de la rodilla y el garrón (lo que hace que se lea "perro" de perfil), cola
media en curva hacia arriba.

Colores (guía 4.2: máximo 4):
    M_Madera (#8C5C33)      pelo caramelo (cuerpo, cabeza, patas, cola)
    M_Tronco (#61452E)      orejas y lomo, más oscuros
    M_BlancoCrema (#F2F2E6) pechera, panza del pecho, garganta, hocico, medias, punta de la cola
    M_Carbon (#262322)      nariz y ojos (cara mínima, guía 5.5)

Medidas (lista ≈ 0,3 × 0,5 × 0,8): 0,23 × 0,55 × 0,79 (ancho de muslo a muslo; alto hasta la
punta de las orejas; largo de la nariz a la punta de la cola). Cruz a 0,42 m, pecho a 0,21.
Origen: en el piso, entre las cuatro patas (las patas apoyan en Y = 0 y el apoyo está centrado
en X y Z; la cabeza y la cola corren la caja envolvente: chequeo propio).

Objetos (hijos del Empty `perro`), sin esqueleto; lo que se mueve va aparte con el origen en
su articulación, para animarlo después girando cada pieza:
    perro_cuerpo          tronco.
    pieza_cabeza          cabeza y cuello. Origen en la base del cuello (0; 0,38; 0,15):
                          X positivo baja la cabeza (olfatear), Y la gira.
    pieza_cola            origen en la base de la cola (0; 0,385; −0,215): Y la mueve de lado.
    pieza_pata_del_izq/der, pieza_pata_tra_izq/der
                          patas (izq = izquierda del perro, +X). Origen en el hombro o la
                          cadera: X las lleva adelante y atrás (caminar).
Sin colisión (es un personaje que camina: si hace falta, la arma el código, como a los peatones).
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402, F401  (antes que bmesh)
import bmesh  # noqa: E402

import _animales as an  # noqa: E402
import comun  # noqa: E402
import piezas  # noqa: E402

ID = "perro"
PRESUPUESTO = 1500  # lista de modelos
PELO, OSCURO, BLANCO, NEGRO = range(4)

# Tronco: cortes z = cte, del pecho a la grupa (z, centro y, alto arriba, alto abajo, medio ancho)
TRONCO = [
    (0.205, 0.360, 0.048, 0.070, 0.060),
    (0.160, 0.345, 0.078, 0.132, 0.095),
    (0.070, 0.348, 0.072, 0.118, 0.100),
    (-0.045, 0.355, 0.062, 0.068, 0.088),
    (-0.150, 0.358, 0.066, 0.080, 0.094),
    (-0.212, 0.364, 0.052, 0.062, 0.072),
]
PECHO = (0.0, 0.350, 0.228)
GRUPA = (0.0, 0.368, -0.238)
CUELLO = (0.0, 0.380, 0.150)
COLA = (0.0, 0.385, -0.215)
X_DEL, X_TRA = 0.052, 0.058
HOMBRO = (X_DEL, 0.340, 0.145)
CADERA = (X_TRA, 0.350, -0.160)


def panza(lados, desde, hasta):
    """¿La cara k está en la panza? (k = 0 en el lomo)."""
    return lambda k: desde <= k * 12 / lados < hasta


def tronco(mats):
    bm = bmesh.new()
    lados = 12
    anillos = [an.anillo((0, cy, z), (0, 0, 1), rx, up, lados, abajo=dn)
               for z, cy, up, dn, rx in TRONCO]
    abajo = panza(lados, 4, 8)
    lomo = lambda k: k in (0, 11)          # noqa: E731

    def color(banda, k):
        if banda <= 1 and abajo(k):
            return BLANCO                  # pechera y panza del pecho
        if lomo(k):
            return OSCURO                  # lomo oscuro
        return PELO
    an.lofteo(bm, anillos, color, punta_ini=PECHO, punta_fin=GRUPA, mat_ini=BLANCO, mat_fin=PELO)
    return an.terminar(f"{ID}_cuerpo", bm, mats, angulo=40)


def cabeza(mats):
    bm = bmesh.new()
    # Cuello: sale alto del pecho, hacia arriba y adelante. Garganta clara.
    lados = 10
    puntos = [(0, 0.355, 0.125), (0, 0.420, 0.190), (0, 0.462, 0.232)]
    radios = [(0.060, 0.070), (0.050, 0.056), (0.044, 0.046)]
    anillos = []
    for i, (p, (rx, rz)) in enumerate(zip(puntos, radios)):
        d = an.V(*puntos[min(i + 1, 2)]) - an.V(*puntos[max(i - 1, 0)])
        anillos.append(an.anillo(p, d, rx, rz, lados, arriba=(0, 0.3, -1)))
    garganta = panza(lados, 4.5, 7.5)
    an.lofteo(bm, anillos, lambda b, k: BLANCO if garganta(k) else PELO, mat_ini=PELO, mat_fin=PELO)
    # Cabeza: cortes z = cte, de la nuca al hocico.
    cortes = [  # (z, centro y, alto arriba, alto abajo, medio ancho)
        (0.218, 0.474, 0.042, 0.036, 0.044),
        (0.250, 0.478, 0.052, 0.046, 0.058),
        (0.288, 0.474, 0.044, 0.044, 0.052),
        (0.318, 0.455, 0.028, 0.034, 0.035),
        (0.362, 0.447, 0.023, 0.028, 0.029),
        (0.392, 0.446, 0.017, 0.020, 0.021),
    ]
    anillos = [an.anillo((0, cy, z), (0, 0, 1), rx, up, lados, abajo=dn) for z, cy, up, dn, rx in cortes]
    abajo = panza(lados, 3, 9)
    an.lofteo(bm, anillos, lambda b, k: BLANCO if b >= 2 and abajo(k) else PELO,
              punta_ini=(0, 0.476, 0.198), mat_ini=PELO, mat_fin=PELO)
    # Nariz y ojos.
    piezas.esfera(bm, 0.013, (0, 0.456, 0.392), lados=6, mat=NEGRO, escala=(1.2, 0.8, 0.8))
    for s in (-1, 1):
        piezas.esfera(bm, 0.0065, (s * 0.036, 0.490, 0.302), lados=6, mat=NEGRO)
    # Orejas semiparadas: suben y se abren, con la punta doblada hacia adelante.
    for s in (-1, 1):
        an.tubo(bm, [(s * 0.032, 0.500, 0.236), (s * 0.052, 0.536, 0.240), (s * 0.064, 0.550, 0.256)],
                [0.027, 0.021, 0.012], 4, mats=OSCURO, punta_fin=(s * 0.070, 0.545, 0.276),
                arriba=(0, 0, 1), aplastar=0.35)
    return an.terminar("pieza_cabeza", bm, mats, origen=CUELLO, angulo=40)


def pata(mats, nombre, puntos, radios, origen, pie_z):
    """Pata de 8 lados que sigue `puntos` (Godot) y una mano/pie que apoya en el piso hacia
    adelante. Las bandas de abajo (desde el penúltimo punto) son la "media" blanca."""
    bm = bmesh.new()
    n = len(puntos)
    an.tubo(bm, puntos, radios, 8, mats=[PELO] * (n - 2) + [BLANCO], arriba=(0, 0, 1), aplastar=1.15)
    x = puntos[-1][0]
    z0, z1 = pie_z
    pie = [
        an.anillo((x, 0.022, z0), (0, 0, 1), 0.021, 0.022, 6, abajo=0.022),
        an.anillo((x, 0.020, (z0 + z1) / 2), (0, 0, 1), 0.025, 0.018, 6, abajo=0.020),
        an.anillo((x, 0.016, z1 - 0.008), (0, 0, 1), 0.020, 0.011, 6, abajo=0.016),
    ]
    an.lofteo(bm, pie, BLANCO, punta_ini=(x, 0.024, z0 - 0.008), punta_fin=(x, 0.010, z1))
    return an.terminar(nombre, bm, mats, origen=origen, angulo=40)


def patas(mats):
    out = []
    for s, lado in ((1, "izq"), (-1, "der")):
        x = s * X_DEL
        out.append(pata(mats, f"pieza_pata_del_{lado}",
                        [(x, 0.385, 0.142), (x, 0.315, 0.150), (x, 0.220, 0.156), (x, 0.105, 0.150),
                         (x, 0.050, 0.154), (x, 0.028, 0.160)],
                        [0.026, 0.040, 0.033, 0.024, 0.022, 0.023], (x, HOMBRO[1], HOMBRO[2]),
                        (0.148, 0.208)))
        x = s * X_TRA
        out.append(pata(mats, f"pieza_pata_tra_{lado}",
                        [(x, 0.390, -0.168), (x, 0.330, -0.150), (x, 0.230, -0.122), (x, 0.115, -0.205),
                         (x, 0.050, -0.198), (x, 0.028, -0.190)],
                        [0.030, 0.056, 0.040, 0.024, 0.022, 0.023], (x, CADERA[1], CADERA[2]),
                        (-0.202, -0.142)))
    return out


def cola(mats):
    bm = bmesh.new()
    puntos = [(0, 0.382, -0.200), (0, 0.395, -0.262), (0, 0.420, -0.322), (0, 0.455, -0.366)]
    an.tubo(bm, puntos, [0.024, 0.021, 0.017, 0.012], 6, mats=[PELO, PELO, BLANCO],
            punta_fin=(0, 0.478, -0.388))
    return an.terminar("pieza_cola", bm, mats, origen=COLA, angulo=40)


def construir():
    mats = comun.cargar_materiales("M_Madera", "M_Tronco", "M_BlancoCrema", "M_Carbon")
    c = tronco(mats)
    cab = cabeza(mats)
    ps = patas(mats)
    co = cola(mats)
    r = an.raiz(ID, [c, cab, co] + ps)
    return {"raiz": r, "cuerpo": c, "cabeza": cab, "cola": co, "patas": ps}


def visibles(m):
    return [m["cuerpo"], m["cabeza"], m["cola"]] + m["patas"]


def revisar(m):
    mn, mx = an.limites(visibles(m))
    d = mx - mn
    res = comun.revisar(visibles(m), PRESUPUESTO, (d.x, d.y, d.z), origen="base")
    ok_m = 0.22 <= d.x <= 0.32 and 0.48 <= d.y <= 0.58 and 0.76 <= d.z <= 0.84
    res = an.reemplazar(res, "Medidas", ok_m, "Medidas %.3f × %.3f × %.3f m (lista ≈ 0,3 × 0,5 × 0,8)"
                        % (d.x, d.y, d.z))
    ok, texto = an.chequeo_patas(m["patas"])
    res = an.reemplazar(res, "Origen", ok, texto)
    p = m["patas"]
    res.insert(1, an.chequeo_piezas([
        (m["cabeza"], CUELLO, "cabeza en la base del cuello"),
        (m["cola"], COLA, "cola en su base"),
        (p[0], HOMBRO, "patas delanteras en el hombro"),
        (p[2], (-HOMBRO[0], HOMBRO[1], HOMBRO[2]), ""),
        (p[1], CADERA, "traseras en la cadera"),
        (p[3], (-CADERA[0], CADERA[1], CADERA[2]), ""),
    ]))
    res[1] = (res[1][0], res[1][1].replace("; ;", ";").rstrip("; "))
    return res


def pose(m, cabeza=(0, 0), cola=0, paso=0):
    """Pose para las fotos, en grados de Godot: cabeza (X baja, Y gira), cola (Y), paso (X de
    las patas: una diagonal adelante y la otra atrás)."""
    def hacer():
        m["cabeza"].rotation_euler = (math.radians(cabeza[0]), 0, math.radians(cabeza[1]))
        m["cola"].rotation_euler = (0, 0, math.radians(cola))
        del_i, tra_i, del_d, tra_d = m["patas"]
        for o, sg in ((del_i, 1), (tra_d, 1), (del_d, -1), (tra_i, -1)):
            o.rotation_euler = (math.radians(-paso * sg), 0, 0)
        bpy.context.view_layer.update()
    return hacer


def main():
    comun.escena_vacia()
    m = construir()
    revision = revisar(m)
    ok = comun.imprimir_revision(ID, revision)
    an.guardar_y_exportar(ID, [m["raiz"]] + visibles(m))
    if "--sin-hoja" not in sys.argv:
        v = visibles(m)
        mn, mx = an.limites(v)
        d = mx - mn
        quieto = pose(m)
        titulo = an.coma("perro · %.2f × %.2f × %.2f m · mestizo caramelo de plaza" % (d.x, d.y, d.z))
        an.hoja(ID, titulo, [
            ("Costado (silueta) · día", v, "costado", "dia", quieto),
            ("Frente · día", v, "frente", "dia", quieto),
            ("3/4 · día", v, "tres_cuartos", "dia", quieto),
            ("3/4 · atardecer", v, "tres_cuartos", "atardecer", quieto),
            ("Pose: olfatea (cabeza 35° en X), cola de lado, paso 20°", v, "tres_cuartos", "dia",
             pose(m, cabeza=(35, 20), cola=25, paso=20)),
            ("3/4 desde atrás · día", v, "tres_cuartos_atras", "dia", quieto),
            ("Arriba · día", v, "arriba", "dia", quieto),
            ("Con la persona de 1,75 m · día", v + ["persona"], "tres_cuartos", "dia", quieto),
        ], revision, persona_en=(0.55, 0.0, -0.2))
        pose(m)()
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
