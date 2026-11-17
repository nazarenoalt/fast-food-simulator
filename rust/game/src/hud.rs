//! Pantalla: mira, cartel de acción, hora y ayuda de controles.

use godot::classes::control::{LayoutPreset, MouseFilter};
use godot::classes::text_server::AutowrapMode;
use godot::classes::{CanvasLayer, Control, ICanvasLayer, Label};
use godot::global::HorizontalAlignment;
use godot::prelude::*;

use crate::dia_noche::{self, DiaNoche};

pub const GRUPO: &str = "hud";

#[derive(GodotClass)]
#[class(base=CanvasLayer, init)]
pub struct Hud {
    base: Base<CanvasLayer>,
    cartel: Option<Gd<Label>>,
    reloj: Option<Gd<Label>>,
}

fn etiqueta(texto: &str, tamano: i32) -> Gd<Label> {
    let mut l = Label::new_alloc();
    l.set_text(texto);
    l.add_theme_font_size_override("font_size", tamano);
    l.add_theme_color_override("font_shadow_color", Color::from_rgba(0.0, 0.0, 0.0, 0.85));
    l.add_theme_constant_override("shadow_offset_x", 2);
    l.add_theme_constant_override("shadow_offset_y", 2);
    l.set_mouse_filter(MouseFilter::IGNORE);
    l
}

impl Hud {
    /// REQ-INT-02, REQ-INT-08
    pub fn set_cartel(&mut self, texto: &str) {
        if let Some(c) = &mut self.cartel {
            if c.get_text().to_string() != texto {
                c.set_text(texto);
            }
        }
    }
}

#[godot_api]
impl ICanvasLayer for Hud {
    fn ready(&mut self) {
        self.base_mut().add_to_group(GRUPO);
        let mut raiz = Control::new_alloc();
        raiz.set_anchors_preset(LayoutPreset::FULL_RECT);
        raiz.set_mouse_filter(MouseFilter::IGNORE);
        self.base_mut().add_child(&raiz);

        // REQ-INT-01: mira en el centro.
        let mut mira = etiqueta("•", 22);
        mira.set_anchors_preset(LayoutPreset::CENTER);
        mira.set_horizontal_alignment(HorizontalAlignment::CENTER);
        mira.set_offset(godot::builtin::Side::LEFT, -20.0);
        mira.set_offset(godot::builtin::Side::RIGHT, 20.0);
        mira.set_offset(godot::builtin::Side::TOP, -16.0);
        mira.set_offset(godot::builtin::Side::BOTTOM, 16.0);
        raiz.add_child(&mira);

        let mut cartel = etiqueta("", 22);
        cartel.set_anchors_preset(LayoutPreset::CENTER_BOTTOM);
        cartel.set_horizontal_alignment(HorizontalAlignment::CENTER);
        cartel.set_autowrap_mode(AutowrapMode::WORD_SMART);
        cartel.set_offset(godot::builtin::Side::LEFT, -400.0);
        cartel.set_offset(godot::builtin::Side::RIGHT, 400.0);
        cartel.set_offset(godot::builtin::Side::TOP, -120.0);
        cartel.set_offset(godot::builtin::Side::BOTTOM, -60.0);
        raiz.add_child(&cartel);

        let mut reloj = etiqueta("", 24);
        reloj.set_anchors_preset(LayoutPreset::TOP_RIGHT);
        reloj.set_horizontal_alignment(HorizontalAlignment::RIGHT);
        reloj.set_offset(godot::builtin::Side::LEFT, -320.0);
        reloj.set_offset(godot::builtin::Side::RIGHT, -20.0);
        reloj.set_offset(godot::builtin::Side::TOP, 16.0);
        raiz.add_child(&reloj);

        let mut ayuda = etiqueta(
            "WASD moverse · Shift correr · Espacio saltar\n\
             Clic agarrar/soltar · Clic derecho tirar · E usar\n\
             T tiempo ×30 · Esc soltar el mouse",
            15,
        );
        ayuda.set_position(Vector2::new(16.0, 12.0));
        ayuda.set_modulate(Color::from_rgba(1.0, 1.0, 1.0, 0.8));
        raiz.add_child(&ayuda);

        self.cartel = Some(cartel);
        self.reloj = Some(reloj);
    }

    fn process(&mut self, _delta: f64) {
        // REQ-DIA-07: la hora en pantalla.
        let arbol = self.base().get_tree();
        let Some(n) = arbol.get_first_node_in_group(dia_noche::GRUPO) else { return };
        let Ok(dn) = n.try_cast::<DiaNoche>() else { return };
        let texto = dn.bind().hora_texto();
        if let Some(r) = &mut self.reloj {
            r.set_text(&texto);
        }
    }
}
