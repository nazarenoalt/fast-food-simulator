//! Prueba de humo de esperar en el cordón si viene un auto (REQ-AMB-18). (TASK-0509)

use carrito_core::autos::{self, Recorrido};
use carrito_core::caminos::Z_VEREDA_PEATONES;
use carrito_core::ciudad::SENDAS;
use carrito_core::cruces;
use godot::prelude::*;

use super::{PruebaHumo, todos};
use crate::gente::Gente;
use crate::peaton::Peaton;
use crate::transito::Autos;

/// Los dos casos armados a mano: (desde, ruta). Uno cruza la calle por la senda del este y el
/// otro la calle lateral del este, hacia la salida del borde; los dos arrancan a 0,3 m del
/// cordón.
fn casos() -> [(Vector3, Vec<Vector3>); 2] {
    let x = SENDAS[1];
    let v = |x: f32, z: f32| Vector3::new(x, 0.0, z);
    [
        (v(x, -24.7), vec![v(x, -36.0)]),
        (v(45.7, Z_VEREDA_PEATONES), vec![v(50.0, Z_VEREDA_PEATONES), v(55.0, -15.0), v(59.5, -5.0)]),
    ]
}

// Lugares en `notas5`.
const ID: usize = 0; // id del peatón de cada caso (dos lugares)
const DESDE: usize = 2; // cuadro en que se lo puso
const ESPERO: usize = 4; // 1 si esperó en el cordón antes de bajar
const CRUZO: usize = 6; // 1 si terminó de cruzar
const PELIGROS: usize = 8; // veces que alguien estuvo en la calzada justo delante de un auto rápido
const PARADAS: usize = 9; // paradas en el cordón al empezar
const LARGO: usize = 10;

impl PruebaHumo {
    /// Se llama cada cuadro hasta que devuelve true (brazo de la cadena del paso 31).
    /// REQ-AMB-18: cuando un auto está a unos 2 s de la senda (y de la lateral), aparece
    /// alguien en el cordón que va a cruzar: tiene que esperar sin bajar, y cruzar después.
    /// Mientras tanto, nadie puede estar en la calzada justo delante de un auto rápido.
    pub(super) fn chequear_cruces(&mut self) -> bool {
        let mundo = self.mundo();
        let (Some(mut gente), Some(autos)) = (todos::<Gente>(&mundo).pop(), todos::<Autos>(&mundo).pop()) else {
            self.chequear(false, "REQ-AMB-18 hay gente y autos");
            return true;
        };
        if self.notas5.len() < LARGO {
            self.notas5 = vec![-1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, gente.bind().paradas_en_cordon() as f64];
        }
        let recorridos: Vec<Recorrido> = (0..autos::CARRILES.len()).map(autos::recorrido).collect();
        let estado = autos.bind().estado();
        let peatones = todos::<Peaton>(&mundo);

        // Nadie en la calzada a menos de 1,5 m delante de la trompa de un auto rápido.
        for p in &peatones {
            let q = p.get_global_position();
            if !cruces::en_calzada([q.x, q.z]) {
                continue;
            }
            for &(carril, s, v) in &estado {
                let (c, d) = recorridos[carril].punto(s);
                let rel = [q.x - c[0] - d[0] * 2.1, q.z - c[1] - d[1] * 2.1];
                let adelante = rel[0] * d[0] + rel[1] * d[1];
                let costado = (rel[0] * d[1] - rel[1] * d[0]).abs();
                if v > 6.0 && (0.0..1.5).contains(&adelante) && costado < 1.2 {
                    self.notas5[PELIGROS] += 1.0;
                }
            }
        }

        let transcurrido = self.cuadro - self.cuadro5;
        for (k, (desde, ruta)) in casos().into_iter().enumerate() {
            if self.notas5[ID + k] < 0.0 {
                // Se espera un auto que llegue al paso en 1,5 a 2,5 s.
                let mut puntos = vec![[desde.x, desde.z]];
                puntos.extend(ruta.iter().map(|v| [v.x, v.z]));
                let Some(cruce) = cruces::cruce(&puntos) else { continue };
                let justo = estado.iter().any(|&(carril, s, v)| {
                    cruces::tiempo_hasta_el_paso(&recorridos[carril], s, v, &cruce)
                        .is_some_and(|t| (1.5..2.5).contains(&t))
                });
                if justo {
                    let id = gente.bind_mut().probar_cruce(desde, ruta);
                    self.notas5[ID + k] = id as f64;
                    self.notas5[DESDE + k] = self.cuadro as f64;
                }
                continue;
            }
            let id = self.notas5[ID + k] as u64;
            let Some(p) = peatones.iter().find(|p| p.bind().id == id) else {
                // Ya se fue por la salida (o por la punta de la ruta): cruzó.
                self.notas5[CRUZO + k] = 1.0;
                continue;
            };
            let q = p.get_global_position();
            let en_calle = cruces::en_calzada([q.x, q.z]);
            if self.notas5[CRUZO + k] == 0.0 && self.notas5[ESPERO + k] == 0.0 {
                if en_calle {
                    // Bajó sin esperar: queda en 0 y se cuenta al final.
                    self.notas5[ESPERO + k] = -1.0;
                } else if gente.bind().espero_en_cordon(id) {
                    self.notas5[ESPERO + k] = 1.0;
                }
            }
            // Cruzó: pasó la calzada y subió del otro lado.
            let del_otro_lado = if k == 0 { q.z < -33.0 } else { q.x > 54.0 };
            if del_otro_lado && !en_calle {
                self.notas5[CRUZO + k] = 1.0;
            }
        }

        let listos = (0..2).all(|k| self.notas5[CRUZO + k] == 1.0);
        // Casos armados: hasta 40 s (esperar el auto + de 10 a 20 s en el cordón + cruzar).
        if !listos && transcurrido < 60 * 40 {
            return false;
        }
        for (k, que) in ["la calle por la senda", "una calle lateral"].iter().enumerate() {
            let puesto = self.notas5[ID + k] >= 0.0;
            let espero = self.notas5[ESPERO + k] == 1.0;
            let cruzo = self.notas5[CRUZO + k] == 1.0;
            let tardo = if puesto { (self.cuadro as f64 - self.notas5[DESDE + k]) / 60.0 } else { 0.0 };
            self.chequear(
                puesto && espero && cruzo,
                &format!(
                    "REQ-AMB-18 quien va a cruzar {que} con un auto a 2 s espera en el cordón y cruza después \
                     (puesto: {puesto}, esperó: {espero}, cruzó: {cruzo}, {tardo:.1} s)"
                ),
            );
        }
        let paradas = gente.bind().paradas_en_cordon() as f64 - self.notas5[PARADAS];
        let peligros = self.notas5[PELIGROS];
        self.chequear(
            paradas >= 2.0 && peligros == 0.0,
            &format!(
                "REQ-AMB-18 paradas en el cordón: {paradas}; veces que alguien estuvo en la calzada delante de un auto \
                 rápido: {peligros}"
            ),
        );
        true
    }
}
