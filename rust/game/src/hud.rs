//! Pantalla: mira, cartel de acción, hora, caja, reputación, avisos y resumen del día.

use godot::builtin::Side;
use godot::classes::control::{LayoutPreset, MouseFilter};
use godot::classes::text_server::AutowrapMode;
use godot::classes::{CanvasLayer, Control, ICanvasLayer, Label, VBoxContainer};
use godot::global::HorizontalAlignment;
use godot::prelude::*;

use crate::dia_noche::{self, DiaNoche};
use crate::negocio::{self, Negocio};
use crate::util;

pub const GRUPO: &str = "hud";
const SEGUNDOS_AVISO: f32 = 5.0;
const SEGUNDOS_RESUMEN: f32 = 14.0;

#[derive(GodotClass)]
#[class(base=CanvasLayer, init)]
pub struct Hud {
    base: Base<CanvasLayer>,
    cartel: Option<Gd<Label>>,
    reloj: Option<Gd<Label>>,
    caja: Option<Gd<Label>>,
    avisos: Option<Gd<VBoxContainer>>,
    vivos: Vec<(Gd<Label>, f32)>,
    resumen: Option<Gd<Label>>,
    resumen_t: f32,
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

fn ubicar(c: &mut Gd<impl Inherits<Control>>, preset: LayoutPreset, izq: f32, arr: f32, der: f32, aba: f32) {
    let mut c = c.clone().upcast::<Control>();
    c.set_anchors_preset(preset);
    c.set_offset(Side::LEFT, izq);
    c.set_offset(Side::TOP, arr);
    c.set_offset(Side::RIGHT, der);
    c.set_offset(Side::BOTTOM, aba);
}

/// Muestra un aviso abajo a la izquierda, desde cualquier nodo.
pub fn avisar(desde: &Gd<impl Inherits<Node>>, texto: &str) {
    if let Some(mut h) = util::unico::<Hud>(desde, GRUPO) {
        h.bind_mut().aviso(texto);
    }
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

    pub fn aviso(&mut self, texto: &str) {
        godot_print!("[aviso] {texto}");
        let Some(cont) = &mut self.avisos else { return };
        let l = etiqueta(texto, 19);
        cont.add_child(&l);
        self.vivos.push((l, SEGUNDOS_AVISO));
        // No más de 5 a la vez.
        while self.vivos.len() > 5 {
            let (mut viejo, _) = self.vivos.remove(0);
            viejo.queue_free();
        }
    }

    /// REQ-ECO-05
    pub fn mostrar_resumen(&mut self, texto: &str) {
        godot_print!("[resumen] {texto}");
        if let Some(r) = &mut self.resumen {
            r.set_text(texto);
            r.set_visible(true);
        }
        self.resumen_t = SEGUNDOS_RESUMEN;
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
        mira.set_horizontal_alignment(HorizontalAlignment::CENTER);
        ubicar(&mut mira, LayoutPreset::CENTER, -20.0, -16.0, 20.0, 16.0);
        raiz.add_child(&mira);

        let mut cartel = etiqueta("", 22);
        cartel.set_horizontal_alignment(HorizontalAlignment::CENTER);
        cartel.set_autowrap_mode(AutowrapMode::WORD_SMART);
        ubicar(&mut cartel, LayoutPreset::CENTER_BOTTOM, -420.0, -130.0, 420.0, -60.0);
        raiz.add_child(&cartel);

        let mut reloj = etiqueta("", 24);
        reloj.set_horizontal_alignment(HorizontalAlignment::RIGHT);
        ubicar(&mut reloj, LayoutPreset::TOP_RIGHT, -360.0, 14.0, -20.0, 44.0);
        raiz.add_child(&reloj);

        // REQ-ECO-06: caja y reputación siempre visibles.
        let mut caja = etiqueta("", 22);
        caja.set_horizontal_alignment(HorizontalAlignment::RIGHT);
        ubicar(&mut caja, LayoutPreset::TOP_RIGHT, -360.0, 46.0, -20.0, 76.0);
        raiz.add_child(&caja);

        let mut ayuda = etiqueta(
            "WASD moverse · Shift correr · Espacio saltar\n\
             Clic agarrar/soltar · Clic derecho tirar · E usar\n\
             Tab proveedor · T tiempo ×30 · C traer cliente (prueba) · Esc soltar el mouse",
            15,
        );
        ayuda.set_position(Vector2::new(16.0, 12.0));
        ayuda.set_modulate(Color::from_rgba(1.0, 1.0, 1.0, 0.8));
        raiz.add_child(&ayuda);

        let mut avisos = VBoxContainer::new_alloc();
        avisos.set_mouse_filter(MouseFilter::IGNORE);
        ubicar(&mut avisos, LayoutPreset::BOTTOM_LEFT, 16.0, -260.0, 700.0, -16.0);
        avisos.set_alignment(godot::classes::box_container::AlignmentMode::END);
        raiz.add_child(&avisos);

        let mut resumen = etiqueta("", 24);
        resumen.set_horizontal_alignment(HorizontalAlignment::CENTER);
        resumen.set_autowrap_mode(AutowrapMode::WORD_SMART);
        resumen.add_theme_color_override("font_color", Color::from_rgb(1.0, 0.9, 0.5));
        ubicar(&mut resumen, LayoutPreset::CENTER_TOP, -450.0, 80.0, 450.0, 180.0);
        resumen.set_visible(false);
        raiz.add_child(&resumen);

        self.cartel = Some(cartel);
        self.reloj = Some(reloj);
        self.caja = Some(caja);
        self.avisos = Some(avisos);
        self.resumen = Some(resumen);
    }

    fn process(&mut self, delta: f64) {
        let dt = delta as f32;
        let yo = self.to_gd();
        // REQ-DIA-07: la hora en pantalla.
        if let Some(dn) = util::unico::<DiaNoche>(&yo, dia_noche::GRUPO) {
            let texto = dn.bind().hora_texto();
            if let Some(r) = &mut self.reloj {
                r.set_text(&texto);
            }
        }
        if let Some(n) = util::unico::<Negocio>(&yo, negocio::GRUPO) {
            let texto = n.bind().texto_hud();
            if let Some(c) = &mut self.caja {
                c.set_text(&texto);
            }
        }
        // Avisos que se apagan solos.
        for (l, t) in &mut self.vivos {
            *t -= dt;
            l.set_modulate(Color::from_rgba(1.0, 1.0, 1.0, (*t / 1.0).clamp(0.0, 1.0)));
        }
        self.vivos.retain_mut(|(l, t)| {
            if *t <= 0.0 {
                l.queue_free();
                false
            } else {
                true
            }
        });
        if self.resumen_t > 0.0 {
            self.resumen_t -= dt;
            if self.resumen_t <= 0.0 {
                if let Some(r) = &mut self.resumen {
                    r.set_visible(false);
                }
            }
        }
    }
}
