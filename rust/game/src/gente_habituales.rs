//! TASK-0504 · SPEC-030: clientes habituales. Submódulo de `gente`: ve los campos de `Gente`.
//! Las reglas están en `carrito_core::habituales`; acá solo se las aplica a las personas.

use std::collections::HashSet;

use carrito_core::caminos::TipoNodo;
use carrito_core::clientes::{self, Evaluacion, ItemMenu, Pedido};
use carrito_core::habituales::{self as hab, Habitual, Habituales};
use carrito_core::peatones::Plan;
use godot::prelude::*;

use super::{Gente, Origen, texto_pedido};
use crate::carrito::{self, Carrito};
use crate::datos::plaza;
use crate::peaton::Accion;
use crate::util;

/// Estado propio de esta tarea (los habituales y su memoria). REQ-HAB-07: no se guarda.
#[derive(Default)]
pub(super) struct Estado {
    habituales: Habituales,
    /// REQ-HAB-05: clientes habituales con memoria buena que saludan al llegar a la fila.
    por_saludar: HashSet<u64>,
    /// Para pruebas: clientes que ya saludaron.
    saludaron: Vec<u64>,
    /// Para pruebas: la próxima atención con 4,5★ o más lo vuelve habitual sin sortear.
    forzar_promocion: bool,
}

impl Gente {
    /// Cada cuadro: una vez por día se decide quién viene y a qué hora; ¿llega algún
    /// habitual? (REQ-HAB-03, REQ-HAB-06)
    pub(super) fn cuadro_habituales(&mut self, _dt: f32) {
        let dia = self.dia;
        self.est_habituales.habituales.planear_dia(&mut self.azar, dia);
        let hora = self.hora;
        for hid in self.est_habituales.habituales.llegan(hora) {
            self.llega_habitual(hid);
        }
        self.saludar_habituales();
    }

    /// REQ-HAB-03: el habitual `hid` llega caminando desde el borde y se suma a la fila. Con
    /// la fila llena o el cartel de cerrado no viene (no cuenta como visita).
    fn llega_habitual(&mut self, hid: usize) -> Option<u64> {
        if !clientes::llegan_clientes(&self.fila, self.cartel_cerrado())
            || self.clientes.values().any(|c| c.habitual == Some(hid))
        {
            return None;
        }
        let h = self.est_habituales.habituales.get(hid)?.clone();
        let carrito = util::unico::<Carrito>(&self.to_gd(), carrito::GRUPO)?;
        let destino = carrito.bind().posicion_fila(self.fila.len());
        let nodo_fila = self.red.mas_cercano(destino.x, destino.z);
        let inicio = self
            .red
            .de_tipo(|t| *t == TipoNodo::Salida)
            .into_iter()
            .min_by(|&a, &b| self.pos(a).distance_to(destino).total_cmp(&self.pos(b).distance_to(destino)))
            .unwrap_or(0);
        let ruta = self.ruta(inicio, nodo_fila, 0.0);
        let vel = plaza().agenda.velocidad(&mut self.azar, h.perfil);
        // REQ-HAB-01: con su cara, su ropa y su perfil.
        let mut peaton = self.agregar_con(
            inicio,
            vec![Accion::Caminar(ruta), Accion::EnFila],
            h.perfil,
            Plan::Pasear,
            Origen::Vuelve(h.apariencia.clone()),
            vel,
        );
        // REQ-HAB-06: con memoria buena tiene más paciencia.
        let Some(id) = self.sumar_a_la_fila(peaton.clone(), h.perfil, h.factor_paciencia(), Some(hid)) else {
            peaton.queue_free();
            return None;
        };
        if h.memoria_buena() {
            self.est_habituales.por_saludar.insert(id);
        }
        Some(id)
    }

    /// REQ-HAB-05: con memoria buena saluda al llegar a la fila.
    fn saludar_habituales(&mut self) {
        let llegaron: Vec<u64> = self
            .est_habituales
            .por_saludar
            .iter()
            .copied()
            .filter(|id| self.clientes.get(id).is_none_or(|c| c.llego))
            .collect();
        for id in llegaron {
            self.est_habituales.por_saludar.remove(&id);
            if let Some(c) = self.clientes.get_mut(&id)
                && c.peaton.is_instance_valid()
            {
                c.peaton.bind_mut().decir(hab::SALUDO, Color::from_rgb(0.6, 1.0, 0.6), 2.5);
                self.est_habituales.saludaron.push(id);
            }
        }
    }

    /// El habitual del cliente `id`, si es uno.
    fn habitual_del_cliente(&self, id: u64) -> Option<&Habitual> {
        let hid = self.clientes.get(&id)?.habitual?;
        self.est_habituales.habituales.get(hid)
    }

    /// REQ-HAB-04: si el cliente `id` es habitual, su pedido.
    pub(super) fn pedido_habitual(&mut self, id: u64, menu: &[ItemMenu], aderezos: &[String]) -> Option<Pedido> {
        self.habitual_del_cliente(id)?.pedido(menu, aderezos)
    }

    /// REQ-CLI-05, REQ-HAB-05: el texto del globo del cliente `id`.
    pub(super) fn texto_globo(&self, id: u64, p: &Pedido) -> String {
        let texto = texto_pedido(p);
        match self.habitual_del_cliente(id) {
            Some(h) => hab::texto_globo(&h.nombre, &texto, h.es_lo_de_siempre(p)),
            None => texto,
        }
    }

    /// El cliente `id` aceptó lo que le dieron (REQ-HAB-01, REQ-HAB-02, REQ-HAB-06). Se llama
    /// antes de despedirlo: todavía está en `self.clientes`.
    pub(super) fn al_atender(&mut self, id: u64, ev: &Evaluacion, pedido: &Pedido) {
        let Some(c) = self.clientes.get(&id) else { return };
        if let Some(hid) = c.habitual {
            self.est_habituales.habituales.recordar(hid, ev.estrellas);
            return;
        }
        if !c.peaton.is_instance_valid() {
            return;
        }
        let apariencia = c.peaton.bind().apariencia().clone();
        let perfil = c.perfil;
        let forzar = std::mem::take(&mut self.est_habituales.forzar_promocion);
        let nombres = &plaza().habituales.nombres;
        let habs = &mut self.est_habituales.habituales;
        let hid = if forzar && ev.estrellas >= hab::ESTRELLAS_PROMOCION {
            habs.promover(&mut self.azar, nombres, apariencia, perfil, pedido.clone(), self.hora, ev.estrellas)
        } else {
            habs.quizas_promover(&mut self.azar, nombres, apariencia, perfil, pedido.clone(), self.hora, ev.estrellas)
        };
        if let Some(c) = self.clientes.get_mut(&id) {
            c.habitual = hid;
        }
    }

    /// El cliente `id` se fue enojado: si es habitual, lo recuerda como 1 estrella (REQ-HAB-06).
    pub(super) fn al_perder(&mut self, id: u64) {
        if let Some(hid) = self.clientes.get(&id).and_then(|c| c.habitual) {
            self.est_habituales.habituales.recordar(hid, hab::ESTRELLAS_ENOJADO);
        }
    }

    // ── Para pruebas ──────────────────────────────────────────────

    /// Para pruebas: atiende al primero de la fila (si ya pidió) con esas estrellas, como si le
    /// hubieran dado lo que pidió, y lo despide. Con `forzar_promocion`, si puso 4,5★ o más se
    /// vuelve habitual seguro. Devuelve el número de habitual que quedó (si es uno).
    pub fn probar_atender_primero(&mut self, estrellas: f32, forzar_promocion: bool) -> Option<usize> {
        let id = self.fila.primero()?;
        let pedido = self.clientes.get(&id)?.pedido.clone()?;
        self.est_habituales.forzar_promocion = forzar_promocion;
        self.al_atender(id, &Evaluacion { estrellas, pago: 0.0, propina: 0.0 }, &pedido);
        self.est_habituales.forzar_promocion = false;
        let hid = self.clientes.get(&id).and_then(|c| c.habitual);
        self.despedir(id);
        hid
    }

    /// Para pruebas: una copia del habitual `hid` (si sigue siéndolo).
    pub fn probar_habitual(&self, hid: usize) -> Option<Habitual> {
        self.est_habituales.habituales.get(hid).cloned()
    }

    /// Para pruebas: cuántos habituales hay.
    pub fn cantidad_habituales(&self) -> usize {
        self.est_habituales.habituales.len()
    }

    /// Para pruebas: el habitual `hid` viene ya (su visita de hoy pasa a ser ahora).
    pub fn adelantar_visita(&mut self, hid: usize) {
        let hora = self.hora;
        if let Some(h) = self.est_habituales.habituales.get_mut(hid) {
            h.visita = Some(hora);
        }
    }

    /// Para pruebas: el cliente que es el habitual `hid`, dónde está y si se ve como siempre.
    pub fn cliente_habitual(&self, hid: usize) -> Option<(u64, Vector3, bool)> {
        let (id, c) = self.clientes.iter().find(|(_, c)| c.habitual == Some(hid))?;
        if !c.peaton.is_instance_valid() {
            return None;
        }
        let igual =
            self.est_habituales.habituales.get(hid).is_some_and(|h| &h.apariencia == c.peaton.bind().apariencia());
        Some((*id, c.peaton.get_global_position(), igual))
    }

    /// Para pruebas: ¿el cliente `id` saludó al llegar? (REQ-HAB-05)
    pub fn saludo(&self, id: u64) -> bool {
        self.est_habituales.saludaron.contains(&id)
    }

    /// Para pruebas: ¿el primero de la fila es el cliente `id`, ya llegó y pidió?
    pub fn primero_listo(&self, id: u64) -> bool {
        self.fila.primero() == Some(id) && self.clientes.get(&id).is_some_and(|c| c.llego && c.pedido.is_some())
    }

    /// Para pruebas: el texto del globo del primero de la fila (REQ-HAB-05).
    pub fn globo_del_primero(&self) -> Option<String> {
        let id = self.fila.primero()?;
        let p = self.clientes.get(&id)?.pedido.as_ref()?;
        Some(self.texto_globo(id, p))
    }

    /// Para pruebas: despide a los clientes de la fila (sin contar como perdidos); con
    /// `dejar_habituales`, menos a los habituales.
    pub fn despejar_fila(&mut self, dejar_habituales: bool) {
        let ids: Vec<u64> = self
            .clientes
            .iter()
            .filter(|(_, c)| !(dejar_habituales && c.habitual.is_some()))
            .map(|(id, _)| *id)
            .collect();
        for id in ids {
            self.despedir(id);
        }
    }

    /// Para pruebas: pone al habitual `hid` en su lugar de la fila (para no esperar que camine).
    pub fn acercar_habitual(&mut self, hid: usize) {
        let Some((id, _, _)) = self.cliente_habitual(hid) else { return };
        let Some(carrito) = util::unico::<Carrito>(&self.to_gd(), carrito::GRUPO) else { return };
        let Some(lugar) = self.fila.lugar(id) else { return };
        let destino = carrito.bind().posicion_fila(lugar);
        if let Some(c) = self.clientes.get_mut(&id) {
            c.peaton.set_global_position(destino);
            c.peaton.bind_mut().reemplazar_acciones(vec![Accion::EnFila]);
        }
    }
}
