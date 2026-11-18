"""Persona base parametrizada de la familia `personajes` (guía 5.5).

De acá salen `persona_adulto_a` (= `cliente_base`), `persona_adulto_b`, `persona_mayor` y
`persona_chico`: cada script define sus PARAMETROS y llama a main(). Los peinados
(`pelos_set`) también se arman acá (pelo()), porque se apoyan sobre la misma cabeza.

Ejes: se trabaja directo en ejes de Blender. La persona mira hacia −Y de Blender (= +Z de
Godot, guía 2.3); su izquierda es +X. Origen en el piso, entre los pies.

── Malla ──────────────────────────────────────────────────────────────────────
Un solo objeto `cuerpo` con piel (skin), hecho de piezas cerradas que se pisan en las
articulaciones (como un muñeco articulado, pero con las uniones suavizadas): torso, cuello,
cabeza (con nariz, orejas, ojos y cejas), brazos, manos tipo mitón y zapatillas. Cada pieza es
un "lofteo" de anillos, sombreado suave, con arista dura donde cambia el material.
Superficies (materiales, en este orden en el .glb):
    0 piel        cara, cuello, brazos, manos (y piernas si el pantalón es corto)
    1 pelo        las cejas (el peinado va aparte, `pelo`); el juego le pone el color del pelo
    2 remera      remera o camisa (con la manga y el ruedo marcados con un escalón)
    3 pantalon    pantalón (largo o corto)
    4 zapatillas  zapatillas
    5 detalles    ojos y suela de las zapatillas (gris casi negro, no se cambia)
6 materiales (excepción a la regla de 4, como los carritos: cada parte es una superficie que el
juego colorea por separado).

── Esqueleto ──────────────────────────────────────────────────────────────────
Nombres del perfil humanoide de Godot (SkeletonProfileHumanoid), sin dedos (manos mitón):
    Root → Hips → Spine → Chest → UpperChest → Neck → Head
    UpperChest → LeftShoulder → LeftUpperArm → LeftLowerArm → LeftHand   (ídem Right…)
    Hips → LeftUpperLeg → LeftLowerLeg → LeftFoot → LeftToes              (ídem Right…)
Mismos nombres y jerarquía en todas las variantes. Root está en el origen (piso), sin pesos.
Pose de descanso: parado, brazos colgando apenas separados del cuerpo (no T-pose: en Godot,
para reasignar a otro esqueleto, usar "Fix Silhouette" en la importación).
Pesos semirrígidos: cada pieza sigue a su hueso; en rodillas, codos, cintura, caderas y
cuello los anillos de la unión se reparten entre los dos huesos (máx. 2–3 por vértice).

── Puntos ─────────────────────────────────────────────────────────────────────
    punto_pelo  hijo del hueso Head, en la base del cráneo (la cabeza del hueso), escalado por
                la escala de la cabeza de la variante. El peinado (`pelo`) es su hijo con
                transformación identidad: para cambiarlo, se pone un `pelo_<nombre>` de
                pelos_set.glb como hijo de punto_pelo, en (0, 0, 0), sin giro ni escala.
    punto_mano_d  hijo de RightHand, en la palma (donde va el pancho al comer).

── Animaciones ────────────────────────────────────────────────────────────────
Acciones calculadas por código para las medidas de cada variante (los pies apoyados no
patinan: las piernas se resuelven con IK analítica). 30 cuadros por segundo, todas en loop (el
último cuadro es igual al primero; en Godot hay que ponerles loop_mode = LOOP_LINEAR):
    quieto            4 s    respiración y balanceo leve
    caminar           1 ciclo (adulto 1,0 s a 1,2 m/s), en el lugar
    trotar            1 ciclo (adulto 0,7 s a 2,8 m/s = VEL_TROTE), en el lugar
    esperar           8 s    en la fila: cambia el peso, mira a los costados y una vez el reloj
    charlar           6 s    gestos con las manos, asiente, se encoge de hombros
    comer             3 s    brazo derecho a la boca (con el pancho en punto_mano_d); el resto
                             del cuerpo queda en la pose de descanso: para mezclarla arriba de
                             otra, filtrar RightShoulder…RightHand, Neck y Head
    caminar_comiendo  3 ciclos de caminar con el brazo de comer (se va comiendo)
    sentado           6 s    en el banco: el origen es el punto del asiento (0,12 m delante del
                             centro del banco, como caminos.rs); la cola apoya a 0,45 m
La velocidad de cada variante está en sus PARAMETROS (vel_caminar, vel_trotar): el código
tiene que reproducir caminar a velocidad = vel_del_peatón / vel_caminar para no patinar.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402  (antes que bmesh)
import bmesh  # noqa: E402
from mathutils import Matrix, Quaternion, Vector  # noqa: E402
from mathutils.bvhtree import BVHTree  # noqa: E402

import comun  # noqa: E402

FAMILIA = "personajes"
FPS = 30
V = Vector
ADELANTE = V((0, -1, 0))   # hacia donde mira la persona
ARRIBA = V((0, 0, 1))
IZQ = V((1, 0, 0))         # izquierda de la persona (+X)

SUPERFICIES = ["piel", "pelo", "remera", "pantalon", "zapatillas", "detalles"]
PIEL, PELO, REMERA, PANTALON, ZAPAS, DETALLE = range(6)

# (hueso, padre). Orden: padres primero.
HUESOS = [
    ("Root", None), ("Hips", "Root"), ("Spine", "Hips"), ("Chest", "Spine"),
    ("UpperChest", "Chest"), ("Neck", "UpperChest"), ("Head", "Neck"),
]
for _l in ("Left", "Right"):
    HUESOS += [
        (f"{_l}Shoulder", "UpperChest"), (f"{_l}UpperArm", f"{_l}Shoulder"),
        (f"{_l}LowerArm", f"{_l}UpperArm"), (f"{_l}Hand", f"{_l}LowerArm"),
    ]
for _l in ("Left", "Right"):
    HUESOS += [
        (f"{_l}UpperLeg", "Hips"), (f"{_l}LowerLeg", f"{_l}UpperLeg"),
        (f"{_l}Foot", f"{_l}LowerLeg"), (f"{_l}Toes", f"{_l}Foot"),
    ]
NOMBRES = [h for h, _ in HUESOS]
PADRE = dict(HUESOS)
LADOS = (("Left", 1.0), ("Right", -1.0))


# ── Medidas ────────────────────────────────────────────────────────────

def medidas(P):
    """Puntos y largos de la variante, a partir de sus parámetros.

    P: altura (m), cabeza (escala de la cabeza; 1 = adulto, 23,5 cm de mentón a coronilla),
    hombros, cadera, cintura, pecho (0–1), panza (0–1), grosor (brazos y piernas),
    piernas (largo relativo de las piernas), ancho (escala general de anchos).
    """
    s = P.get("cabeza", 1.0)
    H = P["altura"]
    alto_cabeza = 0.235 * s
    L = H - alto_cabeza                 # del piso al mentón
    k = L / 1.515                       # escala del cuerpo respecto del adulto de 1,75
    w = k * P.get("ancho", 1.0)         # escala de anchos
    g = w * P.get("grosor", 1.0)        # escala de brazos y piernas
    pier = P.get("piernas", 1.0)
    M = dict(H=H, s=s, L=L, k=k, w=w, g=g, alto_cabeza=alto_cabeza)
    M["tobillo"] = 0.083 * k
    M["rodilla"] = 0.335 * L * pier
    M["cadera"] = 0.575 * L * pier
    M["entrepierna"] = M["cadera"] - 0.06 * k
    # Del pantalón para arriba, el torso se reparte entre la cadera y el mentón.
    tor = lambda f: M["cadera"] + (L - M["cadera"]) * f  # noqa: E731
    M["tor"] = tor
    M["spine"] = tor(0.18)
    M["chest"] = tor(0.43)
    M["upperchest"] = tor(0.63)
    M["hombro"] = tor(0.80)             # articulación del hombro
    M["cuello"] = tor(0.88)             # base del cuello
    M["menton"] = L
    M["nuca"] = L + 0.03 * s            # cabeza del hueso Head (base del cráneo)
    M["x_cadera"] = 0.088 * w * P.get("cadera", 1.0) ** 0.5
    M["x_hombro"] = 0.183 * w * P.get("hombros", 1.0)
    M["brazo"] = 0.215 * L / 1.0 * (1.515 / 1.515)
    M["antebrazo"] = 0.168 * L
    M["mano"] = 0.118 * L
    # Pie (en el plano de la marcha): talón atrás y metatarso adelante del tobillo.
    M["talon"] = 0.062 * k
    M["metatarso"] = 0.145 * k
    M["punta"] = 0.065 * k
    return M


# ── Lofteo ─────────────────────────────────────────────────────────────

def _marco(d, ref=IZQ):
    """Dos vectores perpendiculares a d: u (hacia `ref`) y w = d × u."""
    u = ref - d * ref.dot(d)
    if u.length < 1e-6:
        u = ADELANTE - d * ADELANTE.dot(d)
    u.normalize()
    return u, d.cross(u).normalized()


def anillo_eje(c, d, rx, ry, n, ref=IZQ, giro=0.0, expo=2.0):
    """Anillo de n puntos alrededor del eje d, centrado en c. rx en la dirección `ref`."""
    u, w = _marco(d.normalized(), ref)
    pts = []
    for i in range(n):
        a = giro + 2 * math.pi * i / n
        ca, sa = math.cos(a), math.sin(a)
        ex = 2.0 / expo
        x = math.copysign(abs(ca) ** ex, ca) * rx
        y = math.copysign(abs(sa) ** ex, sa) * ry
        pts.append(c + u * x + w * y)
    return pts


def anillo_torso(z, ancho, frente, atras, yc=0.0, n=14, expo=2.6, x0=0.0):
    """Anillo horizontal: media ancho, profundidad hacia adelante y hacia atrás distintas.
    El punto 0 queda a la izquierda (+X); los puntos van de la izquierda al frente."""
    pts = []
    ex = 2.0 / expo
    for i in range(n):
        a = 2 * math.pi * i / n
        ca, sa = math.cos(a), math.sin(a)
        x = math.copysign(abs(ca) ** ex, ca) * ancho
        prof = frente if sa > 0 else atras
        y = -math.copysign(abs(sa) ** ex, sa) * prof   # sa > 0 → adelante (−Y)
        pts.append(V((x0 + x, yc + y, z)))
    return pts


class Malla:
    """bmesh con pesos (capa deform) y materiales por cara."""

    def __init__(self):
        self.bm = bmesh.new()
        self.dl = self.bm.verts.layers.deform.verify()
        self.grupos = {n: i for i, n in enumerate(NOMBRES)}

    def _pesar(self, v, pesos):
        tot = sum(pesos.values())
        for n, p in pesos.items():
            if p > 1e-4:
                v[self.dl][self.grupos[n]] = p / tot

    def loft(self, anillos, pesos, mats, tapa_ini=None, tapa_fin=None, mat_tapas=None):
        """anillos: [[Vector]] (mismo n); pesos: un dict por anillo; mats: material de cada
        banda (lista) o función (banda, k) → material. tapa_*: punto (abanico) o "plana"."""
        bm = self.bm
        n = len(anillos[0])
        vs = []
        for a, p in zip(anillos, pesos):
            fila = [bm.verts.new(q) for q in a]
            for v in fila:
                self._pesar(v, p)
            vs.append(fila)
        caras = []
        mat = mats if callable(mats) else (lambda b, k: mats[b])
        for b, (a1, a2) in enumerate(zip(vs, vs[1:])):
            for k in range(n):
                f = bm.faces.new((a1[k], a1[(k + 1) % n], a2[(k + 1) % n], a2[k]))
                f.material_index = mat(b, k)
                caras.append(f)
        for tapa, fila, p, m in ((tapa_ini, vs[0], pesos[0], 0), (tapa_fin, vs[-1], pesos[-1], -1)):
            mt = mat_tapas if mat_tapas is not None else (mat(0, 0) if m == 0 else mat(len(vs) - 2, 0))
            if tapa is None:
                continue
            if isinstance(tapa, str):
                f = bm.faces.new(fila)
                f.material_index = mt
                caras.append(f)
            else:
                c = bm.verts.new(tapa)
                self._pesar(c, p)
                for k in range(n):
                    f = bm.faces.new((fila[k], fila[(k + 1) % n], c))
                    f.material_index = mt
                    caras.append(f)
        bmesh.ops.recalc_face_normals(bm, faces=caras)
        # La heurística de Blender a veces se equivoca en piezas con escalones (mangas):
        # se decide por el volumen con signo de la pieza cerrada.
        vol = 0.0
        for f in caras:
            v = [x.co for x in f.verts]
            for i in range(1, len(v) - 1):
                vol += v[0].dot(v[i].cross(v[i + 1])) / 6
        if vol < 0:
            for f in caras:
                f.normal_flip()
        return caras

    def objeto(self, nombre, materiales):
        bm = self.bm
        for f in bm.faces:
            f.smooth = True
        for e in bm.edges:
            fs = e.link_faces
            if len(fs) == 2:
                distinto = fs[0].material_index != fs[1].material_index
                e.smooth = not (distinto or fs[0].normal.angle(fs[1].normal, 0) > math.radians(55))
        obj = comun.objeto_desde_bmesh(nombre, bm, materiales)
        for n in NOMBRES:
            obj.vertex_groups.new(name=n)
        return obj


def mezcla(a, b, t):
    """Pesos entre el hueso a (t = 0) y el b (t = 1)."""
    t = min(1.0, max(0.0, t))
    return {a: 1 - t, b: t}


def suave(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


# ── Cuerpo ─────────────────────────────────────────────────────────────

def puntos_brazo(M, lado):
    """Hombro, codo y muñeca (pose de descanso: brazo colgando, 7° separado, codo apenas
    doblado hacia adelante)."""
    hombro = V((lado * M["x_hombro"], 0.0, M["hombro"]))
    a0 = math.radians(7)
    d1 = V((lado * math.sin(a0), 0.0, -math.cos(a0)))
    codo = hombro + d1 * M["brazo"]
    d2 = V((lado * math.sin(a0) * 0.8, -math.sin(math.radians(8)), -1)).normalized()
    muneca = codo + d2 * M["antebrazo"]
    return hombro, codo, muneca


def puntos_pierna(M, lado):
    cadera = V((lado * M["x_cadera"], 0.0, M["cadera"]))
    rodilla = V((lado * M["x_cadera"] * 0.93, -0.004 * M["k"], M["rodilla"]))
    tobillo = V((lado * M["x_cadera"] * 0.9, 0.0, M["tobillo"]))
    return cadera, rodilla, tobillo


def torso(m, M, P):
    w, tor = M["w"], M["tor"]
    hom, cad, cin = P.get("hombros", 1.0), P.get("cadera", 1.0), P.get("cintura", 1.0)
    pecho, panza = P.get("pecho", 0.0), P.get("panza", 0.0)
    c, ent = M["cadera"], M["entrepierna"]
    ruedo = tor(0.15)   # ruedo de la remera
    filas = [
        # (z, ancho, frente, atrás, yc, material de la banda de arriba)
        (ent - 0.01 * w, 0.075 * w * cad, 0.05 * w, 0.06 * w, 0.005, PANTALON),
        (ent + 0.035 * w, 0.150 * w * cad, 0.080 * w, 0.100 * w, 0.010, PANTALON),
        (c + 0.035 * w, 0.163 * w * cad, 0.090 * w, 0.105 * w, 0.008, PANTALON),
        (ruedo, 0.156 * w * (cad + cin) / 2, 0.092 * w + 0.012 * w * panza, 0.092 * w, 0.004, None),
        (ruedo, 0.166 * w * (cad + cin) / 2, 0.100 * w + 0.014 * w * panza, 0.100 * w, 0.004, REMERA),
        (tor(0.30), 0.150 * w * cin, 0.098 * w + 0.03 * w * panza, 0.090 * w, 0.0, REMERA),
        (tor(0.47), 0.158 * w * (cin + hom) / 2, 0.104 * w + 0.022 * w * panza + 0.008 * w * pecho,
         0.092 * w, -0.002, REMERA),
        (tor(0.60), 0.165 * w * hom, 0.112 * w + 0.03 * w * pecho, 0.098 * w, -0.004, REMERA),
        (tor(0.71), 0.174 * w * hom, 0.104 * w + 0.012 * w * pecho, 0.098 * w, -0.002, REMERA),
        (tor(0.80), 0.178 * w * hom, 0.084 * w, 0.087 * w, 0.004, REMERA),
        (tor(0.86), 0.150 * w * hom, 0.070 * w, 0.076 * w, 0.010, REMERA),
        (tor(0.915), 0.100 * w * hom ** 0.5, 0.058 * w, 0.064 * w, 0.010, REMERA),
        (tor(0.945), 0.062 * w, 0.052 * w, 0.056 * w, 0.010, REMERA),
    ]
    anillos, pesos, mats = [], [], []
    for z, an, fr, at, yc, mt in filas:
        anillos.append(anillo_torso(z, an, fr, at, yc * w))
        if z < c + 0.04 * w:
            p = {"Hips": 1.0}
        elif z < M["spine"] + 0.05 * w:
            p = mezcla("Hips", "Spine", (z - c - 0.04 * w) / (M["spine"] + 0.05 * w - c - 0.04 * w))
        elif z < M["chest"]:
            p = mezcla("Spine", "Chest", (z - M["spine"] - 0.05 * w) / (M["chest"] - M["spine"] - 0.05 * w))
        elif z < M["upperchest"] + 0.03 * w:
            p = mezcla("Chest", "UpperChest", (z - M["chest"]) / (M["upperchest"] + 0.03 * w - M["chest"]))
        else:
            p = {"UpperChest": 1.0}
        pesos.append(p)
        mats.append(mt)
    # Material de cada banda = el de su anillo de arriba (None = escalón del ruedo: remera).
    bandas = [(mats[i + 1] if mats[i + 1] is not None else REMERA) for i in range(len(filas) - 1)]
    bandas[2] = PANTALON  # de la cadera al ruedo
    bandas[3] = REMERA    # el escalón del ruedo es la remera vista desde abajo
    m.loft(anillos, pesos, bandas, tapa_ini=V((0, 0.004, ent - 0.03 * w)),
           tapa_fin=V((0, 0.010 * w, tor(0.965))))


def cuello(m, M):
    k = M["w"]
    z0, z1 = M["tor"](0.86), M["nuca"] + 0.03 * M["s"]
    anillos, pesos = [], []
    for t, r in ((0.0, 0.060), (0.35, 0.054), (0.75, 0.051), (1.0, 0.048)):
        z = z0 + (z1 - z0) * t
        anillos.append(anillo_eje(V((0, 0.012 * k + 0.004 * t, z)), ARRIBA, r * k, r * k * 1.05, 8))
        pesos.append({"UpperChest": 0.5, "Neck": 0.5} if t == 0 else
                     ({"Neck": 1.0} if t < 0.9 else {"Neck": 0.5, "Head": 0.5}))
    m.loft(anillos, pesos, [PIEL] * 3, tapa_ini="plana", tapa_fin="plana")


# Cabeza (escala 1, adulto). Anillos: (z sobre el mentón, media ancho, frente, atrás, yc).
CABEZA = [
    (0.000, 0.034, 0.016, 0.016, -0.072),
    (0.030, 0.061, 0.032, 0.052, -0.050),
    (0.070, 0.071, 0.052, 0.085, -0.040),
    (0.112, 0.076, 0.096, 0.096, 0.000),
    (0.150, 0.078, 0.094, 0.100, 0.002),
    (0.188, 0.073, 0.084, 0.096, 0.004),
    (0.212, 0.065, 0.070, 0.084, 0.006),
    (0.229, 0.042, 0.044, 0.054, 0.006),
]
LADOS_CABEZA = 12
NUCA_REL = V((0, 0.012, 0.030))   # cabeza del hueso Head respecto del mentón (centro)


def anillos_cabeza(s, origen):
    """Anillos de la cabeza a escala s; origen = punto del mentón (centro del eje)."""
    return [anillo_torso(origen.z + z * s, an * s, fr * s, at * s, origen.y + yc * s, n=LADOS_CABEZA,
                         expo=2.15, x0=origen.x)
            for z, an, fr, at, yc in CABEZA]


def cabeza(m, M):
    s = M["s"]
    o = V((0, 0, M["menton"]))
    anillos = anillos_cabeza(s, o)
    m.loft(anillos, [{"Head": 1.0}] * len(anillos), [PIEL] * (len(anillos) - 1),
           tapa_ini=o + V((0, -0.070 * s, -0.004 * s)), tapa_fin=o + V((0, 0.006 * s, 0.235 * s)))
    H = {"Head": 1.0}
    # Nariz: cuña chica.
    bm = m.bm
    base_z, punta_z = o.z + 0.069 * s, o.z + 0.104 * s
    y_cara = o.y - 0.094 * s
    pts = [V((-0.011 * s, y_cara + 0.008 * s, base_z)), V((0.011 * s, y_cara + 0.008 * s, base_z)),
           V((0, y_cara - 0.010 * s, base_z + 0.006 * s)), V((0, y_cara + 0.004 * s, punta_z)),
           V((0, y_cara + 0.016 * s, base_z + 0.01 * s))]
    vs = [bm.verts.new(p) for p in pts]
    for v in vs:
        m._pesar(v, H)
    caras = [bm.faces.new((vs[0], vs[2], vs[1])), bm.faces.new((vs[0], vs[3], vs[2])),
             bm.faces.new((vs[1], vs[2], vs[3])), bm.faces.new((vs[0], vs[1], vs[4])),
             bm.faces.new((vs[1], vs[3], vs[4])), bm.faces.new((vs[0], vs[4], vs[3]))]
    for f in caras:
        f.material_index = PIEL
    bmesh.ops.recalc_face_normals(bm, faces=caras)
    for lado in (1, -1):
        # Ojos: lentejas oscuras chicas, a media altura de la cabeza.
        c = V((lado * 0.031 * s, o.y - 0.087 * s, o.z + 0.116 * s))
        d = V((lado * 0.25, -1, 0)).normalized()
        a1 = anillo_eje(c, d, 0.0085 * s, 0.0068 * s, 6, ref=IZQ)
        m.loft([a1], [H], [], tapa_ini=c + d * 0.0045 * s, tapa_fin=c - d * 0.004 * s, mat_tapas=DETALLE)
        # Cejas: barritas del color del pelo, un poco inclinadas.
        c = V((lado * 0.033 * s, o.y - 0.091 * s, o.z + 0.141 * s))
        e = V((lado, -0.18 * lado * 0, 0.06)).normalized()
        a1 = anillo_eje(c - e * 0.014 * s, e, 0.0030 * s, 0.0045 * s, 4, ref=ARRIBA, giro=math.pi / 4)
        a2 = anillo_eje(c + e * 0.014 * s + V((0, 0.005 * s, 0.002 * s)), e, 0.0024 * s, 0.0038 * s, 4,
                        ref=ARRIBA, giro=math.pi / 4)
        m.loft([a1, a2], [H, H], [PELO], tapa_ini="plana", tapa_fin="plana")
        # Orejas: medio disco aplastado al costado.
        c = V((lado * 0.074 * s, o.y + 0.008 * s, o.z + 0.105 * s))
        d = V((lado, 0.25, 0)).normalized()
        a1 = anillo_eje(c, d, 0.022 * s, 0.013 * s, 6, ref=ARRIBA)
        a2 = anillo_eje(c + d * 0.011 * s, d, 0.019 * s, 0.011 * s, 6, ref=ARRIBA)
        m.loft([a1, a2], [H, H], [PIEL], tapa_ini="plana", tapa_fin="plana")


def brazo(m, M, P, lado, nombre):
    g = M["g"]
    hombro, codo, muneca = puntos_brazo(M, lado)
    larga = P.get("manga", "corta") == "larga"
    d1 = (codo - hombro).normalized()
    d2 = (muneca - codo).normalized()
    dc = (d1 + d2).normalized()
    S, U, Lo = f"{nombre}Shoulder", f"{nombre}UpperArm", f"{nombre}LowerArm"
    afuera = V((lado, 0, 0))
    filas = []  # (centro, eje, radio x, radio y, pesos, material de la banda que sigue)
    # Hombro redondo: el eje del brazo sale de al lado del cuello hacia afuera y se dobla
    # por encima de la articulación hacia abajo (los anillos siguen la curva).
    p0 = hombro + V((-lado * 0.070 * g, 0, 0.040 * g))
    p1 = hombro + V((-lado * 0.018 * g, 0, 0.030 * g))
    d0 = V((lado, 0, -0.25)).normalized()
    dm = (V((lado, 0, -1.0)) + d1).normalized()
    tope = p0 - d0 * 0.03 * g
    filas.append((p0, d0, 0.034 * g, 0.036 * g, {S: 0.8, U: 0.2}, REMERA))
    filas.append((p1, dm, 0.043 * g, 0.045 * g, {S: 0.45, U: 0.55}, REMERA))
    filas.append((hombro - d1 * 0.025 * g, d1, 0.048 * g, 0.050 * g, {U: 0.9, S: 0.1}, REMERA))
    fin_manga = 0.45 if not larga else 1.0
    if not larga:
        filas.append((hombro + d1 * M["brazo"] * 0.30, d1, 0.047 * g, 0.048 * g, {U: 1.0}, REMERA))
        fm = hombro + d1 * M["brazo"] * fin_manga
        filas.append((fm, d1, 0.047 * g, 0.048 * g, {U: 1.0}, PIEL))      # borde de la manga
        filas.append((fm, d1, 0.039 * g, 0.041 * g, {U: 1.0}, PIEL))      # brazo adentro
        filas.append((hombro + d1 * M["brazo"] * 0.78, d1, 0.037 * g, 0.039 * g, {U: 1.0}, PIEL))
        mat_brazo = PIEL
    else:
        filas.append((hombro + d1 * M["brazo"] * 0.40, d1, 0.048 * g, 0.050 * g, {U: 1.0}, REMERA))
        filas.append((hombro + d1 * M["brazo"] * 0.78, d1, 0.043 * g, 0.045 * g, {U: 1.0}, REMERA))
        mat_brazo = REMERA
    filas.append((codo - d1 * 0.03 * g, d1, 0.036 * g, 0.038 * g, {U: 0.8, Lo: 0.2}, mat_brazo) if not larga
                 else (codo - d1 * 0.03 * g, d1, 0.041 * g, 0.043 * g, {U: 0.8, Lo: 0.2}, mat_brazo))
    rl = 0.005 * g if larga else 0.0
    filas.append((codo, dc, 0.035 * g + rl, 0.036 * g + rl, {U: 0.5, Lo: 0.5}, mat_brazo))
    filas.append((codo + d2 * 0.035 * g, d2, 0.037 * g + rl, 0.038 * g + rl, {U: 0.15, Lo: 0.85}, mat_brazo))
    filas.append((codo + d2 * M["antebrazo"] * 0.35, d2, 0.039 * g + rl, 0.036 * g + rl, {Lo: 1.0}, mat_brazo))
    if larga:
        pu = codo + d2 * M["antebrazo"] * 0.9
        filas.append((pu, d2, 0.036 * g, 0.034 * g, {Lo: 1.0}, PIEL))   # puño de la camisa
        filas.append((pu, d2, 0.027 * g, 0.024 * g, {Lo: 1.0}, PIEL))
    else:
        filas.append((codo + d2 * M["antebrazo"] * 0.75, d2, 0.031 * g, 0.028 * g, {Lo: 1.0}, PIEL))
    filas.append((muneca, d2, 0.026 * g, 0.022 * g, {Lo: 0.7, f"{nombre}Hand": 0.3}, PIEL))
    anillos = [anillo_eje(c, d, ry, rx, 8, ref=ADELANTE) for c, d, rx, ry, _, _ in filas]
    m.loft(anillos, [f[4] for f in filas], [f[5] for f in filas[:-1]],
           tapa_ini=tope, tapa_fin=muneca + d2 * 0.02 * g)
    mano(m, M, lado, nombre, muneca, d2)


def mano(m, M, lado, nombre, muneca, d):
    """Mitón: palma aplastada (la palma mira al muslo) y pulgar adelante."""
    g = M["g"]
    lm = M["mano"]
    Hn = {f"{nombre}Hand": 1.0}
    afuera = V((lado, 0, 0))
    filas = [(-0.015, 0.020, 0.028), (0.18, 0.019, 0.042), (0.45, 0.018, 0.045),
             (0.72, 0.016, 0.040), (0.92, 0.012, 0.028)]
    anillos = []
    for t, rx, ry in filas:
        c = muneca + d * lm * t + afuera * (-0.004 * g * t)
        anillos.append(anillo_eje(c, d, rx * g, ry * g, 8, ref=afuera))
    m.loft(anillos, [Hn] * len(anillos), [PIEL] * (len(anillos) - 1),
           tapa_ini=muneca - d * 0.025 * g, tapa_fin=muneca + d * lm * 1.0 + afuera * (-0.004 * g))
    # Pulgar: sale del lado de adelante de la palma, hacia abajo y adelante.
    base = muneca + d * lm * 0.22 + ADELANTE * 0.028 * g + afuera * (-0.006 * g)
    dp = (d * 0.75 + ADELANTE * 0.55 + afuera * (-0.25)).normalized()
    a = [anillo_eje(base + dp * lm * t, dp, r * g, r * g * 0.85, 6, ref=afuera)
         for t, r in ((0.0, 0.013), (0.25, 0.012), (0.45, 0.010))]
    m.loft(a, [Hn] * 3, [PIEL] * 2, tapa_ini=base - dp * 0.012 * g, tapa_fin=base + dp * lm * 0.55)


def pierna(m, M, P, lado, nombre):
    g = M["g"]
    cadera, rodilla, tobillo = puntos_pierna(M, lado)
    corto = P.get("pantalon", "largo") == "corto"
    Hp, U, Lo, F = "Hips", f"{nombre}UpperLeg", f"{nombre}LowerLeg", f"{nombre}Foot"
    d1 = (rodilla - cadera).normalized()
    d2 = (tobillo - rodilla).normalized()
    dr = (d1 + d2).normalized()
    largo1 = (rodilla - cadera).length
    largo2 = (tobillo - rodilla).length
    afuera = V((lado, 0, 0))
    atras = V((0, 1, 0))
    rp = 0.006 * g if not corto else 0.0   # el pantalón agrega un poco de volumen
    filas = [
        (cadera + V((lado * 0.012 * g, 0.004, 0.02 * g)), d1, 0.084 * g, 0.088 * g, {U: 0.5, Hp: 0.5}, PANTALON),
        (cadera + d1 * 0.07 * g + afuera * 0.006 * g, d1, 0.088 * g, 0.090 * g, {U: 0.85, Hp: 0.15}, PANTALON),
        (cadera + d1 * largo1 * 0.45, d1, 0.076 * g, 0.080 * g, {U: 1.0}, PANTALON),
    ]
    if corto:
        fb = cadera + d1 * largo1 * 0.80
        filas.append((fb, d1, 0.070 * g, 0.072 * g, {U: 1.0}, PIEL))       # ruedo de la bermuda
        filas.append((fb, d1, 0.058 * g, 0.060 * g, {U: 1.0}, PIEL))
        mat = PIEL
    else:
        filas.append((cadera + d1 * largo1 * 0.78, d1, 0.066 * g, 0.068 * g, {U: 1.0}, PANTALON))
        mat = PANTALON
    filas += [
        (rodilla - d1 * 0.035 * g, d1, 0.054 * g + rp, 0.056 * g + rp, {U: 0.8, Lo: 0.2}, mat),
        (rodilla, dr, 0.053 * g + rp, 0.055 * g + rp, {U: 0.5, Lo: 0.5}, mat),
        (rodilla + d2 * 0.045 * g, d2, 0.054 * g + rp, 0.055 * g + rp, {U: 0.15, Lo: 0.85}, mat),
        (rodilla + d2 * largo2 * 0.30 + atras * 0.010 * g, d2, 0.057 * g + rp, 0.060 * g + rp, {Lo: 1.0}, mat),
        (rodilla + d2 * largo2 * 0.62, d2, 0.045 * g + rp, 0.046 * g + rp, {Lo: 1.0}, mat),
    ]
    if corto:
        filas.append((rodilla + d2 * largo2 * 0.86, d2, 0.037 * g, 0.038 * g, {Lo: 1.0}, PIEL))
    else:
        rb = rodilla + d2 * largo2 * 0.86
        filas.append((rb, d2, 0.052 * g, 0.054 * g, {Lo: 1.0}, PANTALON))   # botamanga
        filas.append((rb, d2, 0.038 * g, 0.039 * g, {Lo: 1.0}, PIEL))
    filas.append((tobillo + V((0, 0, 0.005 * g)), d2, 0.034 * g, 0.036 * g, {Lo: 0.7, F: 0.3}, PIEL))
    anillos = [anillo_eje(c, d, rx, ry, 10, ref=afuera) for c, d, rx, ry, _, _ in filas]
    m.loft(anillos, [f[4] for f in filas], [f[5] for f in filas[:-1]],
           tapa_ini=cadera + V((-lado * 0.01 * g, 0.004, 0.075 * g)),
           tapa_fin=tobillo - V((0, 0, 0.03 * g)))
    zapatilla(m, M, lado, nombre, tobillo)


def zapatilla(m, M, lado, nombre, tobillo):
    """Zapatilla con suela (superficie `detalles`). Lofteo hacia adelante, del talón a la
    punta; la suela es la banda de abajo de cada anillo."""
    k = M["k"]
    F, T = f"{nombre}Foot", f"{nombre}Toes"
    ys = tobillo.y
    x0 = tobillo.x + lado * 0.004 * k
    suela = 0.022 * k
    # (y relativo al tobillo: + atrás; media ancho; alto de arriba)
    perfil = [(0.070, 0.030, 0.075), (0.050, 0.040, 0.105), (0.015, 0.045, 0.118), (-0.035, 0.048, 0.098),
              (-0.090, 0.052, 0.070), (-0.145, 0.050, 0.055), (-0.185, 0.043, 0.048), (-0.205, 0.030, 0.038)]
    anillos, pesos = [], []
    for y, an, alto in perfil:
        an *= k
        alto *= k
        yy = ys + y * k
        z1 = suela
        pts = [V((-an * 0.92, yy, 0.0)), V((an * 0.92, yy, 0.0)), V((an, yy, z1)),
               V((an * 0.97, yy, z1 + (alto - z1) * 0.5)), V((an * 0.70, yy, alto * 0.95)), V((0, yy, alto)),
               V((-an * 0.70, yy, alto * 0.95)), V((-an * 0.97, yy, z1 + (alto - z1) * 0.5)),
               V((-an, yy, z1))]
        anillos.append([p + V((x0, 0, 0)) for p in pts])
        tb = (-(y * k) - M["metatarso"] + 0.03 * k) / (0.06 * k)
        pesos.append(mezcla(F, T, tb))
    mat = lambda b, kk: DETALLE if kk in (8, 0, 1) else ZAPAS  # noqa: E731
    m.loft(anillos, pesos, mat, tapa_ini="plana", tapa_fin="plana", mat_tapas=ZAPAS)


def construir_cuerpo(nombre, M, P, materiales):
    m = Malla()
    torso(m, M, P)
    cuello(m, M)
    cabeza(m, M)
    for lado, ln in ((1, "Left"), (-1, "Right")):
        brazo(m, M, P, lado, ln)
        pierna(m, M, P, lado, ln)
    return m.objeto(nombre, materiales)


# ── Esqueleto ──────────────────────────────────────────────────────────

def juntas(M):
    """{hueso: (cabeza, cola, eje Z del hueso)} en la pose de descanso derecha."""
    s = M["s"]
    J = {}
    J["Root"] = (V((0, 0, 0)), V((0, 0, 0.1 * M["k"])), ADELANTE)
    J["Hips"] = (V((0, 0, M["cadera"])), V((0, 0, M["spine"])), ADELANTE)
    J["Spine"] = (V((0, 0, M["spine"])), V((0, 0, M["chest"])), ADELANTE)
    J["Chest"] = (V((0, 0, M["chest"])), V((0, 0, M["upperchest"])), ADELANTE)
    J["UpperChest"] = (V((0, 0, M["upperchest"])), V((0, 0.006 * M["k"], M["cuello"])), ADELANTE)
    nuca = V((0, 0, M["menton"])) + NUCA_REL * s
    J["Neck"] = (V((0, 0.006 * M["k"], M["cuello"])), nuca, ADELANTE)
    J["Head"] = (nuca, V((nuca.x, nuca.y, M["H"])), ADELANTE)
    for ln, lado in LADOS:
        hombro, codo, muneca = puntos_brazo(M, lado)
        J[f"{ln}Shoulder"] = (V((lado * 0.03 * M["w"], 0.0, M["hombro"] + 0.03 * M["k"])), hombro, ADELANTE)
        J[f"{ln}UpperArm"] = (hombro, codo, ADELANTE)
        J[f"{ln}LowerArm"] = (codo, muneca, ADELANTE)
        d = (muneca - codo).normalized()
        J[f"{ln}Hand"] = (muneca, muneca + d * M["mano"], ADELANTE)
        cadera, rodilla, tobillo = puntos_pierna(M, lado)
        J[f"{ln}UpperLeg"] = (cadera, rodilla, ADELANTE)
        J[f"{ln}LowerLeg"] = (rodilla, tobillo, ADELANTE)
        meta = V((tobillo.x + lado * 0.004 * M["k"], tobillo.y - M["metatarso"], 0.024 * M["k"]))
        J[f"{ln}Foot"] = (tobillo, meta, ARRIBA)
        J[f"{ln}Toes"] = (meta, meta + V((0, -M["punta"], -0.004 * M["k"])), ARRIBA)
    return J


def crear_esqueleto(nombre, J):
    datos = bpy.data.armatures.new(nombre)
    datos.display_type = "STICK"
    arm = bpy.data.objects.new(nombre, datos)
    bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    for n in NOMBRES:
        cab, cola, z = J[n]
        eb = datos.edit_bones.new(n)
        eb.head, eb.tail = cab, cola
        eb.align_roll(z)
        if PADRE[n]:
            eb.parent = datos.edit_bones[PADRE[n]]
        eb.use_connect = False
        eb.use_deform = n != "Root"
    bpy.ops.object.mode_set(mode="OBJECT")
    return arm


class Esqueleto:
    """Datos de descanso para calcular poses sin Blender (FK propia, igual a la de Blender)."""

    def __init__(self, arm):
        self.rest = {b.name: b.matrix_local.copy() for b in arm.data.bones}
        self.largo = {b.name: b.length for b in arm.data.bones}

    def rot(self, n):
        return self.rest[n].to_3x3().to_quaternion()

    def dir(self, n):
        return (self.rest[n].to_3x3() @ V((0, 1, 0))).normalized()


class Pose:
    """Rotaciones locales (cuaterniones) y traslación de Hips. Los giros se piden con ejes
    del espacio de la armadura en la pose de descanso (rel), o como orientación final (fijar)."""

    def __init__(self, esq):
        self.e = esq
        self.q = {n: Quaternion() for n in NOMBRES}
        self.loc = {n: V() for n in NOMBRES}

    def rel(self, n, eje, grados):
        if abs(grados) < 1e-9:
            return
        B = self.e.rot(n)
        R = Quaternion(V(eje).normalized(), math.radians(grados))
        self.q[n] = self.q[n] @ (B.inverted() @ R @ B)

    # Giros con nombre (positivos: hacia adelante, a la izquierda de la persona, hacia arriba).
    def adelante(self, n, g):
        self.rel(n, self.e.dir(n).cross(ADELANTE), g)

    def girar(self, n, g):
        self.rel(n, ARRIBA, g)

    def hacia_izq(self, n, g):
        self.rel(n, self.e.dir(n).cross(IZQ), g)

    def arriba(self, n, g):
        self.rel(n, self.e.dir(n).cross(ARRIBA), g)

    def mover(self, n, delta_mundo):
        B = self.e.rot(n)
        self.loc[n] = B.inverted() @ V(delta_mundo)

    def matrices(self):
        P = {}
        for n in NOMBRES:
            base = Matrix.Translation(self.loc[n]) @ self.q[n].to_matrix().to_4x4()
            p = PADRE[n]
            if p is None:
                P[n] = self.e.rest[n] @ base
            else:
                P[n] = P[p] @ (self.e.rest[p].inverted() @ self.e.rest[n]) @ base
        return P

    def delta(self, n, P):
        return P[n].to_quaternion() @ self.e.rot(n).inverted()

    def fijar(self, n, delta, P):
        """Pone el hueso n con orientación final delta (respecto del descanso)."""
        p = PADRE[n]
        dp = self.delta(p, P) if p else Quaternion()
        B = self.e.rot(n)
        self.q[n] = B.inverted() @ dp.inverted() @ delta @ B

    def cabeza(self, n, P):
        return P[n].translation.copy()

    def punta(self, n, P):
        return (P[n] @ V((0, self.e.largo[n], 0)))


def _dos_huesos(a, objetivo, l1, l2, polo):
    """IK de dos huesos: devuelve la articulación del medio (rodilla, codo)."""
    d = objetivo - a
    D = max(1e-4, min(d.length, (l1 + l2) * 0.9995))
    u = d.normalized()
    x = (l1 * l1 - l2 * l2 + D * D) / (2 * D)
    h = math.sqrt(max(0.0, l1 * l1 - x * x))
    n = polo - u * polo.dot(u)
    if n.length < 1e-6:
        n = V((0, -1, 0))
    n.normalize()
    return a + u * x + n * h, d.length / (l1 + l2)


def alinear(pose, n, hacia, P):
    """Gira el hueso n (desde su orientación heredada del padre) para que apunte a `hacia`."""
    p = PADRE[n]
    dp = pose.delta(p, P) if p else Quaternion()
    actual = dp @ pose.e.dir(n)
    pose.fijar(n, actual.rotation_difference((hacia).normalized()) @ dp, P)


def pierna_ik(pose, ln, tobillo, pitch_pie, pitch_dedos=0.0, polo=None):
    """Ubica la pierna para que el tobillo quede en `tobillo` y el pie con ese pitch (grados,
    + = punta arriba) respecto del piso. Devuelve cuánto se estira (1 = pierna derecha)."""
    P = pose.matrices()
    U, Lo, F, T = f"{ln}UpperLeg", f"{ln}LowerLeg", f"{ln}Foot", f"{ln}Toes"
    cad = pose.cabeza(U, P)
    l1, l2 = pose.e.largo[U], pose.e.largo[Lo]
    polo = polo if polo is not None else ADELANTE + V((0.08 if ln == "Left" else -0.08, 0, 0))
    rod, estira = _dos_huesos(cad, tobillo, l1, l2, polo)
    alinear(pose, U, rod - cad, P)
    P = pose.matrices()
    alinear(pose, Lo, tobillo - rod, P)
    P = pose.matrices()
    pose.fijar(F, Quaternion(-IZQ, math.radians(pitch_pie)), P)
    P = pose.matrices()
    pose.fijar(T, Quaternion(-IZQ, math.radians(pitch_dedos)), P)
    return estira


def brazo_ik(pose, ln, muneca, polo=None, giro_mano=0.0, flex_mano=0.0):
    P = pose.matrices()
    U, Lo, Hn = f"{ln}UpperArm", f"{ln}LowerArm", f"{ln}Hand"
    hom = pose.cabeza(U, P)
    l1, l2 = pose.e.largo[U], pose.e.largo[Lo]
    lado = 1 if ln == "Left" else -1
    polo = polo if polo is not None else V((lado * 0.6, 1.0, -0.2))
    codo, estira = _dos_huesos(hom, muneca, l1, l2, polo)
    alinear(pose, U, codo - hom, P)
    P = pose.matrices()
    alinear(pose, Lo, muneca - codo, P)
    pose.q[Hn] = Quaternion()
    pose.adelante(Hn, flex_mano)
    pose.rel(Hn, pose.e.dir(Hn), giro_mano)
    return estira


def aplicar_postura(arm, cuerpo, esq, P_param):
    """Persona mayor: encorva la pose de descanso (columna y cuello hacia adelante, cabeza
    levantada para mirar al frente, rodillas apenas flojas no: solo arriba). Se deforma la malla
    con los mismos pesos y se mueve el esqueleto: las animaciones mantienen la postura."""
    e = P_param.get("postura", 0.0)
    if e <= 0:
        return esq
    pose = Pose(esq)
    pose.adelante("Spine", 4 * e)
    pose.adelante("Chest", 5 * e)
    pose.adelante("UpperChest", 6 * e)
    pose.adelante("Neck", 7 * e)
    pose.adelante("Head", -20 * e)      # la cara queda mirando al frente
    for ln, lado in LADOS:
        pose.adelante(f"{ln}Shoulder", 4 * e)
        pose.adelante(f"{ln}UpperArm", -10 * e)   # los brazos siguen colgando derechos
        pose.adelante(f"{ln}LowerArm", 6 * e)
    P = pose.matrices()
    # Malla: skinning lineal con los pesos.
    malla = cuerpo.data
    idx = {g.index: g.name for g in cuerpo.vertex_groups}
    skin = {n: P[n] @ esq.rest[n].inverted() for n in NOMBRES}
    for v in malla.vertices:
        acc = V()
        tot = 0.0
        for g in v.groups:
            acc += (skin[idx[g.group]] @ v.co) * g.weight
            tot += g.weight
        v.co = acc / tot
    malla.update()
    # Esqueleto: la pose pasa a ser el descanso.
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    for n in NOMBRES:
        arm.data.edit_bones[n].matrix = P[n]
    bpy.ops.object.mode_set(mode="OBJECT")
    return Esqueleto(arm)


# ── Pelo ───────────────────────────────────────────────────────────────

ESTILOS_PELO = ["corto", "rapado", "raya", "largo", "colita", "rodete", "rulos", "pelado"]


def _bvh_cabeza(s=1.0):
    """Cabeza a escala s con el mentón en el origen (para apoyar el pelo encima)."""
    bm = bmesh.new()
    vs = [[bm.verts.new(p) for p in a] for a in anillos_cabeza(s, V())]
    n = len(vs[0])
    for a, b in zip(vs, vs[1:]):
        for k in range(n):
            bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]))
    for punta, fila in ((V((0, -0.070 * s, -0.004 * s)), vs[0]), (V((0, 0.006 * s, 0.235 * s)), vs[-1])):
        c = bm.verts.new(punta)
        for k in range(n):
            bm.faces.new((fila[k], fila[(k + 1) % n], c))
    bvh = BVHTree.FromBMesh(bm)
    bm.free()
    return bvh


def _superficie(bvh, centro, d):
    """Punto de la cabeza en la dirección d desde el centro (de afuera hacia adentro)."""
    lejos = centro + d * 0.5
    hit = bvh.ray_cast(lejos, -d, 0.6)
    return hit[0] if hit[0] is not None else centro + d * 0.1


def pelo(estilo, material, nombre=None):
    """Peinado `pelo_<estilo>` (≈300 tris), con el origen en la base del cráneo (la cabeza del
    hueso Head de una cabeza de escala 1). Volumen cerrado: el casco del peinado, que en el
    borde se mete adentro de la cabeza."""
    import random
    rnd = random.Random(ESTILOS_PELO.index(estilo) * 31 + 7)
    bvh = _bvh_cabeza()
    centro = V((0, 0.004, 0.118))
    m = Malla()
    bm = m.bm
    NA = 14                         # direcciones alrededor
    # grosor(φ, a), límite(a): hasta qué ángulo polar baja el pelo (desde arriba), por azimut.
    # a = 0 adelante (−Y), π/2 izquierda (+X).

    def front(a):  # 1 adelante, 0 atrás
        return (math.cos(a) + 1) / 2

    # arriba/borde: grosor del pelo arriba y en el borde; frente/lados/atras: hasta qué ángulo
    # polar baja (rad, desde arriba); patilla: cuánto más baja adelante de las orejas;
    # pelos: irregularidad del grosor (0–1).
    estilos = {
        "corto":  dict(arriba=0.012, borde=0.003, frente=0.98, lados=1.50, atras=1.84, patilla=0.25, pelos=0.30),
        "rapado": dict(arriba=0.009, borde=0.006, frente=1.06, lados=1.52, atras=1.86, patilla=0.20, pelos=0.15),
        "raya":   dict(arriba=0.022, borde=0.008, frente=0.86, lados=1.50, atras=1.84, patilla=0.15, pelos=0.25,
                       flequillo=0.016),
        "largo":  dict(arriba=0.015, borde=0.013, frente=0.92, lados=1.90, atras=2.0, patilla=0.0, pelos=0.15,
                       cortina=0.17),
        "colita": dict(arriba=0.010, borde=0.006, frente=0.98, lados=1.58, atras=1.88, patilla=0.10, pelos=0.15,
                       cola=True),
        "rodete": dict(arriba=0.010, borde=0.006, frente=0.98, lados=1.58, atras=1.86, patilla=0.10, pelos=0.15,
                       rodete=True),
        "rulos":  dict(arriba=0.036, borde=0.020, frente=0.92, lados=1.60, atras=1.86, patilla=0.0, pelos=0.55),
        "pelado": dict(arriba=0.006, borde=0.008, frente=1.45, lados=1.66, atras=2.12, patilla=0.0, pelos=0.2,
                       coronilla=1.10),
    }
    E = estilos[estilo]

    def limite(a):
        f = front(a)
        if f > 0.5:
            t = (f - 0.5) * 2
            lim = E["lados"] * (1 - t) + E["frente"] * t
        else:
            t = (0.5 - f) * 2
            lim = E["lados"] * (1 - t) + E["atras"] * t
        # patilla: delante de la oreja (azimut ≈ ±65°)
        cerca = max(0.0, 1 - abs(abs(math.degrees(math.atan2(math.sin(a), math.cos(a)))) - 68) / 16)
        return lim + E["patilla"] * cerca

    filas = 6
    anillos = []
    for j in range(1, filas + 1):
        fila = []
        for i in range(NA):
            a = 2 * math.pi * i / NA
            phi_max = limite(a)
            phi = phi_max * j / filas
            esconder = 0.0
            if "coronilla" in E:     # pelado: corona de pelo solo a los costados y atrás
                esconder = suave((front(a) - 0.62) / 0.16)   # adelante: queda adentro de la cabeza
                tope = E["coronilla"] + 0.25 * esconder - 0.30 * (1 - front(a)) ** 1.5   # herradura
                phi = tope + (phi_max - tope) * (j - 1) / (filas - 1)
            d = V((math.sin(phi) * math.sin(a), -math.sin(phi) * math.cos(a), math.cos(phi)))
            p = _superficie(bvh, centro, d)
            tt = (j - 1) / (filas - 1)
            gro = E["arriba"] * (1 - tt) + E["borde"] * tt
            if E.get("flequillo") and front(a) > 0.72 and j >= filas - 2:
                gro += E["flequillo"] * (1.0 if math.sin(a) > -0.3 else 0.35)
            gro *= 1 + E["pelos"] * (rnd.random() - 0.5)
            gro = gro * (1 - esconder) - 0.006 * esconder
            fila.append(p + (p - centro).normalized() * gro)
        anillos.append(fila)
    # Borde: se mete hacia adentro de la cabeza (no se ve) y se cierra.
    borde = [centro + (p - centro) * 0.80 for p in anillos[-1]]
    if "coronilla" in E:
        arriba = [centro + (p - centro) * 0.80 for p in anillos[0]]
        anillos = [arriba] + anillos + [borde]
        tapa_ini = centro + V((0, 0, 0.06))
    else:
        anillos = anillos + [borde]
        tapa_ini = centro + V((0, 0.004, 0.126 + E["arriba"]))
    if E.get("cortina"):
        _cortina(m, bvh, centro, E, material)
    pesos = [{"Head": 1.0}] * len(anillos)
    m.loft(anillos, pesos, [0] * (len(anillos) - 1), tapa_ini=tapa_ini, tapa_fin=centro + V((0, 0.01, -0.02)))
    if E.get("cola"):
        base = V((0, 0.098, 0.150))
        dd = V((0, 0.55, -1)).normalized()
        pts = [(0.0, 0.020), (0.03, 0.026), (0.09, 0.024), (0.15, 0.017), (0.19, 0.008)]
        a = [anillo_eje(base + dd * t + V((0, 0.03 * t, 0)), dd, r, r, 6, ref=IZQ) for t, r in pts]
        m.loft(a, [{"Head": 1.0}] * len(a), [0] * (len(a) - 1), tapa_ini=base - dd * 0.02,
               tapa_fin=base + dd * 0.21 + V((0, 0.006, 0)))
    if E.get("rodete"):
        c = V((0, 0.085, 0.205))
        d = V((0, 0.6, 0.8)).normalized()
        perf = [(-0.024, 0.016), (-0.014, 0.034), (0.006, 0.038), (0.022, 0.026), (0.030, 0.008)]
        a = [anillo_eje(c + d * t, d, r, r, 8, ref=IZQ) for t, r in perf]
        m.loft(a, [{"Head": 1.0}] * len(a), [0] * (len(a) - 1), tapa_ini=c - d * 0.03, tapa_fin=c + d * 0.034)
    obj = m.objeto(nombre or f"pelo_{estilo}", [material])
    for f in obj.data.polygons:      # facetado: se lee como mechones, no como gorro
        f.use_smooth = estilo == "rapado"
    for g in list(obj.vertex_groups):
        obj.vertex_groups.remove(g)
    # Origen en la base del cráneo (cabeza del hueso Head de escala 1).
    obj.data.transform(Matrix.Translation(-NUCA_REL))
    return obj


def _cortina(m, bvh, centro, E, material):
    """Pelo largo: una cortina de atrás que baja hasta los hombros (lofteo de arcos)."""
    filas = []
    largo = E["cortina"]
    n = 7
    for j, (dz, abre, gro) in enumerate(((0.03, 0.93, 0.0), (-0.07, 1.0, 0.016), (-largo, 0.90, 0.010))):
        arco_ext, arco_int = [], []
        for i in range(n):
            a = math.pi * (0.48 + 1.04 * i / (n - 1))      # de un costado al otro, por atrás
            d = V((math.sin(a), -math.cos(a), 0.0))
            z = 0.115 + dz
            r_x, r_y = 0.083 * abre, 0.104 * abre
            p = V((d.x * r_x, 0.004 + d.y * r_y, z))
            arco_ext.append(p + V((d.x, d.y, 0)) * gro)
            arco_int.append(p - V((d.x, d.y, 0)) * 0.006)
        filas.append(arco_ext + list(reversed(arco_int)))
    pesos = [{"Head": 1.0}] * len(filas)
    m.loft(filas, pesos, [0] * (len(filas) - 1), tapa_ini="plana", tapa_fin="plana")


# ── Animaciones ────────────────────────────────────────────────────────

def _e(t):  # ida y vuelta suave 0 → 1 → 0 en [0, 1]
    return 0.5 - 0.5 * math.cos(2 * math.pi * t)


def _ventana(t, a, b, rampa):
    """0 fuera de [a, b], 1 adentro, con rampas suaves."""
    if t < a - rampa or t > b + rampa:
        return 0.0
    if t < a:
        return suave((t - (a - rampa)) / rampa)
    if t > b:
        return 1 - suave((t - b) / rampa)
    return 1.0


class Ciclo:
    """Marcha (caminar o trotar) en el lugar: el pie apoyado va hacia atrás a la velocidad
    exacta, rodando del talón a la punta; el pie en el aire vuelve adelante."""

    def __init__(self, M, vel, periodo, apoyo, talon_frac, despegue, golpe, alto_paso,
                 baja_cadera, rebote, atras_paso=0.0):
        self.M = M
        self.v, self.T, self.ap = vel, periodo, apoyo
        self.uA, self.uB = talon_frac, despegue
        self.p_hs, self.p_to = golpe, 45.0 if atras_paso else 38.0
        self.alto = alto_paso
        self.baja, self.rebote = baja_cadera, rebote
        self.atras_paso = atras_paso
        self.s = vel * periodo * apoyo
        self.hb, self.bf, self.ha = M["talon"], M["metatarso"], M["tobillo"]
        self.g0 = -self.hb + 0.36 * self.s

    @staticmethod
    def _rot(v, p):
        c, s = math.cos(p), math.sin(p)
        return (v[0] * c - v[1] * s, v[0] * s + v[1] * c)

    def apoyo_en(self, u):
        """(adelante, alto) del tobillo y pitch (rad) del pie, con u ∈ [0, 1] del apoyo."""
        G = self.g0 - u * self.s
        talon, meta = (-self.hb, -self.ha), (self.bf, -self.ha)
        if u < self.uA:
            p = math.radians(self.p_hs) * (1 - suave(u / self.uA))
            r = self._rot(talon, p)
            return (G - r[0], -r[1]), p, p
        if u < self.uB:
            return (G + self.hb, self.ha), 0.0, 0.0
        p = -math.radians(self.p_to) * suave((u - self.uB) / (1 - self.uB))
        r = self._rot(meta, p)
        bola = G + self.hb + self.bf
        return (bola - r[0], -r[1]), p, 0.0

    def pie(self, t):
        """t ∈ [0, 1) del ciclo, 0 = el talón toca el piso. → (adelante, alto), pitch, dedos."""
        t %= 1.0
        if t < self.ap:
            return self.apoyo_en(t / self.ap)
        u = (t - self.ap) / (1 - self.ap)
        (f1, z1), p1, _ = self.apoyo_en(1.0)
        (f0, z0), p0, _ = self.apoyo_en(0.0)
        e = suave(u)
        f = f1 + (f0 - f1) * e
        z = z1 + (z0 - z1) * u + self.alto * math.sin(math.pi * u) ** 1.3
        if self.atras_paso:   # trote: el talón sube atrás antes de ir adelante
            f -= self.atras_paso * math.sin(math.pi * min(1.0, u * 1.6)) * (1 - u)
            z += self.atras_paso * 0.8 * math.sin(math.pi * min(1.0, u * 1.4)) * (1 - u)
        p = p1 + (p0 - p1) * suave(min(1.0, u * 1.3))
        dedos = p + math.radians(10) * math.sin(math.pi * u) * (1 if self.atras_paso else 0.5)
        return (f, z), p, dedos

    def cadera(self, t):
        """Altura de la cadera: más baja al apoyar, más alta al pasar sobre el pie."""
        return -self.baja + self.rebote * math.cos(4 * math.pi * (t - 0.36 * self.ap))


def _pose_marcha(esq, M, ciclo, t, P, trote=False, comer_t=None):
    pose = Pose(esq)
    fase = t
    # Cadera: sube y baja, gira un poco con el paso; el torso compensa.
    giro = (6 if trote else 5) * math.cos(2 * math.pi * fase)
    pose.mover("Hips", (0, 0, ciclo.cadera(fase)))
    pose.girar("Hips", -giro)
    pose.hacia_izq("Hips", 2.0 * math.sin(2 * math.pi * fase))
    incl = (9 if trote else 2.5) + P.get("postura", 0) * 2
    pose.adelante("Spine", incl * 0.5)
    pose.girar("Spine", giro * 0.6)
    pose.girar("Chest", giro * 0.5)
    pose.adelante("Chest", incl * 0.3)
    pose.girar("UpperChest", giro * 0.4)
    pose.girar("Neck", -giro * 0.3)
    pose.adelante("Neck", -incl * 0.5)
    pose.adelante("Head", -incl * 0.3 + 1.0 * math.cos(4 * math.pi * fase))
    # Piernas: izquierda apoya en t = 0, derecha en t = 0,5.
    estira = 0.0
    for ln, lado, off in (("Left", 1, 0.0), ("Right", -1, 0.5)):
        (f, z), p, dedos = ciclo.pie(fase - off)
        x = lado * M["x_cadera"] * 0.92
        estira = max(estira, pierna_ik(pose, ln, V((x, -f, z)), math.degrees(p), math.degrees(dedos)))
    # Brazos: al revés que las piernas.
    A = 32 if trote else 17
    for ln, lado, off in (("Left", 1, 0.5), ("Right", -1, 0.0)):
        if comer_t is not None and ln == "Right":
            continue
        a = A * math.cos(2 * math.pi * (fase - off))
        pose.adelante(f"{ln}UpperArm", a - (6 if trote else 0))
        pose.hacia_izq(f"{ln}UpperArm", lado * (6 if trote else 2))
        codo = (80 if trote else 14) + max(0.0, a) * (0.6 if trote else 0.7)
        pose.adelante(f"{ln}LowerArm", codo)
        pose.adelante(f"{ln}Hand", 4)
    if comer_t is not None:
        _brazo_comer(pose, M, comer_t)
    return pose, estira


def _respirar(pose, t, periodo=4.0, fuerza=1.0):
    r = math.sin(2 * math.pi * t / periodo)
    pose.adelante("Chest", -1.2 * r * fuerza)
    pose.adelante("UpperChest", -0.8 * r * fuerza)
    pose.adelante("Neck", 1.4 * r * fuerza)
    for ln, lado in LADOS:
        pose.arriba(f"{ln}Shoulder", 1.2 * r * fuerza)


def _parado(pose, M, cad_x=0.0, baja=0.0, apertura=1.0):
    """Pies quietos en el piso (pose de descanso) con la cadera corrida cad_x."""
    pose.mover("Hips", (cad_x, 0, -baja))
    pose.hacia_izq("Hips", -cad_x * 60)          # la cadera se inclina hacia la pierna libre
    pose.hacia_izq("Spine", cad_x * 50)
    pose.hacia_izq("Chest", cad_x * 30)
    for ln, lado in LADOS:
        x = lado * M["x_cadera"] * 0.92 * apertura
        pierna_ik(pose, ln, V((x, 0.0, M["tobillo"])), 0.0)


def _brazos_caidos(pose, t=0.0, amp=1.0):
    for ln, lado in LADOS:
        pose.adelante(f"{ln}UpperArm", amp * 1.5 * math.sin(2 * math.pi * t / 4 + lado))
        pose.adelante(f"{ln}LowerArm", 6 + amp * 2 * math.sin(2 * math.pi * t / 4 + lado))


def _brazo_comer(pose, M, u):
    """Brazo derecho con el pancho: sostenido adelante y, en la mitad del ciclo, a la boca."""
    P = pose.matrices()
    boca = pose.punta("Neck", P) + V((0, -0.11 * M["s"], 0.015 * M["s"]))
    mano_abajo = pose.cabeza("RightUpperArm", P) + V((0.05 * M["w"], -0.24 * M["k"], -0.27 * M["k"]))
    sube = _ventana(u, 0.32, 0.55, 0.14)
    muneca = mano_abajo.lerp(boca + V((-0.05 * M["s"], -0.085 * M["s"], -0.115 * M["s"])), sube)
    brazo_ik(pose, "Right", muneca, polo=V((-1.0, 0.6, -0.6)), giro_mano=-60 * sube - 20,
             flex_mano=10 - 55 * sube)
    pose.adelante("Head", 7 * sube)
    pose.adelante("Neck", 4 * sube)


def animaciones(M, P):
    """Lista de (nombre, segundos, función t → Pose). Todas en loop."""
    vel = P.get("vel_caminar", 1.2)
    per = P.get("periodo_caminar", 1.0)
    caminar = Ciclo(M, vel, per, apoyo=0.62, talon_frac=0.12, despegue=0.56, golpe=14,
                    alto_paso=0.07 * M["k"], baja_cadera=0.024 * M["k"], rebote=0.012 * M["k"])
    vel_t = P.get("vel_trotar", 2.8)
    per_t = P.get("periodo_trotar", 0.7)
    trotar = Ciclo(M, vel_t, per_t, apoyo=0.36, talon_frac=0.01, despegue=0.35, golpe=4,
                   alto_paso=0.10 * M["k"], baja_cadera=0.055 * M["k"], rebote=0.025 * M["k"],
                   atras_paso=0.16 * M["k"])
    lista = []

    def quieto(esq, t):
        pose = Pose(esq)
        _parado(pose, M, cad_x=0.004 * math.sin(2 * math.pi * t / 4), baja=0.004)
        _respirar(pose, t)
        _brazos_caidos(pose, t)
        pose.girar("Head", 2 * math.sin(2 * math.pi * t / 4))
        return pose
    lista.append(("quieto", 4.0, quieto))

    def caminar_f(esq, t):
        return _pose_marcha(esq, M, caminar, t / per, P)[0]
    lista.append(("caminar", per, caminar_f))

    def trotar_f(esq, t):
        return _pose_marcha(esq, M, trotar, t / per_t, P, trote=True)[0]
    lista.append(("trotar", per_t, trotar_f))

    def esperar(esq, t):
        # 8 s: cambia el peso de pierna, mira a los costados y una vez el reloj.
        pose = Pose(esq)
        peso = 0.022 * M["k"] * math.sin(2 * math.pi * t / 8)
        _parado(pose, M, cad_x=peso, baja=0.008 * M["k"])
        _respirar(pose, t)
        _brazos_caidos(pose, t, 0.6)
        reloj = _ventana(t, 4.6, 5.8, 0.45)
        mira_izq = _ventana(t, 1.4, 2.6, 0.5)
        mira_der = _ventana(t, 6.6, 7.2, 0.4)
        pose.girar("Neck", 14 * mira_izq - 16 * mira_der + 6 * reloj)
        pose.girar("Head", 14 * mira_izq - 16 * mira_der + 6 * reloj)
        pose.adelante("Head", 16 * reloj)
        pose.adelante("Neck", 10 * reloj)
        if reloj > 0:
            P_ = pose.matrices()
            hom = pose.cabeza("LeftUpperArm", P_)
            caida = pose.punta("LeftLowerArm", P_)
            frente = hom + V((-0.13 * M["w"], -0.27 * M["k"], -0.17 * M["k"]))
            brazo_ik(pose, "Left", caida.lerp(frente, reloj), polo=V((1, 0.6, -0.8)),
                     giro_mano=-80 * reloj, flex_mano=0)
        return pose
    lista.append(("esperar", 8.0, esperar))

    def charlar(esq, t):
        # 6 s: gestos con las manos, asiente, se encoge de hombros.
        pose = Pose(esq)
        _parado(pose, M, cad_x=-0.016 * M["k"] + 0.004 * math.sin(2 * math.pi * t / 6), baja=0.006 * M["k"])
        _respirar(pose, t, 3.0)
        g1 = _ventana(t, 0.6, 2.4, 0.4)
        g2 = _ventana(t, 3.0, 4.3, 0.35)
        hombros = _ventana(t, 4.9, 5.2, 0.25)
        pose.adelante("Head", 4 * math.sin(2 * math.pi * t * 0.75) * (1 - hombros))
        pose.hacia_izq("Head", 3 * math.sin(2 * math.pi * t / 6))
        for ln, lado, g in (("Right", -1, g1), ("Left", 1, g2)):
            osc = math.sin(2 * math.pi * t * 1.4 + lado)
            pose.adelante(f"{ln}UpperArm", 1.5 + g * (8 + 3 * osc) + hombros * 6)
            pose.hacia_izq(f"{ln}UpperArm", lado * (g * 8 + hombros * 14))
            pose.adelante(f"{ln}LowerArm", 8 + g * (72 + 12 * osc) + hombros * 62)
            pose.hacia_izq(f"{ln}LowerArm", -lado * g * 22)
            pose.rel(f"{ln}LowerArm", pose.e.dir(f"{ln}LowerArm"), lado * (g * 60 + hombros * 75))
            pose.adelante(f"{ln}Hand", -g * 15)
            pose.arriba(f"{ln}Shoulder", hombros * 10)
        return pose
    lista.append(("charlar", 6.0, charlar))

    def comer(esq, t):
        # Solo brazo derecho, cuello y cabeza: se mezcla arriba de quieto, esperar o caminar.
        pose = Pose(esq)
        _brazo_comer(pose, M, t / 3.0)
        return pose
    lista.append(("comer", 3.0, comer))

    def caminar_comiendo(esq, t):
        return _pose_marcha(esq, M, caminar, (t / per) % 1.0, P, comer_t=t / (3 * per))[0]
    lista.append(("caminar_comiendo", 3 * per, caminar_comiendo))

    def sentado(esq, t):
        pose = Pose(esq)
        cad = M["cadera"]
        l1 = M["cadera"] - M["rodilla"]
        borde = -0.16     # borde del asiento, respecto del punto del banco (ver notas)
        cy = min(0.15, borde - 0.05 + l1)
        cz = 0.45 + 0.085 * M["g"]
        pose.mover("Hips", (0, cy, cz - cad))
        pose.adelante("Spine", -6 + 1.0 * math.sin(2 * math.pi * t / 6))
        pose.adelante("Chest", 2)
        _respirar(pose, t)
        pose.girar("Head", 10 * _ventana(t, 2.0, 3.4, 0.6))
        pose.girar("Neck", 6 * _ventana(t, 2.0, 3.4, 0.6))
        P_ = pose.matrices()
        for ln, lado in LADOS:
            U, Lo = f"{ln}UpperLeg", f"{ln}LowerLeg"
            c = pose.cabeza(U, P_)
            rod = c + V((lado * 0.025 * M["k"], -l1 * math.cos(math.radians(4)), l1 * math.sin(math.radians(4))))
            l2 = M["rodilla"] - M["tobillo"]
            alto = rod.z - M["tobillo"]
            if l2 > alto:
                adel = math.sqrt(l2 * l2 - alto * alto)
                tob = V((rod.x, rod.y - adel, M["tobillo"]))
                pitch = 0.0
            else:
                ang = math.radians(12)
                tob = rod + V((0, -math.sin(ang) * l2, -math.cos(ang) * l2))
                pitch = -20.0
            alinear(pose, U, rod - c, P_)
            P_ = pose.matrices()
            alinear(pose, Lo, tob - rod, P_)
            P_ = pose.matrices()
            pose.fijar(f"{ln}Foot", Quaternion(-IZQ, math.radians(pitch)), P_)
            P_ = pose.matrices()
        P_ = pose.matrices()
        for ln, lado in LADOS:
            c = pose.cabeza(f"{ln}UpperLeg", P_)
            muslo = c + V((lado * 0.03 * M["w"], -l1 * 0.62, 0.10 * M["g"]))
            brazo_ik(pose, ln, muslo, polo=V((lado * 0.8, 1, 0)), giro_mano=lado * 70, flex_mano=25)
        return pose
    lista.append(("sentado", 6.0, sentado))
    return lista, caminar, trotar


def _keyframes(arm, esq, nombre, segundos, funcion, solo=None):
    """Una acción de Blender con un key por cuadro (rotaciones en cuaterniones y traslación
    de Hips). solo = huesos a guardar (comer: solo el brazo y la cabeza)."""
    ad = arm.animation_data or arm.animation_data_create()
    act = bpy.data.actions.new(nombre)
    act.use_fake_user = True
    ad.action = act
    cuadros = max(2, round(segundos * FPS))
    assert abs(cuadros - segundos * FPS) < 1e-6, f"{nombre}: {segundos} s no da cuadros enteros (loop)"
    huesos = solo or NOMBRES
    previo = {}
    for f in range(cuadros + 1):
        pose = funcion(esq, (f % cuadros) / FPS)
        for n in huesos:
            pb = arm.pose.bones[n]
            pb.rotation_mode = "QUATERNION"
            q = pose.q[n].normalized()
            if n in previo and previo[n].dot(q) < 0:
                q = -q
            previo[n] = q
            pb.rotation_quaternion = q
            pb.keyframe_insert("rotation_quaternion", frame=f)
            if n == "Hips" and solo is None:
                pb.location = pose.loc[n]
                pb.keyframe_insert("location", frame=f)
    track = ad.nla_tracks.new()
    track.name = nombre
    track.strips.new(nombre, 0, act)
    track.mute = True
    ad.action = None
    return act, cuadros


def poner_pose(arm, pose):
    """Pone una Pose en la armadura (para las fotos y el chequeo)."""
    if arm.animation_data:
        arm.animation_data.action = None
    for n in NOMBRES:
        pb = arm.pose.bones[n]
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = pose.q[n]
        pb.location = pose.loc[n]
    bpy.context.view_layer.update()


# ── Armado del modelo ──────────────────────────────────────────────────

def construir(id_, P):
    M = medidas(P)
    J = juntas(M)
    arm = crear_esqueleto(id_, J)
    mats = comun.cargar_materiales(*[P["materiales"][s] for s in SUPERFICIES])
    cuerpo = construir_cuerpo(f"{id_}_cuerpo", M, P, mats)
    esq = Esqueleto(arm)
    esq = aplicar_postura(arm, cuerpo, esq, P)
    cuerpo.parent = arm
    mod = cuerpo.modifiers.new("Armature", "ARMATURE")
    mod.object = arm
    # Punto del pelo (hijo del hueso Head, en su cabeza, escalado por la cabeza) y peinado.
    bpy.context.view_layer.update()
    punto = bpy.data.objects.new("punto_pelo", None)
    punto.empty_display_size = 0.05
    bpy.context.scene.collection.objects.link(punto)
    punto.parent = arm
    punto.parent_type = "BONE"
    punto.parent_bone = "Head"
    rest_head = esq.rest["Head"]
    # Orientación del hueso Head descontando su eje propio: Head de descanso derecho = identidad.
    base = esq.rot("Head") @ Quaternion(V((1, 0, 0)), math.radians(90)).inverted()
    bpy.context.view_layer.update()
    punto.matrix_world = (Matrix.Translation(rest_head.translation) @ base.to_matrix().to_4x4() @
                          Matrix.Scale(M["s"], 4))
    pelo_obj = pelo(P["pelo"], comun.cargar_materiales(P["materiales"]["pelo"])[0], nombre="pelo")
    pelo_obj.parent = punto
    pelo_obj.matrix_parent_inverse = Matrix()
    pelo_obj.matrix_basis = Matrix()
    mano = bpy.data.objects.new("punto_mano_d", None)
    mano.empty_display_size = 0.04
    bpy.context.scene.collection.objects.link(mano)
    mano.parent = arm
    mano.parent_type = "BONE"
    mano.parent_bone = "RightHand"
    bpy.context.view_layer.update()
    rh = esq.rest["RightHand"]
    palma = rh @ V((0.0, esq.largo["RightHand"] * 0.45, 0.0)) + V((0.012 * M["g"], 0, 0))
    mano.matrix_world = Matrix.Translation(palma)   # en descanso, alineado con el mundo
    # Animaciones.
    bpy.context.scene.render.fps = FPS
    lista, caminar, trotar = animaciones(M, P)
    acciones = []
    for nombre, seg, fun in lista:
        solo = None
        if nombre == "comer":
            solo = ["RightShoulder", "RightUpperArm", "RightLowerArm", "RightHand", "Neck", "Head"]
        act, cuadros = _keyframes(arm, esq, nombre, seg, fun, solo)
        acciones.append((nombre, act, cuadros, fun))
    return dict(M=M, arm=arm, cuerpo=cuerpo, pelo=pelo_obj, punto=punto, mano=mano, esq=esq,
                acciones=acciones, caminar=caminar, trotar=trotar)


# ── Revisión ───────────────────────────────────────────────────────────

def _componentes_bien(obj):
    """Cada pieza cerrada con normales hacia afuera (volumen con signo > 0)."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    vistas = set()
    malas = 0
    abiertas = 0
    for f0 in bm.faces:
        if f0.index in vistas:
            continue
        pila, comp = [f0], []
        vistas.add(f0.index)
        while pila:
            f = pila.pop()
            comp.append(f)
            for e in f.edges:
                for g in e.link_faces:
                    if g.index not in vistas:
                        vistas.add(g.index)
                        pila.append(g)
        vol = 0.0
        for f in comp:
            v = [x.co for x in f.verts]
            for i in range(1, len(v) - 1):
                vol += v[0].dot(v[i].cross(v[i + 1])) / 6
        if vol <= 0:
            malas += 1
        if any(len(e.link_faces) != 2 for f in comp for e in f.edges):
            abiertas += 1
    bm.free()
    return malas, abiertas


def revisar(R, P, presupuesto):
    M, arm, cuerpo, pel = R["M"], R["arm"], R["cuerpo"], R["pelo"]
    poner_pose(arm, Pose(R["esq"]))
    res = []
    vs = [cuerpo.matrix_world @ v.co for v in cuerpo.data.vertices]
    mn = V(map(min, *vs))
    mx = V(map(max, *vs))
    alto = mx.z
    tol = 0.006 if not P.get("postura") else 0.03
    res.append((abs(alto - P["altura"]) <= tol,
                "Alto %.3f m sin el pelo (esperado %.2f)%s · ancho %.2f · profundidad %.2f m" % (
                    alto, P["altura"], " (encorvada)" if P.get("postura") else "", mx.x - mn.x, mx.y - mn.y)))
    tc = comun.contar_triangulos(cuerpo)
    tp = comun.contar_triangulos(pel)
    res.append((tc + tp <= presupuesto, f"Triángulos: {tc} cuerpo + {tp} pelo = {tc + tp} (máx. {presupuesto})"))
    limpio = all(o.rotation_euler.to_quaternion().angle < 1e-5 and all(abs(s - 1) < 1e-5 for s in o.scale)
                 for o in (arm, cuerpo, pel))
    res.append((limpio, "Rotación 0 y escala 1 aplicadas (armadura, cuerpo y pelo)"))
    pies = [v for v in vs if v.z < 0.05]
    cx = (min(v.x for v in pies) + max(v.x for v in pies)) / 2
    res.append((abs(mn.z) < 0.002 and abs(cx) < 0.002,
                "Origen en el piso entre los pies (suela en z = %.3f, centro de los pies x = %.3f)" % (mn.z, cx)))
    nombres = [m.name for m in cuerpo.data.materials]
    validos = comun.paleta()
    fuera = [n for n in nombres + [pel.data.materials[0].name] if n not in validos]
    res.append((not fuera, "Materiales de la paleta: " + ", ".join(
        f"{s}={n.removeprefix('M_')}" for s, n in zip(SUPERFICIES, nombres)) + f" · pelo={pel.data.materials[0].name.removeprefix('M_')}"))
    usados = {p.material_index for p in cuerpo.data.polygons} == set(range(len(nombres)))
    res.append((len(nombres) <= 6 and usados, f"Superficies: {len(nombres)} (máx. 6 en personajes), todas se usan"))
    sueltos = dobles = 0
    for o in (cuerpo, pel):
        bm = bmesh.new()
        bm.from_mesh(o.data)
        sueltos += sum(1 for v in bm.verts if not v.link_faces)
        antes = len(bm.verts)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
        dobles += antes - len(bm.verts)
        bm.free()
    malas, abiertas = _componentes_bien(cuerpo)
    m2, a2 = _componentes_bien(pel)
    res.append((sueltos == 0 and dobles == 0 and malas + m2 == 0 and abiertas + a2 == 0,
                f"Piezas cerradas con normales hacia afuera ({malas + m2} mal, {abiertas + a2} abiertas); "
                f"sin vértices sueltos ({sueltos}) ni duplicados ({dobles})"))
    # Esqueleto.
    huesos = [(b.name, b.parent.name if b.parent else None) for b in arm.data.bones]
    ok = huesos and dict(huesos) == PADRE and len(huesos) == len(HUESOS)
    res.append((ok, f"Esqueleto humanoide de Godot: {len(huesos)} huesos con los nombres y la jerarquía del perfil"))
    # Pesos.
    malos = 0
    maxinf = 0
    for v in cuerpo.data.vertices:
        ws = [g.weight for g in v.groups if g.weight > 1e-4]
        maxinf = max(maxinf, len(ws))
        if not ws or abs(sum(ws) - 1) > 1e-3:
            malos += 1
    res.append((malos == 0 and maxinf <= 4, f"Pesos: todos los vértices suman 1 ({malos} mal), máx. {maxinf} huesos por vértice"))
    return res


def chequeo_pies(R, cual="caminar"):
    """Velocidad del pie apoyado en la acción: tiene que ir hacia atrás a la velocidad del ciclo."""
    ciclo = R[cual]
    esq, M = R["esq"], R["M"]
    nombre, act, cuadros, fun = next(a for a in R["acciones"] if a[0] == cual)
    errores, estira = [], 0.0
    for f in range(cuadros):
        t0, t1 = f / FPS, (f + 1) / FPS
        p0, p1 = fun(esq, t0), fun(esq, t1)
        for ln, off in (("Left", 0.0), ("Right", 0.5)):
            u0, u1 = (t0 / ciclo.T - off) % 1.0, (t1 / ciclo.T - off) % 1.0
            if not (u0 < ciclo.ap and u1 < ciclo.ap and u1 > u0):
                continue   # solo cuadros de la fase de apoyo de ese pie
            P0, P1 = p0.matrices(), p1.matrices()
            b0 = P0[f"{ln}Toes"].translation
            b1 = P1[f"{ln}Toes"].translation
            if b0.z < 0.03 * M["k"] and b1.z < 0.03 * M["k"]:   # metatarso en el piso
                vel = (b1.y - b0.y) * FPS
                errores.append(abs(vel - ciclo.v))
    _, est = _pose_marcha(esq, M, ciclo, 0.0, {}, trote=(cual == "trotar"))
    err = max(errores) if errores else 99
    return (err < 0.15 * ciclo.v,
            f"{cual}: pie apoyado hacia atrás a {ciclo.v:.2f} m/s (error máx. {err:.2f} m/s en {len(errores)} muestras)")


# ── Exportar ───────────────────────────────────────────────────────────

def exportar_glb(objetos, ruta, animaciones=True):
    """Como comun.exportar_glb (guía 7.3), pero con piel y animaciones (solo personajes)."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for o in objetos:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objetos[0]
    bpy.ops.export_scene.gltf(
        filepath=str(ruta),
        export_format="GLB",
        use_selection=True,
        export_yup=True,
        export_apply=True,
        export_texcoords=False,
        export_normals=True,
        export_materials="EXPORT",
        export_cameras=False,
        export_lights=False,
        export_extras=False,
        export_animations=animaciones,
        export_animation_mode="ACTIONS",
        export_force_sampling=True,
        export_frame_step=1,
        export_optimize_animation_size=True,   # saca las claves que no cambian (pesa ~1/3)
        export_anim_slide_to_zero=True,
        export_reset_pose_bones=True,
        export_rest_position_armature=True,
        export_skins=True,
        export_influence_nb=4,
        export_def_bones=False,
        export_leaf_bone=False,
        export_morph=False,
    )
    print(f"Exportado {ruta.relative_to(comun.RAIZ)}")


def leer_glb(ruta):
    import json
    import struct
    b = Path(ruta).read_bytes()
    largo = struct.unpack_from("<I", b, 12)[0]
    return json.loads(b[20:20 + largo])


def chequeo_glb(ruta, nombres_anim):
    j = leer_glb(ruta)
    skins = j.get("skins", [])
    nodos = j["nodes"]
    juntas_ = [nodos[i]["name"] for i in skins[0]["joints"]] if skins else []
    anims = {a["name"]: a for a in j.get("animations", [])}
    faltan = [n for n in nombres_anim if n not in anims]
    ok = len(skins) == 1 and set(juntas_) == set(NOMBRES) and not faltan
    return (ok, f".glb: 1 piel con {len(juntas_)} huesos humanoides, {len(anims)} animaciones "
                f"({', '.join(anims)})" + (f" — faltan {faltan}" if faltan else ""))


# ── Hoja de revisión ───────────────────────────────────────────────────

def _importar_banco():
    ruta = comun.RAIZ / "godot/modelos/plaza/banco.glb"
    antes = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(ruta))
    nuevos = [o for o in bpy.data.objects if o not in antes]
    visibles = []
    for o in nuevos:
        if "colonly" in o.name or o.type != "MESH":
            o.hide_render = True
        else:
            visibles.append(o)
    raiz = [o for o in nuevos if o.parent is None]
    for r in raiz:
        r.location = (0, 0.12, 0)     # el punto del asiento está 0,12 m adelante del banco
    bpy.context.view_layer.update()
    return visibles


def hoja(id_, titulo, R, revision, extra_cuadros=None):
    import tempfile
    import _plaza as plaza
    comun.preparar_revision()
    persona = bpy.data.objects["ref_persona_1,75m"]
    persona.location = (0.75, 0.0, 0.0)
    arm, cuerpo, pel = R["arm"], R["cuerpo"], R["pelo"]
    esq = R["esq"]
    funs = {n: (f, c) for n, a, c, f in R["acciones"]}
    rapido = "--rapido" in sys.argv
    if rapido:
        bpy.context.scene.cycles.samples = 10
        bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y = 480, 360
    banco = _importar_banco()
    yo = [cuerpo, pel]
    todos = set(yo) | {persona} | set(banco)

    def pose_de(nombre, t):
        poner_pose(arm, funs[nombre][0](esq, t))

    per = R["caminar"].T
    pedidos = [
        ("Frente, al lado de 1,75 m · día", yo + [persona], "frente", "dia", ("quieto", 0.0)),
        ("Costado · día", yo + [persona], "costado", "dia", ("quieto", 0.0)),
        ("3/4 · día", yo, "tres_cuartos", "dia", ("quieto", 0.0)),
        ("3/4 · atardecer", yo, "tres_cuartos", "atardecer", ("quieto", 0.0)),
        ("caminar: talón izquierdo apoya", yo, "costado_p", "dia", ("caminar", 0.0)),
        ("caminar: pasa la pierna derecha", yo, "tres_cuartos", "dia", ("caminar", per * 0.3)),
        ("trotar (en el aire)", yo, "costado_p", "dia", ("trotar", R["trotar"].T * 0.43)),
        ("sentado en el banco", yo + banco, "tres_cuartos", "dia", ("sentado", 0.0)),
        ("esperar: mira el reloj", yo, "tres_cuartos", "dia", ("esperar", 5.2)),
        ("charlar", yo, "tres_cuartos", "atardecer", ("charlar", 1.5)),
        ("comer (a la boca)", yo, "cerca", "dia", ("caminar_comiendo", 1.3 * per)),
        ("cara de cerca", yo, "cara", "dia", ("quieto", 0.0)),
    ]
    if extra_cuadros:
        pedidos = extra_cuadros(pedidos)
    tmp = Path(tempfile.mkdtemp())
    cuadros = []
    for etiqueta, objs, vista, luz, (anim, t) in pedidos:
        pose_de(anim, t)
        comun.poner_luz(luz)
        for o in todos:
            o.hide_render = o not in objs
        if vista in ("frente", "costado"):
            comun.encuadrar(objs, vista, margen=1.08, de_cerca=True)
        elif vista == "costado_p":
            _encuadre(objs, V((1, -0.15, 0.12)))
        elif vista == "cerca":
            _encuadre(objs, V((0.9, -1.3, 0.35)), solo_arriba=True)
        elif vista == "cara":
            _encuadre_cara(R, V((0.55, -1.3, 0.18)))
        else:
            plaza.encuadre_ajustado(objs, vista)
        cuadros.append((etiqueta, comun.render(tmp / f"{len(cuadros)}.png")))
    poner_pose(arm, Pose(esq))
    destino = comun.RAIZ / f"docs/arte/revisiones/{id_}.jpg"
    if rapido:   # prueba: la hoja va a la carpeta temporal del sistema, no a docs/
        import shutil
        import tempfile
        destino = comun.RAIZ / f".hoja_rapida_{id_}.jpg"
    comun.componer_hoja(titulo, cuadros, revision, destino, columnas=4)
    if rapido:
        final = Path(tempfile.gettempdir()) / f"hoja_rapida_{id_}.jpg"
        shutil.move(destino, final)
        print(f"Hoja rápida: {final}")


def _caja(centro, medio):
    """Caja invisible (malla) para encuadrar una parte del cuerpo."""
    caja = bpy.data.objects.get("_caja_tmp")
    if caja is None:
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=2.0)
        caja = comun.objeto_desde_bmesh("_caja_tmp", bm, [])
        caja.hide_render = True
    caja.location = centro
    caja.scale = medio
    bpy.context.view_layer.update()
    return caja


def _encuadre(objs, d, solo_arriba=False):
    import _plaza as plaza
    plaza.PERSPECTIVAS["_tmp"] = d
    if solo_arriba:
        bpy.context.view_layer.update()
        vs = [o.matrix_world @ v.co for o in objs if o.type == "MESH"
              for v in o.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh().vertices]
        zmax = max(v.z for v in vs)
        caja = _caja((0, -0.05, zmax - 0.42), (0.32, 0.32, 0.42))
        plaza.encuadre_ajustado([caja], "_tmp", margen=1.0)
    else:
        plaza.encuadre_ajustado(objs, "_tmp")


def _encuadre_cara(R, d):
    import _plaza as plaza
    P = R["arm"].pose
    bpy.context.view_layer.update()
    head = R["arm"].matrix_world @ P.bones["Head"].head
    s = R["M"]["s"]
    caja = _caja(head + V((0, -0.01, 0.07 * s)), (0.13 * s, 0.13 * s, 0.15 * s))
    plaza.PERSPECTIVAS["_tmp"] = d
    plaza.encuadre_ajustado([caja], "_tmp", margen=1.0)


def m(texto):
    return texto.replace(".", ",")


def main(id_, P, presupuesto, descripcion):
    comun.escena_vacia()
    R = construir(id_, P)
    revision = revisar(R, P, presupuesto)
    revision.append(chequeo_pies(R, "caminar"))
    revision.append(chequeo_pies(R, "trotar"))
    nombres = [a[0] for a in R["acciones"]]
    durac = ", ".join(f"{a[0]} {m('%.2g' % (a[2] / FPS))} s" for a in R["acciones"])
    revision.append((True, f"Animaciones (loop, {FPS} cuadros/s): {durac}"))
    exportar = [R["arm"], R["cuerpo"], R["punto"], R["pelo"], R["mano"]]
    comun.guardar_blend(comun.RAIZ / f"arte/fuentes/{FAMILIA}/{id_}.blend")
    glb = comun.RAIZ / f"godot/modelos/{FAMILIA}/{id_}.glb"
    exportar_glb(exportar, glb)
    revision.append(chequeo_glb(glb, nombres))
    ok = comun.imprimir_revision(id_, revision)
    M = R["M"]
    titulo = m(f"{id_} · alto {P['altura']:.2f} m · {descripcion} · camina a {R['caminar'].v:.2f} m/s")
    if "--sin-hoja" not in sys.argv:
        hoja(id_, titulo, R, revision)
    if not ok:
        sys.exit(1)
    return R
