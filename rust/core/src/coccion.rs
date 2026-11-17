//! SPEC-003 · Cocción.

use serde::Deserialize;

use crate::TEMP_AMBIENTE;

/// Cómo se cocina un alimento. Valores en `godot/data/productos.ron`.
#[derive(Debug, Clone, PartialEq, Deserialize)]
pub struct PerfilCoccion {
    /// Qué tan rápido toma la temperatura del entorno (1/s). REQ-COC-02
    pub k: f32,
    /// Temperatura desde la que empieza a cocinarse (°C). REQ-COC-03
    pub t_min: f32,
    /// Avance por grado por encima de t_min por segundo. REQ-COC-03
    pub velocidad: f32,
    /// Avance a partir del cual está cocido. REQ-COC-04
    pub punto: f32,
    /// Avance a partir del cual está pasado. REQ-COC-04
    pub pasado: f32,
    /// Temperatura a partir de la cual se quema (°C). REQ-COC-04
    pub t_quemado: f32,
    /// Segundos acumulados sobre t_quemado para quemarse. REQ-COC-04
    pub segundos_quemado: f32,
    pub color_crudo: [f32; 3],
    pub color_cocido: [f32; 3],
    pub color_pasado: [f32; 3],
    pub color_quemado: [f32; 3],
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Punto {
    Crudo,
    Cocido,
    Pasado,
    Quemado,
}

impl Punto {
    /// Igual que `nombre`, en masculino (chorizo, pan).
    pub fn nombre_masculino(self) -> &'static str {
        match self {
            Punto::Crudo => "crudo",
            Punto::Cocido => "cocido",
            Punto::Pasado => "pasado",
            Punto::Quemado => "quemado",
        }
    }

    /// Para mostrar en pantalla (femenino/masculino lo maneja quien lo muestra).
    pub fn nombre(self) -> &'static str {
        match self {
            Punto::Crudo => "cruda",
            Punto::Cocido => "cocida",
            Punto::Pasado => "pasada",
            Punto::Quemado => "quemada",
        }
    }
}

/// Estado de cocción de un alimento concreto.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct EstadoCoccion {
    pub temp: f32,
    pub avance: f32,
    pub segundos_sobre_quemado: f32,
    pub quemado: bool,
}

impl Default for EstadoCoccion {
    // REQ-COC-01: arranca a temperatura ambiente y sin cocción.
    fn default() -> Self {
        Self { temp: TEMP_AMBIENTE, avance: 0.0, segundos_sobre_quemado: 0.0, quemado: false }
    }
}

impl EstadoCoccion {
    /// Avanza `dt` segundos con el alimento expuesto a `t_entorno`.
    pub fn paso(&mut self, perfil: &PerfilCoccion, t_entorno: f32, dt: f32) {
        // REQ-COC-02: ley de enfriamiento de Newton. Se limita el factor a 1 para no "pasarse"
        // con pasos de tiempo grandes.
        let factor = (perfil.k * dt).min(1.0);
        self.temp += (t_entorno - self.temp) * factor;

        // REQ-COC-03: solo avanza por encima de t_min, más rápido cuanto más caliente; no retrocede.
        if self.temp > perfil.t_min {
            self.avance += (self.temp - perfil.t_min) * perfil.velocidad * dt;
        }

        // REQ-COC-04: quemado por tiempo acumulado sobre la temperatura de quemado; definitivo.
        if self.temp > perfil.t_quemado {
            self.segundos_sobre_quemado += dt;
            if self.segundos_sobre_quemado >= perfil.segundos_quemado {
                self.quemado = true;
            }
        }
    }

    /// REQ-COC-04
    pub fn punto(&self, perfil: &PerfilCoccion) -> Punto {
        if self.quemado {
            Punto::Quemado
        } else if self.avance >= perfil.pasado {
            Punto::Pasado
        } else if self.avance >= perfil.punto {
            Punto::Cocido
        } else {
            Punto::Crudo
        }
    }

    /// REQ-COC-06: color continuo según el avance.
    pub fn color(&self, perfil: &PerfilCoccion) -> [f32; 3] {
        if self.quemado {
            return perfil.color_quemado;
        }
        if self.avance < perfil.punto {
            mezclar(perfil.color_crudo, perfil.color_cocido, self.avance / perfil.punto)
        } else {
            let t = (self.avance - perfil.punto) / (perfil.pasado - perfil.punto);
            mezclar(perfil.color_cocido, perfil.color_pasado, t)
        }
    }
}

pub fn mezclar(a: [f32; 3], b: [f32; 3], t: f32) -> [f32; 3] {
    let t = t.clamp(0.0, 1.0);
    [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t]
}

#[cfg(test)]
pub(crate) fn perfil_salchicha() -> PerfilCoccion {
    // Mismos valores que godot/data/productos.ron (el test de datos verifica que coincidan).
    PerfilCoccion {
        k: 0.06,
        t_min: 55.0,
        velocidad: 0.0025,
        punto: 3.0,
        pasado: 13.0,
        t_quemado: 180.0,
        segundos_quemado: 20.0,
        color_crudo: [0.93, 0.55, 0.5],
        color_cocido: [0.72, 0.3, 0.2],
        color_pasado: [0.5, 0.22, 0.14],
        color_quemado: [0.12, 0.08, 0.06],
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    const DT: f32 = 1.0 / 60.0;

    /// Simula hasta que llega al punto pedido o pasan `max_s` segundos. Devuelve los segundos.
    fn segundos_hasta(p: &PerfilCoccion, t_entorno: f32, objetivo: Punto, max_s: f32) -> Option<f32> {
        let mut e = EstadoCoccion::default();
        let mut t = 0.0;
        while t < max_s {
            e.paso(p, t_entorno, DT);
            t += DT;
            if e.punto(p) == objetivo {
                return Some(t);
            }
        }
        None
    }

    #[test]
    fn req_coc_01_arranca_ambiente_y_crudo() {
        let e = EstadoCoccion::default();
        assert_eq!(e.temp, 20.0);
        assert_eq!(e.avance, 0.0);
        assert_eq!(e.punto(&perfil_salchicha()), Punto::Crudo);
    }

    #[test]
    fn req_coc_02_se_acerca_gradualmente_al_entorno() {
        let p = perfil_salchicha();
        let mut e = EstadoCoccion::default();
        e.paso(&p, 95.0, 1.0);
        // ΔT = (95-20) * 0.06 * 1 = 4.5
        assert!((e.temp - 24.5).abs() < 1e-4);
        for _ in 0..600 {
            e.paso(&p, 95.0, DT);
        }
        assert!(e.temp < 95.0 && e.temp > 24.5);
        // Fuera del calor se enfría hacia el ambiente.
        let antes = e.temp;
        e.paso(&p, 20.0, 1.0);
        assert!(e.temp < antes);
    }

    #[test]
    fn req_coc_03_no_avanza_bajo_t_min_y_no_retrocede() {
        let p = perfil_salchicha();
        let mut e = EstadoCoccion::default();
        for _ in 0..6000 {
            e.paso(&p, 50.0, DT); // nunca supera 55
        }
        assert_eq!(e.avance, 0.0);

        e.temp = 90.0;
        e.paso(&p, 90.0, 1.0);
        let a = e.avance;
        assert!(a > 0.0);
        e.paso(&p, 0.0, 10.0); // se enfría
        assert!(e.avance >= a);
    }

    #[test]
    fn req_coc_03_mas_caliente_cocina_mas_rapido() {
        let p = perfil_salchicha();
        let mut a = EstadoCoccion { temp: 70.0, ..Default::default() };
        let mut b = EstadoCoccion { temp: 90.0, ..Default::default() };
        a.paso(&p, 70.0, 1.0);
        b.paso(&p, 90.0, 1.0);
        assert!(b.avance > a.avance);
    }

    #[test]
    fn req_coc_04_estados_y_quemado_definitivo() {
        let p = perfil_salchicha();
        let mut e = EstadoCoccion::default();
        e.avance = 3.0;
        assert_eq!(e.punto(&p), Punto::Cocido);
        e.avance = 13.0;
        assert_eq!(e.punto(&p), Punto::Pasado);

        let mut q = EstadoCoccion { temp: 250.0, ..Default::default() };
        for _ in 0..(25 * 60) {
            q.paso(&p, 250.0, DT);
        }
        assert_eq!(q.punto(&p), Punto::Quemado);
        for _ in 0..(600 * 60) {
            q.paso(&p, 20.0, DT);
        }
        assert_eq!(q.punto(&p), Punto::Quemado);
    }

    #[test]
    fn req_coc_05_salchicha_en_hervidor() {
        let p = perfil_salchicha();
        let cocida = segundos_hasta(&p, 95.0, Punto::Cocido, 600.0).expect("nunca se cocinó");
        assert!((30.0..=90.0).contains(&cocida), "cocida a los {cocida} s");
        let pasada = segundos_hasta(&p, 95.0, Punto::Pasado, 1200.0).expect("nunca se pasó");
        assert!(pasada > 150.0, "pasada a los {pasada} s");
        // En agua nunca se quema.
        assert_eq!(segundos_hasta(&p, 95.0, Punto::Quemado, 3600.0), None);
    }

    #[test]
    fn req_coc_06_color_continuo() {
        let p = perfil_salchicha();
        let mut e = EstadoCoccion::default();
        assert_eq!(e.color(&p), p.color_crudo);
        e.avance = 1.5;
        let medio = e.color(&p);
        assert!(medio[0] < p.color_crudo[0] && medio[0] > p.color_cocido[0]);
        e.avance = 3.0;
        assert_eq!(e.color(&p), p.color_cocido);
        e.quemado = true;
        assert_eq!(e.color(&p), p.color_quemado);
    }
}
