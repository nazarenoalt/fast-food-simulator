//! TASK-0503 · SPEC-018: perfiles con comportamiento propio y grupos que caminan juntos
//! (REQ-RUT-05 a REQ-RUT-09, y "después de las 21 no hay chicos" de REQ-RUT-11).
//! Submódulo de `gente`: ve los campos de `Gente`. Las reglas están en `carrito_core::grupos`.

use std::collections::{HashMap, HashSet};

use carrito_core::caminos::TipoNodo;
use carrito_core::grupos as reglas;
use carrito_core::peatones::Plan;
use carrito_core::rutinas::Perfil;
use carrito_core::vestimenta;
use godot::prelude::*;

use super::{Gente, Origen};
use crate::datos::plaza;
use crate::peaton::{Accion, Peaton};

/// REQ-RUT-08: gente que llegó junta (en el orden de a dos en que camina).
struct Grupo {
    ids: Vec<u64>,
    /// Cuánto puede adelantarse uno antes de esperar (3 m; con chicos, menos).
    umbral: f32,
    /// REQ-RUT-07: el lugar de ronda que ocupa (índice de `reglas::lugares_ronda`).
    lugar: Option<usize>,
}

/// REQ-RUT-06: un chico de una familia.
struct Chico {
    adultos: Vec<u64>,
    vel_paseo: f32,
    vel_correr: f32,
}

/// Acciones que le quedan a un chico mientras da las vueltas a la fuente (después de las
/// vueltas: volver con los adultos, esperar, irse, desaparecer).
const PENDIENTES_EN_VUELTAS: usize = 4;

/// Estado propio de esta tarea.
#[derive(Default)]
pub(super) struct Estado {
    grupos: Vec<Grupo>,
    chicos: HashMap<u64, Chico>,
    /// REQ-RUT-05: oficinistas que sacan la comida al sentarse.
    por_comer: Vec<u64>,
    /// Los que ya están comiendo (para las pruebas).
    comiendo: HashSet<u64>,
    /// REQ-RUT-05, REQ-RUT-11: los que ya mandamos a casa (oficinistas a las 14:30, familias a
    /// las 21), para no volver a mandarlos.
    idos: HashSet<u64>,
}

impl Estado {
    /// ¿`id` es un chico de una familia? (REQ-RUT-06)
    pub(super) fn es_chico(&self, id: u64) -> bool {
        self.chicos.contains_key(&id)
    }
}

/// Cómo arranca cada integrante de un grupo.
struct Integrante {
    en: usize,
    /// Si arranca ya en su lugar (población inicial), dónde.
    pos: Option<Vector3>,
    acciones: Vec<Accion>,
    chico: bool,
}

fn v3(p: [f32; 2]) -> Vector3 {
    Vector3::new(p[0], 0.0, p[1])
}

/// REQ-RUT-08: la fila de atrás arranca un poco después.
fn demora(fila: usize) -> Option<Accion> {
    (fila > 0).then_some(Accion::Esperar { mirar: None, segundos: fila as f32 * reglas::DEMORA_FILA_S })
}

impl Gente {
    /// ¿`id` va en un grupo o es un chico de una familia? (Para que otras tareas no le
    /// cambien las acciones: los grupos se esperan y los chicos se siguen por sus acciones.)
    pub(super) fn en_grupo(&self, id: u64) -> bool {
        self.est_grupos.chicos.contains_key(&id) || self.est_grupos.grupos.iter().any(|g| g.ids.contains(&id))
    }

    /// Si `perfil` llega en grupo o tiene un comportamiento propio, arma a la gente acá y
    /// devuelve `true`; si no, `Gente` lo arma como un paseante común. REQ-RUT-05 a REQ-RUT-09
    pub(super) fn planear_grupo(&mut self, perfil: Perfil, desde_salida: bool) -> bool {
        if !reglas::arma_grupos(perfil) {
            // REQ-RUT-09: corredor, paseador, jubilado y trasnochado: paseantes comunes con su
            // perfil (trota, con perro, lento y sentado largo, solo).
            return false;
        }
        let plan = self.plan_para(perfil); // REQ-RUT-02, REQ-RUT-11
        self.armar_grupo(perfil, plan, desde_salida);
        true
    }

    /// REQ-RUT-05 a REQ-RUT-09: arma a un grupo de `perfil` con esa actividad. Devuelve los ids.
    fn armar_grupo(&mut self, perfil: Perfil, plan: Plan, desde_salida: bool) -> Vec<u64> {
        let agenda = &plaza().agenda;
        let mut n = agenda.tamano_grupo(&mut self.azar, perfil);
        let vel = agenda.velocidad(&mut self.azar, perfil);
        let inicio = if desde_salida { self.salida_al_azar() } else { self.al_azar(|t| *t == TipoNodo::Paso) };
        let salida = self.salida_al_azar();

        if perfil == Perfil::AlTrabajo {
            // REQ-RUT-09: cruza la plaza sin parar, de una salida a otra.
            return self.al_trabajo(inicio, vel);
        }

        // REQ-RUT-06, REQ-RUT-11: la familia, con sus chicos (a la noche, sin chicos).
        let mut chicos = vec![false; n];
        if perfil == Perfil::Familia {
            let (ad, ch) = reglas::composicion_familia(&mut self.azar, n, self.hora);
            n = ad + ch;
            chicos = intercalar_chicos(ad, ch);
        }
        let con_chicos = chicos.contains(&true);
        let mut plan = plan;
        // REQ-RUT-05: después de las 14:30 los oficinistas solo cruzan (y ya se van).
        let ya_se_van = (perfil == Perfil::Oficinista && reglas::oficinistas_se_van(self.hora))
            || (perfil == Perfil::Familia && reglas::familias_se_van(self.hora));
        if ya_se_van {
            plan = Plan::Pasear;
        }

        let mut lugar = None;
        let integrantes = match plan {
            Plan::Sentarse => self.sentarse_juntos(perfil, n, inicio, salida, desde_salida),
            Plan::Charlar => {
                lugar = self.lugar_libre();
                lugar.map(|l| self.ronda(perfil, n, l, inicio, salida, desde_salida))
            }
            Plan::Pasear if con_chicos => Some(self.a_la_fuente(&chicos, inicio, salida, desde_salida)),
            _ => None,
        };
        let integrantes = integrantes.unwrap_or_else(|| {
            lugar = None;
            self.pasear_juntos(n, inicio, salida)
        });

        // Se crean todos, con la misma velocidad (caminan juntos).
        let paleta = vestimenta::paleta(perfil, self.hora); // REQ-RUT-10
        let mut paleta_chicos = paleta.clone();
        paleta_chicos.altura = reglas::ALTURA_CHICOS; // REQ-RUT-06
        let mut ids = Vec::new();
        for (i, it) in integrantes.into_iter().enumerate() {
            let chico = it.chico || chicos.get(i).copied().unwrap_or(false);
            let pal = if chico { paleta_chicos.clone() } else { paleta.clone() };
            let mut p = self.agregar_con(it.en, it.acciones, perfil, plan, Origen::Nueva(pal), vel);
            if let Some(pos) = it.pos {
                p.set_global_position(pos);
            }
            let id = p.bind().id;
            ids.push(id);
            if chico {
                let vel_correr = self.azar.rango(reglas::VEL_CORRER[0], reglas::VEL_CORRER[1]);
                self.est_grupos.chicos.insert(id, Chico { adultos: Vec::new(), vel_paseo: vel, vel_correr });
            }
        }
        // REQ-RUT-06: cada chico sabe quiénes son sus adultos.
        let adultos: Vec<u64> = ids.iter().copied().filter(|id| !self.est_grupos.chicos.contains_key(id)).collect();
        for id in &ids {
            if let Some(c) = self.est_grupos.chicos.get_mut(id) {
                c.adultos = adultos.clone();
            }
        }
        // REQ-RUT-05: los oficinistas que se sientan sacan la comida.
        if perfil == Perfil::Oficinista && plan == Plan::Sentarse {
            self.est_grupos.por_comer.extend(&ids);
        }
        if ya_se_van {
            self.est_grupos.idos.extend(&ids);
        }
        if ids.len() > 1 || lugar.is_some() {
            let umbral = if con_chicos { reglas::UMBRAL_FAMILIA } else { reglas::UMBRAL_GRUPO };
            self.est_grupos.grupos.push(Grupo { ids: ids.clone(), umbral, lugar });
        }
        ids
    }

    /// Nodo de paso de la red más cercano a un punto.
    fn paso_cercano(&self, p: [f32; 2]) -> usize {
        self.red
            .de_tipo(|t| *t == TipoNodo::Paso)
            .into_iter()
            .min_by(|&a, &b| {
                let (pa, pb) = (self.red.pos[a], self.red.pos[b]);
                (pa[0] - p[0]).hypot(pa[1] - p[1]).total_cmp(&(pb[0] - p[0]).hypot(pb[1] - p[1]))
            })
            .unwrap_or(0)
    }

    /// REQ-RUT-08: la ruta por la red pasando por `nodos` (en orden), corrida `lateral`.
    fn ruta_por(&self, nodos: &[usize], lateral: f32) -> Vec<Vector3> {
        let mut camino: Vec<usize> = Vec::new();
        for w in nodos.windows(2) {
            let tramo = self.red.camino(w[0], w[1]).unwrap_or_else(|| vec![w[0], w[1]]);
            let salta = usize::from(!camino.is_empty());
            camino.extend(tramo.into_iter().skip(salta));
        }
        if camino.is_empty() {
            camino = nodos.to_vec();
        }
        let puntos: Vec<[f32; 2]> = camino.iter().map(|&k| self.red.pos[k]).collect();
        reglas::correr_lateral(&puntos, lateral).into_iter().map(v3).collect()
    }

    /// REQ-RUT-09: alguien que va al trabajo cruza la plaza sin parar, de una salida a otra.
    fn al_trabajo(&mut self, inicio: usize, vel: f32) -> Vec<u64> {
        let medio = carrito_core::plaza::LADO_PLAZA / 2.0;
        let en_la_plaza = self
            .red
            .de_tipo(|t| *t == TipoNodo::Paso)
            .into_iter()
            .filter(|&k| self.red.pos[k][0].abs() < medio && self.red.pos[k][1].abs() < medio)
            .collect::<Vec<_>>();
        let cruce = *self.azar.elegir(&en_la_plaza).unwrap_or(&inicio);
        let salidas: Vec<usize> =
            self.red.de_tipo(|t| *t == TipoNodo::Salida).into_iter().filter(|&s| s != inicio).collect();
        let salida = *self.azar.elegir(&salidas).unwrap_or(&inicio);
        let lateral = self.azar.rango(-0.4, 0.4);
        let ruta = self.ruta_por(&[inicio, cruce, salida], lateral);
        let paleta = vestimenta::paleta(Perfil::AlTrabajo, self.hora);
        let p = self.agregar_con(
            inicio,
            vec![Accion::Caminar(ruta), Accion::Desaparecer],
            Perfil::AlTrabajo,
            Plan::Pasear,
            Origen::Nueva(paleta),
            vel,
        );
        vec![p.bind().id]
    }

    /// REQ-RUT-08, REQ-RUT-09: pasean juntos, de a dos, por uno o dos lugares y se van (los
    /// oficinistas cruzan: un solo lugar).
    fn pasear_juntos(&mut self, n: usize, inicio: usize, salida: usize) -> Vec<Integrante> {
        let paradas = 1 + self.azar.entero(2);
        let mut nodos = vec![inicio];
        for _ in 0..paradas {
            nodos.push(self.al_azar(|t| *t == TipoNodo::Paso));
        }
        nodos.push(salida);
        reglas::de_a_dos(n)
            .into_iter()
            .map(|(lateral, fila)| {
                let ruta = self.ruta_por(&nodos, lateral);
                let pos = ruta.first().copied();
                let mut acciones: Vec<Accion> = demora(fila).into_iter().collect();
                acciones.extend([Accion::Caminar(ruta), Accion::Desaparecer]);
                Integrante { en: inicio, pos, acciones, chico: false }
            })
            .collect()
    }

    /// REQ-RUT-05, REQ-RUT-06, REQ-RUT-09: se sientan juntos en un banco libre (de noche, cerca
    /// de un farol: REQ-RUT-11). `None` si no hay banco libre.
    fn sentarse_juntos(
        &mut self,
        perfil: Perfil,
        n: usize,
        inicio: usize,
        salida: usize,
        desde_salida: bool,
    ) -> Option<Vec<Integrante>> {
        let ocupados: Vec<usize> = self.asientos.values().copied().collect();
        let libres: Vec<usize> = self
            .red
            .de_tipo(|t| matches!(t, TipoNodo::Asiento { .. }))
            .into_iter()
            .filter(|a| !ocupados.contains(a))
            .filter(|a| vestimenta::asiento_permitido(self.red.pos[*a], self.hora)) // REQ-RUT-11
            .collect();
        let asiento = *self.azar.elegir(&libres)?;
        let TipoNodo::Asiento { rot_y } = self.red.tipo[asiento] else { return None };
        let lugares = reglas::lugares_banco(self.red.pos[asiento], rot_y, n);
        let segundos = plaza().agenda.quieto(&mut self.azar, perfil);
        let centro = v3(self.red.pos[asiento]);
        let v = reglas::de_a_dos(n)
            .into_iter()
            .zip(lugares)
            .map(|((lateral, fila), (lugar, sentado))| {
                let mut ida = self.ruta_por(&[inicio, asiento], lateral);
                ida.push(v3(lugar));
                let quieto = if sentado {
                    Accion::Sentarse { rot_y, segundos }
                } else {
                    Accion::Esperar { mirar: Some(centro), segundos }
                };
                let vuelta = self.ruta_por(&[asiento, salida], lateral);
                let mut acciones: Vec<Accion> = if desde_salida { demora(fila).into_iter().collect() } else { vec![] };
                acciones.extend([
                    Accion::Caminar(if desde_salida { ida } else { vec![v3(lugar)] }),
                    quieto,
                    Accion::Caminar(vuelta),
                    Accion::Desaparecer,
                ]);
                Integrante {
                    en: if desde_salida { inicio } else { asiento },
                    pos: (!desde_salida).then(|| v3(lugar)),
                    acciones,
                    chico: false,
                }
            })
            .collect();
        Some(v)
    }

    /// REQ-RUT-07: un lugar de ronda (junto a un farol o a la fuente) que no use otro grupo.
    fn lugar_libre(&mut self) -> Option<usize> {
        let usados: Vec<usize> = self.est_grupos.grupos.iter().filter_map(|g| g.lugar).collect();
        let libres: Vec<usize> = (0..reglas::lugares_ronda().len()).filter(|l| !usados.contains(l)).collect();
        self.azar.elegir(&libres).copied()
    }

    /// REQ-RUT-07, REQ-RUT-09: charlan en ronda, mirando al centro (con gestos), y se van juntos.
    fn ronda(
        &mut self,
        perfil: Perfil,
        n: usize,
        lugar: usize,
        inicio: usize,
        salida: usize,
        desde_salida: bool,
    ) -> Vec<Integrante> {
        let centro = reglas::lugares_ronda()[lugar];
        let giro = self.azar.rango(0.0, std::f32::consts::TAU);
        let puntos = reglas::ronda(centro, n, giro);
        let nodo = self.paso_cercano(centro);
        let segundos = plaza().agenda.quieto(&mut self.azar, perfil); // REQ-RUT-07: 30–90 min
        reglas::de_a_dos(n)
            .into_iter()
            .zip(puntos)
            .map(|((lateral, fila), p)| {
                let mut ida = self.ruta_por(&[inicio, nodo], lateral);
                ida.push(v3(p));
                let vuelta = self.ruta_por(&[nodo, salida], lateral);
                let mut acciones: Vec<Accion> = if desde_salida { demora(fila).into_iter().collect() } else { vec![] };
                acciones.extend([
                    Accion::Caminar(if desde_salida { ida } else { vec![v3(p)] }),
                    Accion::Charlar { mirar: v3(centro), segundos },
                    Accion::Caminar(vuelta),
                    Accion::Desaparecer,
                ]);
                Integrante {
                    en: if desde_salida { inicio } else { nodo },
                    pos: (!desde_salida).then(|| v3(p)),
                    acciones,
                    chico: false,
                }
            })
            .collect()
    }

    /// REQ-RUT-06: la familia va a la fuente; los adultos esperan mirando mientras los chicos
    /// corren de 1 a 3 vueltas alrededor; después se van todos juntos.
    fn a_la_fuente(&mut self, chicos: &[bool], inicio: usize, salida: usize, desde_salida: bool) -> Vec<Integrante> {
        let n = chicos.len();
        let angulo = reglas::angulo_espera(&mut self.azar);
        let espera = reglas::espera_fuente(angulo);
        let fuente = v3(reglas::fuente());
        let nodo = self.paso_cercano(espera);
        let vueltas = reglas::VUELTAS[0] + self.azar.entero(reglas::VUELTAS[1] - reglas::VUELTAS[0] + 1);
        // Lo que tardan los chicos más lentos posibles: así los adultos no se van antes.
        let t_vueltas = reglas::tiempo_vueltas(vueltas, reglas::VEL_CORRER[0]);
        // Uno al lado del otro, sobre la tangente al anillo de la fuente.
        let tangente = [-angulo.sin(), angulo.cos()];
        let mut k_chico = 0;
        reglas::de_a_dos(n)
            .into_iter()
            .enumerate()
            .map(|(i, (lateral, fila))| {
                let d = (i as f32 - (n as f32 - 1.0) / 2.0) * 0.8;
                let lugar = v3([espera[0] + tangente[0] * d, espera[1] + tangente[1] * d]);
                let mut ida = self.ruta_por(&[inicio, nodo], lateral);
                ida.push(lugar);
                let vuelta = self.ruta_por(&[nodo, salida], lateral);
                let mut acciones: Vec<Accion> = if desde_salida { demora(fila).into_iter().collect() } else { vec![] };
                acciones.push(Accion::Caminar(if desde_salida { ida } else { vec![lugar] }));
                if chicos[i] {
                    // Arrancan escalonados para no chocarse.
                    let a = angulo - k_chico as f32 * 0.4;
                    k_chico += 1;
                    let vuelta_fuente = reglas::vueltas_fuente(a, vueltas).into_iter().map(v3).collect();
                    acciones.extend([
                        Accion::Caminar(vuelta_fuente),
                        Accion::Caminar(vec![lugar]),
                        Accion::Esperar { mirar: Some(fuente), segundos: 1.5 },
                    ]);
                } else {
                    acciones.push(Accion::Esperar { mirar: Some(fuente), segundos: t_vueltas });
                }
                acciones.extend([Accion::Caminar(vuelta), Accion::Desaparecer]);
                Integrante {
                    en: if desde_salida { inicio } else { nodo },
                    pos: (!desde_salida).then_some(lugar),
                    acciones,
                    chico: chicos[i],
                }
            })
            .collect()
    }

    /// REQ-RUT-05, REQ-RUT-11: los de `perfil` que quedan (menos los que están en la fila)
    /// cortan lo que hacen y se van, cada grupo junto y por la misma salida.
    fn mandar_a_casa(&mut self, perfil: Perfil, mapa: &HashMap<u64, Gd<Peaton>>) {
        let quedan: Vec<u64> = self
            .perfiles
            .iter()
            .filter(|(id, p)| {
                **p == perfil
                    && mapa.contains_key(id)
                    && !self.clientes.contains_key(id)
                    && !self.est_grupos.idos.contains(id)
            })
            .map(|(id, _)| *id)
            .collect();
        if quedan.is_empty() {
            return;
        }
        // Por grupo (cada grupo por una salida); los sueltos, cada uno por la suya.
        let mut tandas: Vec<Vec<u64>> = Vec::new();
        let mut hechos: HashSet<u64> = HashSet::new();
        for g in &self.est_grupos.grupos {
            let t: Vec<u64> = g.ids.iter().copied().filter(|id| quedan.contains(id)).collect();
            if !t.is_empty() {
                hechos.extend(&t);
                tandas.push(t);
            }
        }
        tandas.extend(quedan.iter().filter(|id| !hechos.contains(id)).map(|id| vec![*id]));
        for t in tandas {
            let salida = self.salida_al_azar();
            for ((lateral, _), id) in reglas::de_a_dos(t.len()).into_iter().zip(t) {
                let mut p = mapa[&id].clone();
                let pos = p.get_global_position();
                let desde = self.red.mas_cercano(pos.x, pos.z);
                let ruta = self.ruta_por(&[desde, salida], lateral);
                p.bind_mut().reemplazar_acciones(vec![Accion::Caminar(ruta), Accion::Desaparecer]);
                self.asientos.remove(&id);
                self.est_grupos.idos.insert(id);
            }
        }
    }

    /// Cada cuadro: oficinistas que comen y se van a las 14:30, familias que se van a las 21,
    /// grupos que caminan juntos y chicos que siguen a los adultos.
    pub(super) fn cuadro_grupos(&mut self, _dt: f32) {
        let mapa: HashMap<u64, Gd<Peaton>> =
            self.peatones.iter().filter(|p| p.is_instance_valid()).map(|p| (p.bind().id, p.clone())).collect();
        let clientes: HashSet<u64> = self.clientes.keys().copied().collect();
        let est = &mut self.est_grupos;
        // Quien se fue o se hizo cliente deja el grupo.
        for g in &mut est.grupos {
            g.ids.retain(|id| mapa.contains_key(id) && !clientes.contains(id));
        }
        est.grupos.retain(|g| !g.ids.is_empty());
        est.chicos.retain(|id, _| mapa.contains_key(id) && !clientes.contains(id));
        est.idos.retain(|id| mapa.contains_key(id));
        est.comiendo.retain(|id| mapa.contains_key(id));
        est.por_comer.retain(|id| mapa.contains_key(id) && !clientes.contains(id));

        // REQ-RUT-05: al sentarse en el banco sacan la comida.
        let sentados: Vec<u64> = est
            .por_comer
            .iter()
            .copied()
            .filter(|id| matches!(mapa[id].bind().accion_actual(), Some(Accion::Sentarse { .. })))
            .collect();
        for id in sentados {
            mapa[&id].clone().bind_mut().comer();
            est.comiendo.insert(id);
            est.por_comer.retain(|x| *x != id);
        }

        // REQ-RUT-05: a las 14:30 los oficinistas se van. REQ-RUT-11: a las 21, las familias.
        if reglas::oficinistas_se_van(self.hora) {
            self.mandar_a_casa(Perfil::Oficinista, &mapa);
        }
        if reglas::familias_se_van(self.hora) {
            self.mandar_a_casa(Perfil::Familia, &mapa);
        }

        let est = &self.est_grupos;
        let en_vueltas = |id: u64| {
            est.chicos.contains_key(&id) && {
                let b = mapa[&id].bind();
                matches!(b.accion_actual(), Some(Accion::Caminar(_)))
                    && b.acciones_pendientes() == PENDIENTES_EN_VUELTAS
            }
        };

        // REQ-RUT-08: si uno se adelanta más de 3 m (con chicos, 1,5 m) del último, espera.
        let mut esperan: Vec<(u64, Vector3)> = Vec::new();
        for g in est.grupos.iter().filter(|g| g.ids.len() > 1) {
            let caminando: Vec<(u64, [f32; 2], [f32; 2])> = g
                .ids
                .iter()
                .filter(|id| matches!(mapa[id].bind().accion_actual(), Some(Accion::Caminar(_))) && !en_vueltas(**id))
                .map(|id| {
                    let p = &mapa[id];
                    let pos = p.get_global_position();
                    let r = p.get_rotation().y;
                    (*id, [pos.x, pos.z], [r.sin(), r.cos()])
                })
                .collect();
            for (i, (id, pos, dir)) in caminando.iter().enumerate() {
                let otros: Vec<[f32; 2]> =
                    caminando.iter().enumerate().filter(|(k, _)| *k != i).map(|(_, (_, p, _))| *p).collect();
                if let Some(j) = reglas::a_quien_esperar(*pos, *dir, &otros, g.umbral) {
                    esperan.push((*id, v3(otros[j])));
                }
            }
        }

        // REQ-RUT-06: los chicos corren alrededor de la fuente; caminando, siguen a los adultos.
        let mut velocidades: Vec<(u64, f32)> = Vec::new();
        for (id, c) in &est.chicos {
            let v = if en_vueltas(*id) {
                c.vel_correr
            } else {
                let yo = mapa[id].get_global_position();
                let d = c
                    .adultos
                    .iter()
                    .filter_map(|a| mapa.get(a))
                    .map(|a| a.get_global_position().distance_to(yo))
                    .fold(f32::INFINITY, f32::min);
                if d.is_finite() { reglas::vel_chico(c.vel_paseo, d) } else { c.vel_paseo }
            };
            velocidades.push((*id, v));
        }

        for (id, mirar) in esperan {
            mapa[&id].clone().bind_mut().intercalar(Accion::Esperar { mirar: Some(mirar), segundos: 0.4 });
        }
        for (id, v) in velocidades {
            mapa[&id].clone().bind_mut().set_velocidad(v);
        }
    }

    // ── Para pruebas ──────────────────────────────────────────────

    /// Para pruebas: arma un grupo de `perfil` (con esa actividad, o la que le toque) a la hora
    /// actual. Devuelve los ids. REQ-RUT-05 a REQ-RUT-09
    pub fn probar_grupo(&mut self, perfil: Perfil, plan: Option<Plan>, desde_salida: bool) -> Vec<u64> {
        if !reglas::arma_grupos(perfil) {
            return Vec::new();
        }
        let plan = plan.unwrap_or_else(|| self.plan_para(perfil));
        self.armar_grupo(perfil, plan, desde_salida)
    }

    /// Para pruebas: la persona con ese id, si sigue.
    pub fn peaton(&self, id: u64) -> Option<Gd<Peaton>> {
        self.peatones.iter().find(|p| p.is_instance_valid() && p.bind().id == id).cloned()
    }

    /// Para pruebas: los ids de los presentes con ese perfil que no son clientes.
    pub fn paseantes_de(&self, perfil: Perfil) -> Vec<u64> {
        self.perfiles
            .iter()
            .filter(|(id, p)| **p == perfil && !self.clientes.contains_key(id))
            .map(|(id, _)| *id)
            .collect()
    }

    /// Para pruebas: ¿está comiendo? REQ-RUT-05
    pub fn esta_comiendo(&self, id: u64) -> bool {
        self.est_grupos.comiendo.contains(&id)
    }

    /// Para pruebas: ¿es un chico? REQ-RUT-06
    pub fn es_chico(&self, id: u64) -> bool {
        self.est_grupos.chicos.contains_key(&id)
    }

    /// Para pruebas: ¿ya lo mandamos a casa? REQ-RUT-05, REQ-RUT-11
    pub fn se_esta_yendo(&self, id: u64) -> bool {
        self.est_grupos.idos.contains(&id)
    }
}

/// REQ-RUT-06, REQ-RUT-08: el orden de a dos de la familia: cada chico al lado de un adulto.
fn intercalar_chicos(adultos: usize, chicos: usize) -> Vec<bool> {
    let (mut a, mut c) = (adultos, chicos);
    let mut turno_chico = chicos > adultos;
    let mut v = Vec::new();
    while a + c > 0 {
        if (turno_chico && c > 0) || a == 0 {
            v.push(true);
            c -= 1;
        } else {
            v.push(false);
            a -= 1;
        }
        turno_chico = !turno_chico;
    }
    v
}
