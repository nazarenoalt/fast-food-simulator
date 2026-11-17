//! SPEC-011 · Proveedor: pedidos y horarios de entrega.
//! Los tiempos son "minutos absolutos": (día − 1) × 1440 + minuto del día.

use crate::reloj::MINUTOS_DIA;

pub const ABRE: f64 = 8.0 * 60.0; // REQ-PRO-03
pub const CIERRA: f64 = 20.0 * 60.0;
pub const DEMORA: f64 = 60.0;
pub const ENTREGA_FUERA_DE_HORARIO: f64 = 9.0 * 60.0;

/// REQ-PRO-03: cuándo llega un pedido hecho en `ahora`.
pub fn hora_llegada(ahora: f64) -> f64 {
    let dia = (ahora / MINUTOS_DIA).floor();
    let minuto = ahora - dia * MINUTOS_DIA;
    if (ABRE..CIERRA).contains(&minuto) {
        ahora + DEMORA
    } else if minuto < ABRE {
        dia * MINUTOS_DIA + ENTREGA_FUERA_DE_HORARIO
    } else {
        (dia + 1.0) * MINUTOS_DIA + ENTREGA_FUERA_DE_HORARIO
    }
}

#[derive(Debug, Clone, PartialEq)]
pub struct PedidoCompra {
    pub bloque: String,
    pub llega: f64,
}

#[derive(Debug, Clone, Default, PartialEq)]
pub struct Proveedor {
    pub pendientes: Vec<PedidoCompra>,
}

impl Proveedor {
    /// REQ-PRO-02
    pub fn pedir(&mut self, bloque: &str, ahora: f64) -> f64 {
        let llega = hora_llegada(ahora);
        self.pendientes.push(PedidoCompra { bloque: bloque.to_string(), llega });
        llega
    }

    /// REQ-PRO-04: devuelve (y saca de pendientes) lo que ya llegó.
    pub fn tomar_llegados(&mut self, ahora: f64) -> Vec<String> {
        let (llegados, siguen): (Vec<_>, Vec<_>) = self.pendientes.drain(..).partition(|p| p.llega <= ahora);
        self.pendientes = siguen;
        llegados.into_iter().map(|p| p.bloque).collect()
    }
}

/// "11:00" o "mañana 09:00"
pub fn texto_llegada(llega: f64, ahora: f64) -> String {
    let dia_llega = (llega / MINUTOS_DIA).floor();
    let dia_ahora = (ahora / MINUTOS_DIA).floor();
    let m = (llega - dia_llega * MINUTOS_DIA) as u32;
    let hora = format!("{:02}:{:02}", m / 60, m % 60);
    if dia_llega > dia_ahora { format!("mañana {hora}") } else { hora }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn abs(dia: u32, h: u32, m: u32) -> f64 {
        (dia as f64 - 1.0) * MINUTOS_DIA + (h * 60 + m) as f64
    }

    #[test]
    fn req_pro_03_horarios() {
        assert_eq!(hora_llegada(abs(1, 10, 0)), abs(1, 11, 0));
        assert_eq!(hora_llegada(abs(1, 19, 30)), abs(1, 20, 30), "hecho en horario llega igual");
        assert_eq!(hora_llegada(abs(1, 21, 0)), abs(2, 9, 0));
        assert_eq!(hora_llegada(abs(2, 3, 0)), abs(2, 9, 0));
    }

    #[test]
    fn req_pro_02_04_pedir_y_recibir() {
        let mut p = Proveedor::default();
        p.pedir("bolsa_panes_12", abs(1, 10, 0));
        p.pedir("caja_salchichas_12", abs(1, 10, 30));
        assert!(p.tomar_llegados(abs(1, 10, 59)).is_empty());
        assert_eq!(p.tomar_llegados(abs(1, 11, 0)), vec!["bolsa_panes_12".to_string()]);
        assert_eq!(p.pendientes.len(), 1);
        assert_eq!(p.tomar_llegados(abs(1, 12, 0)), vec!["caja_salchichas_12".to_string()]);
    }

    #[test]
    fn req_pro_01_texto_de_llegada() {
        assert_eq!(texto_llegada(abs(1, 11, 0), abs(1, 10, 0)), "11:00");
        assert_eq!(texto_llegada(abs(2, 9, 0), abs(1, 21, 0)), "mañana 09:00");
    }
}
