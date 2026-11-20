//! SPEC-014 · Cocción por lados (hamburguesa, y después chorizo y pan).

use crate::coccion::{EstadoCoccion, PerfilCoccion, Punto};

/// Un alimento con dos lados, cada uno con su propia temperatura y avance. REQ-PLA-04
/// El lado 0 es el de abajo en reposo; el 1, el de arriba.
#[derive(Debug, Clone, Copy, PartialEq, Default)]
pub struct CoccionLados {
    pub lados: [EstadoCoccion; 2],
}

impl CoccionLados {
    /// Avanza `dt` segundos. `abajo` es el lado que mira hacia abajo (REQ-PLA-07);
    /// cada lado toma su propio entorno (REQ-PLA-03). Mismas fórmulas que REQ-COC-02/03.
    pub fn paso(&mut self, perfil: &PerfilCoccion, abajo: usize, t_abajo: f32, t_arriba: f32, dt: f32) {
        let arriba = 1 - abajo;
        self.lados[abajo].paso(perfil, t_abajo, dt);
        self.lados[arriba].paso(perfil, t_arriba, dt);
    }

    /// REQ-PLA-05: el más grave de los dos lados (Quemado, Pasado, Crudo, Cocido).
    pub fn punto(&self, perfil: &PerfilCoccion) -> Punto {
        let p = [self.lados[0].punto(perfil), self.lados[1].punto(perfil)];
        for grave in [Punto::Quemado, Punto::Pasado, Punto::Crudo] {
            if p.contains(&grave) {
                return grave;
            }
        }
        Punto::Cocido
    }

    /// REQ-PLA-05: color propio de cada lado.
    pub fn color(&self, perfil: &PerfilCoccion, lado: usize) -> [f32; 3] {
        self.lados[lado].color(perfil)
    }

    /// Texto de cada lado, ej. "abajo cocida, arriba cruda".
    pub fn descripcion(&self, perfil: &PerfilCoccion, abajo: usize) -> String {
        format!(
            "abajo {}, arriba {}",
            self.lados[abajo].punto(perfil).nombre(),
            self.lados[1 - abajo].punto(perfil).nombre()
        )
    }
}

/// Mismos valores que `hamburguesa` en godot/data/productos.ron (lo verifica un test de datos).
#[cfg(test)]
pub(crate) fn perfil_hamburguesa() -> PerfilCoccion {
    PerfilCoccion {
        k: 0.03,
        t_min: 60.0,
        velocidad: 0.0012,
        punto: 6.0,
        pasado: 14.0,
        t_quemado: 210.0,
        segundos_quemado: 15.0,
        color_crudo: [0.62, 0.3, 0.27],
        color_cocido: [0.45, 0.25, 0.14],
        color_pasado: [0.3, 0.17, 0.1],
        color_quemado: [0.1, 0.07, 0.06],
    }
}

/// Mismos valores que `chorizo` en godot/data/productos.ron (lo verifica un test de datos).
#[cfg(test)]
pub(crate) fn perfil_chorizo() -> PerfilCoccion {
    PerfilCoccion {
        k: 0.05,
        t_min: 60.0,
        velocidad: 0.0012,
        punto: 7.0,
        pasado: 18.0,
        t_quemado: 280.0,
        segundos_quemado: 60.0,
        color_crudo: [0.75, 0.3, 0.25],
        color_cocido: [0.5, 0.22, 0.14],
        color_pasado: [0.33, 0.15, 0.1],
        color_quemado: [0.1, 0.06, 0.05],
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    const DT: f32 = 1.0 / 60.0;

    /// Cuánto tarda el lado de abajo en llegar al punto pedido sobre una plancha a `plancha` °C.
    fn segundos_hasta(plancha: f32, objetivo: Punto, max_s: f32) -> Option<f32> {
        let p = perfil_hamburguesa();
        let mut c = CoccionLados::default();
        let mut t = 0.0;
        while t < max_s {
            c.paso(&p, 0, plancha, 20.0, DT);
            t += DT;
            if c.lados[0].punto(&p) == objetivo {
                return Some(t);
            }
        }
        None
    }

    #[test]
    fn req_pla_04_arranca_cruda_de_los_dos_lados() {
        let c = CoccionLados::default();
        for l in c.lados {
            assert_eq!(l.avance, 0.0);
            assert_eq!(l.temp, 20.0);
        }
        assert_eq!(c.punto(&perfil_hamburguesa()), Punto::Crudo);
    }

    #[test]
    fn req_pla_04_solo_se_cocina_el_lado_que_toca_la_plancha() {
        let p = perfil_hamburguesa();
        let mut c = CoccionLados::default();
        for _ in 0..(30 * 60) {
            c.paso(&p, 0, 200.0, 20.0, DT);
        }
        assert!(c.lados[0].avance > 0.5);
        assert_eq!(c.lados[1].avance, 0.0);
        // Dada vuelta (abajo = lado 1): el otro lado se calienta y el que quedó arriba se enfría.
        let temp_0 = c.lados[0].temp;
        for _ in 0..(30 * 60) {
            c.paso(&p, 1, 200.0, 20.0, DT);
        }
        assert!(c.lados[1].avance > 0.5);
        assert!(c.lados[1].temp > 100.0);
        assert!(c.lados[0].temp < temp_0);
    }

    #[test]
    fn req_pla_05_estado_es_el_mas_grave() {
        let p = perfil_hamburguesa();
        let mut c = CoccionLados::default();
        c.lados[0].avance = 6.0;
        assert_eq!(c.punto(&p), Punto::Crudo, "un lado crudo la deja cruda");
        c.lados[1].avance = 6.0;
        assert_eq!(c.punto(&p), Punto::Cocido);
        c.lados[1].avance = 14.0;
        assert_eq!(c.punto(&p), Punto::Pasado);
        c.lados[0].quemado = true;
        assert_eq!(c.punto(&p), Punto::Quemado);
    }

    #[test]
    fn req_pla_05_cada_lado_tiene_su_color() {
        let p = perfil_hamburguesa();
        let mut c = CoccionLados::default();
        c.lados[0].avance = 6.0;
        assert_eq!(c.color(&p, 0), p.color_cocido);
        assert_eq!(c.color(&p, 1), p.color_crudo);
    }

    #[test]
    fn req_pla_06_en_plancha_a_200_cocida_entre_40_y_90_s_y_pasada_despues_de_110() {
        let cocida = segundos_hasta(200.0, Punto::Cocido, 600.0).expect("nunca se cocinó");
        assert!((40.0..=90.0).contains(&cocida), "cocida a los {cocida} s");
        let pasada = segundos_hasta(200.0, Punto::Pasado, 600.0).expect("nunca se pasó");
        assert!(pasada > 110.0, "pasada a los {pasada} s");
        assert_eq!(segundos_hasta(200.0, Punto::Quemado, 3600.0), None, "a 200 °C no se quema");
    }

    #[test]
    fn req_pla_06_en_plancha_a_220_se_quema_despues_de_pasarse() {
        let pasada = segundos_hasta(220.0, Punto::Pasado, 600.0).expect("nunca se pasó");
        let quemada = segundos_hasta(220.0, Punto::Quemado, 600.0).expect("nunca se quemó");
        assert!(quemada > pasada, "quemada a los {quemada} s, pasada a los {pasada} s");
    }

    /// Cuánto tarda el lado de abajo del chorizo en llegar al punto pedido sobre una parrilla a `temp` °C.
    fn segundos_chorizo(temp: f32, objetivo: Punto, max_s: f32) -> Option<f32> {
        let p = perfil_chorizo();
        let mut c = CoccionLados::default();
        let mut t = 0.0;
        while t < max_s {
            c.paso(&p, 0, temp, 20.0, DT);
            t += DT;
            if c.lados[0].punto(&p) == objetivo {
                return Some(t);
            }
        }
        None
    }

    #[test]
    fn req_par_05_chorizo_a_250_cada_lado_cocido_entre_40_y_100_s() {
        let cocido = segundos_chorizo(250.0, Punto::Cocido, 600.0).expect("nunca se cocinó");
        assert!((40.0..=100.0).contains(&cocido), "cocido a los {cocido} s");
    }

    /// Chorizo en la parrilla a `temp` °C: se da vuelta cuando el lado de abajo queda Cocido y
    /// se saca cuando el otro también. Devuelve los segundos totales y cómo quedó.
    fn chorizo_dado_vuelta(temp: f32) -> (f32, CoccionLados) {
        let p = perfil_chorizo();
        let mut c = CoccionLados::default();
        let (mut t, mut abajo) = (0.0, 0);
        while t < 600.0 {
            c.paso(&p, abajo, temp, 20.0, DT);
            t += DT;
            if c.lados[abajo].punto(&p) == Punto::Cocido {
                if abajo == 1 {
                    break;
                }
                abajo = 1;
            }
        }
        (t, c)
    }

    #[test]
    fn req_par_05_chorizo_a_320_los_dos_lados_cocidos_entre_80_y_95_s() {
        let p = perfil_chorizo();
        let (t, c) = chorizo_dado_vuelta(320.0);
        assert!((80.0..=95.0).contains(&t), "los dos lados cocidos a los {t} s");
        assert_eq!(c.punto(&p), Punto::Cocido, "ni pasado ni quemado: {c:?}");
    }

    #[test]
    fn req_par_05_chorizo_se_pasa_y_a_250_no_se_quema() {
        let cocido = segundos_chorizo(250.0, Punto::Cocido, 600.0).unwrap();
        let pasado = segundos_chorizo(250.0, Punto::Pasado, 900.0).expect("nunca se pasó");
        assert!(pasado > cocido + 30.0, "pasado a los {pasado} s");
        assert_eq!(segundos_chorizo(250.0, Punto::Quemado, 900.0), None);
    }

    #[test]
    fn req_par_05_con_la_parrilla_a_tope_el_chorizo_se_quema() {
        assert!(segundos_chorizo(320.0, Punto::Quemado, 900.0).is_some());
    }

    #[test]
    fn req_par_05_solo_se_cocina_el_lado_de_abajo() {
        let p = perfil_chorizo();
        let mut c = CoccionLados::default();
        for _ in 0..(40 * 60) {
            c.paso(&p, 0, 250.0, 20.0, DT);
        }
        assert!(c.lados[0].avance > 3.0);
        assert_eq!(c.lados[1].avance, 0.0);
    }
}
