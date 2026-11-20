//! SPEC-031 · Panel "¿Con qué arrancás?" y carrito según el producto (TASK-0267, TASK-0261).
//!
//! Las reglas (qué trae cada producto, la base común, el carrito de la prueba) son de
//! `carrito_core::arranque`; acá se lee `arranque.ron`, se muestra el panel con el mundo en
//! pausa y se rearma el carrito con lo elegido.

use std::sync::OnceLock;

use carrito_core::arranque::{self as regla, Arranque as DatosArranque};
use carrito_core::carrito::ConfigCarrito;
use godot::builtin::Side;
use godot::classes::control::LayoutPreset;
use godot::classes::input::MouseMode;
use godot::classes::node::ProcessMode;
use godot::classes::{Button, CanvasLayer, FileAccess, ICanvasLayer, Input, Label, PanelContainer, VBoxContainer};
use godot::global::HorizontalAlignment;
use godot::prelude::*;

use crate::carrito::{self, Carrito};
use crate::datos::catalogo;
use crate::util;

pub const GRUPO: &str = "arranque";
/// La escena de la partida: el panel solo sale cuando es la escena que se juega (no dentro de
/// la prueba de humo ni de otra escena que la use). REQ-ARR-04
const ESCENA_PARTIDA: &str = "res://scenes/main.tscn";

static DATOS: OnceLock<DatosArranque> = OnceLock::new();

/// `res://data/arranque.ron`, revisado contra el catálogo (REQ-ARR-02).
pub fn datos() -> &'static DatosArranque {
    DATOS.get_or_init(|| {
        let texto = FileAccess::get_file_as_string("res://data/arranque.ron").to_string();
        match regla::parsear(&texto).and_then(|a| regla::validar(&a, catalogo()).map(|_| a)) {
            Ok(a) => a,
            Err(e) => {
                godot_error!("Error en los datos del arranque: {e}");
                panic!("Error en los datos del arranque: {e}");
            }
        }
    })
}

/// REQ-ARR-01 / REQ-ARR-04: se está jugando la partida (main.tscn es la escena actual), no la
/// prueba de humo.
pub fn es_partida(desde: &Gd<impl Inherits<Node>>) -> bool {
    let nodo: Gd<Node> = desde.clone().upcast();
    let Some(arbol) = nodo.get_tree_or_null() else { return false };
    arbol.get_current_scene().is_some_and(|s| s.get_scene_file_path() == ESCENA_PARTIDA)
}

/// Con qué se arma el carrito del jugador al cargar: en la partida, la base común (el panel
/// le suma el producto, REQ-ARR-02); en la prueba de humo, los cuatro equipos sin el cartel
/// (REQ-ARR-04).
pub fn config_inicial(desde: &Gd<impl Inherits<Node>>) -> ConfigCarrito {
    let base = &catalogo().carrito_jugador;
    if es_partida(desde) { base.clone() } else { regla::config_prueba(base, datos()) }
}

/// REQ-ARR-02: el carrito para un producto de `arranque.ron`.
pub fn config_para(producto: &str) -> Option<ConfigCarrito> {
    datos().opcion(producto).map(|o| regla::config_para(&catalogo().carrito_jugador, o))
}

#[derive(GodotClass)]
#[class(base=CanvasLayer, init)]
pub struct Arranque {
    base: Base<CanvasLayer>,
    panel: Option<Gd<PanelContainer>>,
    /// (producto, botón), en el orden de `arranque.ron`.
    botones: Vec<(String, Gd<Button>)>,
    /// Carrito que se rearma al elegir (si falta, el del jugador). La prueba de humo usa otro.
    destino: Option<Gd<Carrito>>,
    abierto: bool,
}

impl Arranque {
    /// REQ-ARR-01: muestra el panel, suelta el mouse y deja el mundo quieto (árbol en pausa;
    /// el panel sigue andando con `ProcessMode::ALWAYS`).
    pub fn abrir(&mut self) {
        self.abierto = true;
        if let Some(p) = &mut self.panel {
            p.set_visible(true);
        }
        self.base().get_tree().set_pause(true);
        Input::singleton().set_mouse_mode(MouseMode::VISIBLE);
    }

    /// Cierra el panel y el mundo sigue.
    pub fn cerrar(&mut self) {
        self.abierto = false;
        if let Some(p) = &mut self.panel {
            p.set_visible(false);
        }
        self.base().get_tree().set_pause(false);
        Input::singleton().set_mouse_mode(MouseMode::CAPTURED);
    }

    /// REQ-ARR-02: rearma el carrito con la base común y lo del producto, y cierra el panel.
    pub fn elegir(&mut self, producto: &str) {
        let Some(config) = config_para(producto) else {
            godot_error!("Arranque: no existe el producto \"{producto}\" en arranque.ron");
            return;
        };
        let destino = self.destino.clone().or_else(|| util::unico::<Carrito>(&self.to_gd(), carrito::GRUPO));
        if let Some(mut c) = destino {
            c.bind_mut().rearmar(config);
        }
        self.cerrar();
    }

    pub fn abierto(&self) -> bool {
        self.abierto
    }

    pub fn panel_visible(&self) -> bool {
        self.panel.as_ref().is_some_and(|p| p.is_visible())
    }

    /// (producto, botón) del panel (para la prueba de humo).
    pub fn botones(&self) -> Vec<(String, Gd<Button>)> {
        self.botones.clone()
    }

    /// Para la prueba de humo: elegir rearma este carrito en lugar del del jugador.
    pub fn set_destino(&mut self, carrito: Option<Gd<Carrito>>) {
        self.destino = carrito;
    }
}

#[godot_api]
impl ICanvasLayer for Arranque {
    fn ready(&mut self) {
        self.base_mut().add_to_group(GRUPO);
        // Por encima del HUD y de los otros paneles.
        self.base_mut().set_layer(8);
        // REQ-ARR-01: el panel anda con el árbol en pausa.
        self.base_mut().set_process_mode(ProcessMode::ALWAYS);

        let mut panel = PanelContainer::new_alloc();
        panel.set_anchors_preset(LayoutPreset::CENTER);
        panel.set_offset(Side::LEFT, -200.0);
        panel.set_offset(Side::RIGHT, 200.0);
        panel.set_offset(Side::TOP, -170.0);
        panel.set_offset(Side::BOTTOM, 170.0);
        let mut v = VBoxContainer::new_alloc();
        v.add_theme_constant_override("separation", 10);
        panel.add_child(&v);

        let mut titulo = Label::new_alloc();
        titulo.set_text(regla::TITULO);
        titulo.add_theme_font_size_override("font_size", 26);
        titulo.set_horizontal_alignment(HorizontalAlignment::CENTER);
        v.add_child(&titulo);
        let mut ayuda = Label::new_alloc();
        ayuda.set_text("Un producto para empezar; los demás equipos se compran en la tienda.");
        ayuda.set_modulate(Color::from_rgba(1.0, 1.0, 1.0, 0.7));
        ayuda.set_horizontal_alignment(HorizontalAlignment::CENTER);
        v.add_child(&ayuda);

        // REQ-ARR-01: un botón por producto (Pancho, Hamburguesa, Choripán, Papas fritas).
        let yo = self.to_gd();
        for o in &datos().productos {
            let mut b = Button::new_alloc();
            b.set_text(&o.nombre);
            b.add_theme_font_size_override("font_size", 22);
            b.set_custom_minimum_size(Vector2::new(0.0, 48.0));
            let producto = o.producto.clone();
            let panel_yo = yo.clone();
            b.signals().pressed().connect(move || {
                let mut a = panel_yo.clone();
                a.bind_mut().elegir(&producto);
            });
            v.add_child(&b);
            self.botones.push((o.producto.clone(), b));
        }

        panel.set_visible(false);
        self.base_mut().add_child(&panel);
        self.panel = Some(panel);

        // REQ-ARR-04: en la prueba de humo (u otra escena que use el mundo) no sale.
        if es_partida(&self.to_gd()) {
            self.abrir();
        }
    }
}
