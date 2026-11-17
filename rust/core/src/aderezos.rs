//! SPEC-012 · Aderezos y pomos.

use serde::Deserialize;

/// REQ-ADE-01
#[derive(Debug, Clone, PartialEq, Deserialize)]
pub struct DefAderezo {
    pub id: String,
    pub nombre: String,
    pub color: [f32; 3],
    pub usos: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ErrorAderezo {
    NoAdmite,
    YaTiene,
    Vacio,
    RepuestoDistinto,
    YaLleno,
}

impl ErrorAderezo {
    pub fn mensaje(&self) -> &'static str {
        match self {
            ErrorAderezo::NoAdmite => "Esto no lleva aderezos",
            ErrorAderezo::YaTiene => "Ya tiene ese aderezo",
            ErrorAderezo::Vacio => "El pomo está vacío",
            ErrorAderezo::RepuestoDistinto => "Ese repuesto no es de este aderezo",
            ErrorAderezo::YaLleno => "El pomo ya está lleno",
        }
    }
}

/// Un pomo concreto. REQ-ADE-02
#[derive(Debug, Clone, PartialEq)]
pub struct Pomo {
    pub aderezo: String,
    pub usos: u32,
    pub max: u32,
}

impl Pomo {
    pub fn lleno(def: &DefAderezo) -> Self {
        Self { aderezo: def.id.clone(), usos: def.usos, max: def.usos }
    }

    /// 0 = vacío, 1 = lleno. REQ-ADE-02
    pub fn nivel(&self) -> f32 {
        if self.max == 0 { 0.0 } else { self.usos as f32 / self.max as f32 }
    }

    /// REQ-ADE-03, REQ-ADE-04: pone este aderezo en `puestos` (lista del producto).
    pub fn aplicar(&mut self, admite: bool, puestos: &mut Vec<String>) -> Result<(), ErrorAderezo> {
        if !admite {
            return Err(ErrorAderezo::NoAdmite);
        }
        if puestos.contains(&self.aderezo) {
            return Err(ErrorAderezo::YaTiene);
        }
        if self.usos == 0 {
            return Err(ErrorAderezo::Vacio);
        }
        self.usos -= 1;
        puestos.push(self.aderezo.clone());
        Ok(())
    }

    /// REQ-ADE-05: un repuesto del mismo aderezo lo llena.
    pub fn recargar(&mut self, repone: &str) -> Result<(), ErrorAderezo> {
        if repone != self.aderezo {
            return Err(ErrorAderezo::RepuestoDistinto);
        }
        if self.usos == self.max {
            return Err(ErrorAderezo::YaLleno);
        }
        self.usos = self.max;
        Ok(())
    }

    /// REQ-ADE-06
    pub fn cartel(&self, nombre: &str) -> String {
        format!("{} ({}/{})", capitalizar(nombre), self.usos, self.max)
    }
}

/// "mostaza", "mostaza y ketchup", "mostaza, ketchup y mayonesa".
pub fn enumerar(nombres: &[String]) -> String {
    match nombres.len() {
        0 => String::new(),
        1 => nombres[0].clone(),
        n => format!("{} y {}", nombres[..n - 1].join(", "), nombres[n - 1]),
    }
}

pub fn capitalizar(s: &str) -> String {
    let mut c = s.chars();
    match c.next() {
        Some(f) => f.to_uppercase().collect::<String>() + c.as_str(),
        None => String::new(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn mostaza() -> DefAderezo {
        DefAderezo { id: "mostaza".into(), nombre: "mostaza".into(), color: [0.9, 0.7, 0.1], usos: 40 }
    }

    #[test]
    fn req_ade_02_nivel() {
        let mut p = Pomo::lleno(&mostaza());
        assert_eq!(p.nivel(), 1.0);
        p.usos = 10;
        assert_eq!(p.nivel(), 0.25);
    }

    #[test]
    fn req_ade_03_aplicar_gasta_un_uso() {
        let mut p = Pomo::lleno(&mostaza());
        let mut puestos = vec![];
        p.aplicar(true, &mut puestos).unwrap();
        assert_eq!(puestos, vec!["mostaza".to_string()]);
        assert_eq!(p.usos, 39);
    }

    #[test]
    fn req_ade_04_no_repetir_ni_vacio_ni_productos_sin_aderezo() {
        let mut p = Pomo::lleno(&mostaza());
        let mut puestos = vec!["mostaza".to_string()];
        assert_eq!(p.aplicar(true, &mut puestos), Err(ErrorAderezo::YaTiene));
        assert_eq!(p.aplicar(false, &mut vec![]), Err(ErrorAderezo::NoAdmite));
        p.usos = 0;
        assert_eq!(p.aplicar(true, &mut vec![]), Err(ErrorAderezo::Vacio));
        assert_eq!(p.usos, 0);
    }

    #[test]
    fn req_ade_05_recargar() {
        let mut p = Pomo::lleno(&mostaza());
        assert_eq!(p.recargar("mostaza"), Err(ErrorAderezo::YaLleno));
        p.usos = 3;
        assert_eq!(p.recargar("ketchup"), Err(ErrorAderezo::RepuestoDistinto));
        p.recargar("mostaza").unwrap();
        assert_eq!(p.usos, 40);
    }

    #[test]
    fn req_ade_06_cartel() {
        let mut p = Pomo::lleno(&mostaza());
        p.usos = 32;
        assert_eq!(p.cartel("mostaza"), "Mostaza (32/40)");
    }

    #[test]
    fn enumerar_en_castellano() {
        let v = |x: &[&str]| x.iter().map(|s| s.to_string()).collect::<Vec<_>>();
        assert_eq!(enumerar(&v(&["mostaza"])), "mostaza");
        assert_eq!(enumerar(&v(&["mostaza", "ketchup"])), "mostaza y ketchup");
        assert_eq!(enumerar(&v(&["a", "b", "c"])), "a, b y c");
    }
}
