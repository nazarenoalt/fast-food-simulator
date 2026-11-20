//! Prueba de humo de la etapa 2.5 · agente A: REQ-CLI-01 (menú), REQ-CLI-06, REQ-ARR-05, REQ-EVE-09, REQ-EVE-10, REQ-PAR-02, REQ-PAR-05. (TASK-0250)
//!
//! REQ-PAR-02 y REQ-PAR-05 (carbón y chorizo) se prueban en core y en la cadena de la parrilla
//! de `prueba_humo.rs`; acá van la primera semana, la paciencia, el menú y el festejo.

use carrito_core::clientes;
use carrito_core::eventos::{self, Modificador};

use super::{PruebaHumo, todos};
use crate::carrito::Carrito;
use crate::datos::plaza;
use crate::dia_noche::DiaNoche;
use crate::gente::Gente;

/// Cuadros que se espera después de mover el reloj para que `Gente` lo lea.
const ESPERA: u32 = 3;
/// Clientes que se intenta traer con la tecla C (más que los lugares de la fila).
const INTENTOS_TECLA_C: usize = 6;

impl PruebaHumo {
    /// Día 1: la fila tiene 3 lugares y la tecla C no la pasa; la paciencia del primero es
    /// 150 s × su perfil; el factor del menú. Sábado 6 y domingo 7 (primera semana) sin
    /// eventos; sábado 13 vuelve la feria; el festejo del miércoles 10 da entre ×2 y ×4. Deja
    /// el reloj (día y minuto) como estaba. Devuelve true cuando termina.
    pub(super) fn chequear_balance(&mut self) -> bool {
        let mundo = self.mundo();
        let (Some(mut gente), Some(mut dn)) = (todos::<Gente>(&mundo).pop(), todos::<DiaNoche>(&mundo).pop()) else {
            self.chequear(false, "REQ-ARR-05 hay gente y reloj");
            return true;
        };
        if self.fase5 > 0 && self.cuadro < self.cuadro5 + ESPERA {
            return false;
        }
        let siguiente = |yo: &mut Self| {
            yo.fase5 += 1;
            yo.cuadro5 = yo.cuadro;
        };
        let sin_eventos = |hora: f32| plaza().agenda.cantidad_objetivo(hora, &Modificador::default());
        match self.fase5 {
            0 => {
                // Se guardan el día y la hora para dejarlos como estaban.
                let (dia, minuto) = {
                    let d = dn.bind();
                    (d.dia() as f64, d.hora() as f64 * 60.0)
                };
                self.notas5 = vec![dia, minuto];
                gente.bind_mut().vaciar_fila();
                dn.bind_mut().set_dia(1);
                dn.bind_mut().set_minuto(13.0 * 60.0);
                siguiente(self);
                false
            }
            1 => {
                // REQ-ARR-05: el día 1 la fila tiene 3 lugares; la tecla C la respeta.
                gente.bind_mut().vaciar_fila();
                let lugares = gente.bind().lugares_fila();
                let traidos = (0..INTENTOS_TECLA_C).filter(|_| gente.bind_mut().traer_cliente().is_some()).count();
                let largo = gente.bind().largo_fila();
                self.chequear(
                    lugares == 3 && traidos == 3 && largo == 3,
                    &format!(
                        "REQ-ARR-05 día 1: fila de {lugares} lugares, la tecla C trajo {traidos} de \
                         {INTENTOS_TECLA_C} y hay {largo} en la fila"
                    ),
                );
                // REQ-CLI-06: paciencia de 150 s por el factor del perfil (agenda.ron).
                let primero = gente.bind().paciencia_total_del_primero();
                let ok = primero
                    .is_some_and(|(perfil, total)| (total - 150.0 * plaza().agenda.paciencia(perfil)).abs() < 1e-3);
                self.chequear(ok, &format!("REQ-CLI-06 paciencia del primero: {primero:?} (150 s × perfil)"));
                // REQ-CLI-01: factor por el menú del carrito.
                let productos = todos::<Carrito>(&mundo).pop().map_or(0, |c| c.bind().menu().len());
                let factor = gente.bind().factor_menu();
                self.chequear(
                    productos >= 1 && (factor - (1.0 + 0.15 * (productos as f32 - 1.0))).abs() < 1e-5,
                    &format!("REQ-CLI-01 clientes ×{factor:.2} con {productos} productos en el menú"),
                );
                siguiente(self);
                false
            }
            2 => {
                // Un cuadro después, otra vez la tecla C: la fila sigue en 3.
                let otro = gente.bind_mut().traer_cliente();
                let largo = gente.bind().largo_fila();
                self.chequear(
                    otro.is_none() && largo == 3,
                    &format!("REQ-CLI-03 con la fila llena la tecla C no trae a nadie ({largo} en la fila)"),
                );
                gente.bind_mut().vaciar_fila();
                // REQ-EVE-10: sábado de la primera semana, a la hora de la feria.
                dn.bind_mut().set_dia(6);
                dn.bind_mut().set_minuto(12.0 * 60.0);
                siguiente(self);
                false
            }
            3 => {
                let texto = dn.bind().hora_texto();
                let (puestos, vendedores) = gente.bind().puestos_y_vendedores();
                let aviso = gente.bind().aviso_de_hoy();
                let factor = gente.bind().factor_eventos();
                let objetivo = gente.bind().objetivo_gente();
                self.chequear(
                    texto.contains("Sáb") && puestos == 0 && vendedores == 0 && aviso.is_none() && factor == 1.0,
                    &format!(
                        "REQ-EVE-10 «{texto}»: sin feria ({puestos} puestos, {vendedores} vendedores, \
                         aviso {aviso:?}, clientes ×{factor})"
                    ),
                );
                self.chequear(
                    objetivo == sin_eventos(12.0),
                    &format!("REQ-EVE-10 la plaza quiere {objetivo} personas, como sin eventos"),
                );
                self.chequear(
                    gente.bind().lugares_fila() == clientes::LUGARES_FILA,
                    "REQ-ARR-05 desde el día 6 la fila tiene 6 lugares",
                );
                // Domingo de la primera semana: tampoco hay partido (ni camisetas).
                dn.bind_mut().set_dia(7);
                dn.bind_mut().set_minuto(19.0 * 60.0);
                siguiente(self);
                false
            }
            4 => {
                let ids = gente.bind_mut().probar_paseantes(20);
                let con = ids.iter().filter(|id| gente.bind().con_camiseta(**id)).count();
                let factor = gente.bind().factor_eventos();
                self.chequear(
                    con == 0 && factor == 1.0 && gente.bind().aviso_de_hoy().is_none(),
                    &format!("REQ-EVE-10 domingo 7 19:00: {con} de {} con camiseta, clientes ×{factor}", ids.len()),
                );
                dn.bind_mut().set_minuto(23.0 * 60.0 + 30.0);
                siguiente(self);
                false
            }
            5 => {
                let factor = gente.bind().factor_eventos();
                self.chequear(factor == 1.0, &format!("REQ-EVE-10 domingo 7 23:30 sin festejo (clientes ×{factor})"));
                // La segunda semana vuelve la feria: sábado 13.
                dn.bind_mut().set_dia(13);
                dn.bind_mut().set_minuto(12.0 * 60.0);
                siguiente(self);
                false
            }
            6 => {
                let (puestos, vendedores) = gente.bind().puestos_y_vendedores();
                let aviso = gente.bind().aviso_de_hoy();
                let factor = gente.bind().factor_eventos();
                self.chequear(
                    puestos == 6 && vendedores == 6 && aviso.is_some() && (factor - 1.3).abs() < 1e-5,
                    &format!(
                        "REQ-EVE-10 sábado 13: vuelve la feria ({puestos} puestos, {vendedores} vendedores, \
                         aviso {aviso:?}, clientes ×{factor})"
                    ),
                );
                // REQ-EVE-09: festejo del miércoles 10.
                dn.bind_mut().set_dia(10);
                dn.bind_mut().set_minuto(23.0 * 60.0 + 30.0);
                siguiente(self);
                false
            }
            7 => {
                let factor = gente.bind().factor_eventos();
                let esperado = eventos::modificador(&plaza().eventos, 10, 23.5).clientes;
                self.chequear(
                    (2.0..=4.0).contains(&factor) && (factor - esperado).abs() < 1e-5,
                    &format!("REQ-EVE-09 festejo del miércoles 10: clientes ×{factor:.2} (entre ×2 y ×4)"),
                );
                // Se devuelve el reloj como estaba.
                let dia = self.notas5.first().copied().unwrap_or(9.0) as u32;
                let minuto = self.notas5.get(1).copied().unwrap_or(17.0 * 60.0);
                dn.bind_mut().set_dia(dia);
                dn.bind_mut().set_minuto(minuto);
                siguiente(self);
                false
            }
            8 => {
                let lugares = gente.bind().lugares_fila();
                self.chequear(
                    lugares == clientes::LUGARES_FILA,
                    &format!(
                        "REQ-ARR-05 al volver el reloj (día {}), la fila tiene {lugares} lugares",
                        dn.bind().dia()
                    ),
                );
                true
            }
            _ => true,
        }
    }
}
