//! Prueba de humo de SPEC-029 · pelar y cortar (CA-FRE-01): con la tabla_papas del carro de las
//! papas, el jugador pela la papa con 3 E y la corta con 4. Submódulo de `prueba_humo.rs`.

use std::cell::RefCell;

use godot::prelude::*;

use super::{PruebaHumo, todos};
use crate::comida::Comida;
use crate::jugador::{Jugador, Objetivo};
use crate::preparar;

/// Lo que se mide entre cuadros (en un lugar propio para no tocar los campos de `PruebaHumo`).
#[derive(Default)]
struct Estado {
    fase: u32,
    papa: Option<Gd<Comida>>,
    lugar: Vector3,
    giro: Basis,
    jugador_antes: Option<Transform3D>,
}

thread_local! {
    static ESTADO: RefCell<Estado> = RefCell::default();
}

/// Comida suelta (no por borrarse) de `producto` a menos de `radio` de `centro`.
fn cerca(mundo: &Gd<Node>, producto: &str, centro: Vector3, radio: f32) -> Option<Gd<Comida>> {
    todos::<Comida>(mundo).into_iter().find(|c| {
        !c.is_queued_for_deletion()
            && c.bind().producto() == producto
            && c.get_global_position().distance_to(centro) < radio
    })
}

/// La pone cerca de la mano del jugador y la agarra (así no empuja la papa al venir).
fn agarrar_herramienta(j: &mut Gd<Jugador>, mut h: Gd<Comida>) {
    h.set_global_position(j.get_global_position() + Vector3::new(0.0, 1.4, 0.0));
    j.bind_mut().agarrar(h.upcast());
}

fn apunta_a(j: &mut Gd<Jugador>, c: &Gd<Comida>) -> bool {
    matches!(j.bind_mut().objetivo(), Some(Objetivo::Comida(o)) if o.instance_id() == c.instance_id())
}

impl PruebaHumo {
    /// CA-FRE-01 y REQ-FRE-01..03 con la tabla del carro de las papas (después de
    /// `chequear_papas_y_puerta`). Se llama en varios cuadros; devuelve true al terminar.
    pub(super) fn chequear_pelar(&mut self) -> bool {
        let mundo = self.mundo();
        let Some(mut j) = todos::<Jugador>(&mundo).pop() else {
            self.chequear(false, "CA-FRE-01 hay jugador");
            return true;
        };
        let fase = ESTADO.with_borrow(|e| e.fase);
        match fase {
            0 => {
                let Some(carro) = self.carro_papas.clone() else {
                    self.chequear(false, "CA-FRE-01 está el carro con la tabla de papas");
                    return true;
                };
                let base = carro.get_global_position();
                let (Some(mut papa), Some(pelapapas)) =
                    (cerca(&mundo, "papa_cruda", base, 2.0), cerca(&mundo, "pelapapas", base, 2.0))
                else {
                    self.chequear(false, "CA-FRE-01 la tabla trae la papa y el pelapapas");
                    return true;
                };
                let antes = j.get_global_transform();
                if let Some(mut m) = j.bind_mut().soltar() {
                    m.set_global_position(base + Vector3::new(3.0, 0.3, -2.0));
                }
                // Parado del lado del vendedor (atrás del carro), mirando la papa de la tabla.
                let pos = papa.get_global_position();
                j.set_global_position(Vector3::new(pos.x, base.y, base.z - 1.0));
                j.set_velocity(Vector3::ZERO);
                j.bind_mut().apuntar_a(pos);
                let mira = apunta_a(&mut j, &papa);
                // REQ-FRE-03: sin la herramienta, E no hace nada y el cartel dice cuál hace falta.
                j.bind_mut().usar();
                let cartel = preparar::cartel(None, &papa);
                self.chequear(
                    mira && papa.bind().pasadas == 0 && cartel.contains("Necesitás el pelapapas"),
                    &format!("REQ-FRE-03 sin el pelapapas, E no hace nada y el cartel lo pide (\"{cartel}\")"),
                );
                // REQ-FRE-01: con el pelapapas, cada E es una pasada.
                agarrar_herramienta(&mut j, pelapapas);
                j.bind_mut().apuntar_a(pos);
                j.bind_mut().usar();
                let cartel = preparar::cartel(Some("pelapapas"), &papa);
                self.chequear(
                    papa.bind().pasadas == 1 && cartel.contains("[E] Pelar papa (2/3)"),
                    &format!("REQ-FRE-01 una E con el pelapapas es una pasada (\"{cartel}\")"),
                );
                // REQ-FRE-03: la corro un poco sobre la tabla; la pasada queda en la papa.
                papa.set_global_position(pos + Vector3::new(0.03, 0.005, 0.0));
                ESTADO.with_borrow_mut(|e| {
                    e.papa = Some(papa);
                    e.jugador_antes = Some(antes);
                });
                self.esperar(20);
            }
            1 => {
                let Some(papa) = ESTADO.with_borrow(|e| e.papa.clone()) else { return true };
                let t = papa.get_global_transform();
                j.bind_mut().apuntar_a(t.origin);
                let mira = apunta_a(&mut j, &papa);
                let pasadas = papa.bind().pasadas;
                j.bind_mut().usar();
                j.bind_mut().usar();
                self.chequear(
                    mira && pasadas == 1 && papa.is_queued_for_deletion(),
                    &format!("REQ-FRE-01/03 la papa movida conserva su pasada ({pasadas}): 2 E más y se pela"),
                );
                ESTADO.with_borrow_mut(|e| {
                    e.papa = None;
                    e.lugar = t.origin;
                    e.giro = t.basis;
                });
                self.esperar(20);
            }
            2 => {
                let (lugar, giro) = ESTADO.with_borrow(|e| (e.lugar, e.giro));
                let pelada = cerca(&mundo, "papa_pelada", lugar, 0.05);
                let mismo_giro = pelada.as_ref().is_some_and(|p| {
                    let b = p.get_global_transform().basis;
                    b.col_a().normalized().dot(giro.col_a().normalized()) > 0.99
                });
                self.chequear(
                    mismo_giro,
                    &format!(
                        "REQ-FRE-01 queda una papa pelada en el mismo lugar y giro ({:?})",
                        pelada.as_ref().map(|p| p.get_global_position() - lugar)
                    ),
                );
                let Some(pelada) = pelada else { return true };
                // REQ-FRE-02: cambio el pelapapas por el cuchillo y corto con 4 E.
                j.bind_mut().soltar();
                let Some(cuchillo) = cerca(&mundo, "cuchillo", lugar, 1.0) else {
                    self.chequear(false, "REQ-FRE-02 la tabla trae el cuchillo");
                    return true;
                };
                agarrar_herramienta(&mut j, cuchillo);
                j.bind_mut().apuntar_a(pelada.get_global_position());
                let mira = apunta_a(&mut j, &pelada);
                for _ in 0..3 {
                    j.bind_mut().usar();
                }
                let cartel = preparar::cartel(Some("cuchillo"), &pelada);
                let tres = pelada.bind().pasadas == 3 && cartel.contains("[E] Cortar papa (4/4)");
                j.bind_mut().usar();
                self.chequear(
                    mira && tres && pelada.is_queued_for_deletion(),
                    &format!("REQ-FRE-02 con el cuchillo, 4 E cortan la papa pelada (\"{cartel}\")"),
                );
                self.esperar(20);
            }
            3 => {
                let lugar = ESTADO.with_borrow(|e| e.lugar);
                let cortada = cerca(&mundo, "papa_cortada", lugar, 0.05);
                self.chequear(
                    cortada.is_some(),
                    "CA-FRE-01 con la tabla_papas: pelo la papa con 3 E y la corto con 4 (sale una papa cortada)",
                );
                j.bind_mut().soltar();
                if let Some(t) = ESTADO.with_borrow_mut(|e| e.jugador_antes.take()) {
                    j.set_global_transform(t);
                }
                ESTADO.with_borrow_mut(|e| *e = Estado { fase: 99, ..Default::default() });
                return true;
            }
            _ => return true, // ya se hizo
        }
        ESTADO.with_borrow_mut(|e| e.fase += 1);
        false
    }
}
