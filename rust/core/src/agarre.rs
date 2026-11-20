//! SPEC-002 · Agarre: dónde va lo que tenés en la mano y dónde queda al colocarlo.
//! Vectores como `[x, y, z]`; en la cámara, +X derecha, +Y arriba y −Z adelante.

/// REQ-INT-03: lo agarrado va abajo a la derecha de la vista, cerca (como en la mano).
pub const MANO_DERECHA: f32 = 0.2;
pub const MANO_ABAJO: f32 = 0.17;
/// Distancia adelante de los ojos, sin contar el tamaño del objeto (m).
pub const MANO_ADELANTE: f32 = 0.35;
/// REQ-INT-09: una superficie sirve de apoyo si se inclina 50° o menos (coseno de 50°).
pub const COS_APOYO: f32 = 0.643;
/// Espacio que queda entre el objeto colocado y la superficie (m).
pub const HOLGURA: f32 = 0.005;
/// REQ-INT-09: un paquete va a un lugar libre del depósito si la mira está así de cerca (m).
pub const RADIO_LUGAR: f32 = 0.3;
/// REQ-INT-06: hasta dónde llega la cruz al colocar (m). Más lejos, se suelta.
pub const ALCANCE_COLOCAR: f32 = 3.0;
/// REQ-INT-03: lo de la mano se inclina así hacia los ojos (grados).
pub const INCLINACION_MANO: f32 = 25.0;

/// REQ-INT-03: punto de la mano relativo a la cámara. Los objetos grandes van un poco más
/// adelante para no tapar la vista (`medio` = mitad de su medida más larga).
pub fn punto_mano(medio: f32) -> [f32; 3] {
    [MANO_DERECHA, -MANO_ABAJO, -(MANO_ADELANTE + medio)]
}

/// REQ-INT-09
pub fn es_apoyo(normal: [f32; 3]) -> bool {
    normal[1] >= COS_APOYO
}

/// REQ-INT-09: centro del objeto colocado donde la mira toca `punto` (con su `normal`).
/// Sobre un apoyo queda parado encima; contra una pared, delante del punto (y después cae).
/// `media_altura` y `medio_ancho` son las mitades de su alto y de su medida horizontal mayor.
pub fn centro_colocado(punto: [f32; 3], normal: [f32; 3], media_altura: f32, medio_ancho: f32) -> [f32; 3] {
    let [px, py, pz] = punto;
    if es_apoyo(normal) {
        return [px, py + media_altura + HOLGURA, pz];
    }
    let s = medio_ancho + HOLGURA;
    [px + normal[0] * s, py + normal[1] * s, pz + normal[2] * s]
}

/// REQ-INT-09: el lugar libre del depósito más cercano a `punto`, si está a `RADIO_LUGAR` o menos.
pub fn lugar_cercano(punto: [f32; 3], lugares: &[[f32; 3]]) -> Option<usize> {
    let d2 = |l: &[f32; 3]| (0..3).map(|i| (l[i] - punto[i]).powi(2)).sum::<f32>();
    lugares
        .iter()
        .enumerate()
        .filter(|(_, l)| d2(l) <= RADIO_LUGAR * RADIO_LUGAR)
        .min_by(|a, b| d2(a.1).total_cmp(&d2(b.1)))
        .map(|(i, _)| i)
}

/// REQ-INT-03 (TASK-0265): giro de lo agarrado relativo a la cámara, como columnas (sus ejes
/// X, Y, Z locales vistos desde la cámara). Acostado, con su largo (el eje horizontal mayor:
/// X si `ancho_x >= fondo_z`, si no Z) cruzado a la vista, la parte de arriba (+Y) hacia arriba
/// e inclinada `INCLINACION_MANO` hacia los ojos (+Z de la cámara). `volteado`: lo que se
/// cocina por lados y tenía la otra cara abajo queda dado vuelta sobre su largo.
pub fn giro_mano(ancho_x: f32, fondo_z: f32, volteado: bool) -> [[f32; 3]; 3] {
    let (s, c) = INCLINACION_MANO.to_radians().sin_cos();
    let signo = if volteado { -1.0 } else { 1.0 };
    let largo = [1.0, 0.0, 0.0];
    let arriba = [0.0, c * signo, s * signo];
    if ancho_x >= fondo_z {
        // X = largo, Y = arriba, Z = X × Y
        [largo, arriba, cruz(largo, arriba)]
    } else {
        // Z = largo, Y = arriba, X = Y × Z
        [cruz(arriba, largo), arriba, largo]
    }
}

fn cruz(a: [f32; 3], b: [f32; 3]) -> [f32; 3] {
    [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]
}

/// REQ-INT-08: lo que hace el clic con algo en la mano. De acá salen el cartel y el clic.
#[derive(Debug, Clone, PartialEq)]
pub enum AccionClic {
    /// REQ-INT-06: no hay dónde apoyarlo (lejos, pared, cielo): se suelta donde está y cae.
    Soltar,
    /// REQ-INT-09: sobre una superficie.
    Apoyar,
    /// REQ-INT-10: en la zona de encastre de la base (su nombre).
    Armar(String),
    /// REQ-INT-09, REQ-PRO-06: un paquete a un lugar libre del depósito.
    Guardar,
    /// REQ-FRE-07: papas adentro del colador.
    Colador,
    /// REQ-FRE-07: el colador está lleno: se apoya como siempre.
    ColadorLleno,
    /// REQ-INT-09, REQ-COC-10: al agua del hervidor, al primer lugar libre.
    AlAgua,
    /// REQ-COC-08: no hay lugar en el agua: el clic no hace nada.
    HervidorLleno,
}

/// REQ-INT-08: lo que hay donde apunta la cruz (lo junta el juego para `accion_clic`).
#[derive(Debug, Clone, Default, PartialEq)]
pub struct Mira {
    /// Normal de la superficie que toca la cruz a `ALCANCE_COLOCAR` o menos (`None`: nada).
    pub normal: Option<[f32; 3]>,
    /// Papas sobre un colador: `Some(hay lugar)`.
    pub colador: Option<bool>,
    /// Un agregado sobre una base que lo combina: el nombre de la base.
    pub base: Option<String>,
    /// La cruz en el hervidor con algo que va al agua: `Some(hay lugar)`.
    pub hervidor: Option<bool>,
    /// Un paquete con la cruz cerca de un lugar libre del depósito (y a la vista).
    pub lugar_libre: bool,
}

/// REQ-INT-06, REQ-INT-08, REQ-INT-09, REQ-INT-10: qué hace el clic con lo que tenés en la mano.
pub fn accion_clic(m: &Mira) -> AccionClic {
    let Some(normal) = m.normal else { return AccionClic::Soltar };
    if m.colador == Some(true) {
        return AccionClic::Colador;
    }
    if let Some(base) = &m.base {
        return AccionClic::Armar(base.clone());
    }
    match m.hervidor {
        Some(true) => return AccionClic::AlAgua,
        Some(false) => return AccionClic::HervidorLleno,
        None => {}
    }
    if m.lugar_libre {
        return AccionClic::Guardar;
    }
    match (es_apoyo(normal), m.colador.is_some()) {
        (true, true) => AccionClic::ColadorLleno,
        (true, false) => AccionClic::Apoyar,
        (false, _) => AccionClic::Soltar,
    }
}

impl AccionClic {
    /// REQ-INT-08: texto del cartel para el clic.
    pub fn cartel(&self) -> String {
        match self {
            AccionClic::Soltar => "[Clic] Soltar".into(),
            AccionClic::Apoyar => "[Clic] Apoyar acá".into(),
            AccionClic::Armar(base) => format!("[Clic] Poner en el {base}"),
            AccionClic::Guardar => "[Clic] Guardar en el estante".into(),
            AccionClic::Colador => "[Clic] Poner en el colador".into(),
            AccionClic::ColadorLleno => "[Clic] Apoyar acá (el colador está lleno)".into(),
            AccionClic::AlAgua => "[Clic] Al agua".into(),
            AccionClic::HervidorLleno => "Hervidor lleno".into(),
        }
    }
}

/// REQ-INT-08: el clic hace lo último que dijo el cartel si desde entonces la vista casi no se
/// movió: los ojos menos de `MIRA_QUIETA_M` y la dirección menos de `MIRA_QUIETA_GRADOS`.
pub const MIRA_QUIETA_M: f32 = 0.05;
pub const MIRA_QUIETA_GRADOS: f32 = 3.0;

/// REQ-INT-08: si la mira de ahora (`ojos_b`, `dir_b`) es casi la de antes (`ojos_a`, `dir_a`).
/// Las direcciones no hace falta que tengan largo 1.
pub fn misma_mira(ojos_a: [f32; 3], dir_a: [f32; 3], ojos_b: [f32; 3], dir_b: [f32; 3]) -> bool {
    let dot = |a: [f32; 3], b: [f32; 3]| a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
    let d = [ojos_a[0] - ojos_b[0], ojos_a[1] - ojos_b[1], ojos_a[2] - ojos_b[2]];
    let largos = (dot(dir_a, dir_a) * dot(dir_b, dir_b)).sqrt();
    dot(d, d) <= MIRA_QUIETA_M * MIRA_QUIETA_M
        && largos > 0.0
        && dot(dir_a, dir_b) / largos >= MIRA_QUIETA_GRADOS.to_radians().cos()
}

/// REQ-COC-10: de `unidades` de un paquete volcado, cuántas van al agua (las que entran en
/// `libres` lugares) y cuántas quedan en el paquete.
pub fn repartir_volcado(unidades: u32, libres: usize) -> (u32, u32) {
    let al_agua = unidades.min(libres as u32);
    (al_agua, unidades - al_agua)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn req_int_03_la_mano_queda_cerca_abajo_a_la_derecha() {
        let [x, y, z] = punto_mano(0.05);
        assert!(x > 0.0 && y < 0.0, "abajo a la derecha");
        assert!(-z < 0.5, "cerca: a {} m (antes 1 m)", -z);
        assert!(punto_mano(0.3)[2] < z, "lo grande va más adelante");
    }

    #[test]
    fn req_int_09_sobre_la_mesada_queda_parado_encima_del_punto() {
        let c = centro_colocado([1.0, 0.9, 2.0], [0.0, 1.0, 0.0], 0.02, 0.08);
        assert_eq!(c[0], 1.0);
        assert_eq!(c[2], 2.0);
        assert!((c[1] - (0.9 + 0.02 + HOLGURA)).abs() < 1e-6);
    }

    #[test]
    fn req_int_09_contra_una_pared_queda_delante() {
        assert!(!es_apoyo([1.0, 0.0, 0.0]));
        assert!(!es_apoyo([0.0, 0.6, 0.8]), "53° es muy empinado");
        assert!(es_apoyo([0.0, 0.8, 0.6]), "37° sirve");
        let c = centro_colocado([0.0, 1.0, 0.0], [0.0, 0.0, 1.0], 0.02, 0.08);
        assert!((c[2] - (0.08 + HOLGURA)).abs() < 1e-6 && c[1] == 1.0);
    }

    #[test]
    fn req_int_09_un_paquete_va_al_lugar_libre_mas_cercano() {
        let lugares = [[0.0, 1.0, 0.0], [0.25, 1.0, 0.0], [2.0, 1.0, 0.0]];
        assert_eq!(lugar_cercano([0.2, 1.05, 0.0], &lugares), Some(1));
        assert_eq!(lugar_cercano([1.0, 1.0, 0.0], &lugares), None, "lejos de todos");
        assert_eq!(lugar_cercano([0.0, 1.0, 0.0], &[]), None);
    }

    fn aplicar(g: [[f32; 3]; 3], v: [f32; 3]) -> [f32; 3] {
        let mut r = [0.0; 3];
        for (i, col) in g.iter().enumerate() {
            for k in 0..3 {
                r[k] += col[k] * v[i];
            }
        }
        r
    }

    fn cerca(a: [f32; 3], b: [f32; 3]) -> bool {
        (0..3).all(|i| (a[i] - b[i]).abs() < 1e-5)
    }

    #[test]
    fn req_int_03_lo_agarrado_va_derecho_cruzado_e_inclinado_25_grados() {
        // Salchicha (larga en X): su largo cruzado a la vista, arriba hacia arriba.
        let g = giro_mano(0.15, 0.02, false);
        assert!(cerca(aplicar(g, [1.0, 0.0, 0.0]), [1.0, 0.0, 0.0]), "largo cruzado");
        let arriba = aplicar(g, [0.0, 1.0, 0.0]);
        assert!(arriba[1] > 0.0 && arriba[2] > 0.0, "arriba, inclinado hacia los ojos: {arriba:?}");
        let grados = arriba[2].atan2(arriba[1]).to_degrees();
        assert!((grados - 25.0).abs() < 1e-3, "25°: {grados}");
        // Un paquete más largo en Z: ese largo también queda cruzado.
        let g = giro_mano(0.1, 0.3, false);
        assert!(cerca(aplicar(g, [0.0, 0.0, 1.0]), [1.0, 0.0, 0.0]));
        assert!(cerca(aplicar(g, [0.0, 1.0, 0.0]), arriba));
        // Es un giro: ejes de largo 1, perpendiculares y sin espejar.
        for g in [giro_mano(0.15, 0.02, false), giro_mano(0.1, 0.3, true)] {
            let [x, y, z] = g;
            assert!(cerca(cruz(x, y), z), "derecho (sin espejar)");
            for e in g {
                assert!((e.iter().map(|v| v * v).sum::<f32>() - 1.0).abs() < 1e-5);
            }
        }
    }

    #[test]
    fn req_int_03_lo_que_se_cocina_por_lados_conserva_la_cara_de_abajo() {
        let g = giro_mano(0.1, 0.1, true);
        let arriba = aplicar(g, [0.0, 1.0, 0.0]);
        assert!(arriba[1] < 0.0, "dado vuelta: la cara de arriba mira abajo");
        assert!(cerca(aplicar(g, [1.0, 0.0, 0.0]), [1.0, 0.0, 0.0]), "sigue cruzada");
    }

    #[test]
    fn req_int_06_sin_donde_apoyarlo_se_suelta() {
        assert_eq!(accion_clic(&Mira::default()), AccionClic::Soltar, "lejos o el cielo");
        let pared = Mira { normal: Some([0.0, 0.0, 1.0]), ..Mira::default() };
        assert_eq!(accion_clic(&pared), AccionClic::Soltar);
        assert_eq!(AccionClic::Soltar.cartel(), "[Clic] Soltar");
        let mesada = Mira { normal: Some([0.0, 1.0, 0.0]), ..Mira::default() };
        assert_eq!(accion_clic(&mesada), AccionClic::Apoyar);
        assert_eq!(ALCANCE_COLOCAR, 3.0);
    }

    #[test]
    fn req_int_08_el_cartel_dice_lo_que_hace_el_clic() {
        let arriba = Some([0.0, 1.0, 0.0]);
        let estante = Mira { normal: arriba, lugar_libre: true, ..Mira::default() };
        assert_eq!(accion_clic(&estante), AccionClic::Guardar);
        assert_eq!(accion_clic(&estante).cartel(), "[Clic] Guardar en el estante");
        // Un lugar libre del estante se ofrece aunque la cruz toque el borde de la tabla.
        let borde = Mira { normal: Some([0.0, 0.0, 1.0]), lugar_libre: true, ..Mira::default() };
        assert_eq!(accion_clic(&borde), AccionClic::Guardar);
        let pan = Mira { normal: arriba, base: Some("pan de pancho".into()), ..Mira::default() };
        assert_eq!(accion_clic(&pan).cartel(), "[Clic] Poner en el pan de pancho");
        let colador = Mira { normal: arriba, colador: Some(true), ..Mira::default() };
        assert_eq!(accion_clic(&colador), AccionClic::Colador);
        let lleno = Mira { normal: arriba, colador: Some(false), ..Mira::default() };
        assert_eq!(accion_clic(&lleno), AccionClic::ColadorLleno);
    }

    #[test]
    fn req_int_09_en_cualquier_parte_del_hervidor_va_al_agua() {
        for normal in [[0.0, 1.0, 0.0], [1.0, 0.0, 0.0]] {
            let borde = Mira { normal: Some(normal), hervidor: Some(true), ..Mira::default() };
            assert_eq!(accion_clic(&borde), AccionClic::AlAgua, "borde, cuba o agua");
        }
        assert_eq!(AccionClic::AlAgua.cartel(), "[Clic] Al agua");
        let lleno = Mira { normal: Some([0.0, 1.0, 0.0]), hervidor: Some(false), ..Mira::default() };
        assert_eq!(accion_clic(&lleno), AccionClic::HervidorLleno);
        assert_eq!(AccionClic::HervidorLleno.cartel(), "Hervidor lleno");
    }

    #[test]
    fn req_int_08_el_clic_hace_lo_que_mostro_el_cartel_si_la_mira_casi_no_se_movio() {
        let ojos = [0.0, 1.65, 0.0];
        let adelante = [0.0, 0.0, -1.0];
        assert!(misma_mira(ojos, adelante, ojos, adelante));
        // Un temblor del mouse (1°) y el balanceo de la cámara (2 cm): lo mismo.
        let un_grado = [1f32.to_radians().sin(), 0.0, -1f32.to_radians().cos()];
        assert!(misma_mira(ojos, adelante, [0.0, 1.67, 0.0], un_grado));
        // Apuntar a otro lado o moverse: se decide de nuevo.
        let diez = [10f32.to_radians().sin(), 0.0, -10f32.to_radians().cos()];
        assert!(!misma_mira(ojos, adelante, ojos, diez));
        assert!(!misma_mira(ojos, adelante, [0.2, 1.65, 0.0], adelante));
    }

    #[test]
    fn req_coc_10_al_volcar_van_al_agua_las_que_entran() {
        assert_eq!(repartir_volcado(12, 14), (12, 0), "entran todas: el paquete se va");
        assert_eq!(repartir_volcado(12, 5), (5, 7), "sobran 7: quedan en el paquete");
        assert_eq!(repartir_volcado(12, 0), (0, 12), "lleno");
    }
}
