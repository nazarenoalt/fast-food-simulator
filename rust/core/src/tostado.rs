//! SPEC-015 · Pan tostado: mismas fórmulas de cocción por lados, con otros valores y otros nombres.

use crate::coccion::{PerfilCoccion, Punto};
use crate::lados::CoccionLados;

/// REQ-PAR-06
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum EstadoPan {
    Blando,
    Tostado,
    Quemado,
}

impl EstadoPan {
    pub fn nombre(self) -> &'static str {
        match self {
            EstadoPan::Blando => "blando",
            EstadoPan::Tostado => "tostado",
            EstadoPan::Quemado => "quemado",
        }
    }
}

/// REQ-PAR-06: estado de un lado según su punto (el "pasado" del perfil es el pan quemado).
pub fn estado_lado(p: Punto) -> EstadoPan {
    match p {
        Punto::Crudo => EstadoPan::Blando,
        Punto::Cocido => EstadoPan::Tostado,
        Punto::Pasado | Punto::Quemado => EstadoPan::Quemado,
    }
}

/// REQ-PAR-06, REQ-PAR-07: el pan está Quemado si alguna cara se quemó; si no, Tostado si al
/// menos una cara se tostó; si no, Blando.
pub fn estado_pan(lados: &CoccionLados, perfil: &PerfilCoccion) -> EstadoPan {
    let e = [estado_lado(lados.lados[0].punto(perfil)), estado_lado(lados.lados[1].punto(perfil))];
    if e.contains(&EstadoPan::Quemado) {
        EstadoPan::Quemado
    } else if e.contains(&EstadoPan::Tostado) {
        EstadoPan::Tostado
    } else {
        EstadoPan::Blando
    }
}

/// Mismos valores que `pan_choripan` en godot/data/productos.ron (lo verifica un test de datos).
#[cfg(test)]
pub(crate) fn perfil_pan() -> PerfilCoccion {
    PerfilCoccion {
        k: 0.15,
        t_min: 90.0,
        velocidad: 0.0020,
        punto: 4.0,
        pasado: 15.0,
        t_quemado: 1000.0,
        segundos_quemado: 1000.0,
        color_crudo: [0.9, 0.76, 0.52],
        color_cocido: [0.72, 0.46, 0.2],
        color_pasado: [0.16, 0.1, 0.07],
        color_quemado: [0.16, 0.1, 0.07],
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    const DT: f32 = 1.0 / 60.0;

    fn con_avance(a: f32, b: f32) -> CoccionLados {
        let mut c = CoccionLados::default();
        c.lados[0].avance = a;
        c.lados[1].avance = b;
        c
    }

    #[test]
    fn req_par_06_estados_del_pan() {
        let p = perfil_pan();
        assert_eq!(estado_pan(&con_avance(0.0, 0.0), &p), EstadoPan::Blando);
        assert_eq!(estado_pan(&con_avance(4.0, 0.0), &p), EstadoPan::Tostado, "una cara alcanza");
        assert_eq!(estado_pan(&con_avance(4.0, 14.0), &p), EstadoPan::Tostado);
        assert_eq!(estado_pan(&con_avance(15.0, 4.0), &p), EstadoPan::Quemado, "una cara quemada lo quema");
    }

    #[test]
    fn req_par_06_cada_cara_tiene_su_color() {
        let p = perfil_pan();
        let c = con_avance(4.0, 0.0);
        assert_eq!(c.color(&p, 0), p.color_cocido);
        assert_eq!(c.color(&p, 1), p.color_crudo);
    }

    #[test]
    fn req_par_06_en_parrilla_a_250_se_tuesta_y_despues_se_quema() {
        let p = perfil_pan();
        let mut c = CoccionLados::default();
        let (mut tostado, mut quemado) = (None, None);
        let mut t = 0.0;
        while t < 300.0 && quemado.is_none() {
            c.paso(&p, 0, 250.0, 20.0, DT);
            t += DT;
            match estado_pan(&c, &p) {
                EstadoPan::Tostado if tostado.is_none() => tostado = Some(t),
                EstadoPan::Quemado => quemado = Some(t),
                _ => {}
            }
        }
        let (tostado, quemado) = (tostado.expect("nunca se tostó"), quemado.expect("nunca se quemó"));
        assert!((5.0..=30.0).contains(&tostado), "tostado a los {tostado} s");
        assert!(quemado > tostado + 10.0, "quemado a los {quemado} s");
        assert_eq!(c.lados[1].avance, 0.0, "la cara de arriba sigue blanda");
    }
}
