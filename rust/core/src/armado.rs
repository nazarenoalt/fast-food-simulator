//! SPEC-005 · Armado de comida.

use serde::Deserialize;

/// Regla `base + agregado → resultado`. REQ-ARM-01
#[derive(Debug, Clone, PartialEq, Eq, Deserialize)]
pub struct Combinacion {
    pub base: String,
    pub agregado: String,
    pub resultado: String,
}

/// Devuelve el producto resultante, o `None` si la combinación no es válida. REQ-ARM-01, REQ-ARM-04
pub fn combinar<'a>(reglas: &'a [Combinacion], base: &str, agregado: &str) -> Option<&'a str> {
    reglas.iter().find(|r| r.base == base && r.agregado == agregado).map(|r| r.resultado.as_str())
}

/// ¿Este producto puede recibir algo encima? (para saber si necesita zona de encastre). REQ-ARM-02
pub fn es_base(reglas: &[Combinacion], producto: &str) -> bool {
    reglas.iter().any(|r| r.base == producto)
}

/// REQ-ARM-05: la masa del resultado es la suma.
pub fn masa_combinada(base: f32, agregado: f32) -> f32 {
    base + agregado
}

#[cfg(test)]
mod tests {
    use super::*;

    fn reglas() -> Vec<Combinacion> {
        vec![Combinacion { base: "pan_pancho".into(), agregado: "salchicha".into(), resultado: "pancho".into() }]
    }

    #[test]
    fn req_arm_01_pan_mas_salchicha_es_pancho() {
        assert_eq!(combinar(&reglas(), "pan_pancho", "salchicha"), Some("pancho"));
    }

    #[test]
    fn req_arm_02_el_pan_es_base_la_salchicha_no() {
        assert!(es_base(&reglas(), "pan_pancho"));
        assert!(!es_base(&reglas(), "salchicha"));
    }

    #[test]
    fn req_arm_04_combinaciones_invalidas_no_hacen_nada() {
        assert_eq!(combinar(&reglas(), "salchicha", "salchicha"), None);
        assert_eq!(combinar(&reglas(), "salchicha", "pan_pancho"), None);
    }

    #[test]
    fn req_arm_05_masa_suma() {
        assert_eq!(masa_combinada(0.04, 0.05), 0.09);
    }
}
