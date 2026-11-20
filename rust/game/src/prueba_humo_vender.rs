//! Prueba de humo de TASK-0358 (SPEC-029, SPEC-009): armo papas en cajita y se las vendo a un
//! cliente, y el cartel de cerrado frena a los clientes nuevos pero no al que ya está en la fila.
//! Va sobre el carrito del jugador (el food truck, después de `chequear_papas_y_puerta`).

use carrito_core::clientes::Pedido;
use carrito_core::coccion::Punto;
use carrito_core::plaza;
use carrito_core::tienda::Origen;
use godot::classes::Input;
use godot::prelude::*;

use super::{PruebaHumo, todos};
use crate::armado::ModoArmado;
use crate::carrito::{self, Carrito};
use crate::cartel::CartelCerrado;
use crate::comida::Comida;
use crate::gente::Gente;
use crate::jugador::{Jugador, Objetivo};
use crate::negocio::Negocio;
use crate::util;

const PRECIO_PAPAS: f32 = 10.0; // REQ-FRE-11, REQ-ECO-03

/// Lo que la prueba guarda entre cuadros.
#[derive(Default)]
pub(super) struct Vender {
    pub(super) fase: u32,
    fila_antes: usize,
    saldo_antes: f32,
    cajita: Option<Gd<Comida>>,
    cajitas_antes: Vec<InstanceId>,
    reintentos: u32,
}

/// Dónde se arman las papas: en el piso de la vereda, lejos del carrito.
fn lugar_armado() -> Vector3 {
    Vector3::new(-7.5, 0.3, plaza::Z_VEREDA)
}

impl PruebaHumo {
    fn carrito_jugador(&self) -> Gd<Carrito> {
        // El mismo que usa la gente (el primero del grupo), no el carro de las papas.
        util::unico::<Carrito>(&self.mundo(), carrito::GRUPO).expect("carrito del jugador")
    }

    fn cartel_jugador(&self) -> Option<Gd<CartelCerrado>> {
        self.carrito_jugador().bind().cartel_cerrado()
    }

    /// Se llama en varios cuadros; devuelve true al terminar.
    pub(super) fn chequear_vender(&mut self) -> bool {
        let mundo = self.mundo();
        let mut gente = todos::<Gente>(&mundo).pop().expect("gente");
        let carrito = self.carrito_jugador();
        match self.vender.fase {
            0 => {
                // REQ-CLI-04: las papas solo están en el menú de un carrito con freidora.
                let tiene = |c: &Gd<Carrito>| c.bind().menu().iter().any(|i| i.producto == "papas_en_cajita");
                let con_freidora = self.carro_papas.as_ref().is_some_and(tiene);
                self.chequear(
                    con_freidora && !tiene(&carrito),
                    "REQ-CLI-04 con freidora el menú tiene papas en cajita; sin freidora, no",
                );
                // REQ-CLI-13: pongo el cartel de cerrado en el carrito del jugador: arranca colgado.
                let mut neg = todos::<Negocio>(&mundo).pop().expect("negocio");
                let saldo = neg.bind().saldo();
                neg.bind_mut().set_saldo(saldo.max(1000.0));
                if let Some(mut m) = todos::<ModoArmado>(&mundo).pop() {
                    m.bind_mut().elegir("cartel", "cartel_cerrado", Origen::Tienda);
                    m.bind_mut().cerrar_panel();
                }
                let cartel = self.cartel_jugador();
                let texto = cartel.as_ref().map(|c| c.bind().cartel()).unwrap_or_default();
                let visible = cartel.as_ref().is_some_and(|c| c.bind().colgado() && c.bind().dibujo_visible());
                self.chequear(
                    visible && texto == "[Clic/E] Abrir el puesto (sacar el cartel)",
                    &format!("REQ-CLI-13 el cartel de cerrado arranca colgado y se ve («{texto}»)"),
                );
                // Hay alguien en la fila; con el cartel colgado no entra nadie más.
                if gente.bind().largo_fila() == 0 {
                    gente.bind_mut().forzar_cliente();
                }
                gente.bind_mut().set_paciencia_del_primero(100.0);
                self.vender.fila_antes = gente.bind().largo_fila();
                let entraron = (0..3).filter(|_| gente.bind_mut().probar_llegada()).count();
                let fila = gente.bind().largo_fila();
                self.chequear(
                    entraron == 0 && fila == self.vender.fila_antes,
                    &format!("REQ-CLI-12 con el cartel colgado no se suman clientes nuevos (fila {fila})"),
                );
                // Una cajita vacía en el piso, para armarle las papas encima.
                self.vender.cajitas_antes = todos::<Comida>(&mundo)
                    .iter()
                    .filter(|c| c.bind().producto() == "papas_en_cajita")
                    .map(|c| c.instance_id())
                    .collect();
                self.vender.cajita = Some(self.agregar_comida("cajita_papas", lugar_armado()));
                self.esperar(60);
            }
            1 => {
                // REQ-FRE-11: suelto papas fritas cocidas en la cajita (donde las pone la mira).
                let Some(cajita) = self.vender.cajita.clone() else { return true };
                let pos = cajita.bind().encastre_para("papas_fritas");
                self.chequear(pos.is_some(), "REQ-FRE-11 la cajita recibe papas fritas encima");
                let pos = pos.unwrap_or(cajita.get_global_position() + Vector3::new(0.0, 0.08, 0.0));
                let mut papas = self.agregar_comida("papas_fritas", pos);
                papas.set_global_rotation(cajita.get_global_rotation());
                // Cocidas: con su perfil (TASK-0357) a mitad de camino entre cocida y pasada; si
                // todavía no se fríen, con el punto fijo.
                let perfil = crate::datos::catalogo().producto("papas_fritas").and_then(|p| p.coccion.clone());
                match perfil {
                    Some(p) => papas.bind_mut().forzar_avance((p.punto + p.pasado) / 2.0),
                    None => papas.bind_mut().forzar_punto(Punto::Cocido),
                }
                self.esperar(30);
            }
            2 => {
                let hecha = todos::<Comida>(&mundo).into_iter().find(|c| {
                    c.bind().producto() == "papas_en_cajita"
                        && !c.is_queued_for_deletion()
                        && !self.vender.cajitas_antes.contains(&c.instance_id())
                });
                // La cajita vacía ya se borró: se mira sin clonarla.
                let usada =
                    self.vender.cajita.as_ref().is_none_or(|c| !c.is_instance_valid() || c.is_queued_for_deletion());
                let desc = hecha.as_ref().map(|c| c.bind().descripcion()).unwrap_or_default();
                let punto = hecha.as_ref().and_then(|c| c.bind().punto());
                if self.vender.reintentos == 0 {
                    self.chequear(
                        usada && punto == Some(Punto::Cocido),
                        &format!(
                            "REQ-FRE-11 cajita + papas fritas = papas en cajita, con la cocción de las papas ({desc})"
                        ),
                    );
                }
                self.vender.cajita = None;
                let Some(mut hecha) = hecha else { return true };
                // El primero de la fila tiene que haber llegado y pedido (puede venir caminando).
                if gente.bind().pedido_del_primero().is_none() && self.vender.reintentos < 20 {
                    self.vender.reintentos += 1;
                    self.esperar(60);
                    return false; // se repite esta fase
                }
                gente
                    .bind_mut()
                    .set_pedido_del_primero(Pedido { producto: "papas_en_cajita".into(), aderezos: vec![] });
                gente.bind_mut().set_paciencia_del_primero(100.0);
                let fila = gente.bind().largo_fila();
                self.chequear(
                    fila >= 1 && fila <= self.vender.fila_antes,
                    &format!(
                        "REQ-CLI-12 con el cartel colgado, el de la fila se queda (fila {} → {fila})",
                        self.vender.fila_antes
                    ),
                );
                // CA-FRE-03: la apoyo en la bandeja.
                // Con una caja chica, para que el f32 no redondee los centavos de la propina.
                todos::<Negocio>(&mundo).pop().expect("negocio").bind_mut().set_saldo(100.0);
                self.vender.saldo_antes = 100.0;
                let bandeja = carrito.bind().pos_bandeja();
                hecha.set_global_position(bandeja + Vector3::new(0.0, 0.07, 0.0));
                hecha.set_global_rotation(Vector3::ZERO);
                hecha.set_linear_velocity(Vector3::ZERO);
                self.esperar(120);
            }
            3 => {
                let saldo = todos::<Negocio>(&mundo).pop().expect("negocio").bind().saldo();
                let cobro = saldo - self.vender.saldo_antes;
                self.chequear(
                    (PRECIO_PAPAS - 0.01..=PRECIO_PAPAS * 1.2 + 0.01).contains(&cobro),
                    &format!(
                        "CA-FRE-03 / REQ-CLI-12 con el cartel colgado se atiende al de la fila: paga $8 \
                         y propina por las papas (caja {} → {saldo})",
                        self.vender.saldo_antes
                    ),
                );
                // REQ-CLI-13: E sobre el cartel, apuntándolo desde la vereda, lo saca: desaparece y
                // su zona de uso queda en el frente.
                let Some(cartel) = self.cartel_jugador() else { return true };
                let mut j = todos::<Jugador>(&mundo).pop().expect("jugador");
                let t = carrito.get_global_transform();
                let zona = cartel.bind().centro_zona();
                let frente = t.basis.col_c().normalized();
                let mut parado = cartel.get_global_position() + frente * 1.2;
                parado.y = t.origin.y + 0.05;
                j.set_global_position(parado);
                j.set_velocity(Vector3::ZERO);
                j.bind_mut().apuntar_a(zona);
                let mira_cartel = |j: &mut Gd<Jugador>| matches!(j.bind_mut().objetivo(), Some(Objetivo::Cartel(_)));
                let mira = mira_cartel(&mut j);
                j.bind_mut().usar();
                let sacado = !cartel.bind().colgado() && !cartel.bind().dibujo_visible();
                let sigue = mira_cartel(&mut j) && cartel.bind().centro_zona().distance_to(zona) < 1e-4;
                self.chequear(
                    mira && sacado && sigue && cartel.bind().cartel() == "[Clic/E] Cerrar el puesto (colgar el cartel)",
                    "REQ-CLI-13 con la mira en el cartel, E lo saca: no se ve y su zona sigue en el frente",
                );
                // Descolgado está abierto: llega alguien nuevo.
                let antes = gente.bind().largo_fila();
                let entro = gente.bind_mut().probar_llegada();
                self.chequear(
                    entro && gente.bind().largo_fila() == antes + 1,
                    "REQ-CLI-12 con el cartel descolgado se suman clientes nuevos",
                );
                // REQ-CLI-13: el clic con la mano libre alterna igual que E: lo cuelga (se ve), lo
                // saca, y otra E lo vuelve a colgar.
                j.bind_mut().clic_izquierdo();
                let colgado_clic = cartel.bind().colgado() && cartel.bind().dibujo_visible();
                j.bind_mut().clic_izquierdo();
                let sacado_clic = !cartel.bind().colgado() && !cartel.bind().dibujo_visible();
                self.chequear(
                    colgado_clic && sacado_clic,
                    "REQ-CLI-13 el clic con la mano libre en la zona lo cuelga y lo vuelve a sacar",
                );
                j.bind_mut().usar();
                self.chequear(
                    cartel.bind().colgado() && cartel.bind().dibujo_visible(),
                    "REQ-CLI-13 otra E lo vuelve a colgar y se ve",
                );
                // Con algo en la mano, el clic coloca como siempre (no alterna el cartel).
                let mut pan = Comida::crear("pan_pancho");
                mundo.clone().add_child(&pan);
                pan.set_global_position(parado + Vector3::new(0.0, 1.2, 0.0));
                j.bind_mut().agarrar(pan.clone().upcast());
                j.bind_mut().apuntar_a(zona);
                // REQ-CLI-13: con algo en la mano, E igual lo saca y lo vuelve a colgar.
                j.bind_mut().usar();
                let sacado_e = !cartel.bind().colgado() && j.bind().en_mano().is_some();
                j.bind_mut().usar();
                self.chequear(
                    sacado_e && cartel.bind().colgado(),
                    "REQ-CLI-13 con algo en la mano, E saca el cartel y lo vuelve a colgar",
                );
                j.bind_mut().clic_izquierdo();
                self.chequear(
                    cartel.bind().colgado() && j.bind().en_mano().is_none(),
                    "REQ-CLI-13 con algo en la mano, el clic en la zona del cartel coloca y no lo alterna",
                );
                pan.queue_free();
                // La tecla C trae un cliente igual (REQ-CLI-11).
                self.vender.fila_antes = gente.bind().largo_fila();
                Input::singleton().action_press("traer_cliente");
                self.esperar(2);
            }
            _ => {
                Input::singleton().action_release("traer_cliente");
                let fila = gente.bind().largo_fila();
                self.chequear(
                    fila == self.vender.fila_antes + 1,
                    &format!(
                        "REQ-CLI-11/12 con el cartel colgado, la tecla C trae un cliente igual (fila {} → {fila})",
                        self.vender.fila_antes
                    ),
                );
                return true;
            }
        }
        self.vender.fase += 1;
        false
    }
}
