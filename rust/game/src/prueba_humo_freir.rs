//! Prueba de humo de SPEC-029 (freír papas): en la freidora doble del carro de las papas,
//! prende una cuba, la deja a 180 °C, pone una papa cortada en el colador con el jugador y lo
//! baja; con el colador abajo mete otra tanda (y llena el colador: la 5.ª no entra), espera que
//! la primera salga Cocida antes que la segunda, la saca sola (las otras siguen en el aceite),
//! sube el colador y saca la segunda agarrándola.

use carrito_core::coccion::Punto;
use godot::classes::Engine;
use godot::prelude::*;

use super::{PruebaHumo, material_pieza, todos};
use crate::comida::Comida;
use crate::freidora::{self, Colador, Freidora};
use crate::jugador::{Jugador, Objetivo};

/// Cuadros como mucho esperando que la papa se fría (con el tiempo ×6: ~10 min de juego).
const ESPERA_MAX: u32 = 6000;
const ACELERADO: f64 = 6.0;
/// Cuadros que la primera tanda se fríe sola antes de meter la segunda (×6: ~15 s de juego).
const VENTAJA: u32 = 150;
/// Alturas (relativas a la freidora) del techo del aceite y del piso de la cuba.
const TECHO_ACEITE: f32 = 0.19;
const PISO_CUBA: f32 = 0.1055;
/// Metadato con la posición de una porción antes de sacar otra (REQ-FRE-08).
const POS_ANTES: &str = "prueba_pos_antes";

impl PruebaHumo {
    fn freidora_de_papas(&self) -> Option<Gd<Freidora>> {
        let carro = self.carro_papas.clone()?.upcast::<Node>();
        todos::<Freidora>(&carro).pop()
    }

    /// Para al jugador delante de la freidora, un poco alto (mira desde arriba, sin que tape
    /// el borde de la cuba), apuntando al centro del colador.
    fn mirar_colador(&self, j: &mut Gd<Jugador>, col: &Gd<Comida>) {
        self.mirar_punto(j, col.get_global_position() + Vector3::new(0.0, 0.03, 0.0));
    }

    /// Para al jugador delante de un punto (0,6 m, un poco alto) y apunta ahí.
    fn mirar_punto(&self, j: &mut Gd<Jugador>, p: Vector3) {
        let carro_y = self.carro_papas.clone().map(|c| c.get_global_position().y).unwrap_or(0.0);
        j.set_global_position(Vector3::new(p.x, carro_y + 0.3, p.z + 0.6));
        j.bind_mut().apuntar_a(p);
    }

    /// Apunta a una porción del colador: al punto de la tapa del canasto que está justo encima
    /// de ella (la mira toca el colador ahí). REQ-FRE-08
    fn mirar_porcion(&self, j: &mut Gd<Jugador>, col: &Gd<Comida>, papa: &Gd<Comida>) {
        let t = col.get_global_transform();
        let t = Transform3D::new(t.basis.orthonormalized(), t.origin);
        let l = t.affine_inverse() * papa.get_global_position();
        let tapa = t * Vector3::new(l.x, freidora::canasto()[1] / 2.0, l.z);
        self.mirar_punto(j, tapa);
    }

    /// Lo que la mira tiene como objetivo, si es comida.
    fn comida_apuntada(j: &mut Gd<Jugador>) -> Option<Gd<Comida>> {
        match j.bind_mut().objetivo() {
            Some(Objetivo::Comida(c)) => Some(c),
            _ => None,
        }
    }

    /// Altura de una comida relativa a la freidora.
    fn altura_en(f: &Gd<Freidora>, c: &Gd<Comida>) -> f32 {
        (f.get_global_transform().affine_inverse() * c.get_global_position()).y
    }

    /// Las porciones del colador que no son `primera`.
    fn otras_tandas(col: &Gd<Comida>, primera: &Gd<Comida>) -> Vec<Gd<Comida>> {
        let todas = Colador::de(col).map(|c| c.bind().contenido()).unwrap_or_default();
        todas.into_iter().filter(|c| c != primera).collect()
    }

    /// Una fase por llamada; devuelve true al terminar.
    pub(super) fn chequear_freir(&mut self) -> bool {
        let mundo = self.mundo();
        let Some(mut f) = self.freidora_de_papas() else {
            self.chequear(false, "REQ-FRE-04 el carro de las papas tiene una freidora");
            return true;
        };
        let Some(mut j) = todos::<Jugador>(&mundo).pop() else {
            self.chequear(false, "REQ-FRE-07 hay jugador");
            return true;
        };
        let colador = f.bind().colador(1).map(|(c, _)| c);
        match self.fase_freir {
            0 => {
                let (cubas, t0, t1) = { (f.bind().cantidad_cubas(), f.bind().temperatura(0), f.bind().temperatura(1)) };
                let arriba = f.bind().colador(0).is_some_and(|(_, abajo)| !abajo)
                    && f.bind().colador(1).is_some_and(|(_, abajo)| !abajo);
                self.chequear(
                    cubas == 2 && t0 == 20.0 && t1 == 20.0 && arriba,
                    &format!("REQ-FRE-04/08 doble: 2 cubas a 20 °C ({t0}, {t1}) con su colador arriba ({arriba})"),
                );
                // REQ-FRE-05: E prende solo la segunda cuba.
                f.bind_mut().alternar(1);
                self.esperar(120);
            }
            1 => {
                let (t0, t1) = (f.bind().temperatura(0), f.bind().temperatura(1));
                let nodo = f.clone().upcast::<Node>();
                let luz =
                    |n: &str| material_pieza(&nodo, n).map(|m| m.get_emission_energy_multiplier()).unwrap_or(-1.0);
                let (l1, l2) = (luz("pieza_piloto_1"), luz("pieza_piloto_2"));
                self.chequear(
                    t0 == 20.0 && (t1 - 25.0).abs() < 0.5 && f.bind().encendida(1) && l1 == 0.0 && l2 > 0.0,
                    &format!(
                        "REQ-FRE-04/05 la cuba 2 sube 2,5 °C/s sola ({t0:.1}, {t1:.1}) y prende su piloto ({l1}, {l2})"
                    ),
                );
                let cartel = f.bind().cartel(f.get_global_position() + Vector3::new(0.13, 0.0, 0.0));
                self.chequear(cartel.starts_with("[E] Apagar freidora 2"), &format!("REQ-FRE-05 cartel: {cartel}"));
                // Acelera: el aceite ya caliente (como otros chequeos que fijan la temperatura).
                f.bind_mut().set_temperatura(1, 180.0);
                // REQ-FRE-07: con una papa cortada en la mano, colocar sobre el colador la deja adentro.
                let Some(col) = colador else {
                    self.chequear(false, "REQ-FRE-07 la cuba 2 tiene colador");
                    return true;
                };
                let pc = col.get_global_position();
                let papa = self.agregar_comida("papa_cortada", Vector3::new(pc.x, pc.y + 0.4, pc.z + 0.5));
                j.bind_mut().agarrar(papa.clone().upcast());
                self.mirar_colador(&mut j, &col);
                j.bind_mut().colocar();
                self.papa_freir = Some(papa);
                self.esperar(5);
            }
            2 => {
                let papa = self.papa_freir.clone().unwrap();
                let col = colador.clone().unwrap();
                let adentro = Colador::de(&col).is_some_and(|c| c.bind().contenido().contains(&papa));
                self.chequear(
                    adentro && papa.is_freeze_enabled(),
                    "REQ-FRE-07 la papa cortada queda adentro del colador",
                );
                // REQ-FRE-08: E sobre el colador lo baja.
                self.mirar_colador(&mut j, &col);
                j.bind_mut().usar();
                self.esperar(40);
            }
            3 => {
                let papa = self.papa_freir.clone().unwrap();
                let abajo = f.bind().colador(1).is_some_and(|(_, abajo)| abajo);
                let y = Self::altura_en(&f, &papa);
                self.chequear(
                    abajo && y < TECHO_ACEITE && y > PISO_CUBA,
                    &format!("REQ-FRE-08 E baja el colador y la papa queda en el aceite (y = {y:.3})"),
                );
                // La primera tanda se fríe un rato sola.
                Engine::singleton().set_time_scale(ACELERADO);
                self.esperar(VENTAJA);
            }
            4 => {
                Engine::singleton().set_time_scale(1.0);
                // REQ-FRE-07: con el colador bajado, otra tanda también entra.
                let col = colador.clone().unwrap();
                let pc = col.get_global_position();
                let papa = self.agregar_comida("papa_cortada", Vector3::new(pc.x, pc.y + 0.5, pc.z + 0.5));
                j.bind_mut().agarrar(papa.upcast());
                self.mirar_colador(&mut j, &col);
                j.bind_mut().colocar();
                self.esperar(5);
            }
            5 => {
                let primera = self.papa_freir.clone().unwrap();
                let col = colador.clone().unwrap();
                let otras = Self::otras_tandas(&col, &primera);
                let Some(segunda) = otras.first().cloned() else {
                    self.chequear(false, "REQ-FRE-07 la segunda tanda entra con el colador bajado");
                    return true;
                };
                let y = Self::altura_en(&f, &segunda);
                let abajo = f.bind().colador(1).is_some_and(|(_, abajo)| abajo);
                let (p1, p2) = (primera.bind().punto(), segunda.bind().punto());
                let avance = |c: &Gd<Comida>| c.bind().estado_coccion().map(|e| e.avance).unwrap_or(0.0);
                let (a1, a2) = (avance(&primera), avance(&segunda));
                self.chequear(
                    otras.len() == 1
                        && abajo
                        && segunda.is_freeze_enabled()
                        && y < TECHO_ACEITE
                        && y > PISO_CUBA
                        && p2 == Some(Punto::Crudo)
                        && a1 > a2,
                    &format!(
                        "REQ-FRE-07 con el colador bajado entra otra tanda: queda en el aceite (y = {y:.3}) y \
                         arranca cruda ({p2:?}, avance {a2:.2}) mientras la primera sigue ({p1:?}, {a1:.2})"
                    ),
                );
                // Llena el colador con dos porciones de fritas (también van) y prueba la 5.ª.
                let mut c = Colador::de(&col).unwrap();
                for _ in 0..2 {
                    let fritas = self.agregar_comida("papas_fritas", col.get_global_position() + Vector3::UP * 0.5);
                    if c.bind_mut().meter(fritas.clone(), None).is_err() {
                        fritas.clone().queue_free();
                    }
                }
                let contenido = c.bind().contenido();
                let t = col.get_global_transform();
                let inv = Transform3D::new(t.basis.orthonormalized(), t.origin).affine_inverse();
                let locales: Vec<Vector3> = contenido.iter().map(|x| inv * x.get_global_position()).collect();
                let [w, h, d] = freidora::canasto();
                let adentro = locales.iter().all(|l| l.x.abs() < w / 2.0 && l.z.abs() < d / 2.0 && l.y.abs() < h / 2.0);
                let separadas = locales.iter().enumerate().all(|(i, a)| {
                    locales.iter().skip(i + 1).all(|b| Vector2::new(a.x - b.x, a.z - b.z).length() > 0.06)
                });
                self.chequear(
                    contenido.len() == 4 && adentro && separadas,
                    &format!(
                        "REQ-FRE-07 caben 4 porciones, cada una en su cuarto del canasto sin pisarse {:?}",
                        locales.iter().map(|l| format!("({:.3}, {:.3}, {:.3})", l.x, l.y, l.z)).collect::<Vec<_>>()
                    ),
                );
                // REQ-FRE-07: lleno, la 5.ª se apoya como siempre (no entra).
                let pc = col.get_global_position();
                let quinta = self.agregar_comida("papa_cortada", Vector3::new(pc.x, pc.y + 0.5, pc.z + 0.5));
                j.bind_mut().agarrar(quinta.clone().upcast());
                self.mirar_colador(&mut j, &col);
                j.bind_mut().colocar();
                let porciones = c.bind().porciones();
                let dentro = c.bind().contenido().contains(&quinta);
                self.chequear(
                    porciones == 4 && !dentro && !quinta.is_freeze_enabled() && j.bind().en_mano().is_none(),
                    &format!("REQ-FRE-07 lleno ({porciones}/4), la 5.ª porción no entra y se apoya"),
                );
                quinta.clone().queue_free();
                Engine::singleton().set_time_scale(ACELERADO);
                self.cuadros_freir = 0;
            }
            6 => {
                let papa = self.papa_freir.clone().unwrap();
                self.cuadros_freir += 1;
                if papa.bind().producto() != "papas_fritas" && self.cuadros_freir < ESPERA_MAX {
                    return false; // se repite esta fase
                }
                Engine::singleton().set_time_scale(1.0);
                let col = colador.clone().unwrap();
                let otras = Self::otras_tandas(&col, &papa);
                let segunda = otras.iter().find(|x| x.bind().producto() == "papa_cortada");
                let s2 = segunda.map(|x| x.bind().punto());
                let sigue = Colador::de(&col).is_some_and(|c| c.bind().contenido().contains(&papa));
                let segundos = self.cuadros_freir as f64 * ACELERADO / 60.0;
                let (producto, punto, temp) = {
                    let p = papa.bind();
                    (p.producto().to_string(), p.punto(), p.temperatura().unwrap_or(0.0))
                };
                self.chequear(
                    producto == "papas_fritas"
                        && punto == Some(Punto::Cocido)
                        && sigue
                        && s2 == Some(Some(Punto::Crudo)),
                    &format!(
                        "REQ-FRE-07/09/10 la primera tanda sale papas fritas Cocida en el colador antes que la \
                         segunda ({producto}, {punto:?}, {temp:.0} °C, ~{segundos:.0} s; la segunda: {s2:?})"
                    ),
                );
                // REQ-FRE-08: con el colador abajo, mirando la primera se agarra solo esa.
                for mut o in otras {
                    let pos = o.get_global_position();
                    o.set_meta(POS_ANTES, &pos.to_variant());
                }
                self.mirar_porcion(&mut j, &col, &papa);
                let apuntada = Self::comida_apuntada(&mut j);
                self.chequear(
                    apuntada.as_ref() == Some(&papa),
                    &format!(
                        "REQ-FRE-08 mirando la primera tanda en el colador bajado, el objetivo es esa porción ({:?})",
                        apuntada.map(|c| c.bind().producto().to_string())
                    ),
                );
                j.bind_mut().agarrar(papa.upcast());
                self.esperar(3);
            }
            7 => {
                let papa = self.papa_freir.clone().unwrap();
                let col = colador.clone().unwrap();
                let otras = Self::otras_tandas(&col, &papa);
                let quietas = otras.iter().all(|o| {
                    o.get_meta(POS_ANTES)
                        .try_to::<Vector3>()
                        .is_ok_and(|p| p.distance_to(o.get_global_position()) < 0.001)
                });
                let abajo = f.bind().colador(1).is_some_and(|(_, abajo)| abajo);
                let segunda = otras.iter().find(|x| x.bind().producto() == "papa_cortada").cloned();
                let en_aceite = segunda.as_ref().is_some_and(|s| {
                    let y = Self::altura_en(&f, s);
                    y < TECHO_ACEITE && y > PISO_CUBA && s.is_freeze_enabled()
                });
                self.chequear(
                    papa.bind().sostenida
                        && !papa.is_freeze_enabled()
                        && otras.len() == 3
                        && quietas
                        && abajo
                        && en_aceite,
                    &format!(
                        "REQ-FRE-08 la primera tanda se saca sola con el colador abajo: las otras {} quedan \
                         quietas en su lugar ({quietas}) y la segunda sigue en el aceite ({en_aceite})",
                        otras.len()
                    ),
                );
                // La primera, vendida (se va); la segunda se sigue friendo.
                j.bind_mut().soltar();
                papa.clone().queue_free();
                self.papa_freir = segunda;
                // REQ-FRE-08: E otra vez lo sube.
                self.mirar_colador(&mut j, &col);
                j.bind_mut().usar();
                self.esperar(40);
            }
            8 => {
                let Some(papa) = self.papa_freir.clone() else {
                    self.chequear(false, "REQ-FRE-07 la segunda tanda sigue en el colador");
                    return true;
                };
                let y = Self::altura_en(&f, &papa);
                let arriba = f.bind().colador(1).is_some_and(|(_, abajo)| !abajo);
                let t = papa.bind().temperatura().unwrap_or(0.0);
                self.chequear(
                    arriba && y - 0.017 > TECHO_ACEITE && t > 100.0,
                    &format!(
                        "REQ-FRE-08 E sube el colador: la segunda tanda escurre encima del aceite (y = {y:.3}, {t:.0} °C)"
                    ),
                );
                // Arriba también se saca agarrándola, sola.
                let col = colador.clone().unwrap();
                self.mirar_porcion(&mut j, &col, &papa);
                let apuntada = Self::comida_apuntada(&mut j);
                self.chequear(
                    apuntada.as_ref() == Some(&papa),
                    "REQ-FRE-08 arriba, mirando una porción se apunta a ella",
                );
                j.bind_mut().agarrar(papa.upcast());
                self.esperar(3);
            }
            _ => {
                let papa = self.papa_freir.clone().unwrap();
                let col = colador.clone().unwrap();
                let quedan = Colador::de(&col).map(|c| c.bind().contenido()).unwrap_or_default();
                self.chequear(
                    quedan.len() == 2 && !quedan.contains(&papa) && !papa.is_freeze_enabled() && papa.bind().sostenida,
                    &format!(
                        "REQ-FRE-08 las papas se sacan del colador agarrándolas, de a una (quedan {})",
                        quedan.len()
                    ),
                );
                j.bind_mut().soltar();
                // Limpieza: las porciones de la prueba se van.
                papa.clone().queue_free();
                for mut q in quedan {
                    q.queue_free();
                }
                let t0 = f.bind().temperatura(0);
                let sigue = f.bind().encendida(1);
                self.chequear(
                    t0 < 20.5 && sigue,
                    &format!("REQ-FRE-05 la cuba 2 sigue prendida y la otra siguió apagada ({t0:.1} °C)"),
                );
                return true;
            }
        }
        self.fase_freir += 1;
        false
    }
}
