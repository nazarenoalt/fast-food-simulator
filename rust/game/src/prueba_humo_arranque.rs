//! Prueba de humo de la etapa 2.5 · agente C: REQ-ARR-01, REQ-ARR-02, REQ-ARR-03, REQ-ARR-04. (TASK-0250)
//!
//! El carrito del jugador no se toca: se arma un carrito aparte con la base común, se abre el
//! panel del arranque apuntado a ese carrito y se aprieta Choripán; después se prueban los otros
//! productos y se borra.

use carrito_core::arranque as regla;
use carrito_core::carrito::{ConfigCarrito, armar};
use godot::classes::node::ProcessMode;
use godot::prelude::*;

use super::{PruebaHumo, todos};
use crate::arranque::{self, Arranque};
use crate::carrito::{self, Carrito};
use crate::datos::catalogo;
use crate::util;

const NOMBRE: &str = "CarritoArranque";

/// Productos de los bloques que hay en el estante (anclaje `lateral`).
fn estante(c: &Gd<Carrito>) -> Vec<String> {
    let Some(nodo) = c.bind().nodo_puesto("lateral") else { return Vec::new() };
    carrito::lugares_de(&nodo)
        .iter()
        .filter_map(|l| l.bind().bloque())
        .map(|b| b.bind().producto().to_string())
        .collect()
}

fn menu(c: &Gd<Carrito>) -> Vec<String> {
    c.bind().menu().into_iter().map(|i| i.producto).collect()
}

/// Menú (REQ-CLI-04) de una config, armada con la regla de core.
fn menu_config(c: &ConfigCarrito) -> Option<Vec<String>> {
    let cat = catalogo();
    let armado = armar(c, &cat.bases, &cat.accesorios, &cat.ids_bloques()).ok()?;
    Some(regla::menu_de(&armado, cat))
}

impl PruebaHumo {
    fn carrito_arranque(&self) -> Option<Gd<Carrito>> {
        self.mundo().get_node_or_null(NOMBRE)?.try_cast::<Carrito>().ok()
    }

    /// Se llama cada cuadro hasta que devuelve true. Usa self.fase5. No cambia día ni hora.
    pub(super) fn chequear_arranque(&mut self) -> bool {
        let mundo = self.mundo();
        match self.fase5 {
            0 => {
                // REQ-ARR-02 con la regla de core: cada producto arma su carrito y su menú es él solo.
                let base = &catalogo().carrito_jugador;
                for o in &arranque::datos().productos {
                    let m = arranque::config_para(&o.producto).as_ref().and_then(menu_config);
                    self.chequear(
                        m.as_deref() == Some(std::slice::from_ref(&o.producto)),
                        &format!("REQ-ARR-02 {}: carrito válido y el menú tiene solo {} ({m:?})", o.nombre, o.producto),
                    );
                }
                let chori = arranque::config_para("choripan").unwrap_or_else(|| base.clone());
                let acc: Vec<&str> = chori.accesorios.values().map(String::as_str).collect();
                let stock: Vec<&str> = chori.stock.values().flatten().flatten().map(String::as_str).collect();
                self.chequear(
                    acc.contains(&"parrilla_chica")
                        && acc.contains(&"aderecera_cinco")
                        && !acc.contains(&"hervidor_chico")
                        && !acc.contains(&"plancha_chica")
                        && ["caja_chorizos_12", "bolsa_panes_choripan_12", "pack_carbon"]
                            .iter()
                            .all(|b| stock.contains(b)),
                    &format!("CA-ARR-01 Choripán: parrilla y aderecera, sin hervidor ni plancha; estante {stock:?}"),
                );
                // REQ-ARR-03: en la config normal el cartel viene puesto en su anclaje.
                self.chequear(
                    chori.accesorios.get(regla::ANCLAJE_CARTEL).map(String::as_str) == Some(regla::CARTEL_CERRADO),
                    "REQ-ARR-03 el carrito normal trae el cartel de cerrado en el anclaje cartel",
                );
                // REQ-ARR-04: la prueba no muestra el panel y arranca con los cuatro equipos sin cartel.
                let prueba = arranque::config_inicial(&mundo);
                let mut m = menu_config(&prueba).unwrap_or_default();
                m.sort();
                self.chequear(
                    !arranque::es_partida(&mundo)
                        && !prueba.accesorios.contains_key(regla::ANCLAJE_CARTEL)
                        && m == ["choripan", "hamburguesa", "pancho"],
                    &format!("REQ-ARR-04 la prueba usa los cuatro equipos y sin cartel (menú {m:?})"),
                );
                let jugador = util::unico::<Carrito>(&mundo, carrito::GRUPO);
                let puestos = jugador.as_ref().map(|c| c.bind().accesorios_puestos()).unwrap_or_default();
                let equipos = ["hervidor_chico", "plancha_chica", "aderecera_cinco", "parrilla_chica"]
                    .iter()
                    .all(|e| puestos.values().any(|v| v == e));
                self.chequear(equipos, "REQ-ARR-04 el carrito del jugador de la prueba tiene los cuatro equipos");
                let panel = todos::<Arranque>(&mundo).pop();
                let quieto = panel.as_ref().is_some_and(|a| !a.bind().abierto() && !a.bind().panel_visible());
                self.chequear(
                    quieto && !self.base().get_tree().is_paused(),
                    "REQ-ARR-04 en la prueba de humo el panel del arranque no sale y el mundo no está en pausa",
                );
                // Un carrito aparte con la base común, lejos (no es el que usa la gente).
                let mut c = Carrito::new_alloc();
                c.set_name(NOMBRE);
                c.bind_mut().forzar_config(base.clone());
                c.set_position(Vector3::new(0.0, 0.0, -37.0));
                mundo.clone().add_child(&c);
                self.esperar(30);
            }
            1 => {
                let (Some(c), Some(mut a)) = (self.carrito_arranque(), todos::<Arranque>(&mundo).pop()) else {
                    self.chequear(false, "REQ-ARR-01 hay panel del arranque y carrito de prueba");
                    return true;
                };
                // REQ-ARR-03: la base común sola trae el cartel colgado (el puesto arranca cerrado).
                let colgado = c.bind().cartel_cerrado().is_some_and(|k| k.bind().colgado());
                self.chequear(colgado, "REQ-ARR-03 el cartel de cerrado arranca colgado");
                self.chequear(menu(&c).is_empty(), "REQ-ARR-02 la base común sola no cocina nada");
                // REQ-ARR-01: el panel pausa el mundo y tiene los cuatro botones.
                a.bind_mut().set_destino(Some(c.clone()));
                a.bind_mut().abrir();
                let pausa = self.base().get_tree().is_paused();
                let siempre = a.get_process_mode() == ProcessMode::ALWAYS;
                let botones = a.bind().botones();
                let textos: Vec<String> = botones.iter().map(|(_, b)| b.get_text().to_string()).collect();
                self.chequear(
                    pausa && siempre && a.bind().panel_visible(),
                    "REQ-ARR-01 el panel se ve, el mundo queda en pausa y el panel sigue andando",
                );
                self.chequear(
                    textos == ["Pancho", "Hamburguesa", "Choripán", "Papas fritas"],
                    &format!("REQ-ARR-01 cuatro botones: {textos:?}"),
                );
                // Clic en Choripán (sin tener tomado el panel: el botón lo usa).
                if let Some((_, mut b)) = botones.into_iter().find(|(p, _)| p == "choripan") {
                    b.emit_signal("pressed", &[]);
                }
                let sigue = !self.base().get_tree().is_paused() && !a.bind().panel_visible();
                self.chequear(sigue, "REQ-ARR-01 al elegir se cierra el panel y el mundo sigue");
                a.bind_mut().set_destino(None);
                self.esperar(30);
            }
            _ => {
                let Some(mut c) = self.carrito_arranque() else { return true };
                let puestos = c.bind().accesorios_puestos();
                let tiene = |id: &str| puestos.values().any(|v| v == id);
                let e = estante(&c);
                self.chequear(
                    tiene("parrilla_chica")
                        && tiene("aderecera_cinco")
                        && !tiene("hervidor_chico")
                        && !tiene("plancha_chica")
                        && ["chorizo", "pan_choripan", "bolsa_carbon"].iter().all(|p| e.iter().any(|x| x == p)),
                    &format!("CA-ARR-01 elijo Choripán: parrilla y aderecera, sin hervidor ni plancha; estante {e:?}"),
                );
                let m = menu(&c);
                self.chequear(m == ["choripan"], &format!("CA-ARR-01 los clientes solo piden choripán ({m:?})"));
                let colgado = c.bind().cartel_cerrado().is_some_and(|k| k.bind().colgado());
                self.chequear(colgado, "REQ-ARR-03 después de elegir, el cartel sigue colgado");
                // Los otros productos, rearmando el mismo carrito.
                for p in ["pancho", "hamburguesa", "papas_en_cajita"] {
                    if let Some(cfg) = arranque::config_para(p) {
                        c.bind_mut().rearmar(cfg);
                    }
                    let m = menu(&c);
                    let n = c.bind().accesorios_puestos().len();
                    self.chequear(m == [p], &format!("REQ-ARR-02 rearmado para {p}: menú {m:?}, {n} accesorios"));
                }
                let errores = self.base().get_tree().get_nodes_in_group("errores_carrito").len();
                self.chequear(errores == 0, "REQ-ARR-02 los carritos del arranque se arman sin errores");
                c.queue_free();
                return true;
            }
        }
        self.fase5 += 1;
        false
    }
}
