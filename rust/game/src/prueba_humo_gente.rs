//! Prueba de humo de la gente que se renueva (TASK-0506): REQ-AMB-15 y REQ-AMB-16.

use carrito_core::caminos::{self, TipoNodo};
use carrito_core::ciudad;
use godot::prelude::*;

use super::{PruebaHumo, todos};
use crate::carrito::Carrito;
use crate::gente::Gente;

impl PruebaHumo {
    /// Para este momento ya pasaron varios minutos de juego y se fue gente: todos
    /// desaparecieron en una salida del borde del mapa, sin que se vea desde el carrito, y
    /// nadie se ve igual que otro presente ni que los últimos que se fueron. Devuelve true.
    pub(super) fn chequear_gente_se_renueva(&mut self) -> bool {
        let mundo = self.mundo();
        let Some(gente) = todos::<Gente>(&mundo).pop() else {
            self.chequear(false, "REQ-AMB-15 hay gente");
            return true;
        };
        let idas = gente.bind().desapariciones();
        // Desde donde está el carrito del jugador (el de la escena principal).
        let carrito = todos::<Carrito>(&mundo)
            .into_iter()
            .map(|c| c.get_global_position())
            .min_by(|a, b| a.distance_to(punto_carrito()).total_cmp(&b.distance_to(punto_carrito())))
            .unwrap_or(punto_carrito());
        let ojo = [carrito.x, carrito.z];
        let red = caminos::red();
        let salidas = red.de_tipo(|t| *t == TipoNodo::Salida);
        let edificios = ciudad::edificios();
        let mal: Vec<Vector3> = idas
            .iter()
            .copied()
            .filter(|p| {
                let en_salida = salidas.iter().any(|&s| (red.pos[s][0] - p.x).hypot(red.pos[s][1] - p.z) < 1.5);
                !en_salida || !caminos::tapado(ojo, [p.x, p.z], &edificios)
            })
            .collect();
        self.chequear(
            !idas.is_empty() && mal.is_empty(),
            &format!(
                "REQ-AMB-15 la gente se va por el borde, fuera de la vista ({} se fueron, a la vista: {mal:?})",
                idas.len()
            ),
        );
        self.chequear(
            gente.bind().apariencias_sin_repetir(),
            "REQ-AMB-16 nadie se ve igual que otro presente ni que los últimos que se fueron",
        );
        true
    }
}

fn punto_carrito() -> Vector3 {
    Vector3::new(caminos::PUNTO_CARRITO[0], 0.0, caminos::PUNTO_CARRITO[1])
}
