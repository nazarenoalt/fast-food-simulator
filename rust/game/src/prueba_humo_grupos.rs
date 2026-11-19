//! Prueba de humo de oficinistas, familias y salida nocturna (REQ-RUT-05 a REQ-RUT-09). (TASK-0503)

use carrito_core::grupos as reglas;
use carrito_core::peatones::Plan;
use carrito_core::plaza::{self, TipoProp};
use carrito_core::rutinas::Perfil;
use godot::prelude::*;

use super::{PruebaHumo, todos};
use crate::dia_noche::DiaNoche;
use crate::gente::Gente;
use crate::peaton::Accion;

/// `notas5`: [minuto, día, máx. chico–adulto, máx. pareja, y listas de ids (largo y después
/// los ids): oficinistas o familia, familia en la fuente, pareja].
const LISTAS: usize = 4;

fn lista(notas: &[f64], k: usize) -> Vec<u64> {
    let mut i = LISTAS;
    for _ in 0..k {
        i += 1 + notas.get(i).copied().unwrap_or(0.0) as usize;
    }
    let n = notas.get(i).copied().unwrap_or(0.0) as usize;
    notas.iter().skip(i + 1).take(n).map(|x| *x as u64).collect()
}

fn poner_listas(notas: &mut Vec<f64>, listas: &[Vec<u64>]) {
    notas.truncate(LISTAS);
    notas.resize(LISTAS, 0.0);
    for l in listas {
        notas.push(l.len() as f64);
        notas.extend(l.iter().map(|x| *x as f64));
    }
}

/// Pasa a la fase siguiente (y cambia la hora, si se pide).
fn cambiar(p: &mut PruebaHumo, dn: &mut Gd<DiaNoche>, fase: u32, minuto: Option<f32>) {
    if let Some(m) = minuto {
        dn.bind_mut().set_minuto(m as f64);
    }
    p.fase5 = fase;
    p.cuadro5 = p.cuadro;
}

fn plano(v: Vector3) -> [f32; 2] {
    [v.x, v.z]
}

fn dist(a: [f32; 2], b: [f32; 2]) -> f32 {
    (a[0] - b[0]).hypot(a[1] - b[1])
}

impl PruebaHumo {
    /// Un lunes (sin eventos): a las 13:00 oficinistas sentados comiendo; a las 14:35 ya se van;
    /// a las 17:30 familias con chicos que siguen a los adultos y dan vueltas a la fuente, y una
    /// pareja que camina junta; a las 22:00 las familias se van y hay una ronda nocturna junto a
    /// un farol. Devuelve true cuando termina (dejando el reloj como estaba).
    pub(super) fn chequear_grupos(&mut self) -> bool {
        let mundo = self.mundo();
        let (Some(mut gente), Some(mut dn)) = (todos::<Gente>(&mundo).pop(), todos::<DiaNoche>(&mundo).pop()) else {
            self.chequear(false, "REQ-RUT-05 hay gente y reloj");
            return true;
        };
        let pasados = self.cuadro.saturating_sub(self.cuadro5);
        match self.fase5 {
            0 => {
                // Se guardan día y hora para dejarlos como estaban; un lunes (día 4), sin eventos.
                self.notas5 = vec![dn.bind().hora() as f64 * 60.0, dn.bind().dia() as f64, 0.0, 0.0];
                dn.bind_mut().set_dia(4);
                cambiar(self, &mut dn, 1, Some(13.0 * 60.0));
                false
            }
            1 if pasados >= 2 => {
                // REQ-RUT-05: oficinistas que ya están sentados en un banco (y otros que llegan).
                let mut ofi = gente.bind_mut().probar_grupo(Perfil::Oficinista, Some(Plan::Sentarse), false);
                ofi.extend(gente.bind_mut().probar_grupo(Perfil::Oficinista, Some(Plan::Sentarse), false));
                let llegan = gente.bind_mut().probar_paseantes(12);
                let vels: Vec<f32> = llegan
                    .iter()
                    .filter(|id| gente.bind().perfil_de(**id) == Some(Perfil::Oficinista))
                    .filter_map(|id| gente.bind().peaton(*id))
                    .map(|p| p.bind().velocidad())
                    .collect();
                self.chequear(
                    !vels.is_empty() && vels.iter().all(|v| (1.4..=1.7).contains(v)),
                    &format!("REQ-RUT-05 los oficinistas caminan rápido (1,4–1,7 m/s): {vels:.2?}"),
                );
                poner_listas(&mut self.notas5, &[ofi]);
                cambiar(self, &mut dn, 2, None);
                false
            }
            2 if pasados >= 15 => {
                let ofi = lista(&self.notas5, 0);
                let g = gente.bind();
                let comiendo = ofi
                    .iter()
                    .filter(|id| {
                        g.esta_comiendo(**id)
                            && g.peaton(**id)
                                .is_some_and(|p| matches!(p.bind().accion_actual(), Some(Accion::Sentarse { .. })))
                    })
                    .count();
                drop(g);
                self.chequear(
                    comiendo > 0,
                    &format!("REQ-RUT-05 a las 13:00 hay oficinistas sentados comiendo ({comiendo} de {})", ofi.len()),
                );
                cambiar(self, &mut dn, 3, Some(14.0 * 60.0 + 35.0));
                false
            }
            3 if pasados >= 4 => {
                let g = gente.bind();
                let ofi = g.paseantes_de(Perfil::Oficinista);
                let quietos = ofi.iter().filter(|id| g.peaton(**id).is_some_and(|p| p.bind().ocupado_quieto())).count();
                let yendo = ofi.iter().filter(|id| g.se_esta_yendo(**id)).count();
                drop(g);
                self.chequear(
                    !ofi.is_empty() && quietos == 0 && yendo == ofi.len(),
                    &format!(
                        "REQ-RUT-05 a las 14:35 ningún oficinista sigue sentado y se van ({yendo} de {}, {quietos} quietos)",
                        ofi.len()
                    ),
                );
                cambiar(self, &mut dn, 4, Some(17.0 * 60.0 + 30.0));
                false
            }
            4 if pasados >= 2 => {
                // REQ-RUT-06: una familia que llega y otra que ya está en la fuente; una pareja.
                let fam = gente.bind_mut().probar_grupo(Perfil::Familia, Some(Plan::Pasear), true);
                let fuente = gente.bind_mut().probar_grupo(Perfil::Familia, Some(Plan::Pasear), false);
                let par = gente.bind_mut().probar_grupo(Perfil::Pareja, Some(Plan::Pasear), true);
                let g = gente.bind();
                let mut ok = true;
                let mut texto = Vec::new();
                for f in [&fam, &fuente] {
                    let chicos: Vec<f32> = f
                        .iter()
                        .filter(|id| g.es_chico(**id))
                        .filter_map(|id| g.peaton(*id))
                        .map(|p| p.bind().apariencia().altura)
                        .collect();
                    let adultos = f.len() - chicos.len();
                    ok &= (1..=2).contains(&adultos)
                        && (1..=2).contains(&chicos.len())
                        && chicos.iter().all(|h| (reglas::ALTURA_CHICOS[0]..=reglas::ALTURA_CHICOS[1]).contains(h));
                    texto.push(format!("{adultos} adultos y chicos de {chicos:.2?} m"));
                }
                drop(g);
                self.chequear(ok, &format!("REQ-RUT-06 familias de 1–2 adultos y 1–2 chicos de 1,0–1,3 m: {texto:?}"));
                poner_listas(&mut self.notas5, &[fam, fuente, par]);
                cambiar(self, &mut dn, 5, None);
                false
            }
            5 => {
                // Durante 5 s: los chicos a menos de 2 m de un adulto, la pareja junta.
                let g = gente.bind();
                let pos = |id: &u64| g.peaton(*id).map(|p| plano(p.get_global_position()));
                if pasados >= 90 {
                    let fam = lista(&self.notas5, 0);
                    let adultos: Vec<[f32; 2]> = fam.iter().filter(|id| !g.es_chico(**id)).filter_map(pos).collect();
                    for c in fam.iter().filter(|id| g.es_chico(**id)).filter_map(pos) {
                        let d = adultos.iter().map(|a| dist(*a, c)).fold(f32::INFINITY, f32::min);
                        if d.is_finite() {
                            self.notas5[2] = self.notas5[2].max(d as f64);
                        }
                    }
                    let par: Vec<[f32; 2]> = lista(&self.notas5, 2).iter().filter_map(pos).collect();
                    if par.len() == 2 {
                        self.notas5[3] = self.notas5[3].max(dist(par[0], par[1]) as f64);
                    }
                }
                if pasados < 300 {
                    return false;
                }
                let max_chico = self.notas5[2];
                let max_par = self.notas5[3];
                // En la fuente: los chicos dan vueltas, más rápido; los adultos esperan.
                let fuente = lista(&self.notas5, 1);
                let centro = reglas::fuente();
                let mut vueltas = Vec::new();
                let mut esperan = true;
                for id in &fuente {
                    let Some(p) = g.peaton(*id) else { continue };
                    let b = p.bind();
                    if g.es_chico(*id) {
                        vueltas.push((dist(plano(p.get_global_position()), centro), b.velocidad()));
                    } else {
                        esperan &= matches!(b.accion_actual(), Some(Accion::Esperar { .. }));
                    }
                }
                drop(g);
                self.chequear(
                    max_chico > 0.0 && max_chico < reglas::DISTANCIA_CHICOS as f64,
                    &format!("REQ-RUT-06 los chicos siguen a los adultos a menos de 2 m (máx {max_chico:.2} m)"),
                );
                self.chequear(
                    max_par > 0.0 && max_par < reglas::UMBRAL_GRUPO as f64 + 0.5,
                    &format!("REQ-RUT-08 la pareja camina junta, de a dos (máx {max_par:.2} m)"),
                );
                self.chequear(
                    esperan
                        && !vueltas.is_empty()
                        && vueltas.iter().all(|(r, v)| (3.1..4.3).contains(r) && *v >= reglas::VEL_CORRER[0]),
                    &format!(
                        "REQ-RUT-06 en la fuente los chicos corren vueltas y los adultos esperan (radio y vel.: {vueltas:.2?})"
                    ),
                );
                cambiar(self, &mut dn, 6, Some(22.0 * 60.0));
                false
            }
            6 if pasados >= 3 => {
                // REQ-RUT-11: a las 22 las familias que quedan se van y las que llegan no traen chicos.
                let g = gente.bind();
                let fam = g.paseantes_de(Perfil::Familia);
                let yendo = fam.iter().filter(|id| g.se_esta_yendo(**id)).count();
                drop(g);
                self.chequear(
                    yendo == fam.len(),
                    &format!("REQ-RUT-11 a las 22:00 las familias que quedan se van ({yendo} de {})", fam.len()),
                );
                let tarde = gente.bind_mut().probar_grupo(Perfil::Familia, None, true);
                let chicos = tarde.iter().filter(|id| gente.bind().es_chico(**id)).count();
                self.chequear(
                    !tarde.is_empty() && chicos == 0,
                    &format!("REQ-RUT-11 después de las 21 no llegan chicos ({chicos} en {})", tarde.len()),
                );
                // REQ-RUT-07: una salida nocturna que ya está en su ronda.
                let noc = gente.bind_mut().probar_grupo(Perfil::Nocturno, Some(Plan::Charlar), false);
                poner_listas(&mut self.notas5, &[noc]);
                cambiar(self, &mut dn, 7, None);
                false
            }
            7 if pasados >= 30 => {
                let noc = lista(&self.notas5, 0);
                let g = gente.bind();
                let gente_ronda: Vec<_> = noc.iter().filter_map(|id| g.peaton(*id)).collect();
                drop(g);
                let pos: Vec<[f32; 2]> = gente_ronda.iter().map(|p| plano(p.get_global_position())).collect();
                let n = pos.len().max(1) as f32;
                let centro = [pos.iter().map(|p| p[0]).sum::<f32>() / n, pos.iter().map(|p| p[1]).sum::<f32>() / n];
                let charlan =
                    gente_ronda.iter().all(|p| matches!(p.bind().accion_actual(), Some(Accion::Charlar { .. })));
                let miran = gente_ronda.iter().zip(&pos).all(|(p, q)| {
                    let r = p.get_rotation().y;
                    let (dx, dz) = (centro[0] - q[0], centro[1] - q[1]);
                    let l = dx.hypot(dz).max(1e-3);
                    (r.sin() * dx + r.cos() * dz) / l > 0.8
                });
                let separados = reglas::sin_chocarse(&pos);
                let al_farol = plaza::distribucion()
                    .iter()
                    .filter(|p| p.tipo == TipoProp::Farol)
                    .map(|p| dist([p.x, p.z], centro))
                    .fold(f32::INFINITY, f32::min);
                self.chequear(
                    (3..=4).contains(&pos.len()) && charlan && miran && separados && al_farol < 2.0,
                    &format!(
                        "REQ-RUT-07 a las 22:00 un grupo de {} charla en ronda mirando al centro, a {al_farol:.1} m de un farol \
                         (charlan {charlan}, miran {miran}, separados {separados})",
                        pos.len()
                    ),
                );
                let minuto = self.notas5.first().copied().unwrap_or(17.0 * 60.0);
                let dia = self.notas5.get(1).copied().unwrap_or(1.0);
                dn.bind_mut().set_dia(dia as u32);
                dn.bind_mut().set_minuto(minuto);
                true
            }
            _ => false,
        }
    }
}
