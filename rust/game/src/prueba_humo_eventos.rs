//! Prueba de humo de feria y partido (SPEC-019). (TASK-0505)

use carrito_core::eventos::Modificador;

use super::{PruebaHumo, todos};
use crate::datos::plaza;
use crate::dia_noche::DiaNoche;
use crate::gente::Gente;

/// Cuadros que se espera después de mover el reloj para que `Gente` lo lea.
const ESPERA: u32 = 3;
/// Cuadros como mucho para ver a alguien saltando en el festejo.
const ESPERA_FESTEJO: u32 = 1800;

impl PruebaHumo {
    /// Sábado 12:00: feria con 6 puestos y vendedores, más gente que el viernes y el aviso del
    /// día; viernes sin puestos; miércoles 19:00 media plaza con camiseta, 22:00 casi vacía y
    /// 23:30 festejo con saltos. Deja el reloj (día y minuto) como estaba. Devuelve true
    /// cuando termina.
    pub(super) fn chequear_eventos(&mut self) -> bool {
        let mundo = self.mundo();
        let (Some(mut gente), Some(mut dn)) = (todos::<Gente>(&mundo).pop(), todos::<DiaNoche>(&mundo).pop()) else {
            self.chequear(false, "REQ-EVE-01 hay gente y reloj");
            return true;
        };
        if self.cuadro < self.cuadro5 + ESPERA && self.fase5 > 0 && self.fase5 != 6 {
            return false;
        }
        // Lo que pide la agenda sola (sin eventos) a una hora, para comparar.
        let sin_eventos = |hora: f32| plaza().agenda.cantidad_objetivo(hora, &Modificador::default());
        let siguiente = |yo: &mut Self| {
            yo.fase5 += 1;
            yo.cuadro5 = yo.cuadro;
        };
        match self.fase5 {
            0 => {
                // Se guardan el día y la hora para dejarlos como estaban.
                let (dia, minuto) = {
                    let d = dn.bind();
                    (d.dia() as f64, d.hora() as f64 * 60.0)
                };
                self.notas5 = vec![dia, minuto];
                dn.bind_mut().set_dia(2);
                dn.bind_mut().set_minuto(12.0 * 60.0);
                siguiente(self);
                false
            }
            1 => {
                let texto = dn.bind().hora_texto();
                self.chequear(
                    texto.contains("Día 2 · Sáb 12:00"),
                    &format!("REQ-EVE-01 la hora dice el día: «{texto}»"),
                );
                let aviso = gente.bind().ultimo_aviso();
                self.chequear(
                    aviso.as_deref() == Some("Hoy: feria en la plaza de 10 a 18"),
                    &format!("REQ-EVE-03 aviso del sábado: {aviso:?}"),
                );
                let (puestos, vendedores) = gente.bind().puestos_y_vendedores();
                self.chequear(
                    puestos == 6 && vendedores == 6,
                    &format!("REQ-EVE-05 sábado 12:00: {puestos} puestos y {vendedores} vendedores"),
                );
                let objetivo = gente.bind().objetivo_gente();
                let base = sin_eventos(12.0);
                self.chequear(
                    objetivo as f32 >= base as f32 * 1.4,
                    &format!("REQ-EVE-06 feria: la plaza quiere {objetivo} personas (sin feria {base})"),
                );
                dn.bind_mut().set_dia(1);
                siguiente(self);
                false
            }
            2 => {
                let (puestos, vendedores) = gente.bind().puestos_y_vendedores();
                self.chequear(
                    puestos == 0 && vendedores == 0,
                    &format!("REQ-EVE-05 viernes 12:00 sin feria ({puestos} puestos, {vendedores} vendedores)"),
                );
                dn.bind_mut().set_dia(6);
                dn.bind_mut().set_minuto(19.0 * 60.0);
                siguiente(self);
                false
            }
            3 => {
                let ids = gente.bind_mut().probar_paseantes(40);
                let con = ids.iter().filter(|id| gente.bind().con_camiseta(**id)).count();
                let n = ids.len().max(1);
                self.chequear(
                    con * 4 >= n && con * 4 <= n * 3,
                    &format!("REQ-EVE-07 miércoles 19:00: {con} de {} llegan con camiseta", ids.len()),
                );
                dn.bind_mut().set_minuto(22.0 * 60.0);
                siguiente(self);
                false
            }
            4 => {
                let objetivo = gente.bind().objetivo_gente();
                let base = sin_eventos(22.0);
                self.chequear(
                    (objetivo as f32) <= base as f32 * 0.3 + 1.0,
                    &format!("REQ-EVE-08 durante el partido la plaza quiere {objetivo} personas (sin partido {base})"),
                );
                dn.bind_mut().set_minuto(23.0 * 60.0 + 30.0);
                siguiente(self);
                false
            }
            5 => {
                // Los del festejo, ya en su lugar (todos con camiseta).
                gente.bind_mut().probar_presentes(16);
                siguiente(self);
                false
            }
            6 => {
                let saltando = gente.bind().saltando();
                let paso = self.cuadro - self.cuadro5;
                if saltando == 0 && paso < ESPERA_FESTEJO {
                    return false;
                }
                self.chequear(
                    saltando > 0,
                    &format!("REQ-EVE-09 festejo 23:30: {saltando} saltando con camiseta (tras {paso} cuadros)"),
                );
                let dia = self.notas5.first().copied().unwrap_or(1.0) as u32;
                let minuto = self.notas5.get(1).copied().unwrap_or(17.0 * 60.0);
                dn.bind_mut().set_dia(dia);
                dn.bind_mut().set_minuto(minuto);
                siguiente(self);
                false
            }
            7 => {
                let d = dn.bind();
                let esperado = plaza().modificador(d.dia(), d.hora()).activo("feria/puestos");
                drop(d);
                let (puestos, _) = gente.bind().puestos_y_vendedores();
                self.chequear(
                    (puestos > 0) == esperado,
                    &format!("REQ-EVE-05 al volver el reloj, los puestos quedan como corresponde ({puestos})"),
                );
                true
            }
            _ => true,
        }
    }
}
