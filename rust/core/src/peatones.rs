//! SPEC-013 · Peatones: cuántos hay según la hora, qué hacen y cómo se ven.

use crate::azar::Azar;

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

/// REQ-AMB-05: actividades. Quién hace cuál lo decide su perfil (REQ-RUT-02, `agenda.ron`).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, serde::Deserialize)]
pub enum Plan {
    Pasear,
    Sentarse,
    Charlar,
    Trotar,
    PasearPerro,
}

/// REQ-AMB-06, REQ-AMB-16
#[derive(Debug, Clone, PartialEq)]
pub struct Apariencia {
    pub piel: [f32; 3],
    pub remera: [f32; 3],
    pub pantalon: [f32; 3],
    pub pelo: [f32; 3],
    pub altura: f32,
    /// Color de la gorra, si lleva.
    pub gorra: Option<[f32; 3]>,
    /// REQ-RUT-10: campera o buzo de manga larga (el brazo va del color de la remera hasta
    /// la muñeca).
    pub manga_larga: bool,
}

impl Apariencia {
    /// REQ-AMB-16: en cuántos rasgos (piel, remera, pantalón, pelo, gorra o manga) se diferencian.
    /// La altura no cuenta: de lejos no se distingue.
    pub fn diferencias(&self, otra: &Apariencia) -> usize {
        [
            self.piel != otra.piel,
            self.remera != otra.remera,
            self.pantalon != otra.pantalon,
            self.pelo != otra.pelo,
            self.gorra != otra.gorra || self.manga_larga != otra.manga_larga,
        ]
        .iter()
        .filter(|d| **d)
        .count()
    }
}

const PIELES: [[f32; 3]; 6] = [
    [0.96, 0.8, 0.68],
    [0.87, 0.67, 0.5],
    [0.78, 0.58, 0.42],
    [0.66, 0.47, 0.33],
    [0.52, 0.36, 0.24],
    [0.38, 0.26, 0.18],
];
const ROPA: [[f32; 3]; 16] = [
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
    [0.95, 0.5, 0.15],
    [0.1, 0.25, 0.3],
    [0.5, 0.12, 0.18],
    [0.65, 0.8, 0.35],
    [0.55, 0.57, 0.6],
    [0.85, 0.8, 0.6],
];
const PANTALONES: [[f32; 3]; 8] = [
    [0.15, 0.2, 0.35],
    [0.2, 0.2, 0.22],
    [0.45, 0.4, 0.3],
    [0.3, 0.32, 0.36],
    [0.6, 0.55, 0.45],
    [0.35, 0.45, 0.6],
    [0.3, 0.35, 0.2],
    [0.4, 0.22, 0.15],
];
const PELOS: [[f32; 3]; 8] = [
    [0.08, 0.06, 0.05],
    [0.3, 0.2, 0.1],
    [0.55, 0.4, 0.2],
    [0.85, 0.75, 0.5],
    [0.6, 0.6, 0.6],
    [0.6, 0.25, 0.1],
    [0.18, 0.11, 0.07],
    [0.92, 0.9, 0.86],
];
const GORRAS: [[f32; 3]; 7] = [
    [0.8, 0.15, 0.15],
    [0.12, 0.2, 0.5],
    [0.1, 0.1, 0.1],
    [0.95, 0.95, 0.95],
    [0.2, 0.5, 0.25],
    [0.95, 0.7, 0.1],
    [0.45, 0.6, 0.8],
];
const CHANCE_GORRA: f32 = 0.3;

/// Combinaciones de rasgos distintas que existen (sin contar la altura). REQ-AMB-16
pub const COMBINACIONES: usize = PIELES.len() * ROPA.len() * PANTALONES.len() * PELOS.len() * (GORRAS.len() + 1);

/// REQ-AMB-06, REQ-RUT-10: de dónde se elige la ropa de alguien (cada perfil y hora tiene la
/// suya, ver `vestimenta`). La variedad de REQ-AMB-16 vale dentro de la paleta.
#[derive(Debug, Clone, PartialEq)]
pub struct Paleta {
    pub pieles: Vec<[f32; 3]>,
    pub remeras: Vec<[f32; 3]>,
    pub pantalones: Vec<[f32; 3]>,
    pub pelos: Vec<[f32; 3]>,
    pub gorras: Vec<[f32; 3]>,
    pub chance_gorra: f32,
    /// Metros, mínimo y máximo.
    pub altura: [f32; 2],
    /// Chance de manga larga (REQ-RUT-10).
    pub manga_larga: f32,
}

impl Paleta {
    /// La paleta de siempre (REQ-AMB-06): todo variado, manga corta.
    pub fn comun() -> Self {
        Self {
            pieles: PIELES.to_vec(),
            remeras: ROPA.to_vec(),
            pantalones: PANTALONES.to_vec(),
            pelos: PELOS.to_vec(),
            gorras: GORRAS.to_vec(),
            chance_gorra: CHANCE_GORRA,
            altura: [1.55, 1.9],
            manga_larga: 0.0,
        }
    }
}

/// REQ-AMB-06: una apariencia al azar (sin memoria; ver `Variedad`).
pub fn apariencia(azar: &mut Azar) -> Apariencia {
    apariencia_de(azar, &Paleta::comun())
}

/// REQ-AMB-06, REQ-RUT-10: una apariencia al azar de una paleta.
pub fn apariencia_de(azar: &mut Azar, p: &Paleta) -> Apariencia {
    let uno = |azar: &mut Azar, v: &[[f32; 3]]| *azar.elegir(v).unwrap_or(&[0.5, 0.5, 0.5]);
    Apariencia {
        piel: uno(azar, &p.pieles),
        remera: uno(azar, &p.remeras),
        pantalon: uno(azar, &p.pantalones),
        pelo: uno(azar, &p.pelos),
        altura: azar.rango(p.altura[0], p.altura[1]),
        gorra: if !p.gorras.is_empty() && azar.chance(p.chance_gorra) { azar.elegir(&p.gorras).copied() } else { None },
        manga_larga: azar.chance(p.manga_larga),
    }
}

/// REQ-AMB-16: cuántas de las que se fueron se recuerdan.
pub const MEMORIA_IDAS: usize = 30;
/// Intentos para encontrar alguien que se diferencie en al menos dos rasgos de todos.
const INTENTOS: usize = 200;

/// REQ-AMB-16: recuerda cómo se ven las personas que están en el mapa y las últimas que se
/// fueron, para que cada persona nueva se vea distinta.
#[derive(Debug, Clone, Default)]
pub struct Variedad {
    presentes: Vec<(u64, Apariencia)>,
    idas: std::collections::VecDeque<Apariencia>,
}

impl Variedad {
    fn recordadas(&self) -> impl Iterator<Item = &Apariencia> {
        self.presentes.iter().map(|(_, a)| a).chain(self.idas.iter())
    }

    /// Menor cantidad de rasgos en que `a` se diferencia de las recordadas (5 si no hay nadie).
    fn minimo_de_diferencias(&self, a: &Apariencia) -> usize {
        self.recordadas().map(|r| r.diferencias(a)).min().unwrap_or(5)
    }

    /// Apariencia para la persona `id` que llega: no repite a nadie presente ni a las últimas
    /// `MEMORIA_IDAS` que se fueron, y en lo posible se diferencia en dos rasgos o más.
    pub fn nueva(&mut self, azar: &mut Azar, id: u64) -> Apariencia {
        self.nueva_con(azar, id, &Paleta::comun())
    }

    /// Como `nueva`, eligiendo de una paleta (REQ-RUT-10).
    pub fn nueva_con(&mut self, azar: &mut Azar, id: u64, paleta: &Paleta) -> Apariencia {
        let mut mejor: Option<(usize, Apariencia)> = None;
        for _ in 0..INTENTOS {
            let a = apariencia_de(azar, paleta);
            let d = self.minimo_de_diferencias(&a);
            if mejor.as_ref().is_none_or(|(m, _)| d > *m) {
                mejor = Some((d, a));
            }
            if d >= 2 {
                break;
            }
        }
        let (d, mut a) = mejor.expect("al menos un intento");
        if d == 0 {
            // Muy improbable (hay muchas más combinaciones que recordadas): se recorre la
            // paleta de remeras (y si no alcanza, la de siempre) hasta encontrar una que no repita.
            for r in paleta.remeras.iter().chain(ROPA.iter()).copied() {
                a.remera = r;
                if self.minimo_de_diferencias(&a) > 0 {
                    break;
                }
            }
        }
        self.presentes.push((id, a.clone()));
        a
    }

    /// REQ-HAB-01: alguien que vuelve con la apariencia que ya tenía (un habitual): se anota
    /// como presente pero no se compara con nadie.
    pub fn vuelve(&mut self, id: u64, a: Apariencia) {
        self.presentes.push((id, a));
    }

    /// La persona `id` se fue del mapa.
    pub fn se_fue(&mut self, id: u64) {
        if let Some(i) = self.presentes.iter().position(|(p, _)| *p == id) {
            let (_, a) = self.presentes.remove(i);
            self.idas.push_back(a);
            while self.idas.len() > MEMORIA_IDAS {
                self.idas.pop_front();
            }
        }
    }

    /// Da por idas a las presentes que no están en `vivos`.
    pub fn quedan(&mut self, vivos: &[u64]) {
        let idas: Vec<u64> = self.presentes.iter().map(|(id, _)| *id).filter(|id| !vivos.contains(id)).collect();
        for id in idas {
            self.se_fue(id);
        }
    }

    pub fn presentes(&self) -> usize {
        self.presentes.len()
    }

    /// Ninguna de las recordadas (presentes y últimas idas) repite a otra.
    pub fn sin_repetir(&self) -> bool {
        let v: Vec<_> = self.recordadas().collect();
        (0..v.len()).all(|i| (i + 1..v.len()).all(|j| v[i].diferencias(v[j]) > 0))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

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
    fn req_amb_16_nadie_repite_a_los_presentes_ni_a_las_ultimas_30() {
        let mut a = Azar::new(16);
        let mut v = Variedad::default();
        let mut historia: Vec<(u64, Apariencia)> = Vec::new();
        let mut presentes: Vec<u64> = Vec::new();
        let mut idas: Vec<u64> = Vec::new();
        // Una plaza con 35 personas: cada vez se va la más vieja y llega una nueva.
        for id in 0..400_u64 {
            if presentes.len() >= 35 {
                let sale = presentes.remove(0);
                v.se_fue(sale);
                idas.push(sale);
            }
            let nueva = v.nueva(&mut a, id);
            let ap = |id: &u64| &historia.iter().find(|(h, _)| h == id).unwrap().1;
            for otro in presentes.iter().chain(idas.iter().rev().take(MEMORIA_IDAS)) {
                assert!(nueva.diferencias(ap(otro)) > 0, "la {id} repite a la {otro}");
                assert!(nueva.diferencias(ap(otro)) >= 2, "la {id} se parece mucho a la {otro}");
            }
            historia.push((id, nueva));
            presentes.push(id);
            assert!(v.sin_repetir());
        }
        assert_eq!(v.presentes(), 35);
    }

    #[test]
    fn req_amb_16_hay_variedad_de_sobra() {
        // Muchas más combinaciones que personas recordadas (26 de día, 6 en la fila y 30 idas).
        const { assert!(COMBINACIONES > 50 * (26 + 6 + MEMORIA_IDAS)) };
        // Las que se van y ya no están dejan de contar como presentes.
        let mut a = Azar::new(3);
        let mut v = Variedad::default();
        for id in 0..5 {
            v.nueva(&mut a, id);
        }
        v.quedan(&[1, 3]);
        assert_eq!(v.presentes(), 2);
        assert!(v.sin_repetir());
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
