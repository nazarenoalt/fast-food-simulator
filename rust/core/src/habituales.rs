//! SPEC-030 · Clientes habituales: quiénes son, lo de siempre y su memoria. (TASK-0504)
//!
//! REQ-HAB-07: nada de esto se guarda al cerrar el juego; la partida empieza sin habituales.

use crate::azar::Azar;
use crate::clientes::{ItemMenu, Pedido};
use crate::peatones::Apariencia;
use crate::rutinas::Perfil;

/// REQ-HAB-01: cuántos habituales puede haber a la vez.
pub const MAX_HABITUALES: usize = 8;
/// REQ-HAB-01: estrellas mínimas para volverse habitual y chance de que pase.
pub const ESTRELLAS_PROMOCION: f32 = 4.5;
pub const CHANCE_PROMOCION: f32 = 0.25;
/// REQ-HAB-03: cuánto se puede correr su hora de costumbre cada día (h).
pub const MARGEN_HORA_H: f32 = 1.0;
/// REQ-HAB-03: pasada esta demora (h) desde la hora sorteada, ese día ya no viene (por ejemplo,
/// si el reloj saltó).
pub const DEMORA_MAX_H: f32 = 1.0;
/// REQ-HAB-06: cuántas visitas recuerda, las estrellas de irse enojado y los umbrales.
pub const MEMORIA_VISITAS: usize = 3;
pub const ESTRELLAS_ENOJADO: f32 = 1.0;
pub const PROMEDIO_SIEMPRE: f32 = 4.0;
pub const PROMEDIO_A_VECES: f32 = 2.5;
pub const CHANCE_A_VECES: f32 = 0.5;
pub const FACTOR_PACIENCIA_BUENA: f32 = 1.25;

/// REQ-HAB-06: cada cuánto viene según lo que recuerda.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Frecuencia {
    /// Promedio 4 o más: todos los días.
    Siempre,
    /// Entre 2,5 y 4: la mitad de los días, al azar.
    AVeces,
    /// Menos de 2,5: no vuelve más.
    Nunca,
}

/// Un cliente habitual (REQ-HAB-01, REQ-HAB-02).
#[derive(Debug, Clone, PartialEq)]
pub struct Habitual {
    /// Número fijo (no cambia aunque se vayan otros).
    pub id: usize,
    pub nombre: String,
    /// REQ-HAB-01: su cara y su ropa de siempre.
    pub apariencia: Apariencia,
    pub perfil: Perfil,
    /// REQ-HAB-02: el pedido de la visita en que se volvió habitual.
    pub lo_de_siempre: Pedido,
    /// REQ-HAB-02: su hora de costumbre (la hora a la que pidió).
    pub hora: f32,
    /// REQ-HAB-06: estrellas de sus últimas visitas (la más vieja primero).
    pub memoria: Vec<f32>,
    /// REQ-HAB-03: la hora de la visita de hoy, si viene y todavía no llegó.
    pub visita: Option<f32>,
}

impl Habitual {
    /// REQ-HAB-06: promedio de lo que recuerda (sin visitas, como si fueran buenas).
    pub fn promedio(&self) -> f32 {
        if self.memoria.is_empty() {
            return ESTRELLAS_PROMOCION;
        }
        self.memoria.iter().sum::<f32>() / self.memoria.len() as f32
    }

    /// REQ-HAB-06
    pub fn frecuencia(&self) -> Frecuencia {
        let p = self.promedio();
        if p >= PROMEDIO_SIEMPRE {
            Frecuencia::Siempre
        } else if p >= PROMEDIO_A_VECES {
            Frecuencia::AVeces
        } else {
            Frecuencia::Nunca
        }
    }

    /// REQ-HAB-05, REQ-HAB-06: memoria buena = promedio 4 o más.
    pub fn memoria_buena(&self) -> bool {
        self.frecuencia() == Frecuencia::Siempre
    }

    /// REQ-HAB-06: con memoria buena tiene paciencia ×1,25.
    pub fn factor_paciencia(&self) -> f32 {
        if self.memoria_buena() { FACTOR_PACIENCIA_BUENA } else { 1.0 }
    }

    /// REQ-HAB-06: anota una visita (irse enojado = 1 estrella); recuerda solo las últimas 3.
    pub fn recordar(&mut self, estrellas: f32) {
        self.memoria.push(estrellas.clamp(0.0, 5.0));
        let sobran = self.memoria.len().saturating_sub(MEMORIA_VISITAS);
        self.memoria.drain(..sobran);
    }

    /// REQ-HAB-04: lo de siempre si el producto está en el menú, con los aderezos de siempre
    /// que ese producto admite y el carrito tiene. Si no está, `None` (pide como cualquiera).
    pub fn pedido(&self, menu: &[ItemMenu], disponibles: &[String]) -> Option<Pedido> {
        let item = menu.iter().find(|i| i.producto == self.lo_de_siempre.producto)?;
        let aderezos = self
            .lo_de_siempre
            .aderezos
            .iter()
            .filter(|a| item.aderezos.contains(a) && disponibles.contains(a))
            .cloned()
            .collect();
        Some(Pedido { producto: item.producto.clone(), aderezos })
    }

    /// REQ-HAB-04: ¿este pedido es lo de siempre (el mismo producto)?
    pub fn es_lo_de_siempre(&self, p: &Pedido) -> bool {
        p.producto == self.lo_de_siempre.producto
    }
}

/// REQ-HAB-05: "Marta: lo de siempre (pancho con mostaza)". `texto_pedido` es el texto común
/// del globo (REQ-CLI-05, "Pancho con mostaza"); si no es lo de siempre, "Marta: pancho con
/// ketchup".
pub fn texto_globo(nombre: &str, texto_pedido: &str, lo_de_siempre: bool) -> String {
    let mut c = texto_pedido.chars();
    let texto = match c.next() {
        Some(f) => f.to_lowercase().collect::<String>() + c.as_str(),
        None => String::new(),
    };
    if lo_de_siempre { format!("{nombre}: lo de siempre ({texto})") } else { format!("{nombre}: {texto}") }
}

/// REQ-HAB-05: lo que dice al llegar a la fila con memoria buena.
pub const SALUDO: &str = "¡Hola! ¿Lo de siempre?";

/// Los habituales de la partida (REQ-HAB-01). REQ-HAB-07: arranca vacío y no se guarda.
#[derive(Debug, Clone, Default)]
pub struct Habituales {
    pub lista: Vec<Habitual>,
    sig_id: usize,
    /// El último día para el que se decidió quién viene.
    dia: Option<u32>,
}

impl Habituales {
    pub fn get(&self, id: usize) -> Option<&Habitual> {
        self.lista.iter().find(|h| h.id == id)
    }

    pub fn get_mut(&mut self, id: usize) -> Option<&mut Habitual> {
        self.lista.iter_mut().find(|h| h.id == id)
    }

    pub fn len(&self) -> usize {
        self.lista.len()
    }

    pub fn is_empty(&self) -> bool {
        self.lista.is_empty()
    }

    /// REQ-HAB-01: un nombre de la lista que no use otro habitual.
    fn nombre_libre(&self, azar: &mut Azar, nombres: &[String]) -> Option<String> {
        let libres: Vec<&String> = nombres.iter().filter(|n| !self.lista.iter().any(|h| &h.nombre == *n)).collect();
        azar.elegir(&libres).map(|n| (*n).clone())
    }

    /// REQ-HAB-01, REQ-HAB-02: lo vuelve habitual sin sortear (si hay lugar y nombre libre).
    /// Su primera visita queda en la memoria. Devuelve su número.
    #[allow(clippy::too_many_arguments)]
    pub fn promover(
        &mut self,
        azar: &mut Azar,
        nombres: &[String],
        apariencia: Apariencia,
        perfil: Perfil,
        pedido: Pedido,
        hora: f32,
        estrellas: f32,
    ) -> Option<usize> {
        if self.lista.len() >= MAX_HABITUALES {
            return None;
        }
        let nombre = self.nombre_libre(azar, nombres)?;
        let id = self.sig_id;
        self.sig_id += 1;
        let mut h = Habitual {
            id,
            nombre,
            apariencia,
            perfil,
            lo_de_siempre: pedido,
            hora: hora.rem_euclid(24.0),
            memoria: Vec::new(),
            visita: None,
        };
        h.recordar(estrellas);
        self.lista.push(h);
        Some(id)
    }

    /// REQ-HAB-01: un cliente común que puso 4,5 estrellas o más se vuelve habitual con 25% de
    /// chance, si hay lugar.
    #[allow(clippy::too_many_arguments)]
    pub fn quizas_promover(
        &mut self,
        azar: &mut Azar,
        nombres: &[String],
        apariencia: Apariencia,
        perfil: Perfil,
        pedido: Pedido,
        hora: f32,
        estrellas: f32,
    ) -> Option<usize> {
        if estrellas < ESTRELLAS_PROMOCION || self.lista.len() >= MAX_HABITUALES || !azar.chance(CHANCE_PROMOCION) {
            return None;
        }
        self.promover(azar, nombres, apariencia, perfil, pedido, hora, estrellas)
    }

    /// REQ-HAB-06: anota la visita del habitual `id`. Si su promedio baja de 2,5 no vuelve
    /// más y libera su lugar (devuelve false).
    pub fn recordar(&mut self, id: usize, estrellas: f32) -> bool {
        let Some(h) = self.get_mut(id) else { return false };
        h.recordar(estrellas);
        if h.frecuencia() == Frecuencia::Nunca {
            self.lista.retain(|h| h.id != id);
            return false;
        }
        true
    }

    /// REQ-HAB-03, REQ-HAB-06: una vez por día decide quién viene y a qué hora (su hora ±1 h).
    /// Devuelve true si era un día nuevo.
    pub fn planear_dia(&mut self, azar: &mut Azar, dia: u32) -> bool {
        if self.dia == Some(dia) {
            return false;
        }
        self.dia = Some(dia);
        self.lista.retain(|h| h.frecuencia() != Frecuencia::Nunca);
        for h in &mut self.lista {
            let viene = match h.frecuencia() {
                Frecuencia::Siempre => true,
                Frecuencia::AVeces => azar.chance(CHANCE_A_VECES),
                Frecuencia::Nunca => false,
            };
            h.visita =
                viene.then(|| (h.hora + azar.rango(-MARGEN_HORA_H, MARGEN_HORA_H)).clamp(0.0, 24.0 - 1.0 / 60.0));
        }
        true
    }

    /// REQ-HAB-03: los habituales a los que les llegó la hora. Se les borra la visita de hoy
    /// (si no pueden sumarse a la fila, se van y vuelven otro día). Si la hora ya pasó de largo
    /// (más de 1 h), ese día no vienen.
    pub fn llegan(&mut self, hora: f32) -> Vec<usize> {
        let mut ids = Vec::new();
        for h in &mut self.lista {
            if let Some(v) = h.visita
                && hora >= v
            {
                h.visita = None;
                if hora <= v + DEMORA_MAX_H {
                    ids.push(h.id);
                }
            }
        }
        ids
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::rutinas::tests::plaza_real;

    fn ap() -> Apariencia {
        crate::peatones::apariencia(&mut Azar::new(1))
    }

    fn pancho() -> Pedido {
        Pedido { producto: "pancho".into(), aderezos: vec!["mostaza".into()] }
    }

    fn nombres() -> Vec<String> {
        plaza_real().habituales.nombres
    }

    fn uno(h: &mut Habituales, estrellas: f32) -> usize {
        h.promover(&mut Azar::new(3), &nombres(), ap(), Perfil::Jubilado, pancho(), 12.5, estrellas).unwrap()
    }

    #[test]
    fn req_hab_01_hasta_8_con_chance_y_nombre_propio() {
        let nombres = nombres();
        let mut azar = Azar::new(9);
        let mut h = Habituales::default();
        // Con menos de 4,5 estrellas nunca.
        for _ in 0..200 {
            let r = h.quizas_promover(&mut azar, &nombres, ap(), Perfil::Paseante, pancho(), 13.0, 4.4);
            assert!(r.is_none());
        }
        // Con 4,5 o más, alrededor de 1 de cada 4 (mientras haya lugar).
        let mut si = 0;
        let n = 4000;
        for _ in 0..n {
            let mut otro = Habituales::default();
            if otro.quizas_promover(&mut azar, &nombres, ap(), Perfil::Paseante, pancho(), 13.0, 4.5).is_some() {
                si += 1;
            }
        }
        let frac = si as f32 / n as f32;
        assert!((frac - CHANCE_PROMOCION).abs() < 0.03, "{frac}");
        // Hasta 8, con nombres de la lista sin repetir, y se quedan con su cara y perfil.
        for _ in 0..20 {
            h.promover(&mut azar, &nombres, ap(), Perfil::Familia, pancho(), 13.0, 5.0);
        }
        assert_eq!(h.len(), MAX_HABITUALES);
        let mut usados: Vec<&String> = h.lista.iter().map(|x| &x.nombre).collect();
        assert!(usados.iter().all(|n| nombres.contains(n)));
        usados.sort();
        usados.dedup();
        assert_eq!(usados.len(), MAX_HABITUALES);
        assert!(h.lista.iter().all(|x| x.apariencia == ap() && x.perfil == Perfil::Familia));
        // Sin nombres libres tampoco.
        let pocos = vec!["Marta".to_string()];
        let mut otro = Habituales::default();
        assert!(otro.promover(&mut azar, &pocos, ap(), Perfil::Paseante, pancho(), 13.0, 5.0).is_some());
        assert!(otro.promover(&mut azar, &pocos, ap(), Perfil::Paseante, pancho(), 13.0, 5.0).is_none());
    }

    #[test]
    fn req_hab_02_lo_de_siempre_y_su_hora() {
        let mut h = Habituales::default();
        let id = uno(&mut h, 5.0);
        let x = h.get(id).unwrap();
        assert_eq!(x.lo_de_siempre, pancho());
        assert_eq!(x.hora, 12.5);
        assert_eq!(x.memoria, vec![5.0]);
    }

    #[test]
    fn req_hab_03_una_vez_por_dia_cerca_de_su_hora() {
        let mut azar = Azar::new(5);
        let mut h = Habituales::default();
        let id = uno(&mut h, 5.0);
        let mut horas = Vec::new();
        for dia in 2..200 {
            assert!(h.planear_dia(&mut azar, dia));
            assert!(!h.planear_dia(&mut azar, dia), "una sola vez por día");
            let v = h.get(id).unwrap().visita.expect("con memoria buena viene todos los días");
            assert!((v - 12.5).abs() <= MARGEN_HORA_H + 1e-4, "{v}");
            horas.push(v);
            // Antes de su hora no llega; a su hora sí, una sola vez.
            assert!(h.llegan(v - 0.01).is_empty());
            assert_eq!(h.llegan(v + 0.01), vec![id]);
            assert!(h.llegan(v + 0.5).is_empty());
        }
        // Se sortea cada día.
        horas.sort_by(f32::total_cmp);
        horas.dedup();
        assert!(horas.len() > 100);
        // Si el reloj saltó muy pasada su hora, ese día no viene.
        h.planear_dia(&mut azar, 500);
        let v = h.get(id).unwrap().visita.unwrap();
        assert!(h.llegan(v + DEMORA_MAX_H + 0.1).is_empty());
        assert!(h.get(id).unwrap().visita.is_none());
    }

    #[test]
    fn req_hab_04_pide_lo_de_siempre_si_esta_en_el_menu() {
        let mut h = Habituales::default();
        let id = uno(&mut h, 5.0);
        let x = h.get(id).unwrap();
        let item = |p: &str, ad: &[&str]| ItemMenu {
            producto: p.into(),
            aderezos: ad.iter().map(|a| a.to_string()).collect(),
        };
        let menu = vec![item("pancho", &["mostaza", "ketchup"]), item("choripan", &["chimichurri"])];
        let todos: Vec<String> = vec!["mostaza".into(), "ketchup".into()];
        assert_eq!(x.pedido(&menu, &todos), Some(pancho()));
        // Sin mostaza disponible, el pancho solo.
        let sin = vec!["ketchup".to_string()];
        assert_eq!(x.pedido(&menu, &sin), Some(Pedido { producto: "pancho".into(), aderezos: vec![] }));
        // Sin pancho en el menú: pide como cualquiera.
        assert_eq!(x.pedido(&menu[1..], &todos), None);
        assert!(x.es_lo_de_siempre(&pancho()));
        assert!(!x.es_lo_de_siempre(&Pedido { producto: "choripan".into(), aderezos: vec![] }));
    }

    #[test]
    fn req_hab_05_globo_con_su_nombre() {
        assert_eq!(texto_globo("Marta", "Pancho con mostaza", true), "Marta: lo de siempre (pancho con mostaza)");
        assert_eq!(texto_globo("Hugo", "Choripán sin aderezos", false), "Hugo: choripán sin aderezos");
        assert_eq!(SALUDO, "¡Hola! ¿Lo de siempre?");
    }

    #[test]
    fn req_hab_06_memoria_frecuencia_y_paciencia() {
        let mut azar = Azar::new(11);
        let mut h = Habituales::default();
        let id = uno(&mut h, 5.0);
        assert!(h.get(id).unwrap().memoria_buena());
        assert_eq!(h.get(id).unwrap().factor_paciencia(), FACTOR_PACIENCIA_BUENA);
        // Recuerda solo las últimas 3.
        for e in [4.0, 4.5, 5.0, 4.0] {
            assert!(h.recordar(id, e));
        }
        assert_eq!(h.get(id).unwrap().memoria, vec![4.5, 5.0, 4.0]);
        // Entre 2,5 y 4: la mitad de los días, sin paciencia extra.
        h.recordar(id, ESTRELLAS_ENOJADO); // 5, 4, 1 → 3,33
        let x = h.get(id).unwrap();
        assert_eq!(x.frecuencia(), Frecuencia::AVeces);
        assert_eq!(x.factor_paciencia(), 1.0);
        let n = 2000;
        let vino = (0..n)
            .filter(|d| {
                h.planear_dia(&mut azar, 10 + d);
                h.get(id).unwrap().visita.is_some()
            })
            .count() as f32
            / n as f32;
        assert!((vino - 0.5).abs() < 0.04, "{vino}");
        // CA-HAB-02: dos veces enojado seguidas y no vuelve más; libera su lugar.
        let mut h = Habituales::default();
        let id = uno(&mut h, 5.0);
        assert!(h.recordar(id, ESTRELLAS_ENOJADO)); // 5, 1 → 3
        assert!(!h.recordar(id, ESTRELLAS_ENOJADO)); // 5, 1, 1 → 2,33
        assert!(h.get(id).is_none() && h.is_empty());
        assert!(h.planear_dia(&mut azar, 99) && h.llegan(23.0).is_empty());
    }

    #[test]
    fn req_hab_07_la_partida_empieza_sin_habituales() {
        // No hay nada que cargar ni guardar: siempre arranca vacío.
        let h = Habituales::default();
        assert!(h.is_empty());
    }
}
