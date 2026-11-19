//! Prueba de humo de SPEC-029 (freír papas): en la freidora doble del carro de las papas,
//! prende una cuba, la deja a 180 °C, pone una papa cortada en el colador con el jugador, lo
//! baja y espera que salgan papas fritas Cocidas; lo sube y saca las papas agarrándolas.

use carrito_core::coccion::Punto;
use godot::classes::Engine;
use godot::prelude::*;

use super::{PruebaHumo, material_pieza, todos};
use crate::comida::Comida;
use crate::freidora::{Colador, Freidora};
use crate::jugador::Jugador;

/// Cuadros como mucho esperando que la papa se fría (con el tiempo ×6: ~10 min de juego).
const ESPERA_MAX: u32 = 6000;
const ACELERADO: f64 = 6.0;

impl PruebaHumo {
    fn freidora_de_papas(&self) -> Option<Gd<Freidora>> {
        let carro = self.carro_papas.clone()?.upcast::<Node>();
        todos::<Freidora>(&carro).pop()
    }

    /// Para al jugador delante de la freidora, un poco alto (mira desde arriba, sin que tape
    /// el borde de la cuba), apuntando al centro del colador.
    fn mirar_colador(&self, j: &mut Gd<Jugador>, col: &Gd<Comida>) {
        let carro_y = self.carro_papas.clone().map(|c| c.get_global_position().y).unwrap_or(0.0);
        let pc = col.get_global_position();
        j.set_global_position(Vector3::new(pc.x, carro_y + 0.3, pc.z + 0.6));
        j.bind_mut().apuntar_a(pc + Vector3::new(0.0, 0.03, 0.0));
    }

    /// Una fase por llamada; devuelve true al terminar.
    pub(super) fn chequear_freir(&mut self) -> bool {
        let mundo = self.mundo();
        let Some(mut f) = self.freidora_de_papas() else {
            self.chequear(false, "REQ-FRE-04 el carro de las papas tiene una freidora");
            return true;
        };
        let Some(mut j) = todos::<Jugador>(&mundo).pop() else {
            self.chequear(false, "REQ-FRE-07 hay jugador");
            return true;
        };
        let colador = f.bind().colador(1).map(|(c, _)| c);
        match self.fase_freir {
            0 => {
                let (cubas, t0, t1) = { (f.bind().cantidad_cubas(), f.bind().temperatura(0), f.bind().temperatura(1)) };
                let arriba = f.bind().colador(0).is_some_and(|(_, abajo)| !abajo)
                    && f.bind().colador(1).is_some_and(|(_, abajo)| !abajo);
                self.chequear(
                    cubas == 2 && t0 == 20.0 && t1 == 20.0 && arriba,
                    &format!("REQ-FRE-04/08 doble: 2 cubas a 20 °C ({t0}, {t1}) con su colador arriba ({arriba})"),
                );
                // REQ-FRE-05: E prende solo la segunda cuba.
                f.bind_mut().alternar(1);
                self.esperar(120);
            }
            1 => {
                let (t0, t1) = (f.bind().temperatura(0), f.bind().temperatura(1));
                let nodo = f.clone().upcast::<Node>();
                let luz =
                    |n: &str| material_pieza(&nodo, n).map(|m| m.get_emission_energy_multiplier()).unwrap_or(-1.0);
                let (l1, l2) = (luz("pieza_piloto_1"), luz("pieza_piloto_2"));
                self.chequear(
                    t0 == 20.0 && (t1 - 25.0).abs() < 0.5 && f.bind().encendida(1) && l1 == 0.0 && l2 > 0.0,
                    &format!(
                        "REQ-FRE-04/05 la cuba 2 sube 2,5 °C/s sola ({t0:.1}, {t1:.1}) y prende su piloto ({l1}, {l2})"
                    ),
                );
                let cartel = f.bind().cartel(f.get_global_position() + Vector3::new(0.13, 0.0, 0.0));
                self.chequear(cartel.starts_with("[E] Apagar freidora 2"), &format!("REQ-FRE-05 cartel: {cartel}"));
                // Acelera: el aceite ya caliente (como otros chequeos que fijan la temperatura).
                f.bind_mut().set_temperatura(1, 180.0);
                // REQ-FRE-07: con una papa cortada en la mano, colocar sobre el colador la deja adentro.
                let Some(col) = colador else {
                    self.chequear(false, "REQ-FRE-07 la cuba 2 tiene colador");
                    return true;
                };
                let pc = col.get_global_position();
                let papa = self.agregar_comida("papa_cortada", Vector3::new(pc.x, pc.y + 0.4, pc.z + 0.5));
                j.bind_mut().agarrar(papa.clone().upcast());
                self.mirar_colador(&mut j, &col);
                j.bind_mut().colocar();
                self.papa_freir = Some(papa);
                self.esperar(5);
            }
            2 => {
                let papa = self.papa_freir.clone().unwrap();
                let col = colador.clone().unwrap();
                let adentro = Colador::de(&col).is_some_and(|c| c.bind().contenido().contains(&papa));
                self.chequear(
                    adentro && papa.is_freeze_enabled(),
                    "REQ-FRE-07 la papa cortada queda adentro del colador",
                );
                // REQ-FRE-08: E sobre el colador lo baja.
                self.mirar_colador(&mut j, &col);
                j.bind_mut().usar();
                self.esperar(40);
            }
            3 => {
                let papa = self.papa_freir.clone().unwrap();
                let abajo = f.bind().colador(1).is_some_and(|(_, abajo)| abajo);
                let local = f.get_global_transform().affine_inverse() * papa.get_global_position();
                self.chequear(
                    abajo && local.y < 0.19 && local.y > 0.1055,
                    &format!("REQ-FRE-08 E baja el colador y la papa queda en el aceite (y = {:.3})", local.y),
                );
                Engine::singleton().set_time_scale(ACELERADO);
                self.cuadros_freir = 0;
            }
            4 => {
                let papa = self.papa_freir.clone().unwrap();
                self.cuadros_freir += 1;
                if papa.bind().producto() != "papas_fritas" && self.cuadros_freir < ESPERA_MAX {
                    return false; // se repite esta fase
                }
                Engine::singleton().set_time_scale(1.0);
                let p = papa.bind();
                let col = colador.clone().unwrap();
                let sigue = Colador::de(&col).is_some_and(|c| c.bind().contenido().contains(&papa));
                let segundos = self.cuadros_freir as f64 * ACELERADO / 60.0;
                self.chequear(
                    p.producto() == "papas_fritas" && p.punto() == Some(Punto::Cocido) && sigue,
                    &format!(
                        "REQ-FRE-09/10 a 180 °C sale papas fritas Cocida en el colador ({}, {:?}, {:.0} °C, ~{segundos:.0} s)",
                        p.producto(),
                        p.punto(),
                        p.temperatura().unwrap_or(0.0)
                    ),
                );
                drop(p);
                // REQ-FRE-08: E otra vez lo sube.
                self.mirar_colador(&mut j, &col);
                j.bind_mut().usar();
                self.esperar(40);
            }
            5 => {
                let papa = self.papa_freir.clone().unwrap();
                let local = f.get_global_transform().affine_inverse() * papa.get_global_position();
                let arriba = f.bind().colador(1).is_some_and(|(_, abajo)| !abajo);
                self.chequear(
                    arriba && local.y - 0.017 > 0.19,
                    &format!("REQ-FRE-08 E sube el colador: las papas escurren encima del aceite (y = {:.3})", local.y),
                );
                // Las papas se sacan agarrándolas.
                j.bind_mut().agarrar(papa.clone().upcast());
                self.esperar(3);
            }
            _ => {
                let papa = self.papa_freir.clone().unwrap();
                let col = colador.clone().unwrap();
                let vacio = Colador::de(&col).is_some_and(|c| c.bind().porciones() == 0);
                self.chequear(
                    vacio && !papa.is_freeze_enabled() && papa.bind().sostenida,
                    "REQ-FRE-08 las papas fritas se sacan del colador agarrándolas",
                );
                j.bind_mut().soltar();
                let t0 = f.bind().temperatura(0);
                let sigue = f.bind().encendida(1);
                self.chequear(
                    t0 < 20.5 && sigue,
                    &format!("REQ-FRE-05 la cuba 2 sigue prendida y la otra siguió apagada ({t0:.1} °C)"),
                );
                return true;
            }
        }
        self.fase_freir += 1;
        false
    }
}
