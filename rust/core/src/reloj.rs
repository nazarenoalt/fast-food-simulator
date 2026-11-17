//! SPEC-007 · Día y noche: reloj de juego, sol y curvas de luz.

pub const MINUTOS_DIA: f64 = 1440.0;
pub const SALIDA_SOL: f64 = 6.0 * 60.0 + 30.0; // 6:30
pub const PUESTA_SOL: f64 = 19.0 * 60.0 + 30.0; // 19:30
pub const ALTURA_MAX_SOL: f32 = 60.0;
const PROFUNDIDAD_NOCHE: f32 = 40.0;
/// REQ-DIA-06
pub const UMBRAL_NOCHE: f32 = 3.0;

/// REQ-DIA-01
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Reloj {
    /// Minuto del día, 0 ≤ minuto < 1440.
    pub minuto: f64,
    pub dia: u32,
    /// Minutos de juego por segundo real.
    pub minutos_por_segundo: f64,
    /// Multiplicador de prueba (REQ-DIA-07).
    pub multiplicador: f64,
}

impl Default for Reloj {
    fn default() -> Self {
        // REQ-DIA-01: 1 min de juego = 1 s real; arranca 17:00 del día 1.
        Self { minuto: 17.0 * 60.0, dia: 1, minutos_por_segundo: 1.0, multiplicador: 1.0 }
    }
}

impl Reloj {
    /// REQ-DIA-01, REQ-DIA-02
    pub fn avanzar(&mut self, segundos_reales: f64) {
        self.minuto += segundos_reales * self.minutos_por_segundo * self.multiplicador;
        while self.minuto >= MINUTOS_DIA {
            self.minuto -= MINUTOS_DIA;
            self.dia += 1;
        }
    }

    /// REQ-DIA-07
    pub fn alternar_rapido(&mut self) {
        self.multiplicador = if self.multiplicador > 1.0 { 1.0 } else { 30.0 };
    }

    /// "HH:MM"
    pub fn hora_texto(&self) -> String {
        let m = self.minuto as u32;
        format!("{:02}:{:02}", m / 60, m % 60)
    }

    pub fn sol(&self) -> Sol {
        Sol::en(self.minuto)
    }
}

/// Posición del sol en grados. Azimut: 0 = norte, 90 = este, 180 = sur, 270 = oeste.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Sol {
    pub altura: f32,
    pub azimut: f32,
}

impl Sol {
    /// REQ-DIA-03
    pub fn en(minuto: f64) -> Self {
        let duracion_dia = PUESTA_SOL - SALIDA_SOL;
        if (SALIDA_SOL..PUESTA_SOL).contains(&minuto) {
            let f = ((minuto - SALIDA_SOL) / duracion_dia) as f32;
            Sol { altura: ALTURA_MAX_SOL * (std::f32::consts::PI * f).sin(), azimut: 90.0 + 180.0 * f }
        } else {
            let duracion_noche = MINUTOS_DIA - duracion_dia;
            let desde_puesta = (minuto - PUESTA_SOL).rem_euclid(MINUTOS_DIA);
            let f = (desde_puesta / duracion_noche) as f32;
            Sol { altura: -PROFUNDIDAD_NOCHE * (std::f32::consts::PI * f).sin(), azimut: (270.0 + 180.0 * f) % 360.0 }
        }
    }

    /// Dirección hacia el sol (x = este, y = arriba, z = sur), largo 1.
    pub fn direccion(&self) -> [f32; 3] {
        let (alt, az) = (self.altura.to_radians(), self.azimut.to_radians());
        [az.sin() * alt.cos(), alt.sin(), -az.cos() * alt.cos()]
    }

    /// REQ-DIA-06
    pub fn es_de_noche(&self) -> bool {
        self.altura < UMBRAL_NOCHE
    }

    /// REQ-DIA-04: apagado bajo el horizonte.
    pub fn energia(&self) -> f32 {
        1.0 * suave(-2.0, 12.0, self.altura)
    }

    /// REQ-DIA-04: cálido cerca del horizonte, blanco arriba.
    pub fn color(&self) -> [f32; 3] {
        crate::coccion::mezclar([1.0, 0.5, 0.25], [1.0, 0.97, 0.92], suave(0.0, 25.0, self.altura))
    }

    /// REQ-DIA-05
    pub fn energia_ambiente(&self) -> f32 {
        0.12 + 0.48 * suave(-8.0, 15.0, self.altura)
    }

    /// REQ-DIA-05: luz de luna, solo de noche.
    pub fn energia_luna(&self) -> f32 {
        0.18 * (1.0 - suave(-6.0, 2.0, self.altura))
    }

    /// REQ-AMB-11: blancas de día, anaranjadas al atardecer, oscuras de noche.
    pub fn color_nubes(&self) -> [f32; 3] {
        use crate::coccion::mezclar;
        let dia = suave(-6.0, 10.0, self.altura);
        let atardecer = 1.0 - suave(0.0, 20.0, self.altura.abs());
        let base = mezclar([0.1, 0.11, 0.16], [0.97, 0.97, 0.98], dia);
        mezclar(base, [1.0, 0.6, 0.4], atardecer * 0.7)
    }

    /// REQ-AMB-12
    pub fn luna_visible(&self) -> bool {
        self.altura < -2.0
    }

    /// REQ-DIA-05: (cielo arriba, horizonte).
    pub fn colores_cielo(&self) -> ([f32; 3], [f32; 3]) {
        use crate::coccion::mezclar;
        let dia = suave(-6.0, 20.0, self.altura);
        let atardecer = 1.0 - suave(0.0, 18.0, self.altura.abs());
        let arriba = mezclar([0.015, 0.025, 0.07], [0.3, 0.52, 0.88], dia);
        let horizonte = mezclar([0.05, 0.06, 0.12], [0.68, 0.78, 0.9], dia);
        (arriba, mezclar(horizonte, [0.98, 0.5, 0.28], atardecer * 0.85))
    }
}

/// Curva suave de 0 a 1 entre `a` y `b`.
pub fn suave(a: f32, b: f32, x: f32) -> f32 {
    let t = ((x - a) / (b - a)).clamp(0.0, 1.0);
    t * t * (3.0 - 2.0 * t)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn h(horas: u32, min: u32) -> f64 {
        (horas * 60 + min) as f64
    }

    #[test]
    fn req_dia_01_arranca_17hs_dia_1_y_1min_por_segundo() {
        let mut r = Reloj::default();
        assert_eq!(r.hora_texto(), "17:00");
        assert_eq!(r.dia, 1);
        r.avanzar(60.0);
        assert_eq!(r.hora_texto(), "18:00");
    }

    #[test]
    fn req_dia_02_cambio_de_dia() {
        let mut r = Reloj { minuto: h(23, 59), ..Default::default() };
        r.avanzar(2.0);
        assert_eq!(r.dia, 2);
        assert_eq!(r.hora_texto(), "00:01");
    }

    #[test]
    fn req_dia_03_arco_del_sol() {
        assert!(Sol::en(h(6, 30)).altura.abs() < 0.01);
        assert!(Sol::en(h(19, 30)).altura.abs() < 0.01);
        let mediodia = Sol::en((SALIDA_SOL + PUESTA_SOL) / 2.0);
        assert!((mediodia.altura - 60.0).abs() < 0.01);
        assert!(Sol::en(h(0, 0)).altura < 0.0);
        assert!(Sol::en(h(3, 0)).altura < 0.0);
        // De este a oeste.
        assert!((Sol::en(h(6, 31)).azimut - 90.0).abs() < 1.0);
        assert!((Sol::en(h(19, 29)).azimut - 270.0).abs() < 1.0);
        let d = Sol::en(h(8, 0)).direccion();
        assert!(d[0] > 0.0, "a la mañana el sol está al este");
    }

    #[test]
    fn req_dia_04_color_y_energia_del_sol() {
        let bajo = Sol::en(h(7, 0));
        let alto = Sol::en(h(13, 0));
        assert!(bajo.color()[2] < alto.color()[2], "cerca del horizonte es más cálido");
        assert!(alto.energia() > bajo.energia());
        assert_eq!(Sol::en(h(23, 0)).energia(), 0.0);
    }

    #[test]
    fn req_dia_05_noche_oscura_con_luna() {
        let noche = Sol::en(h(23, 0));
        let dia = Sol::en(h(13, 0));
        assert!(noche.energia_ambiente() < dia.energia_ambiente());
        assert!(noche.energia_luna() > 0.1);
        assert_eq!(dia.energia_luna(), 0.0);
        assert!(noche.colores_cielo().0[2] < dia.colores_cielo().0[2]);
    }

    #[test]
    fn req_amb_11_color_de_nubes() {
        let dia = Sol::en(h(13, 0)).color_nubes();
        let atardecer = Sol::en(h(19, 25)).color_nubes();
        let noche = Sol::en(h(1, 0)).color_nubes();
        assert!(dia.iter().all(|c| *c > 0.9));
        assert!(atardecer[0] > atardecer[2] + 0.15, "anaranjadas: {atardecer:?}");
        assert!(noche.iter().all(|c| *c < 0.2));
    }

    #[test]
    fn req_amb_12_luna_de_noche() {
        assert!(Sol::en(h(23, 0)).luna_visible());
        assert!(!Sol::en(h(13, 0)).luna_visible());
    }

    #[test]
    fn req_dia_06_luces_de_noche() {
        assert!(Sol::en(h(20, 0)).es_de_noche());
        assert!(Sol::en(h(4, 0)).es_de_noche());
        assert!(!Sol::en(h(12, 0)).es_de_noche());
        assert!(!Sol::en(h(17, 0)).es_de_noche());
    }

    #[test]
    fn req_dia_07_velocidad_de_prueba() {
        let mut r = Reloj::default();
        r.alternar_rapido();
        r.avanzar(1.0);
        assert_eq!(r.hora_texto(), "17:30");
        r.alternar_rapido();
        assert_eq!(r.multiplicador, 1.0);
    }
}
