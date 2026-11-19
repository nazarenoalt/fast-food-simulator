//! Prueba de humo de los autos que se renuevan (TASK-0508): REQ-AMB-17.

use carrito_core::{caminos, ciudad};

use super::{PruebaHumo, todos};
use crate::transito::Autos;

impl PruebaHumo {
    /// Para este momento ya pasaron varios minutos de juego y los autos dieron la vuelta:
    /// cada uno salió y el nuevo entró en un punto tapado desde el carrito, con otro color.
    /// Devuelve true.
    pub(super) fn chequear_autos(&mut self) -> bool {
        let mundo = self.mundo();
        let Some(autos) = todos::<Autos>(&mundo).pop() else {
            self.chequear(false, "REQ-AMB-17 hay autos");
            return true;
        };
        let vueltas = autos.bind().vueltas().to_vec();
        let edificios = ciudad::edificios();
        let ojo = caminos::PUNTO_CARRITO;
        let a_la_vista: Vec<_> = vueltas
            .iter()
            .filter(|v| {
                !caminos::tapado(ojo, [v.sale.x, v.sale.y], &edificios)
                    || !caminos::tapado(ojo, [v.entra.x, v.entra.y], &edificios)
            })
            .collect();
        let mismo_color = vueltas.iter().filter(|v| v.color_antes == v.color_despues).count();
        self.chequear(
            !vueltas.is_empty() && a_la_vista.is_empty() && mismo_color == 0,
            &format!(
                "REQ-AMB-17 los autos salen y entran tapados, como otro auto ({} vueltas, a la vista: {a_la_vista:?}, \
                 mismo color: {mismo_color})",
                vueltas.len()
            ),
        );
        true
    }
}
