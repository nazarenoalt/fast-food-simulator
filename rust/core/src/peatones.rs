//! SPEC-013 · Peatones: cuántos hay según la hora, qué hacen y cómo se ven.

use crate::azar::Azar;

pub const VEL_TROTE: f32 = 2.8;

/// REQ-AMB-04: cuánta gente anda por la plaza según la hora (0–24).
pub fn cantidad_objetivo(hora: f32) -> usize {
    match hora.rem_euclid(24.0) {
        h if h < 6.0 => 3,
        h if h < 8.0 => 12,
        h if h < 21.0 => 26,
        _ => 14,
    }
}

/// REQ-AMB-05
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Plan {
    Pasear,
    Sentarse,
    Charlar,
    Trotar,
    PasearPerro,
}

pub fn elegir_plan(azar: &mut Azar) -> Plan {
    match azar.real() {
        r if r < 0.40 => Plan::Pasear,
        r if r < 0.62 => Plan::Sentarse,
        r if r < 0.77 => Plan::Charlar,
        r if r < 0.87 => Plan::Trotar,
        _ => Plan::PasearPerro,
    }
}

/// Segundos que se queda sentado o charlando.
pub fn duracion_quieto(azar: &mut Azar, plan: Plan) -> f32 {
    match plan {
        Plan::Sentarse => azar.rango(20.0, 70.0),
        Plan::Charlar => azar.rango(25.0, 80.0),
        _ => 0.0,
    }
}

pub fn velocidad(azar: &mut Azar, plan: Plan) -> f32 {
    if plan == Plan::Trotar { VEL_TROTE + azar.rango(-0.3, 0.4) } else { azar.rango(1.05, 1.5) }
}

/// REQ-AMB-06
#[derive(Debug, Clone, PartialEq)]
pub struct Apariencia {
    pub piel: [f32; 3],
    pub remera: [f32; 3],
    pub pantalon: [f32; 3],
    pub pelo: [f32; 3],
    pub altura: f32,
    pub gorra: bool,
}

const PIELES: [[f32; 3]; 5] =
    [[0.96, 0.8, 0.68], [0.87, 0.67, 0.5], [0.72, 0.52, 0.38], [0.55, 0.38, 0.26], [0.38, 0.26, 0.18]];
const ROPA: [[f32; 3]; 10] = [
    [0.85, 0.2, 0.2],
    [0.2, 0.35, 0.75],
    [0.95, 0.95, 0.92],
    [0.15, 0.15, 0.17],
    [0.25, 0.6, 0.35],
    [0.95, 0.75, 0.2],
    [0.55, 0.3, 0.6],
    [0.4, 0.75, 0.85],
    [0.9, 0.5, 0.6],
    [0.6, 0.45, 0.3],
];
const PANTALONES: [[f32; 3]; 5] = [[0.15, 0.2, 0.35], [0.2, 0.2, 0.22], [0.45, 0.4, 0.3], [0.3, 0.32, 0.36], [0.6, 0.55, 0.45]];
const PELOS: [[f32; 3]; 5] = [[0.08, 0.06, 0.05], [0.3, 0.2, 0.1], [0.55, 0.4, 0.2], [0.85, 0.75, 0.5], [0.6, 0.6, 0.6]];

pub fn apariencia(azar: &mut Azar) -> Apariencia {
    Apariencia {
        piel: *azar.elegir(&PIELES).unwrap(),
        remera: *azar.elegir(&ROPA).unwrap(),
        pantalon: *azar.elegir(&PANTALONES).unwrap(),
        pelo: *azar.elegir(&PELOS).unwrap(),
        altura: azar.rango(1.55, 1.9),
        gorra: azar.chance(0.2),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn req_amb_04_mas_gente_de_dia() {
        assert!(cantidad_objetivo(3.0) < 5);
        assert!(cantidad_objetivo(13.0) > 20);
        assert!(cantidad_objetivo(22.0) < cantidad_objetivo(13.0));
    }

    #[test]
    fn req_amb_05_todas_las_actividades() {
        let mut a = Azar::new(5);
        let planes: std::collections::HashSet<_> = (0..500).map(|_| format!("{:?}", elegir_plan(&mut a))).collect();
        assert_eq!(planes.len(), 5);
        assert!(duracion_quieto(&mut a, Plan::Sentarse) >= 20.0);
        assert!(velocidad(&mut a, Plan::Trotar) > velocidad(&mut a, Plan::Pasear));
    }

    #[test]
    fn req_amb_06_apariencia_variada() {
        let mut a = Azar::new(9);
        let ap: Vec<_> = (0..50).map(|_| apariencia(&mut a)).collect();
        let remeras: std::collections::HashSet<_> = ap.iter().map(|x| format!("{:?}", x.remera)).collect();
        let pieles: std::collections::HashSet<_> = ap.iter().map(|x| format!("{:?}", x.piel)).collect();
        assert!(remeras.len() >= 6 && pieles.len() >= 4);
        assert!(ap.iter().all(|x| (1.5..2.0).contains(&x.altura)));
    }
}
