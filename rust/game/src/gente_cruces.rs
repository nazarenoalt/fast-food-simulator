//! TASK-0509 · REQ-AMB-18: los peatones esperan en el cordón si viene un auto.
//! Submódulo de `gente`: ve los campos de `Gente`.

use std::collections::{HashMap, HashSet};

use carrito_core::autos::{self, Recorrido};
use carrito_core::cruces;
use carrito_core::peatones::Plan;
use carrito_core::rutinas::Perfil;
use godot::prelude::*;

use super::Gente;
use crate::peaton::Accion;
use crate::transito::{self, Autos};
use crate::util;

/// Cuánto se para cada vez; si el auto sigue viniendo, vuelve a pararse.
const ESPERA_CORTA: f32 = 0.4;

/// Alguien parado en un cordón: en qué cordón, dónde se paró y cuánto lleva esperando.
struct Espera {
    cordon: [f32; 2],
    donde: Vector3,
    segundos: f32,
}

/// Estado propio de esta tarea.
#[derive(Default)]
pub(super) struct Estado {
    recorridos: Vec<Recorrido>,
    esperas: HashMap<u64, Espera>,
    /// Para la prueba de humo: cuántas veces alguien se paró en un cordón y quiénes.
    paradas: u32,
    esperaron: HashSet<u64>,
}

impl Gente {
    /// Cada cuadro, después de avisar vecinos. REQ-AMB-18: quien camina y está por bajar a
    /// una calzada (la calle o una lateral) mira si viene un auto a menos de 3 s del paso;
    /// si viene, espera en el cordón mirándolo, y cruza cuando pasó. Si el paso sigue ocupado
    /// más de `ESPERA_MAXIMA`, se conforma con un hueco más corto (los autos frenan por él,
    /// REQ-AMB-08), y pasado `ESPERA_TOPE` cruza igual.
    pub(super) fn cuadro_cruces(&mut self, _dt: f32) {
        let yo = self.to_gd();
        let Some(autos) = util::unico::<Autos>(&yo, transito::GRUPO) else { return };
        let est = &mut self.est_cruces;
        if est.recorridos.is_empty() {
            est.recorridos = (0..autos::CARRILES.len()).map(autos::recorrido).collect();
        }
        let estado_autos = autos.bind().estado();
        let mut vivos = HashSet::new();
        for p in self.peatones.iter_mut() {
            let (id, ruta) = {
                let b = p.bind();
                (b.id, b.ruta_pendiente().map(|r| r.iter().take(4).map(|v| [v.x, v.z]).collect::<Vec<_>>()))
            };
            vivos.insert(id);
            // Solo quien camina (no el que ya está esperando, sentado o en la fila).
            let Some(ruta) = ruta else { continue };
            let pos = p.get_global_position();
            let mut puntos = vec![[pos.x, pos.z]];
            puntos.extend(ruta);
            let cruce = cruces::cruce(&puntos).filter(|c| c.distancia < 2.0);
            let Some(c) = cruce else {
                // Ya cruzó (o no va a cruzar): la próxima vez empieza de cero.
                est.esperas.remove(&id);
                continue;
            };
            if !c.en_el_cordon() {
                continue;
            }
            // Lo que lleva esperando en este cordón (si es otro, empieza de cero).
            let esperado = est
                .esperas
                .get(&id)
                .filter(|e| (e.cordon[0] - c.cordon[0]).hypot(e.cordon[1] - c.cordon[1]) < 1.0)
                .map_or(0.0, |e| e.segundos);
            let margen = cruces::margen_pedido(esperado);
            let viene = estado_autos
                .iter()
                .find(|&&(carril, s, v)| cruces::viene_auto_antes(&est.recorridos[carril], s, v, &c, margen));
            let Some(&(carril, s, _)) = viene else { continue };
            if esperado == 0.0 {
                est.esperas.insert(id, Espera { cordon: c.cordon, donde: pos, segundos: 0.0 });
            }
            let Some(espera) = est.esperas.get_mut(&id) else { continue };
            if espera.segundos == 0.0 {
                est.paradas += 1;
                est.esperaron.insert(id);
            } else {
                // Entre una espera corta y la siguiente alcanzó a dar un paso (un cuadro): vuelve
                // a donde estaba, para no ir bajando de a poco a la calzada.
                p.set_global_position(espera.donde);
            }
            espera.segundos += ESPERA_CORTA;
            let (a, _) = est.recorridos[carril].punto(s);
            let mirar = Some(Vector3::new(a[0], 0.0, a[1]));
            p.bind_mut().intercalar(Accion::Esperar { mirar, segundos: ESPERA_CORTA });
        }
        est.esperas.retain(|id, _| vivos.contains(id));
        est.esperaron.retain(|id| vivos.contains(id));
    }

    /// Para pruebas: cuántas veces alguien se paró en un cordón porque venía un auto.
    pub fn paradas_en_cordon(&self) -> u32 {
        self.est_cruces.paradas
    }

    /// Para pruebas: ¿esta persona esperó en un cordón (desde que llegó)?
    pub fn espero_en_cordon(&self, id: u64) -> bool {
        self.est_cruces.esperaron.contains(&id)
    }

    /// Para pruebas: pone a alguien en `desde` que camina por `ruta` y después se va.
    pub fn probar_cruce(&mut self, desde: Vector3, ruta: Vec<Vector3>) -> u64 {
        let en = self.red.mas_cercano(desde.x, desde.z);
        let mut p = self.agregar(en, vec![Accion::Caminar(ruta), Accion::Desaparecer], Perfil::Paseante, Plan::Pasear);
        p.set_global_position(desde);
        p.bind().id
    }
}
