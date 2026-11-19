//! SPEC-010 · Economía: caja, reputación y estadísticas del día.

pub const SALDO_INICIAL: f32 = 120.0; // REQ-ECO-01
pub const REPUTACION_INICIAL: f32 = 3.0; // REQ-ECO-04

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct SinSaldo {
    pub falta: f32,
}

/// REQ-ECO-01, REQ-ECO-02
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Caja {
    pub saldo: f32,
}

impl Default for Caja {
    fn default() -> Self {
        Self { saldo: SALDO_INICIAL }
    }
}

impl Caja {
    pub fn cobrar(&mut self, monto: f32) {
        self.saldo += monto.max(0.0);
    }
    pub fn pagar(&mut self, monto: f32) -> Result<(), SinSaldo> {
        if monto > self.saldo {
            return Err(SinSaldo { falta: monto - self.saldo });
        }
        self.saldo -= monto;
        Ok(())
    }
}

/// REQ-ECO-04
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Reputacion(pub f32);

impl Default for Reputacion {
    fn default() -> Self {
        Self(REPUTACION_INICIAL)
    }
}

impl Reputacion {
    pub fn registrar(&mut self, estrellas: f32) {
        self.0 = (self.0 + (estrellas - self.0) * 0.1).clamp(0.0, 5.0);
    }
}

/// REQ-ECO-05
#[derive(Debug, Clone, Default, PartialEq)]
pub struct EstadisticasDia {
    pub ventas: u32,
    pub ingresos: f32,
    pub gastos: f32,
    pub atendidos: u32,
    pub perdidos: u32,
}

impl EstadisticasDia {
    pub fn venta(&mut self, monto: f32) {
        self.ventas += 1;
        self.atendidos += 1;
        self.ingresos += monto;
    }
    pub fn perdido(&mut self) {
        self.perdidos += 1;
    }
    pub fn gasto(&mut self, monto: f32) {
        self.gastos += monto;
    }
    /// REQ-TIE-09: plata que entra sin ser una venta (vender algo usado).
    pub fn ingreso(&mut self, monto: f32) {
        self.ingresos += monto;
    }
    pub fn resumen(&self, dia: u32) -> String {
        format!(
            "Resumen del día {dia}: {} ventas · ingresos {} · gastos {} · ganancia {} · {} clientes se fueron sin comprar",
            self.ventas,
            plata(self.ingresos),
            plata(self.gastos),
            plata(self.ingresos - self.gastos),
            self.perdidos
        )
    }
}

/// "$12", "$2.750", "-$1.200"
pub fn plata(monto: f32) -> String {
    let negativo = monto < 0.0;
    let entero = monto.abs().round() as u64;
    let digitos = entero.to_string();
    let mut con_puntos = String::new();
    for (i, c) in digitos.chars().enumerate() {
        if i > 0 && (digitos.len() - i).is_multiple_of(3) {
            con_puntos.push('.');
        }
        con_puntos.push(c);
    }
    format!("{}${con_puntos}", if negativo { "-" } else { "" })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn req_eco_01_caja_inicial_cobra_y_paga() {
        let mut c = Caja::default();
        assert_eq!(c.saldo, 120.0);
        c.cobrar(11.0);
        assert_eq!(c.saldo, 131.0);
        c.pagar(7.0).unwrap();
        assert_eq!(c.saldo, 124.0);
    }

    #[test]
    fn req_eco_02_no_gastar_lo_que_no_hay() {
        let mut c = Caja { saldo: 4.0 };
        assert_eq!(c.pagar(7.0), Err(SinSaldo { falta: 3.0 }));
        assert_eq!(c.saldo, 4.0);
    }

    #[test]
    fn req_eco_04_reputacion() {
        let mut r = Reputacion::default();
        assert_eq!(r.0, 3.0);
        r.registrar(5.0);
        assert!((r.0 - 3.2).abs() < 1e-5);
        for _ in 0..200 {
            r.registrar(1.0);
        }
        assert!(r.0 >= 0.0 && r.0 < 1.1);
    }

    #[test]
    fn req_eco_05_estadisticas_y_resumen() {
        let mut e = EstadisticasDia::default();
        e.venta(11.0);
        e.venta(10.0);
        e.gasto(7.0);
        e.perdido();
        assert_eq!((e.ventas, e.atendidos, e.perdidos), (2, 2, 1));
        let r = e.resumen(1);
        assert!(r.contains("día 1") && r.contains("2 ventas") && r.contains("$21") && r.contains("$14"));
    }

    #[test]
    fn req_eco_06_formato_de_plata() {
        assert_eq!(plata(2750.0), "$2.750");
        assert_eq!(plata(30000.0), "$30.000");
        assert_eq!(plata(1234567.0), "$1.234.567");
        assert_eq!(plata(-500.0), "-$500");
        assert_eq!(plata(0.0), "$0");
    }
}
