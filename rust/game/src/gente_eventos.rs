//! TASK-0505 · SPEC-019: feria y partido. Submódulo de `gente`: ve los campos de `Gente`
//! (`self.dia`, `self.hora` y `self.modificador` ya están al día en cada cuadro).

use std::collections::{HashMap, HashSet};

use carrito_core::caminos::{TipoNodo, Z_VEREDA_SUR};
use carrito_core::eventos::{self, Puesto};
use carrito_core::peatones::{self, Apariencia, Paleta};
use carrito_core::rutinas::Perfil;
use godot::prelude::*;

use super::Gente;
use crate::datos::plaza;
use crate::feria::Feria;
use crate::hud;
use crate::peaton::{Accion, Peaton};

/// Los vendedores llegan antes de que empiece la feria (como la agenda, REQ-RUT-03): lo que
/// tardan en llegar desde el borde.
const ADELANTO_VENDEDORES_H: f32 = 0.75;
/// Un salto de reloj más grande que esto es un cambio a mano (prueba o partida cargada): las
/// cosas aparecen ya en su lugar, sin caminar.
const SALTO_DE_RELOJ_H: f32 = 0.25;

/// Estado propio de esta tarea (aviso del día, puestos, vendedores...).
#[derive(Default)]
pub(super) struct Estado {
    /// REQ-EVE-03: último día en que salió el aviso de la mañana (0 = ninguno) y su texto.
    dia_avisado: u32,
    ultimo_aviso: Option<String>,
    /// Día en que salió `ultimo_aviso` (REQ-EVE-10: la primera semana no sale ninguno).
    dia_ultimo_aviso: u32,
    /// REQ-EVE-05: los puestos armados y sus vendedores (no cuentan como gente de la plaza
    /// ni como clientes: no están en `Gente::peatones`).
    feria: Option<Gd<Feria>>,
    vendedores: Vec<(Gd<Peaton>, Puesto)>,
    /// REQ-EVE-06: quienes ya pasaron frente a un puesto (se paran una sola vez).
    vieron_puestos: HashSet<u64>,
    /// REQ-EVE-09: cuántas veces saltó cada uno en el festejo.
    saltos: HashMap<u64, u32>,
    /// Día y hora del cuadro anterior (para distinguir el paso del tiempo de un salto de reloj).
    antes: Option<(u32, f32)>,
}

fn v3(p: [f32; 2]) -> Vector3 {
    Vector3::new(p[0], 0.0, p[1])
}

impl Gente {
    /// Cada cuadro: aviso del día, puestos de la feria, festejo...
    pub(super) fn cuadro_eventos(&mut self, dt: f32) {
        let ahora = (self.dia, self.hora);
        let natural = self.est_eventos.antes.is_none_or(|(d, h)| {
            let pasado = (ahora.0 as f32 - d as f32) * 24.0 + ahora.1 - h;
            (0.0..SALTO_DE_RELOJ_H).contains(&pasado)
        });
        self.est_eventos.antes = Some(ahora);
        self.aviso_del_dia();
        self.armar_feria(natural);
        self.mirar_puestos();
        self.festejar(dt);
    }

    /// REQ-EVE-07: retoca la apariencia de alguien que llega (camiseta).
    pub(super) fn retocar_por_evento(&mut self, ap: &mut Apariencia, _perfil: Perfil) {
        if let Some(c) = eventos::camiseta(&mut self.azar, &self.modificador) {
            ap.remera = c;
        }
    }

    /// REQ-EVE-03: a las 7 (o al empezar, si ya pasó) avisa los eventos del día, una vez.
    fn aviso_del_dia(&mut self) {
        if self.est_eventos.dia_avisado == self.dia || self.hora < eventos::HORA_AVISO {
            return;
        }
        self.est_eventos.dia_avisado = self.dia;
        if let Some(texto) = eventos::aviso_del_dia(&plaza().eventos, self.dia) {
            hud::avisar(&self.to_gd(), &texto);
            self.est_eventos.ultimo_aviso = Some(texto);
            self.est_eventos.dia_ultimo_aviso = self.dia;
        }
    }

    /// REQ-EVE-05: los puestos están mientras dura el tramo "feria/puestos" (6–22: aparecen y
    /// desaparecen de noche) y tienen vendedor durante "feria/feria" (10–18).
    fn armar_feria(&mut self, natural: bool) {
        let quiere_puestos = self.modificador.activo("feria/puestos");
        match (&self.est_eventos.feria, quiere_puestos) {
            (None, true) => {
                let f = Feria::crear(eventos::puestos_feria());
                self.base_mut().add_child(&f);
                self.est_eventos.feria = Some(f);
            }
            (Some(_), false) => {
                if let Some(mut f) = self.est_eventos.feria.take() {
                    f.queue_free();
                }
            }
            _ => {}
        }

        self.est_eventos.vendedores.retain(|(v, _)| v.is_instance_valid());
        let adelantado = plaza().modificador(self.dia, self.hora + ADELANTO_VENDEDORES_H);
        let quiere_vendedores = self.est_eventos.feria.is_some()
            && (self.modificador.activo("feria/feria") || adelantado.activo("feria/feria"));
        let hay = !self.est_eventos.vendedores.is_empty();
        if quiere_vendedores && !hay {
            for p in eventos::puestos_feria() {
                self.poner_vendedor(&p, natural);
            }
        } else if !quiere_vendedores && hay {
            let llevar = natural && self.est_eventos.feria.is_some();
            for (mut v, p) in std::mem::take(&mut self.est_eventos.vendedores) {
                if llevar {
                    // Termina la feria: se van caminando por detrás del puesto.
                    let ruta = self.ruta_vendedor(&p, false);
                    v.bind_mut().reemplazar_acciones(vec![Accion::Caminar(ruta), Accion::Desaparecer]);
                } else {
                    v.queue_free();
                }
            }
        }
    }

    /// El camino de un vendedor entre su lugar en el puesto y una salida del borde, por detrás
    /// del puesto y la vereda sur. `ida` = de la salida al puesto.
    fn ruta_vendedor(&mut self, p: &Puesto, ida: bool) -> Vec<Vector3> {
        let (atras, lugar) = (p.atras(), p.vendedor());
        let vereda = self
            .red
            .de_tipo(|t| *t == TipoNodo::Paso)
            .into_iter()
            .filter(|&n| (self.red.pos[n][1] - Z_VEREDA_SUR).abs() < 0.5)
            .min_by(|&a, &b| (self.red.pos[a][0] - atras[0]).abs().total_cmp(&(self.red.pos[b][0] - atras[0]).abs()))
            .unwrap_or(0);
        let salida = self.salida_al_azar();
        if ida {
            let mut r = self.ruta(salida, vereda, 0.0);
            r.extend([v3(atras), v3(lugar)]);
            r
        } else {
            let mut r = vec![v3(atras)];
            r.extend(self.ruta(vereda, salida, 0.0));
            r
        }
    }

    /// REQ-EVE-05: el vendedor de un puesto, parado detrás del mostrador mirando al frente.
    /// Si la feria empieza con el reloj andando, llega caminando desde el borde.
    fn poner_vendedor(&mut self, p: &Puesto, natural: bool) {
        let id = self.sig_id;
        self.sig_id += 1;
        let ap = peatones::apariencia_de(&mut self.azar, &Paleta::comun());
        let lugar = p.vendedor();
        let quieto = Accion::Esperar { mirar: Some(v3(p.frente())), segundos: 1.0e7 };
        let (acciones, inicio) = if natural {
            let ruta = self.ruta_vendedor(p, true);
            let inicio = ruta.first().copied().unwrap_or(v3(lugar));
            (vec![Accion::Caminar(ruta), quieto], inicio)
        } else {
            (vec![quieto], v3(lugar))
        };
        let mut v = Peaton::crear(id, ap, 1.2, false, acciones);
        self.base_mut().add_child(&v);
        v.set_global_position(inicio);
        self.est_eventos.vendedores.push((v, *p));
    }

    /// REQ-EVE-06: durante la feria, algunos paseantes que pasan frente a un puesto se paran a
    /// mirarlo un rato (una sola vez cada uno).
    fn mirar_puestos(&mut self) {
        if !self.modificador.activo("feria/feria") || self.est_eventos.feria.is_none() {
            self.est_eventos.vieron_puestos.clear();
            return;
        }
        let puestos = eventos::puestos_feria();
        let vivos: HashSet<u64> = self.peatones.iter().map(|p| p.bind().id).collect();
        self.est_eventos.vieron_puestos.retain(|id| vivos.contains(id));
        let mut paradas: Vec<(Gd<Peaton>, usize)> = Vec::new();
        for p in &self.peatones {
            let b = p.bind();
            let id = b.id;
            let caminando = matches!(b.accion_actual(), Some(Accion::Caminar(_)));
            // Los que trotan, van a la fila o van en grupo (REQ-RUT-08) siguen de largo.
            if !caminando
                || b.velocidad() > 2.0
                || self.clientes.contains_key(&id)
                || self.est_eventos.vieron_puestos.contains(&id)
                || self.en_grupo(id)
            {
                continue;
            }
            let pos = p.get_global_position();
            if let Some(i) = eventos::puesto_cercano(&puestos, [pos.x, pos.z]) {
                paradas.push((p.clone(), i));
            }
        }
        for (mut p, i) in paradas {
            self.est_eventos.vieron_puestos.insert(p.bind().id);
            if !self.azar.chance(eventos::CHANCE_PARAR_EN_PUESTO) {
                continue;
            }
            let segundos = eventos::segundos_en_puesto(&mut self.azar);
            let centro = Vector3::new(puestos[i].x, 1.0, puestos[i].z);
            p.bind_mut().intercalar(Accion::Esperar { mirar: Some(centro), segundos });
        }
    }

    /// REQ-EVE-09: en el festejo, los que tienen camiseta y están charlando o parados saltan
    /// con los brazos arriba cada tanto.
    fn festejar(&mut self, dt: f32) {
        if !self.modificador.activo("partido/festejo") {
            self.est_eventos.saltos.clear();
            return;
        }
        let mut saltan: Vec<Gd<Peaton>> = Vec::new();
        for p in &self.peatones {
            let b = p.bind();
            let quieto = matches!(b.accion_actual(), Some(Accion::Charlar { .. } | Accion::Esperar { .. }));
            if !quieto
                || self.clientes.contains_key(&b.id)
                || !eventos::es_camiseta(b.apariencia().remera, &self.modificador)
                || self.est_eventos.saltos.get(&b.id).copied().unwrap_or(0) >= eventos::MAX_SALTOS
            {
                continue;
            }
            saltan.push(p.clone());
        }
        for mut p in saltan {
            if !self.azar.chance(eventos::SALTOS_POR_S * dt) {
                continue;
            }
            let [a, b] = eventos::SEGUNDOS_SALTO;
            let segundos = self.azar.rango(a, b);
            *self.est_eventos.saltos.entry(p.bind().id).or_default() += 1;
            p.bind_mut().intercalar(Accion::Saltar { segundos });
        }
    }

    // ── Para pruebas ──────────────────────────────────────────────

    /// Para pruebas: cuántos puestos hay armados y cuántos vendedores parados en su lugar
    /// (o llegando). REQ-EVE-05
    pub fn puestos_y_vendedores(&self) -> (usize, usize) {
        let puestos =
            self.est_eventos.feria.as_ref().filter(|f| f.is_instance_valid()).map_or(0, |f| f.bind().cantidad());
        let vendedores = self.est_eventos.vendedores.iter().filter(|(v, _)| v.is_instance_valid()).count();
        (puestos, vendedores)
    }

    /// Para pruebas: el último aviso de la mañana. REQ-EVE-03
    pub fn ultimo_aviso(&self) -> Option<String> {
        self.est_eventos.ultimo_aviso.clone()
    }

    /// Para pruebas: el aviso de la mañana de hoy, si salió alguno (REQ-EVE-03, REQ-EVE-10).
    pub fn aviso_de_hoy(&self) -> Option<String> {
        (self.est_eventos.dia_ultimo_aviso == self.dia).then(|| self.est_eventos.ultimo_aviso.clone()).flatten()
    }

    /// Para pruebas: ¿esa persona lleva la camiseta de un equipo de hoy? REQ-EVE-07
    pub fn con_camiseta(&self, id: u64) -> bool {
        let equipos: Vec<[f32; 3]> = plaza().eventos.iter().flat_map(|e| e.equipos.clone()).collect();
        self.peatones
            .iter()
            .find(|p| p.is_instance_valid() && p.bind().id == id)
            .is_some_and(|p| equipos.contains(&p.bind().apariencia().remera))
    }

    /// Para pruebas: cuántos están saltando ahora. REQ-EVE-09
    pub fn saltando(&self) -> usize {
        self.peatones
            .iter()
            .filter(|p| p.is_instance_valid() && matches!(p.bind().accion_actual(), Some(Accion::Saltar { .. })))
            .count()
    }

    /// Para pruebas: hace llegar `n` personas de la agenda ya en su lugar (sin caminar desde
    /// el borde), como al empezar la partida. REQ-EVE-09
    pub fn probar_presentes(&mut self, n: usize) {
        for _ in 0..n {
            self.nuevo_paseante(false);
        }
    }
}
