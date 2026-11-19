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
}
