//! Prueba de humo de la agenda por hora (TASK-0502): REQ-RUT-01 a REQ-RUT-04.

use carrito_core::rutinas::Perfil;

use godot::prelude::Gd;

use super::{PruebaHumo, todos};
use crate::dia_noche::DiaNoche;
use crate::gente::Gente;

impl PruebaHumo {
    /// A las 11:30 la agenda ya manda la gente del mediodía (adelanto de 45 min): quiere 28
    /// personas y la mayoría de los que llegan son oficinistas; a las 17:30, familias. Los
    /// clientes tienen la paciencia de su perfil. Devuelve true cuando termina.
    pub(super) fn chequear_agenda(&mut self) -> bool {
        let mundo = self.mundo();
        let (Some(mut gente), Some(mut dn)) = (todos::<Gente>(&mundo).pop(), todos::<DiaNoche>(&mundo).pop()) else {
            self.chequear(false, "REQ-RUT-01 hay gente y reloj");
            return true;
        };
        match self.fase5 {
            0 => {
                // Se guardan día y hora para dejarlos como estaban; un lunes (día 4), sin
                // eventos (SPEC-019).
                self.notas5 = vec![dn.bind().hora() as f64 * 60.0, dn.bind().dia() as f64];
                dn.bind_mut().set_dia(4);
                dn.bind_mut().set_minuto(11.0 * 60.0 + 30.0);
                self.fase5 = 1;
                false
            }
            1 | 3 => {
                // Se espera un cuadro para que Gente lea la hora nueva.
                self.fase5 += 1;
                false
            }
            2 => {
                let objetivo = gente.bind().objetivo_gente();
                self.chequear(
                    objetivo == 28,
                    &format!("REQ-RUT-03 a las 11:30 ya se espera la gente del mediodía ({objetivo})"),
                );
                let (mas, cuantos) = mas_comun(&gente, 30);
                self.chequear(
                    mas == Some(Perfil::Oficinista),
                    &format!("REQ-RUT-01 a las 11:30 los que más llegan son oficinistas ({mas:?}: {cuantos:?})"),
                );
                dn.bind_mut().set_minuto(17.0 * 60.0 + 30.0);
                self.fase5 = 3;
                false
            }
            4 => {
                let (mas, cuantos) = mas_comun(&gente, 30);
                self.chequear(
                    mas == Some(Perfil::Familia),
                    &format!("REQ-RUT-01 a las 17:30 los que más llegan son familias ({mas:?}: {cuantos:?})"),
                );
                // REQ-RUT-04: un cliente con la paciencia de su perfil.
                if gente.bind().largo_fila() == 0 {
                    gente.bind_mut().forzar_cliente();
                }
                if let Some((perfil, total)) = gente.bind().paciencia_total_del_primero() {
                    let esperada = crate::datos::plaza().agenda.paciencia(perfil) * carrito_core::clientes::PACIENCIA_S;
                    self.chequear(
                        (total - esperada).abs() < 0.01,
                        &format!("REQ-RUT-04 paciencia de un cliente {perfil:?}: {total} (esperada {esperada})"),
                    );
                }
                let minuto = self.notas5.first().copied().unwrap_or(17.0 * 60.0);
                let dia = self.notas5.get(1).copied().unwrap_or(1.0);
                dn.bind_mut().set_dia(dia as u32);
                dn.bind_mut().set_minuto(minuto);
                true
            }
            _ => true,
        }
    }
}

/// Hace llegar `n` personas de la agenda y devuelve el perfil más común y la cuenta por perfil.
fn mas_comun(gente: &Gd<Gente>, n: usize) -> (Option<Perfil>, Vec<(Perfil, usize)>) {
    let mut gente = gente.clone();
    let ids = gente.bind_mut().probar_paseantes(n);
    let mut cuenta: Vec<(Perfil, usize)> = Vec::new();
    for id in ids {
        let Some(p) = gente.bind().perfil_de(id) else { continue };
        match cuenta.iter_mut().find(|(q, _)| *q == p) {
            Some((_, c)) => *c += 1,
            None => cuenta.push((p, 1)),
        }
    }
    cuenta.sort_by(|a, b| b.1.cmp(&a.1));
    (cuenta.first().map(|(p, _)| *p), cuenta)
}
