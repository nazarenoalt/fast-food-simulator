//! SPEC-011 · Panel del proveedor (Tab): comprar bloques y ver lo que está en camino.

use std::cell::Cell;

use carrito_core::economia::plata;
use godot::classes::control::{LayoutPreset, SizeFlags};
use godot::classes::input::MouseMode;
use godot::classes::{
    Button, CanvasLayer, HBoxContainer, HSeparator, ICanvasLayer, Input, Label, PanelContainer, VBoxContainer,
};
use godot::builtin::Side;
use godot::prelude::*;

use crate::datos::catalogo;
use crate::hud;
use crate::negocio::{self, Negocio};
use crate::util;

thread_local! {
    static ABIERTA: Cell<bool> = const { Cell::new(false) };
}

/// El jugador no captura el mouse mientras el panel está abierto.
pub fn abierta() -> bool {
    ABIERTA.with(|a| a.get())
}

#[derive(GodotClass)]
#[class(base=CanvasLayer, init)]
pub struct Tienda {
    base: Base<CanvasLayer>,
    panel: Option<Gd<PanelContainer>>,
    saldo: Option<Gd<Label>>,
    pendientes: Option<Gd<Label>>,
}

impl Tienda {
    /// REQ-PRO-02
    fn comprar(&mut self, bloque: &str) {
        let yo = self.to_gd();
        let Some(mut n) = util::unico::<Negocio>(&yo, negocio::GRUPO) else { return };
        let resultado = n.bind_mut().comprar(bloque);
        match resultado {
            Ok(t) | Err(t) => hud::avisar(&yo, &t),
        }
    }

    pub fn alternar(&mut self) {
        let abrir = !abierta();
        ABIERTA.with(|a| a.set(abrir));
        if let Some(p) = &mut self.panel {
            p.set_visible(abrir);
        }
        // REQ-PRO-01: con el panel abierto el mouse queda libre.
        Input::singleton().set_mouse_mode(if abrir { MouseMode::VISIBLE } else { MouseMode::CAPTURED });
    }
}

#[godot_api]
impl ICanvasLayer for Tienda {
    fn ready(&mut self) {
        ABIERTA.with(|a| a.set(false));
        self.base_mut().set_layer(5);
        let mut panel = PanelContainer::new_alloc();
        panel.set_anchors_preset(LayoutPreset::CENTER);
        panel.set_offset(Side::LEFT, -330.0);
        panel.set_offset(Side::RIGHT, 330.0);
        panel.set_offset(Side::TOP, -260.0);
        panel.set_offset(Side::BOTTOM, 260.0);
        let mut v = VBoxContainer::new_alloc();
        v.add_theme_constant_override("separation", 8);
        panel.add_child(&v);

        let mut titulo = Label::new_alloc();
        titulo.set_text("Proveedor — entrega en 1 hora (de 8:00 a 20:00)");
        titulo.add_theme_font_size_override("font_size", 22);
        v.add_child(&titulo);
        let saldo = Label::new_alloc();
        v.add_child(&saldo);
        v.add_child(&HSeparator::new_alloc());

        // REQ-PRO-01: un renglón por bloque, con su botón.
        let yo = self.to_gd();
        for b in &catalogo().bloques {
            let mut fila = HBoxContainer::new_alloc();
            let mut l = Label::new_alloc();
            l.set_text(&format!("{} — {} u.", carrito_core::aderezos::capitalizar(&b.nombre), b.capacidad()));
            l.set_h_size_flags(SizeFlags::EXPAND_FILL);
            fila.add_child(&l);
            let mut boton = Button::new_alloc();
            boton.set_text(&format!("Comprar {}", plata(b.precio)));
            let id = b.id.clone();
            let tienda = yo.clone();
            boton.signals().pressed().connect(move || {
                let mut t = tienda.clone();
                t.bind_mut().comprar(&id);
            });
            fila.add_child(&boton);
            v.add_child(&fila);
        }
        v.add_child(&HSeparator::new_alloc());
        let pendientes = Label::new_alloc();
        v.add_child(&pendientes);
        let mut ayuda = Label::new_alloc();
        ayuda.set_text("Los paquetes llegan al pallet al lado del carrito. Llevalos a un lugar libre del estante.\nTab para cerrar.");
        ayuda.set_modulate(Color::from_rgba(1.0, 1.0, 1.0, 0.7));
        v.add_child(&ayuda);

        panel.set_visible(false);
        self.base_mut().add_child(&panel);
        self.panel = Some(panel);
        self.saldo = Some(saldo);
        self.pendientes = Some(pendientes);
    }

    fn process(&mut self, _delta: f64) {
        if Input::singleton().is_action_just_pressed("tienda") {
            self.alternar();
        }
        if !abierta() {
            return;
        }
        let yo = self.to_gd();
        let Some(n) = util::unico::<Negocio>(&yo, negocio::GRUPO) else { return };
        let (saldo, pend) = {
            let b = n.bind();
            (b.saldo(), b.pendientes_texto())
        };
        if let Some(l) = &mut self.saldo {
            l.set_text(&format!("En la caja: {}", plata(saldo)));
        }
        if let Some(l) = &mut self.pendientes {
            let texto = if pend.is_empty() { "Nada en camino.".to_string() } else { format!("En camino:\n{}", pend.join("\n")) };
            l.set_text(&texto);
        }
    }
}
