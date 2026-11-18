//! SPEC-013 · Peatones: cuántos hay según la hora, qué hacen y cómo se ven.

use crate::azar::Azar;

pub const VEL_TROTE: f32 = 2.8;
/// REQ-AMB-13
pub const DISTANCIA_PERSONAL: f32 = 0.6;
const VISION: f32 = 1.8;

/// REQ-AMB-13: corrige la dirección de marcha para no chocar con nadie.
/// `dir` es hacia dónde quiere ir (largo 1); `otros`, dónde están las demás personas
/// (y el jugador). Devuelve la dirección nueva (largo 1) y un factor de velocidad (0,25 a 1).
pub fn esquivar(pos: [f32; 2], dir: [f32; 2], otros: &[[f32; 2]]) -> ([f32; 2], f32) {
    let derecha = [-dir[1], dir[0]];
    let mut r = dir;
    let mut freno: f32 = 1.0;
    for o in otros {
        let d = [pos[0] - o[0], pos[1] - o[1]];
        let dist = d[0].hypot(d[1]);
        if !(1e-4..=VISION).contains(&dist) {
            continue;
        }
        // Distancia personal: se alejan de quien está demasiado cerca.
        if dist < DISTANCIA_PERSONAL {
            let f = (DISTANCIA_PERSONAL - dist) / DISTANCIA_PERSONAL * 2.5;
            r[0] += d[0] / dist * f;
            r[1] += d[1] / dist * f;
        }
        // Alguien adelante en su camino: se corre a la derecha (o a la izquierda si el otro
        // ya está a su derecha), y frena si lo tiene encima.
        let adelante = -(d[0] * dir[0] + d[1] * dir[1]);
        let lateral = -(d[0] * derecha[0] + d[1] * derecha[1]);
        if adelante > 0.0 && adelante < VISION && lateral.abs() < DISTANCIA_PERSONAL {
            let lado = if lateral > 0.15 { -1.0 } else { 1.0 };
            let k = (1.0 - adelante / VISION) * 1.2 * lado;
            r[0] += derecha[0] * k;
            r[1] += derecha[1] * k;
            if adelante < DISTANCIA_PERSONAL {
                freno = freno.min(adelante / DISTANCIA_PERSONAL);
            }
        }
    }
    let largo = r[0].hypot(r[1]);
    if largo < 1e-3 {
        return (dir, 0.25);
    }
    ([r[0] / largo, r[1] / largo], freno.max(0.25))
}

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
const PANTALONES: [[f32; 3]; 5] =
    [[0.15, 0.2, 0.35], [0.2, 0.2, 0.22], [0.45, 0.4, 0.3], [0.3, 0.32, 0.36], [0.6, 0.55, 0.45]];
const PELOS: [[f32; 3]; 5] =
    [[0.08, 0.06, 0.05], [0.3, 0.2, 0.1], [0.55, 0.4, 0.2], [0.85, 0.75, 0.5], [0.6, 0.6, 0.6]];

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
    fn req_amb_13_sin_nadie_cerca_sigue_igual() {
        assert_eq!(esquivar([0.0, 0.0], [0.0, 1.0], &[]), ([0.0, 1.0], 1.0));
        assert_eq!(esquivar([0.0, 0.0], [0.0, 1.0], &[[5.0, 5.0]]), ([0.0, 1.0], 1.0));
    }

    #[test]
    fn req_amb_13_se_aleja_de_quien_esta_muy_cerca() {
        // Alguien pegado a su izquierda (+X cuando camina hacia +Z): se corre a -X.
        let (d, _) = esquivar([0.0, 0.0], [0.0, 1.0], &[[0.3, 0.0]]);
        assert!(d[0] < -0.3, "{d:?}");
    }

    /// Simula dos personas caminando hacia sus destinos con la regla de esquivar.
    fn simular(a0: [f32; 2], meta_a: [f32; 2], b0: [f32; 2], meta_b: [f32; 2]) -> (f32, bool) {
        let (mut a, mut b) = (a0, b0);
        let mut minima = f32::MAX;
        let dt = 1.0 / 60.0;
        for _ in 0..(60 * 30) {
            let paso = |p: [f32; 2], meta: [f32; 2], otro: [f32; 2]| {
                let d = [meta[0] - p[0], meta[1] - p[1]];
                let l = d[0].hypot(d[1]);
                if l < 0.05 {
                    return p;
                }
                let (dir, f) = esquivar(p, [d[0] / l, d[1] / l], &[otro]);
                [p[0] + dir[0] * 1.3 * f * dt, p[1] + dir[1] * 1.3 * f * dt]
            };
            let na = paso(a, meta_a, b);
            let nb = paso(b, meta_b, a);
            a = na;
            b = nb;
            minima = minima.min((a[0] - b[0]).hypot(a[1] - b[1]));
        }
        let llegaron =
            (a[0] - meta_a[0]).hypot(a[1] - meta_a[1]) < 0.1 && (b[0] - meta_b[0]).hypot(b[1] - meta_b[1]) < 0.1;
        (minima, llegaron)
    }

    #[test]
    fn req_amb_13_de_frente_se_cruzan_sin_atravesarse() {
        let (minima, llegaron) = simular([0.0, -5.0], [0.0, 5.0], [0.02, 5.0], [0.02, -5.0]);
        assert!(minima > 0.45, "se acercaron a {minima:.2} m");
        assert!(llegaron, "no llegaron a destino");
    }

    #[test]
    fn req_amb_13_cruce_en_angulo() {
        let (minima, llegaron) = simular([-5.0, 0.0], [5.0, 0.0], [0.0, -5.0], [0.0, 5.0]);
        assert!(minima > 0.4, "se acercaron a {minima:.2} m");
        assert!(llegaron);
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
