//! SPEC-017 · Modo armado (B): poner, cambiar, mover y guardar accesorios mirando los anclajes
//! del carrito, y el panel del carrito (Tab) con color, bases e inventario. Las reglas viven
//! en `carrito_core::tienda`; acá solo se conectan con el carrito, la caja y la pantalla.

use std::cell::Cell;

use carrito_core::carrito::armar;
use carrito_core::economia::plata;
use carrito_core::tienda::{Armado, Origen, PALETA};
use godot::builtin::Side;
use godot::classes::base_material_3d::{Flags, ShadingMode, Transparency};
use godot::classes::control::{LayoutPreset, SizeFlags};
use godot::classes::input::MouseMode;
use godot::classes::{
    Button, CanvasLayer, GridContainer, HSeparator, ICanvasLayer, Input, InputEvent, InputEventMouseButton, Label,
    MeshInstance3D, Node3D, PanelContainer, ScrollContainer, SphereMesh, StandardMaterial3D, VBoxContainer,
};
use godot::global::MouseButton;
use godot::prelude::*;

use crate::carrito::{self, Carrito};
use crate::datos::catalogo;
use crate::hud::{self, Hud};
use crate::negocio::{self, Negocio};
use crate::util;

thread_local! {
    static ACTIVO: Cell<bool> = const { Cell::new(false) };
    static MENU: Cell<bool> = const { Cell::new(false) };
}

/// REQ-TIE-01: en el modo armado el jugador no agarra ni usa nada.
pub fn activo() -> bool {
    ACTIVO.with(|a| a.get())
}

/// Hay un menú del modo armado abierto (el mouse queda libre).
pub fn menu_abierto() -> bool {
    MENU.with(|m| m.get())
}

/// Ángulo máximo (grados) entre la mirada y una marca para elegirla, y distancia máxima.
const ANGULO_MIRA: f32 = 9.0;
const ALCANCE: f32 = 8.0;
const RADIO_MARCA: f32 = 0.05;
const LIBRE: Color = Color::from_rgba(0.3, 0.95, 0.4, 0.75);
const OCUPADO: Color = Color::from_rgba(0.35, 0.75, 1.0, 0.75);
const MIRADO: Color = Color::from_rgba(1.0, 0.9, 0.2, 0.95);
const ORIGEN: Color = Color::from_rgba(1.0, 0.5, 0.1, 0.95);

struct Marca {
    anclaje: String,
    nodo: Gd<MeshInstance3D>,
    material: Gd<StandardMaterial3D>,
    pos: Vector3,
}

#[derive(GodotClass)]
#[class(base=CanvasLayer, init)]
pub struct ModoArmado {
    base: Base<CanvasLayer>,
    estado: Option<Armado>,
    marcas: Vec<Marca>,
    mirado: Option<String>,
    /// REQ-TIE-04: anclaje de origen mientras se elige el destino.
    moviendo: Option<String>,
    panel: Option<Gd<PanelContainer>>,
    lista: Option<Gd<VBoxContainer>>,
}

fn nombre_acc(id: &str) -> String {
    catalogo().accesorios.iter().find(|a| a.id == id).map(|a| a.nombre.clone()).unwrap_or_else(|| id.to_string())
}

fn nombre_base(id: &str) -> String {
    catalogo().bases.iter().find(|b| b.id == id).map(|b| b.nombre.clone()).unwrap_or_else(|| id.to_string())
}

fn etiqueta(texto: &str, tam: i32) -> Gd<Label> {
    let mut l = Label::new_alloc();
    l.set_text(texto);
    l.add_theme_font_size_override("font_size", tam);
    l
}

impl ModoArmado {
    fn carrito(&self) -> Option<Gd<Carrito>> {
        util::unico::<Carrito>(&self.to_gd(), carrito::GRUPO)
    }

    fn negocio(&self) -> Option<Gd<Negocio>> {
        util::unico::<Negocio>(&self.to_gd(), negocio::GRUPO)
    }

    fn avisar(&self, texto: &str) {
        hud::avisar(&self.to_gd(), texto);
    }

    /// El estado arranca de lo que el carrito tiene puesto la primera vez que se entra.
    fn estado(&mut self) -> Option<&mut Armado> {
        if self.estado.is_none() {
            let c = self.carrito()?;
            let c = c.bind();
            let base = c.base_actual()?.id.clone();
            self.estado = Some(Armado {
                base,
                color: c.color(),
                accesorios: c.accesorios_puestos(),
                inventario: Default::default(),
            });
        }
        self.estado.as_mut()
    }

    // ── Entrar y salir ────────────────────────────────────────────

    /// REQ-TIE-01
    fn alternar(&mut self) {
        let activar = !activo();
        ACTIVO.with(|a| a.set(activar));
        self.moviendo = None;
        self.cerrar_panel();
        self.borrar_marcas();
        if activar {
            self.estado();
            self.crear_marcas();
            self.avisar(
                "Modo armado: mirá un lugar del carrito y hacé clic. Tab: color, bases e inventario. B: salir.",
            );
        } else {
            self.poner_cartel("");
        }
    }

    fn borrar_marcas(&mut self) {
        for mut m in self.marcas.drain(..) {
            m.nodo.queue_free();
        }
        self.mirado = None;
    }

    /// REQ-TIE-01: una marca por anclaje (las del piso, un poco más arriba para verlas).
    fn crear_marcas(&mut self) {
        self.borrar_marcas();
        let Some(mut c) = self.carrito() else { return };
        let anclajes = c.bind().anclajes_globales();
        for (anclaje, pos) in anclajes {
            let pos = if pos.y < c.get_global_position().y + 0.3 { pos + Vector3::UP * 0.4 } else { pos };
            let mut malla = SphereMesh::new_gd();
            malla.set_radius(RADIO_MARCA);
            malla.set_height(RADIO_MARCA * 2.0);
            let mut mat = StandardMaterial3D::new_gd();
            mat.set_shading_mode(ShadingMode::UNSHADED);
            mat.set_transparency(Transparency::ALPHA);
            mat.set_flag(Flags::DISABLE_DEPTH_TEST, true);
            mat.set_albedo(LIBRE);
            let mut nodo = MeshInstance3D::new_alloc();
            nodo.set_mesh(&malla);
            nodo.set_material_override(&mat);
            nodo.set_name(&format!("Marca_{anclaje}"));
            c.add_child(&nodo);
            nodo.set_global_position(pos);
            self.marcas.push(Marca { anclaje, nodo, material: mat, pos });
        }
    }

    fn poner_cartel(&self, texto: &str) {
        if let Some(n) = self.base().get_tree().get_first_node_in_group(hud::GRUPO)
            && let Ok(mut h) = n.try_cast::<Hud>()
        {
            h.bind_mut().set_cartel(texto);
        }
    }

    /// La marca más cerca del centro de la mira, dentro del ángulo y el alcance.
    fn elegir_mirado(&mut self) {
        let Some(cam) = self.base().get_viewport().and_then(|v| v.get_camera_3d()) else { return };
        let t = cam.get_global_transform();
        let adelante = -t.basis.col_c();
        let mut mejor: Option<(f32, String)> = None;
        for m in &self.marcas {
            let d = m.pos - t.origin;
            let dist = d.length();
            if !(0.05..=ALCANCE).contains(&dist) {
                continue;
            }
            let ang = adelante.angle_to(d / dist).to_degrees();
            if ang < ANGULO_MIRA && mejor.as_ref().is_none_or(|(a, _)| ang < *a) {
                mejor = Some((ang, m.anclaje.clone()));
            }
        }
        self.mirado = mejor.map(|(_, a)| a);
    }

    fn pintar_marcas(&mut self) {
        let puestos = self.estado.as_ref().map(|e| e.accesorios.clone()).unwrap_or_default();
        for m in &mut self.marcas {
            let (color, escala) = if self.moviendo.as_deref() == Some(m.anclaje.as_str()) {
                (ORIGEN, 1.4)
            } else if self.mirado.as_deref() == Some(m.anclaje.as_str()) {
                (MIRADO, 1.6)
            } else if puestos.contains_key(&m.anclaje) {
                (OCUPADO, 1.0)
            } else {
                (LIBRE, 1.0)
            };
            m.material.set_albedo(color);
            m.nodo.set_scale(Vector3::ONE * escala);
        }
    }

    /// REQ-TIE-01: nombre del lugar, qué tiene y qué acepta.
    fn texto_cartel(&self) -> String {
        if let Some(desde) = &self.moviendo {
            let que =
                self.estado.as_ref().and_then(|e| e.accesorios.get(desde)).map(|a| nombre_acc(a)).unwrap_or_default();
            return format!("Moviendo {que}: hacé clic en el lugar de destino (clic en otro lado o B cancela)");
        }
        let Some(anc) = &self.mirado else {
            return "Modo armado — mirá un lugar del carrito · Tab: panel · B: salir".into();
        };
        let cats = self
            .carrito()
            .and_then(|c| c.bind().base_actual().and_then(|b| b.anclaje(anc)).map(|a| a.categorias.clone()))
            .map(|v| v.iter().map(|c| format!("{c:?}")).collect::<Vec<_>>().join(", "))
            .unwrap_or_default();
        let tiene = self.estado.as_ref().and_then(|e| e.accesorios.get(anc)).map(|a| nombre_acc(a));
        match tiene {
            Some(t) => format!("[Clic] {anc}: {t} · acepta {cats}"),
            None => format!("[Clic] {anc}: libre · acepta {cats}"),
        }
    }

    // ── Panel (menú de un anclaje o panel del carrito) ────────────

    fn abrir_panel(&mut self, titulo: &str) -> Option<Gd<VBoxContainer>> {
        let mut lista = self.lista.clone()?;
        for mut hijo in lista.get_children().iter_shared() {
            hijo.queue_free();
        }
        lista.add_child(&etiqueta(titulo, 22));
        if let Some(n) = self.negocio() {
            lista.add_child(&etiqueta(&format!("En la caja: {}", plata(n.bind().saldo())), 16));
        }
        lista.add_child(&HSeparator::new_alloc());
        if let Some(p) = &mut self.panel {
            p.set_visible(true);
        }
        MENU.with(|m| m.set(true));
        Input::singleton().set_mouse_mode(MouseMode::VISIBLE);
        Some(lista)
    }

    pub(crate) fn cerrar_panel(&mut self) {
        if let Some(p) = &mut self.panel {
            p.set_visible(false);
        }
        if menu_abierto() {
            MENU.with(|m| m.set(false));
            Input::singleton().set_mouse_mode(MouseMode::CAPTURED);
        }
    }

    fn boton(&self, lista: &mut Gd<VBoxContainer>, texto: &str, accion: impl Fn(&mut ModoArmado) + 'static) {
        let mut b = Button::new_alloc();
        b.set_text(texto);
        b.set_text_alignment(godot::global::HorizontalAlignment::LEFT);
        let yo = self.to_gd();
        b.signals().pressed().connect(move || {
            let mut m = yo.clone();
            accion(&mut m.bind_mut());
        });
        lista.add_child(&b);
    }

    /// REQ-TIE-02, REQ-TIE-03
    fn abrir_menu_anclaje(&mut self, anclaje: String) {
        let Some(estado) = self.estado().cloned() else { return };
        let cat = catalogo();
        let tiene = estado.accesorios.get(&anclaje).cloned();
        let titulo = match &tiene {
            Some(a) => format!("{anclaje}: {}", nombre_acc(a)),
            None => format!("{anclaje}: libre"),
        };
        let Some(mut lista) = self.abrir_panel(&titulo) else { return };
        if tiene.is_some() {
            let a = anclaje.clone();
            self.boton(&mut lista, "Mover a otro lugar", move |m| {
                m.moviendo = Some(a.clone());
                m.cerrar_panel();
            });
            let a = anclaje.clone();
            self.boton(&mut lista, "Guardar en el inventario", move |m| m.guardar(&a));
            lista.add_child(&etiqueta("Cambiar por:", 16));
        } else {
            lista.add_child(&etiqueta("Poner:", 16));
        }
        let mut scroll = ScrollContainer::new_alloc();
        scroll.set_custom_minimum_size(Vector2::new(0.0, 300.0));
        scroll.set_v_size_flags(SizeFlags::EXPAND_FILL);
        let mut opciones = VBoxContainer::new_alloc();
        opciones.set_h_size_flags(SizeFlags::EXPAND_FILL);
        let lista_opciones = estado.opciones(&anclaje, cat);
        if lista_opciones.is_empty() {
            opciones.add_child(&etiqueta("No hay nada que entre acá.", 16));
        }
        for o in lista_opciones {
            if tiene.as_deref() == Some(o.accesorio.as_str()) && o.origen == Origen::Tienda {
                continue;
            }
            let texto = match o.origen {
                Origen::Guardado => format!("{} — guardado", nombre_acc(&o.accesorio)),
                Origen::Tienda => format!("{} — {}", nombre_acc(&o.accesorio), plata(o.precio)),
            };
            let (a, acc, origen) = (anclaje.clone(), o.accesorio.clone(), o.origen);
            self.boton(&mut opciones, &texto, move |m| m.elegir(&a, &acc, origen));
        }
        scroll.add_child(&opciones);
        lista.add_child(&scroll);
        lista.add_child(&HSeparator::new_alloc());
        self.boton(&mut lista, "Cerrar", |m| m.cerrar_panel());
    }

    /// REQ-TIE-07..10: panel del carrito.
    fn abrir_panel_carrito(&mut self) {
        let Some(estado) = self.estado().cloned() else { return };
        let cat = catalogo();
        let Some(mut lista) = self.abrir_panel(&format!("Tu carrito: {}", nombre_base(&estado.base))) else {
            return;
        };
        // REQ-TIE-08
        lista.add_child(&etiqueta("Color (gratis):", 16));
        let mut colores = GridContainer::new_alloc();
        colores.set_columns(5);
        for (nombre, c) in PALETA {
            let mut b = Button::new_alloc();
            b.set_text(nombre);
            b.set_self_modulate(Color::from_rgb(c[0] * 1.3 + 0.2, c[1] * 1.3 + 0.2, c[2] * 1.3 + 0.2));
            let yo = self.to_gd();
            b.signals().pressed().connect(move || {
                let mut m = yo.clone();
                m.bind_mut().pintar(c);
            });
            colores.add_child(&b);
        }
        lista.add_child(&colores);
        lista.add_child(&HSeparator::new_alloc());

        // REQ-TIE-10
        lista.add_child(&etiqueta("Bases:", 16));
        for b in &cat.bases {
            let texto = if b.id == estado.base {
                format!("{} — la que usás", b.nombre)
            } else if estado.inventario.bases.contains(&b.id) {
                format!("{} — usar (guardada)", b.nombre)
            } else {
                format!("{} — comprar {}", b.nombre, plata(b.precio))
            };
            let id = b.id.clone();
            self.boton(&mut lista, &texto, move |m| m.cambiar_base(&id));
        }
        lista.add_child(&HSeparator::new_alloc());

        // REQ-TIE-09
        lista.add_child(&etiqueta("Inventario (se vende a la mitad):", 16));
        let inv = &estado.inventario;
        if inv.accesorios.is_empty() && inv.bases.is_empty() {
            lista.add_child(&etiqueta("Vacío.", 16));
        }
        let mut vistos: Vec<&String> = Vec::new();
        for id in &inv.accesorios {
            if vistos.contains(&id) {
                continue;
            }
            vistos.push(id);
            let n = inv.accesorios.iter().filter(|x| *x == id).count();
            let precio = cat.accesorios.iter().find(|a| &a.id == id).map(|a| a.precio).unwrap_or(0.0);
            let texto = format!(
                "{}{} — vender por {}",
                nombre_acc(id),
                if n > 1 { format!(" ×{n}") } else { String::new() },
                plata(precio * carrito_core::tienda::FRACCION_VENTA)
            );
            let id = id.clone();
            self.boton(&mut lista, &texto, move |m| m.vender_accesorio(&id));
        }
        for id in &inv.bases {
            let precio = cat.bases.iter().find(|b| &b.id == id).map(|b| b.precio).unwrap_or(0.0);
            let texto = format!(
                "{} (base) — vender por {}",
                nombre_base(id),
                plata(precio * carrito_core::tienda::FRACCION_VENTA)
            );
            let id = id.clone();
            self.boton(&mut lista, &texto, move |m| m.vender_base(&id));
        }
        lista.add_child(&HSeparator::new_alloc());
        self.boton(&mut lista, "Cerrar (Tab)", |m| m.cerrar_panel());
    }

    // ── Acciones ──────────────────────────────────────────────────

    /// REQ-TIE-02, REQ-TIE-03
    pub(crate) fn elegir(&mut self, anclaje: &str, acc: &str, origen: Origen) {
        let (Some(mut c), Some(mut n)) = (self.carrito(), self.negocio()) else { return };
        let con_bloques = c.bind().deposito_con_bloques(anclaje);
        let cat = catalogo();
        let Some(estado) = self.estado() else { return };
        let r = estado.poner(anclaje, acc, origen, con_bloques, n.bind_mut().caja_mut(), cat);
        match r {
            Ok(gasto) => {
                n.bind_mut().registrar_gasto(gasto);
                if let Some(def) = cat.accesorios.iter().find(|a| a.id == acc) {
                    c.bind_mut().poner(anclaje, def);
                }
                let costo = if gasto > 0.0 { format!(" (−{})", plata(gasto)) } else { String::new() };
                self.avisar(&format!("Pusiste {}{costo}", nombre_acc(acc)));
                self.cerrar_panel();
                self.crear_marcas();
            }
            Err(e) => self.avisar(&e.to_string()),
        }
    }

    /// REQ-TIE-05
    pub(crate) fn guardar(&mut self, anclaje: &str) {
        let Some(mut c) = self.carrito() else { return };
        let con_bloques = c.bind().deposito_con_bloques(anclaje);
        let Some(estado) = self.estado() else { return };
        match estado.guardar(anclaje, con_bloques) {
            Ok(id) => {
                c.bind_mut().quitar(anclaje);
                self.avisar(&format!("Guardaste {}", nombre_acc(&id)));
                self.cerrar_panel();
            }
            Err(e) => self.avisar(&e.to_string()),
        }
    }

    /// REQ-TIE-04 (también para la prueba de humo).
    pub(crate) fn mover(&mut self, desde: &str, hasta: &str) {
        self.moviendo = Some(desde.to_string());
        self.mover_a(hasta);
    }

    /// REQ-TIE-04
    fn mover_a(&mut self, hasta: &str) {
        let Some(desde) = self.moviendo.take() else { return };
        if desde == hasta {
            return;
        }
        let Some(mut c) = self.carrito() else { return };
        let cat = catalogo();
        let Some(estado) = self.estado() else { return };
        match estado.mover(&desde, hasta, cat) {
            Ok(_) => {
                c.bind_mut().mover(&desde, hasta);
                self.avisar("Listo, movido");
            }
            Err(e) => self.avisar(&e.to_string()),
        }
    }

    /// REQ-TIE-08
    pub(crate) fn pintar(&mut self, color: [f32; 3]) {
        if let Some(e) = self.estado() {
            e.pintar(color);
        }
        if let Some(mut c) = self.carrito() {
            c.bind_mut().pintar(color);
        }
    }

    /// REQ-TIE-09
    pub(crate) fn vender_accesorio(&mut self, id: &str) {
        let Some(mut n) = self.negocio() else { return };
        let cat = catalogo();
        let Some(estado) = self.estado() else { return };
        let r = estado.vender_accesorio(id, n.bind_mut().caja_mut(), cat);
        self.cobrado(&mut n, r, &nombre_acc(id));
    }

    /// REQ-TIE-09
    fn vender_base(&mut self, id: &str) {
        let Some(mut n) = self.negocio() else { return };
        let cat = catalogo();
        let Some(estado) = self.estado() else { return };
        let r = estado.vender_base(id, n.bind_mut().caja_mut(), cat);
        self.cobrado(&mut n, r, &nombre_base(id));
    }

    fn cobrado(&mut self, n: &mut Gd<Negocio>, r: Result<f32, carrito_core::tienda::ErrorArmado>, que: &str) {
        match r {
            Ok(monto) => {
                n.bind_mut().registrar_ingreso(monto);
                self.avisar(&format!("Vendiste {que} (+{})", plata(monto)));
            }
            Err(e) => self.avisar(&e.to_string()),
        }
        self.abrir_panel_carrito();
    }

    /// REQ-TIE-10
    pub(crate) fn cambiar_base(&mut self, id: &str) {
        let (Some(mut c), Some(mut n)) = (self.carrito(), self.negocio()) else { return };
        let con_bloques = c.bind().anclajes_con_bloques();
        let cat = catalogo();
        let Some(estado) = self.estado() else { return };
        let r = estado.cambiar_base(id, n.bind_mut().caja_mut(), cat, &con_bloques);
        let config = estado.config();
        match r {
            Ok(cambio) => {
                n.bind_mut().registrar_gasto(cambio.pagado);
                match armar(&config, &cat.bases, &cat.accesorios, &cat.ids_bloques()) {
                    Ok(a) => c.bind_mut().cambiar_base(&a, &cambio.pasan),
                    Err(e) => godot_error!("Cambio de base: {e}"),
                }
                // Si la base nueva dice dónde va el jugador (bases con interior), lo lleva ahí.
                let lugar = c.bind().posicion_jugador();
                if let (Some(p), Some(n)) = (lugar, self.base().get_tree().get_first_node_in_group("jugador"))
                    && let Ok(mut j) = n.try_cast::<Node3D>()
                {
                    j.set_global_position(p);
                }
                let guardados = if cambio.guardados.is_empty() {
                    String::new()
                } else {
                    format!(" · {} accesorio(s) al inventario", cambio.guardados.len())
                };
                self.avisar(&format!("Ahora usás {}{guardados}", nombre_base(id)));
                self.crear_marcas();
            }
            Err(e) => self.avisar(&e.to_string()),
        }
        self.abrir_panel_carrito();
    }
}

#[godot_api]
impl ICanvasLayer for ModoArmado {
    fn ready(&mut self) {
        ACTIVO.with(|a| a.set(false));
        MENU.with(|m| m.set(false));
        self.base_mut().set_layer(6);
        let mut panel = PanelContainer::new_alloc();
        panel.set_anchors_preset(LayoutPreset::CENTER_RIGHT);
        panel.set_offset(Side::LEFT, -440.0);
        panel.set_offset(Side::RIGHT, -20.0);
        panel.set_offset(Side::TOP, -300.0);
        panel.set_offset(Side::BOTTOM, 300.0);
        let mut scroll = ScrollContainer::new_alloc();
        let mut lista = VBoxContainer::new_alloc();
        lista.set_h_size_flags(SizeFlags::EXPAND_FILL);
        lista.add_theme_constant_override("separation", 6);
        scroll.add_child(&lista);
        panel.add_child(&scroll);
        panel.set_visible(false);
        self.base_mut().add_child(&panel);
        self.panel = Some(panel);
        self.lista = Some(lista);
    }

    fn process(&mut self, _delta: f64) {
        let input = Input::singleton();
        if input.is_action_just_pressed("armado") {
            self.alternar();
        }
        if !activo() {
            return;
        }
        // REQ-TIE-07
        if input.is_action_just_pressed("tienda") && self.moviendo.is_none() {
            if menu_abierto() {
                self.cerrar_panel();
            } else {
                self.abrir_panel_carrito();
            }
        }
        if !menu_abierto() {
            self.elegir_mirado();
        }
        self.pintar_marcas();
        let texto = self.texto_cartel();
        self.poner_cartel(&texto);
    }

    fn unhandled_input(&mut self, event: Gd<InputEvent>) {
        if !activo() || menu_abierto() {
            return;
        }
        let Ok(b) = event.try_cast::<InputEventMouseButton>() else { return };
        if !b.is_pressed() || b.get_button_index() != MouseButton::LEFT {
            return;
        }
        if Input::singleton().get_mouse_mode() != MouseMode::CAPTURED {
            return;
        }
        match (self.moviendo.is_some(), self.mirado.clone()) {
            (true, Some(hasta)) => self.mover_a(&hasta),
            (true, None) => {
                self.moviendo = None;
                self.avisar("Movimiento cancelado");
            }
            (false, Some(a)) => self.abrir_menu_anclaje(a),
            (false, None) => {}
        }
    }
}
