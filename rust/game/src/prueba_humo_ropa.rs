//! Prueba de humo de ropa y actividades de día y de noche (REQ-RUT-10, REQ-RUT-11). (TASK-0507)

use carrito_core::rutinas::Perfil;
use godot::prelude::Gd;

use super::{PruebaHumo, todos};
use crate::dia_noche::DiaNoche;
use crate::gente::Gente;
use crate::peaton::Peaton;

/// Cuánto camina como mucho alguien que no trota (m/s).
const MAS_RAPIDO_SIN_TROTAR: f32 = 2.3;

impl PruebaHumo {
    /// Un jueves (sin eventos): a las 13:00 todos los que llegan van de manga corta; a las 22:30,
    /// todos de manga larga, nadie trota ni pasea al perro. Deja día y hora como estaban.
    /// Se llama cada cuadro hasta que devuelve true.
    pub(super) fn chequear_ropa(&mut self) -> bool {
        let mundo = self.mundo();
        let (Some(mut gente), Some(mut dn)) = (todos::<Gente>(&mundo).pop(), todos::<DiaNoche>(&mundo).pop()) else {
            self.chequear(false, "REQ-RUT-10 hay gente y reloj");
            return true;
        };
        match self.fase5 {
            0 => {
                self.notas5 = vec![dn.bind().hora() as f64 * 60.0, dn.bind().dia() as f64];
                dn.bind_mut().set_dia(11);
                dn.bind_mut().set_minuto(13.0 * 60.0);
                self.fase5 = 1;
                false
            }
            1 | 3 => {
                // Se espera un cuadro para que Gente lea la hora nueva.
                self.fase5 += 1;
                false
            }
            2 => {
                let ids = gente.bind_mut().probar_paseantes(10);
                let llegados = llegados(&mundo, &ids);
                let largas = llegados.iter().filter(|p| p.bind().apariencia().manga_larga).count();
                self.chequear(
                    !llegados.is_empty() && largas == 0,
                    &format!(
                        "REQ-RUT-10 a las 13:00 todos de manga corta ({largas} de {} con manga larga)",
                        llegados.len()
                    ),
                );
                dn.bind_mut().set_minuto(22.0 * 60.0 + 30.0);
                self.fase5 = 3;
                false
            }
            4 => {
                let ids = gente.bind_mut().probar_paseantes(10);
                let llegados = llegados(&mundo, &ids);
                let cortas = llegados.iter().filter(|p| !p.bind().apariencia().manga_larga).count();
                self.chequear(
                    !llegados.is_empty() && cortas == 0,
                    &format!("REQ-RUT-10 a las 22:30 todos con campera o buzo ({cortas} de {} sin)", llegados.len()),
                );
                let trotan = llegados
                    .iter()
                    .filter(|p| {
                        p.bind().velocidad() > MAS_RAPIDO_SIN_TROTAR
                            || gente.bind().perfil_de(p.bind().id) == Some(Perfil::Corredor)
                    })
                    .count();
                let perros = llegados.iter().filter(|p| p.bind().con_perro()).count();
                self.chequear(
                    trotan == 0 && perros == 0,
                    &format!("REQ-RUT-11 a las 22:30 nadie trota ({trotan}) ni pasea al perro ({perros})"),
                );
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

/// Los peatones recién llegados con esos ids.
fn llegados(mundo: &Gd<godot::prelude::Node>, ids: &[u64]) -> Vec<Gd<Peaton>> {
    todos::<Peaton>(mundo).into_iter().filter(|p| ids.contains(&p.bind().id)).collect()
}
