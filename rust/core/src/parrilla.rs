//! SPEC-015 · Parrilla de carbón (fuente de calor que gasta combustible).

use crate::TEMP_AMBIENTE;

/// Carbón máximo que entra en la parrilla (kg). REQ-PAR-01
pub const CARBON_MAX: f32 = 3.0;
/// Carbón que se gasta encendida, por hora de juego (kg). REQ-PAR-02
pub const GASTO_KG_POR_HORA: f32 = 0.25;
/// Subida de las brasas por segundo (°C/s). REQ-PAR-02
pub const SUBIDA_POR_SEGUNDO: f32 = 3.0;
/// Qué tan rápido se enfría (1/s). REQ-PAR-03
pub const K_ENFRIADO: f32 = 0.004;

/// REQ-PAR-02: temperatura máxima según el carbón que queda: 320 °C con 1 kg o más.
pub fn temp_max(carbon: f32) -> f32 {
    TEMP_AMBIENTE + 300.0 * carbon.clamp(0.0, 1.0)
}

/// REQ-PAR-03: cuánto brillan las brasas (0 = apagadas, 1 = al rojo vivo) según su temperatura.
pub fn resplandor(temp: f32) -> f32 {
    ((temp - 100.0) / 220.0).clamp(0.0, 1.0)
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ErrorParrilla {
    /// La bolsa no entra: se pasaría de 3 kg.
    NoEntra,
    /// No se puede encender sin carbón.
    SinCarbon,
}

impl ErrorParrilla {
    pub fn mensaje(&self) -> &'static str {
        match self {
            ErrorParrilla::NoEntra => "No entra tanto carbón",
            ErrorParrilla::SinCarbon => "No tiene carbón",
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Parrilla {
    /// kg de carbón cargado.
    pub carbon: f32,
    pub temp: f32,
    pub encendida: bool,
}

impl Default for Parrilla {
    fn default() -> Self {
        Self { carbon: 0.0, temp: TEMP_AMBIENTE, encendida: false }
    }
}

impl Parrilla {
    /// REQ-PAR-01: carga `kg` de carbón; si se pasa del máximo, no entra y no se pierde nada.
    pub fn cargar(&mut self, kg: f32) -> Result<(), ErrorParrilla> {
        if self.carbon + kg > CARBON_MAX + 1e-4 {
            return Err(ErrorParrilla::NoEntra);
        }
        self.carbon += kg;
        Ok(())
    }

    /// REQ-PAR-01: se enciende solo si tiene carbón.
    pub fn alternar(&mut self) -> Result<(), ErrorParrilla> {
        if !self.encendida && self.carbon <= 0.0 {
            return Err(ErrorParrilla::SinCarbon);
        }
        self.encendida = !self.encendida;
        Ok(())
    }

    /// Avanza `dt` segundos reales, que son `horas` horas de juego (REQ-PAR-02).
    pub fn paso(&mut self, dt: f32, horas: f32) {
        if self.encendida {
            // REQ-PAR-02: el carbón se gasta; sin carbón se apaga sola.
            self.carbon = (self.carbon - GASTO_KG_POR_HORA * horas).max(0.0);
            if self.carbon <= 0.0 {
                self.encendida = false;
            }
        }
        // Encendida, las brasas apuntan a la temperatura máxima; si no, al ambiente.
        let destino = if self.encendida { temp_max(self.carbon) } else { TEMP_AMBIENTE };
        if self.temp < destino && self.encendida {
            self.temp = (self.temp + SUBIDA_POR_SEGUNDO * dt).min(destino);
        } else {
            // REQ-PAR-03: se enfría hacia el destino de forma gradual.
            self.temp += (destino - self.temp) * (K_ENFRIADO * dt).min(1.0);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::plancha::entorno_por_lados;

    #[test]
    fn req_par_01_se_carga_hasta_3_kg_y_no_se_pasa() {
        let mut p = Parrilla::default();
        assert_eq!(p.cargar(1.0), Ok(()));
        assert_eq!(p.cargar(2.0), Ok(()));
        assert_eq!(p.carbon, 3.0);
        assert_eq!(p.cargar(1.0), Err(ErrorParrilla::NoEntra));
        assert_eq!(p.carbon, 3.0, "lo que no entra no se pierde ni se suma");
    }

    #[test]
    fn req_par_01_solo_se_enciende_con_carbon() {
        let mut p = Parrilla::default();
        assert_eq!(p.alternar(), Err(ErrorParrilla::SinCarbon));
        assert!(!p.encendida);
        p.cargar(1.0).unwrap();
        assert_eq!(p.alternar(), Ok(()));
        assert!(p.encendida);
        assert_eq!(p.alternar(), Ok(()), "se puede apagar");
        assert!(!p.encendida);
    }

    #[test]
    fn req_par_02_temperatura_maxima_segun_el_carbon() {
        assert_eq!(temp_max(0.0), 20.0);
        assert_eq!(temp_max(0.5), 170.0);
        assert_eq!(temp_max(1.0), 320.0);
        assert_eq!(temp_max(3.0), 320.0);
    }

    #[test]
    fn req_par_02_sube_3_grados_por_segundo() {
        let mut p = Parrilla::default();
        p.cargar(2.0).unwrap();
        p.alternar().unwrap();
        p.paso(10.0, 0.0);
        assert!((p.temp - 50.0).abs() < 1e-4);
    }

    #[test]
    fn req_par_02_gasta_un_cuarto_de_kilo_por_hora_de_juego() {
        let mut p = Parrilla::default();
        p.cargar(2.0).unwrap();
        p.alternar().unwrap();
        // Una hora de juego (60 s a 1 min/s) en pasos de 1 s.
        for _ in 0..60 {
            p.paso(1.0, 1.0 / 60.0);
        }
        assert!((p.carbon - 1.75).abs() < 1e-3, "quedan {} kg", p.carbon);
    }

    #[test]
    fn req_par_02_sin_carbon_se_apaga_sola() {
        let mut p = Parrilla::default();
        p.cargar(0.5).unwrap();
        p.alternar().unwrap();
        // 0,5 kg duran 2 horas de juego.
        for _ in 0..(2 * 60 - 5) {
            p.paso(1.0, 1.0 / 60.0);
        }
        assert!(p.encendida && p.carbon > 0.0);
        for _ in 0..10 {
            p.paso(1.0, 1.0 / 60.0);
        }
        assert_eq!(p.carbon, 0.0);
        assert!(!p.encendida);
    }

    #[test]
    fn req_par_02_con_poco_carbon_no_llega_tan_alto() {
        let mut p = Parrilla::default();
        p.cargar(0.5).unwrap();
        p.alternar().unwrap();
        // Poco tiempo de juego (no se gasta casi nada): las brasas frenan en T_max.
        for _ in 0..600 {
            p.paso(1.0, 0.0);
        }
        assert!((p.temp - 170.0).abs() < 1e-3, "temp {}", p.temp);
    }

    #[test]
    fn req_par_03_apagada_se_enfria_hacia_el_ambiente() {
        let mut p = Parrilla { carbon: 1.0, temp: 300.0, encendida: false };
        p.paso(1.0, 0.0);
        assert!(p.temp < 300.0 && p.temp > 295.0);
        for _ in 0..10_000 {
            p.paso(1.0, 0.0);
        }
        assert!((p.temp - 20.0).abs() < 0.5);
        assert_eq!(p.carbon, 1.0, "apagada no gasta carbón");
    }

    #[test]
    fn req_par_03_el_resplandor_sigue_la_temperatura() {
        assert_eq!(resplandor(20.0), 0.0);
        assert!(resplandor(200.0) > 0.3 && resplandor(200.0) < 0.6);
        assert_eq!(resplandor(320.0), 1.0);
    }

    #[test]
    fn req_par_04_el_alimento_toma_la_temperatura_de_la_parrilla_por_abajo() {
        assert_eq!(entorno_por_lados(Some(250.0)), (250.0, 20.0));
    }
}
