//! Prueba de humo de clientes habituales (SPEC-030). (TASK-0504)
//!
//! Un cliente atendido con 5★ se vuelve habitual; al día siguiente llega desde el borde cerca
//! de su hora, saluda, pide lo de siempre con su nombre en el globo (CA-HAB-01); se va enojado
//! dos veces y no vuelve más (CA-HAB-02). Con el cartel de cerrado colgado no viene.

use carrito_core::clientes::PACIENCIA_S;
use carrito_core::habituales::{self as hab, Frecuencia};
use godot::prelude::*;

use super::{PruebaHumo, todos};
use crate::carrito::{self, Carrito};
use crate::cartel::CartelCerrado;
use crate::datos::plaza;
use crate::dia_noche::DiaNoche;
use crate::gente::Gente;
use crate::util;

/// Cuadros que se espera cada cosa antes de darla por fallada.
const ESPERA_MAX: u32 = 30 * 60;
/// Fase final: deja el reloj y el cartel como estaban.
const FIN: u32 = 99;

impl PruebaHumo {
    fn fase_habituales(&mut self, fase: u32) -> bool {
        self.fase5 = fase;
        self.cuadro5 = self.cuadro;
        false
    }

    /// Si pasó demasiado, anota la falla y va a la fase final.
    fn tarde_habituales(&mut self, que: &str) -> bool {
        if self.cuadro.saturating_sub(self.cuadro5) > ESPERA_MAX {
            self.chequear(false, que);
            self.fase_habituales(FIN);
        }
        false
    }

    /// Cuelga o saca el cartel de cerrado del carrito de la gente (si tiene).
    fn cartel_habituales(&self, colgado: bool) {
        let cartel = util::unico::<Carrito>(&self.mundo(), carrito::GRUPO).and_then(|c| c.bind().cartel_cerrado());
        if let Some(mut c) = cartel
            && c.bind().colgado() != colgado
        {
            c.bind_mut().alternar();
        }
    }

    fn cartel_colgado_habituales(&self) -> bool {
        let cartel: Option<Gd<CartelCerrado>> =
            util::unico::<Carrito>(&self.mundo(), carrito::GRUPO).and_then(|c| c.bind().cartel_cerrado());
        cartel.is_some_and(|c| c.bind().colgado())
    }

    /// Se llama cada cuadro hasta que devuelve true (brazo de la cadena del paso 31).
    pub(super) fn chequear_habituales(&mut self) -> bool {
        let mundo = self.mundo();
        let (Some(mut gente), Some(mut dn), Some(carrito)) = (
            todos::<Gente>(&mundo).pop(),
            todos::<DiaNoche>(&mundo).pop(),
            util::unico::<Carrito>(&mundo, carrito::GRUPO),
        ) else {
            self.chequear(false, "REQ-HAB-01 hay gente, reloj y carrito");
            return true;
        };
        // notas5: [día, minuto, cartel] para dejar todo como estaba, el habitual y su cliente.
        let hid = self.notas5.get(3).map(|h| *h as usize).unwrap_or(usize::MAX);
        let cliente = self.notas5.get(4).map(|c| *c as u64).unwrap_or(0);
        match self.fase5 {
            0 => {
                let cartel = if self.cartel_colgado_habituales() { 1.0 } else { 0.0 };
                self.notas5 = vec![dn.bind().dia() as f64, dn.bind().hora() as f64 * 60.0, cartel];
                gente.bind_mut().despejar_fila(false);
                gente.bind_mut().forzar_cliente();
                self.fase_habituales(1)
            }
            1 => {
                // Un cliente común pide; lo atiendo con 5★ y se vuelve habitual.
                let Some(pedido) = gente.bind().pedido_del_primero() else {
                    return self.tarde_habituales("REQ-HAB-01 el cliente de prueba pidió");
                };
                let hora = dn.bind().hora();
                let hid = gente.bind_mut().probar_atender_primero(5.0, true);
                let Some(h) = hid.and_then(|i| gente.bind().probar_habitual(i)) else {
                    self.chequear(false, "REQ-HAB-01 un cliente atendido con 5★ se vuelve habitual");
                    return self.fase_habituales(FIN);
                };
                self.chequear(
                    plaza().habituales.nombres.contains(&h.nombre) && h.memoria == vec![5.0],
                    &format!("REQ-HAB-01 un cliente atendido con 5★ se volvió habitual: {}", h.nombre),
                );
                self.chequear(
                    h.lo_de_siempre == pedido && (h.hora - hora).abs() < 0.1,
                    &format!("REQ-HAB-02 lo de siempre: {pedido:?} a las {:.2} h", h.hora),
                );
                self.notas5.push(h.id as f64);
                // Al día siguiente, dos horas antes de su hora de costumbre.
                let dia = dn.bind().dia();
                dn.bind_mut().set_minuto(((h.hora - 2.0).max(0.0) * 60.0) as f64);
                dn.bind_mut().set_dia(dia + 1);
                self.fase_habituales(2)
            }
            2 => {
                // Se esperan unos cuadros para que Gente lea el día nuevo y decida.
                if self.cuadro.saturating_sub(self.cuadro5) < 3 {
                    return false;
                }
                let Some(h) = gente.bind().probar_habitual(hid) else {
                    self.chequear(false, "REQ-HAB-03 el habitual sigue al día siguiente");
                    return self.fase_habituales(FIN);
                };
                let ya_vino = gente.bind().cliente_habitual(hid).is_some();
                let visita = h.visita.or(ya_vino.then(|| dn.bind().hora()));
                self.chequear(
                    visita.is_some_and(|v| (v - h.hora).abs() <= hab::MARGEN_HORA_H + 0.01),
                    &format!("REQ-HAB-03 viene al día siguiente cerca de su hora ({:.2} h → {visita:?})", h.hora),
                );
                if ya_vino {
                    gente.bind_mut().despejar_fila(true);
                    return self.fase_habituales(3);
                }
                // A su hora, con el cartel de cerrado colgado: no viene.
                self.cartel_habituales(true);
                if let Some(v) = h.visita {
                    dn.bind_mut().set_minuto((v * 60.0 + 0.5) as f64);
                }
                self.fase_habituales(20)
            }
            20 => {
                if self.cuadro.saturating_sub(self.cuadro5) < 5 {
                    return false;
                }
                let h = gente.bind().probar_habitual(hid);
                let vino = gente.bind().cliente_habitual(hid).is_some();
                self.chequear(
                    !vino && h.as_ref().is_some_and(|h| h.visita.is_none() && h.memoria == vec![5.0]),
                    "REQ-HAB-03 con el cartel colgado el habitual no viene y no cuenta como visita",
                );
                // Saco el cartel y vuelve.
                self.cartel_habituales(false);
                gente.bind_mut().adelantar_visita(hid);
                gente.bind_mut().despejar_fila(true);
                self.fase_habituales(3)
            }
            3 => {
                let Some((id, pos, igual)) = gente.bind().cliente_habitual(hid) else {
                    return self.tarde_habituales("REQ-HAB-03 el habitual llega a su hora");
                };
                let lejos = pos.distance_to(carrito.get_global_position());
                self.chequear(
                    lejos > 6.0 && igual,
                    &format!("REQ-HAB-03 el habitual llega caminando desde el borde ({lejos:.0} m), igual que siempre"),
                );
                gente.bind_mut().despejar_fila(true);
                let h = gente.bind().probar_habitual(hid);
                let esperada =
                    h.map(|h| plaza().agenda.paciencia(h.perfil) * hab::FACTOR_PACIENCIA_BUENA * PACIENCIA_S);
                let total = gente.bind().paciencia_total_del_primero().map(|(_, t)| t);
                self.chequear(
                    matches!((total, esperada), (Some(t), Some(e)) if (t - e).abs() < 0.01),
                    &format!("REQ-HAB-06 con memoria buena tiene paciencia ×1,25 ({total:?}, esperada {esperada:?})"),
                );
                gente.bind_mut().acercar_habitual(hid);
                self.notas5.push(id as f64);
                self.fase_habituales(4)
            }
            4 => {
                gente.bind_mut().despejar_fila(true);
                if !gente.bind().primero_listo(cliente) {
                    return self.tarde_habituales("REQ-HAB-04 el habitual llega a la fila y pide");
                }
                let h = gente.bind().probar_habitual(hid).expect("sigue siendo habitual");
                let pedido = gente.bind().pedido_del_primero().unwrap();
                self.chequear(
                    pedido.producto == h.lo_de_siempre.producto
                        && pedido.aderezos.iter().all(|a| h.lo_de_siempre.aderezos.contains(a)),
                    &format!("REQ-HAB-04 CA-HAB-01 pide lo de siempre ({pedido:?})"),
                );
                let globo = gente.bind().globo_del_primero().unwrap_or_default();
                self.chequear(
                    globo.starts_with(&format!("{}: lo de siempre (", h.nombre)),
                    &format!("REQ-HAB-05 CA-HAB-01 globo con su nombre: «{globo}»"),
                );
                self.chequear(gente.bind().saludo(cliente), "REQ-HAB-05 con memoria buena saluda al llegar");
                // CA-HAB-02: lo dejo irse enojado.
                gente.bind_mut().set_paciencia_del_primero(0.0);
                self.fase_habituales(5)
            }
            5 => {
                if gente.bind().cliente_habitual(hid).is_some() {
                    return self.tarde_habituales("REQ-HAB-06 el habitual se va enojado");
                }
                let h = gente.bind().probar_habitual(hid);
                self.chequear(
                    h.as_ref().is_some_and(|h| h.memoria == vec![5.0, 1.0] && h.frecuencia() == Frecuencia::AVeces),
                    &format!(
                        "REQ-HAB-06 se fue enojado: recuerda 1★ y viene la mitad de los días ({:?})",
                        h.map(|h| h.memoria)
                    ),
                );
                // Vuelve otra vez (se adelanta su visita) y lo dejo irse enojado de nuevo.
                gente.bind_mut().adelantar_visita(hid);
                gente.bind_mut().despejar_fila(true);
                self.fase_habituales(6)
            }
            6 => {
                let Some((id, _, _)) = gente.bind().cliente_habitual(hid) else {
                    return self.tarde_habituales("REQ-HAB-06 el habitual vuelve otra vez");
                };
                gente.bind_mut().despejar_fila(true);
                gente.bind_mut().acercar_habitual(hid);
                self.notas5.truncate(4);
                self.notas5.push(id as f64);
                self.fase_habituales(7)
            }
            7 => {
                gente.bind_mut().despejar_fila(true);
                if !gente.bind().primero_listo(cliente) {
                    return self.tarde_habituales("REQ-HAB-06 el habitual vuelve a la fila");
                }
                let globo = gente.bind().globo_del_primero().unwrap_or_default();
                self.chequear(
                    !gente.bind().saludo(cliente),
                    &format!("REQ-HAB-05 sin memoria buena no saluda («{globo}»)"),
                );
                gente.bind_mut().set_paciencia_del_primero(0.0);
                self.fase_habituales(8)
            }
            8 => {
                if gente.bind().cliente_habitual(hid).is_some() {
                    return self.tarde_habituales("REQ-HAB-06 el habitual se va enojado otra vez");
                }
                let quedan = gente.bind().cantidad_habituales();
                self.chequear(
                    gente.bind().probar_habitual(hid).is_none(),
                    &format!(
                        "REQ-HAB-06 CA-HAB-02 se fue enojado dos veces seguidas y no vuelve más (quedan {quedan})"
                    ),
                );
                self.fase_habituales(FIN)
            }
            _ => {
                // Deja el reloj como estaba.
                let dia = self.notas5.first().map(|d| *d as u32).unwrap_or(1);
                let minuto = self.notas5.get(1).copied().unwrap_or(17.0 * 60.0);
                dn.bind_mut().set_dia(dia);
                dn.bind_mut().set_minuto(minuto);
                let cartel = self.notas5.get(2).is_some_and(|c| *c > 0.5);
                self.cartel_habituales(cartel);
                true
            }
        }
    }
}
