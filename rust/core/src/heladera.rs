//! SPEC-016 · Heladera y cadena de frío.

use crate::TEMP_AMBIENTE;

/// Temperatura interior de la heladera cerrada y enchufada (°C). REQ-HEL-01
pub const TEMP_INTERIOR: f32 = 4.0;
/// Qué tan rápido se enfría cerrada y enchufada (1/s). REQ-HEL-02
pub const K_FRIA: f32 = 0.01;
/// Abierta o desenchufada se acerca al ambiente 3 veces más lento. REQ-HEL-02
pub const K_ABIERTA: f32 = K_FRIA / 3.0;
/// Qué tan rápido un paquete toma la temperatura de su entorno (1/s). REQ-HEL-06
pub const K_PAQUETE: f32 = 0.002;
/// Hasta esta temperatura la frescura no baja (°C). REQ-HEL-03
pub const TEMP_SEGURA: f32 = 8.0;
/// Desde esta temperatura (bien cocinado) la frescura tampoco baja (°C). REQ-HEL-03
pub const TEMP_COCINADO: f32 = 60.0;
/// Pérdida de frescura por grado sobre TEMP_SEGURA, en % por segundo. REQ-HEL-03
pub const PERDIDA_POR_GRADO: f32 = 0.02;
/// Debajo de esta frescura (%) se ve verdosa y descuenta estrellas. REQ-HEL-04, REQ-HEL-07
pub const FRESCURA_DUDOSA: f32 = 40.0;

/// REQ-HEL-01, REQ-HEL-02
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Heladera {
    pub temp: f32,
    pub abierta: bool,
    pub enchufada: bool,
}

impl Default for Heladera {
    fn default() -> Self {
        // Arranca ya fría: se la considera en funcionamiento desde antes.
        Self { temp: TEMP_INTERIOR, abierta: false, enchufada: true }
    }
}

impl Heladera {
    /// REQ-HEL-01
    pub fn alternar_puerta(&mut self) {
        self.abierta = !self.abierta;
    }

    /// REQ-HEL-02
    pub fn paso(&mut self, dt: f32) {
        let enfria = !self.abierta && self.enchufada;
        let (objetivo, k) = if enfria { (TEMP_INTERIOR, K_FRIA) } else { (TEMP_AMBIENTE, K_ABIERTA) };
        self.temp += (objetivo - self.temp) * (k * dt).min(1.0);
    }
}

/// REQ-HEL-06: un paquete (o cualquier cosa) se acerca a la temperatura de su entorno.
pub fn acercar(temp: f32, entorno: f32, k: f32, dt: f32) -> f32 {
    temp + (entorno - temp) * (k * dt).min(1.0)
}

/// REQ-HEL-03, REQ-HEL-04: frescura de un alimento perecedero, de 100 a 0 %.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Frescura {
    pub porcentaje: f32,
}

impl Default for Frescura {
    fn default() -> Self {
        Self { porcentaje: 100.0 }
    }
}

impl Frescura {
    /// Avanza `dt` segundos con el alimento a `temp` °C. Nunca sube. REQ-HEL-03
    pub fn paso(&mut self, temp: f32, dt: f32) {
        if temp > TEMP_SEGURA && temp < TEMP_COCINADO {
            self.porcentaje = (self.porcentaje - (temp - TEMP_SEGURA) * PERDIDA_POR_GRADO * dt).max(0.0);
        }
    }

    /// REQ-HEL-04: menor a 40 %: verdosa y el cartel avisa.
    pub fn dudosa(&self) -> bool {
        self.porcentaje < FRESCURA_DUDOSA
    }

    /// REQ-HEL-04: en 0 % está echada a perder (definitivo, porque nunca sube).
    pub fn echada_a_perder(&self) -> bool {
        self.porcentaje <= 0.0
    }

    /// REQ-HEL-04: cuánto tirar el color hacia el verde (0 = normal, 1 = muy verdoso).
    pub fn verdor(&self) -> f32 {
        ((FRESCURA_DUDOSA - self.porcentaje) / FRESCURA_DUDOSA).clamp(0.0, 1.0)
    }

    /// Para el cartel. REQ-HEL-04
    pub fn texto(&self) -> Option<String> {
        if self.echada_a_perder() {
            Some("echada a perder".to_string())
        } else if self.dudosa() {
            Some(format!("fresca al {:.0} %, ¡se está echando a perder!", self.porcentaje))
        } else {
            None
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn req_hel_01_arranca_a_4_grados_cerrada() {
        let h = Heladera::default();
        assert_eq!(h.temp, 4.0);
        assert!(!h.abierta && h.enchufada);
    }

    #[test]
    fn req_hel_01_la_puerta_se_abre_y_cierra() {
        let mut h = Heladera::default();
        h.alternar_puerta();
        assert!(h.abierta);
        h.alternar_puerta();
        assert!(!h.abierta);
    }

    #[test]
    fn req_hel_02_cerrada_se_acerca_a_4() {
        let mut h = Heladera { temp: 20.0, abierta: false, enchufada: true };
        for _ in 0..600 {
            h.paso(1.0);
        }
        assert!((h.temp - 4.0).abs() < 0.1, "temp {}", h.temp);
    }

    #[test]
    fn req_hel_02_abierta_sube_al_ambiente_tres_veces_mas_lento() {
        let mut abierta = Heladera { temp: 4.0, abierta: true, enchufada: true };
        let mut cerrada = Heladera { temp: 20.0, abierta: false, enchufada: true };
        abierta.paso(1.0);
        cerrada.paso(1.0);
        let sube = abierta.temp - 4.0; // (20-4)*K_ABIERTA
        let baja = 20.0 - cerrada.temp; // (20-4)*K_FRIA
        assert!((baja / sube - 3.0).abs() < 1e-3, "baja {baja} sube {sube}");
        for _ in 0..5000 {
            abierta.paso(1.0);
        }
        assert!((abierta.temp - 20.0).abs() < 0.2);
    }

    #[test]
    fn req_hel_02_desenchufada_tambien_se_calienta() {
        let mut h = Heladera { temp: 4.0, abierta: false, enchufada: false };
        h.paso(10.0);
        assert!(h.temp > 4.0);
    }

    #[test]
    fn req_hel_03_no_baja_bajo_8_grados() {
        let mut f = Frescura::default();
        for _ in 0..100_000 {
            f.paso(4.0, 1.0);
            f.paso(8.0, 1.0);
        }
        assert_eq!(f.porcentaje, 100.0);
    }

    #[test]
    fn req_hel_03_a_20_grados_baja_024_por_segundo() {
        let mut f = Frescura::default();
        f.paso(20.0, 10.0);
        assert!((f.porcentaje - (100.0 - 12.0 * 0.02 * 10.0)).abs() < 1e-4);
    }

    #[test]
    fn req_hel_03_nunca_sube_y_bien_cocinada_no_baja() {
        let mut f = Frescura { porcentaje: 50.0 };
        f.paso(4.0, 1000.0);
        assert_eq!(f.porcentaje, 50.0);
        f.paso(200.0, 1000.0);
        assert_eq!(f.porcentaje, 50.0, "cocinando no se echa a perder ni se recupera");
    }

    #[test]
    fn req_hel_03_al_sol_del_mediodia_se_echa_a_perder_en_horas_de_juego() {
        // A 20 °C: 0,24 %/s → 100 % en ~417 s ≈ 7 horas de juego a 1 min/s.
        let mut f = Frescura::default();
        let mut s = 0.0;
        while !f.echada_a_perder() && s < 10_000.0 {
            f.paso(20.0, 1.0);
            s += 1.0;
        }
        assert!((400.0..=430.0).contains(&s), "se echó a perder a los {s} s");
    }

    #[test]
    fn req_hel_04_dudosa_bajo_40_y_echada_en_cero() {
        assert!(!Frescura { porcentaje: 40.0 }.dudosa());
        let f = Frescura { porcentaje: 39.9 };
        assert!(f.dudosa() && !f.echada_a_perder() && f.verdor() > 0.0);
        assert!(f.texto().unwrap().contains("echando"));
        let e = Frescura { porcentaje: 0.0 };
        assert!(e.echada_a_perder());
        assert_eq!(e.verdor(), 1.0);
        assert_eq!(e.texto().as_deref(), Some("echada a perder"));
        assert_eq!(Frescura::default().texto(), None);
        assert_eq!(Frescura::default().verdor(), 0.0);
    }

    #[test]
    fn req_hel_05_comida_en_la_heladera_toma_su_temperatura_interior() {
        // El alimento sigue la temperatura del interior (ley de enfriamiento de SPEC-003).
        let mut e = crate::coccion::EstadoCoccion::default();
        let p = crate::lados::perfil_hamburguesa();
        for _ in 0..600 {
            e.paso(&p, TEMP_INTERIOR, 1.0);
        }
        assert!((e.temp - 4.0).abs() < 0.5, "temp {}", e.temp);
        assert_eq!(e.avance, 0.0, "enfriada no se cocina");
    }

    #[test]
    fn req_hel_06_el_paquete_vuelve_al_ambiente_en_el_estante() {
        let mut t = TEMP_INTERIOR;
        // Superar 8 °C lleva unas horas de juego, no segundos.
        let mut s = 0.0;
        while t < TEMP_SEGURA {
            t = acercar(t, TEMP_AMBIENTE, K_PAQUETE, 1.0);
            s += 1.0;
        }
        assert!((120.0..=400.0).contains(&s), "tardó {s} s en pasar los 8 °C");
        for _ in 0..10_000 {
            t = acercar(t, TEMP_AMBIENTE, K_PAQUETE, 1.0);
        }
        assert!((t - 20.0).abs() < 0.1);
    }

    #[test]
    fn req_hel_07_servir_con_frescura_dudosa_descuenta_una_estrella() {
        use crate::clientes::{Entregado, Pedido, evaluar};
        use crate::coccion::Punto;
        let ped = Pedido { producto: "hamburguesa".into(), aderezos: vec![] };
        let e = |fr: f32| Entregado {
            producto: "hamburguesa".into(),
            punto: Some(Punto::Cocido),
            pan: None,
            frescura: Some(fr),
            aderezos: vec![],
        };
        let fresca = evaluar(&ped, &e(100.0), 16.0, 0.0).unwrap().estrellas;
        let dudosa = evaluar(&ped, &e(30.0), 16.0, 0.0).unwrap().estrellas;
        assert_eq!(fresca, 5.0);
        assert_eq!(dudosa, 4.0);
    }

    #[test]
    fn req_hel_04_echada_a_perder_se_rechaza() {
        use crate::clientes::{Entregado, Pedido, Rechazo, evaluar};
        use crate::coccion::Punto;
        let ped = Pedido { producto: "hamburguesa".into(), aderezos: vec![] };
        let e = Entregado {
            producto: "hamburguesa".into(),
            punto: Some(Punto::Cocido),
            pan: None,
            frescura: Some(0.0),
            aderezos: vec![],
        };
        assert_eq!(evaluar(&ped, &e, 16.0, 0.0), Err(Rechazo::EchadaAPerder));
    }
}
