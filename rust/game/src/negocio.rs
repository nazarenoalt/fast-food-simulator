//! SPEC-010 (economía) y SPEC-011 (proveedor): caja, reputación, estadísticas y compras.

use carrito_core::clientes::{Evaluacion, estrellas_texto};
use carrito_core::economia::{Caja, EstadisticasDia, Reputacion, plata};
use carrito_core::proveedor::{Proveedor, texto_llegada};
use godot::classes::{INode, Node};
use godot::prelude::*;

use crate::carrito::{self, Carrito};
use crate::datos::catalogo;
use crate::dia_noche::{self, DiaNoche};
use crate::hud::{self, Hud};
use crate::paquete::Paquete;
use crate::util;

pub const GRUPO: &str = "negocio";

#[derive(GodotClass)]
#[class(base=Node)]
pub struct Negocio {
    base: Base<Node>,
    caja: Caja,
    reputacion: Reputacion,
    hoy: EstadisticasDia,
    proveedor: Proveedor,
    dia_actual: u32,
    entregas: u32,
}

#[godot_api]
impl INode for Negocio {
    fn init(base: Base<Node>) -> Self {
        Self {
            base,
            caja: Caja::default(),
            reputacion: Reputacion::default(),
            hoy: EstadisticasDia::default(),
            proveedor: Proveedor::default(),
            dia_actual: 1,
            entregas: 0,
        }
    }

    fn ready(&mut self) {
        self.base_mut().add_to_group(GRUPO);
    }

    fn physics_process(&mut self, _delta: f64) {
        let yo = self.to_gd();
        let Some(dn) = util::unico::<DiaNoche>(&yo, dia_noche::GRUPO) else { return };
        let (ahora, dia) = {
            let d = dn.bind();
            (d.minuto_absoluto(), d.dia())
        };

        // REQ-ECO-05: al pasar las 00:00, resumen del día que terminó.
        if dia != self.dia_actual {
            let texto = self.hoy.resumen(self.dia_actual);
            if let Some(mut h) = util::unico::<Hud>(&yo, hud::GRUPO) {
                h.bind_mut().mostrar_resumen(&texto);
            }
            self.hoy = EstadisticasDia::default();
            self.dia_actual = dia;
        }

        // REQ-PRO-04: lo que llegó aparece como paquetes sobre el pallet.
        let llegados = self.proveedor.tomar_llegados(ahora);
        if !llegados.is_empty() {
            self.entregar(&llegados);
        }
    }
}

impl Negocio {
    fn entregar(&mut self, bloques: &[String]) {
        let yo = self.to_gd();
        let Some(carrito) = util::unico::<Carrito>(&yo, carrito::GRUPO) else { return };
        let pallet = carrito.bind().pos_pallet();
        let Some(mut mundo) = carrito.get_parent() else { return };
        for id in bloques {
            let Some(def) = catalogo().bloque(id) else { continue };
            // Apilados sobre el pallet, un poco corridos para que no se traben.
            let i = self.entregas % 6;
            self.entregas += 1;
            let pos = pallet + Vector3::new((i % 2) as f32 * 0.3 - 0.15, 0.25 + (i / 2) as f32 * 0.25, 0.0);
            let mut p = Paquete::crear(def.clone());
            mundo.add_child(&p);
            p.set_global_position(pos);
        }
        hud::avisar(
            &yo,
            &format!(
                "Llegó tu pedido ({} paquete{}) — está en el pallet",
                bloques.len(),
                if bloques.len() == 1 { "" } else { "s" }
            ),
        );
    }

    /// REQ-ECO-06
    pub fn texto_hud(&self) -> String {
        format!("Caja {}   ★ {:.1}", plata(self.caja.saldo), self.reputacion.0)
    }

    pub fn saldo(&self) -> f32 {
        self.caja.saldo
    }

    pub fn reputacion(&self) -> f32 {
        self.reputacion.0
    }

    pub fn ventas_de_hoy(&self) -> u32 {
        self.hoy.ventas
    }

    pub fn perdidos_de_hoy(&self) -> u32 {
        self.hoy.perdidos
    }

    /// Solo para pruebas.
    pub fn set_saldo(&mut self, s: f32) {
        self.caja.saldo = s;
    }

    /// REQ-CLI-09, REQ-CLI-10, REQ-ECO-01, REQ-ECO-04
    pub fn venta(&mut self, ev: &Evaluacion) -> String {
        let total = ev.pago + ev.propina;
        self.caja.cobrar(total);
        self.hoy.venta(total);
        self.reputacion.registrar(ev.estrellas);
        let propina = if ev.propina > 0.0 { format!(" (propina {})", plata(ev.propina)) } else { String::new() };
        format!("+{}{propina} · {}", plata(total), estrellas_texto(ev.estrellas))
    }

    /// REQ-CLI-06, REQ-CLI-10: cliente que se fue enojado.
    pub fn cliente_perdido(&mut self) {
        self.hoy.perdido();
        self.reputacion.registrar(1.0);
    }

    /// REQ-PRO-02, REQ-ECO-02. Devuelve el texto para avisar.
    pub fn comprar(&mut self, bloque: &str) -> Result<String, String> {
        let def = catalogo().bloque(bloque).ok_or_else(|| format!("No existe \"{bloque}\""))?.clone();
        let yo = self.to_gd();
        let ahora = util::unico::<DiaNoche>(&yo, dia_noche::GRUPO).map(|d| d.bind().minuto_absoluto()).unwrap_or(0.0);
        self.caja.pagar(def.precio).map_err(|e| format!("No te alcanza: faltan {}", plata(e.falta)))?;
        self.hoy.gasto(def.precio);
        let llega = self.proveedor.pedir(bloque, ahora);
        Ok(format!("Pediste {} ({}) — llega {}", def.nombre, plata(def.precio), texto_llegada(llega, ahora)))
    }

    /// Pedidos en camino, para el panel. REQ-PRO-01
    pub fn pendientes_texto(&self) -> Vec<String> {
        let yo = self.to_gd();
        let ahora = util::unico::<DiaNoche>(&yo, dia_noche::GRUPO).map(|d| d.bind().minuto_absoluto()).unwrap_or(0.0);
        self.proveedor
            .pendientes
            .iter()
            .map(|p| {
                let nombre = catalogo().bloque(&p.bloque).map(|b| b.nombre.clone()).unwrap_or_default();
                format!("{nombre} — llega {}", texto_llegada(p.llega, ahora))
            })
            .collect()
    }
}
