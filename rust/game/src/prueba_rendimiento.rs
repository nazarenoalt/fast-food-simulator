//! Prueba de rendimiento (SPEC-013, REQ-AMB-15/16): carga el juego con la plaza en su
//! hora más poblada y la fila llena, y mide cuánto tarda cada cuadro. Sin pantalla mide
//! solo el procesador (física y lógica); con ventana mide también el dibujo (FPS reales).
//! Se abre con la opción `--rendimiento` del juego o con `tools/prueba_rendimiento.sh`.

use godot::classes::display_server::VSyncMode;
use godot::classes::input::MouseMode;
use godot::classes::performance::Monitor;
use godot::classes::{
    CanvasLayer, ColorRect, DisplayServer, Engine, FileAccess, INode, Input, Label, Os, Performance, ProjectSettings,
    Time, control,
};
use godot::prelude::*;

use crate::dia_noche::{self, DiaNoche};
use crate::gente::{self, Gente};
use crate::util;

const ESCENA: &str = "res://scenes/prueba_rendimiento.tscn";
const OPCION: &str = "--rendimiento";
const ARCHIVO: &str = "user://rendimiento.txt";

/// Momentos que se miden: (nombre, minuto del día).
/// 13:00 tiene la mayor cantidad de gente (REQ-AMB-04); 20:30 suma las luces de la noche.
const MOMENTOS: [(&str, f64); 2] = [("mediodía 13:00", 13.0 * 60.0), ("anochecer 20:30", 20.5 * 60.0)];
const CALENTAR_S: f64 = 3.0;
const MEDIR_S: f64 = 10.0;
/// REQ-AMB-15
const FPS_MINIMO: f64 = 60.0;
/// REQ-AMB-16: promedio máximo y peor caso (un paso a 60 por segundo) del paso de física.
const FISICA_PROMEDIO_MS: f64 = 8.0;
const FISICA_PEOR_MS: f64 = 1000.0 / 60.0;

#[derive(Default)]
struct Muestras {
    cuadros_ms: Vec<f64>,
    fisica_ms: Vec<f64>,
    proceso_ms: Vec<f64>,
    dibujos: f64,
    primitivas: f64,
}

/// Resumen de un momento, para decidir si cumple.
struct Resultado {
    fps: f64,
    fisica_prom: f64,
    fisica_peor: f64,
}

/// Va en `main.tscn`: si el juego se abrió con `--rendimiento`, salta a la prueba.
#[derive(GodotClass)]
#[class(base=Node, init)]
pub struct OpcionRendimiento {
    base: Base<Node>,
}

#[godot_api]
impl INode for OpcionRendimiento {
    fn ready(&mut self) {
        let os = Os::singleton();
        let pedida =
            os.get_cmdline_user_args().as_slice().iter().chain(os.get_cmdline_args().as_slice()).any(|a| *a == OPCION);
        let Some(mut arbol) = self.base().get_tree_or_null() else { return };
        // Solo si el mundo es la escena principal: la prueba también carga main.tscn.
        let es_principal = match (arbol.get_current_scene(), self.base().get_parent()) {
            (Some(actual), Some(padre)) => actual == padre,
            _ => false,
        };
        if pedida && es_principal {
            arbol.call_deferred("change_scene_to_file", &[ESCENA.to_variant()]);
        }
    }
}

#[derive(GodotClass)]
#[class(base=Node, init)]
pub struct PruebaRendimiento {
    base: Base<Node>,
    mundo: Option<Gd<Node>>,
    momento: usize,
    /// Cuándo empezó la etapa actual (µs).
    desde_us: u64,
    ultimo_us: u64,
    midiendo: bool,
    preparado: bool,
    terminada: bool,
    muestras: Muestras,
    peor_fisica: f64,
    informe: Vec<String>,
    resultados: Vec<Resultado>,
}

fn monitor(m: Monitor) -> f64 {
    Performance::singleton().get_monitor(m)
}

fn sin_pantalla() -> bool {
    DisplayServer::singleton().get_name() == "headless"
}

fn ahora_us() -> u64 {
    Time::singleton().get_ticks_usec()
}

fn percentil(v: &[f64], p: f64) -> f64 {
    if v.is_empty() {
        return 0.0;
    }
    let mut o = v.to_vec();
    o.sort_by(|a, b| a.total_cmp(b));
    o[((o.len() - 1) as f64 * p).round() as usize]
}

fn promedio(v: &[f64]) -> f64 {
    if v.is_empty() { 0.0 } else { v.iter().sum::<f64>() / v.len() as f64 }
}

fn si_no(ok: bool) -> &'static str {
    if ok { "CUMPLE" } else { "NO CUMPLE" }
}

impl PruebaRendimiento {
    fn mundo(&self) -> Gd<Node> {
        self.mundo.clone().expect("mundo cargado")
    }

    fn anotar(&mut self, linea: String) {
        godot_print!("{linea}");
        self.informe.push(linea);
    }

    /// Pone la hora del momento y llena la fila.
    fn preparar(&mut self) -> bool {
        let mundo = self.mundo();
        let Some(mut dn) = util::unico::<DiaNoche>(&mundo, dia_noche::GRUPO) else { return false };
        let Some(mut g) = util::unico::<Gente>(&mundo, gente::GRUPO) else { return false };
        dn.bind_mut().set_minuto(MOMENTOS[self.momento].1);
        for _ in 0..carrito_core::clientes::LUGARES_FILA {
            g.bind_mut().forzar_cliente();
        }
        true
    }

    fn informar_momento(&mut self) {
        let m = std::mem::take(&mut self.muestras);
        let mundo = self.mundo();
        let (personas, fila) = util::unico::<Gente>(&mundo, gente::GRUPO)
            .map(|g| (g.bind().cantidad(), g.bind().largo_fila()))
            .unwrap_or_default();
        let n = m.cuadros_ms.len().max(1) as f64;
        let prom = promedio(&m.cuadros_ms);
        let fps = if prom > 0.0 { 1000.0 / prom } else { 0.0 };
        let fisica_prom = promedio(&m.fisica_ms);
        self.anotar(format!("── {} ──", MOMENTOS[self.momento].0));
        self.anotar(format!("  personas {personas} (fila {fila}), nodos {}", monitor(Monitor::OBJECT_NODE_COUNT)));
        // Sin pantalla Godot duerme ~6,9 ms por cuadro a propósito: ese número no dice nada.
        if !sin_pantalla() {
            self.anotar(format!(
                "  cuadro: promedio {prom:.2} ms ({fps:.0} FPS), 99 % debajo de {:.2} ms, peor {:.2} ms",
                percentil(&m.cuadros_ms, 0.99),
                percentil(&m.cuadros_ms, 1.0),
            ));
            self.anotar(format!(
                "  dibujo: {:.0} llamadas y {:.0} mil triángulos por cuadro",
                m.dibujos / n,
                m.primitivas / n / 1000.0
            ));
        }
        self.anotar(format!("  física por paso: promedio {fisica_prom:.2} ms, peor {:.2} ms", self.peor_fisica));
        self.anotar(format!("  lógica por cuadro: promedio {:.2} ms", promedio(&m.proceso_ms)));
        self.resultados.push(Resultado { fps, fisica_prom, fisica_peor: self.peor_fisica });
    }

    /// Veredicto contra REQ-AMB-15 y REQ-AMB-16, archivo y cartel.
    fn cerrar(&mut self) {
        self.anotar("── Resultado ──".into());
        if sin_pantalla() {
            self.anotar("  REQ-AMB-15 (60 FPS): no se mide sin pantalla".into());
        } else {
            let peor = self.resultados.iter().map(|r| r.fps).fold(f64::INFINITY, f64::min);
            self.anotar(format!("  REQ-AMB-15 (60 FPS): {} (peor momento {peor:.0} FPS)", si_no(peor >= FPS_MINIMO)));
        }
        let prom = self.resultados.iter().map(|r| r.fisica_prom).fold(0.0, f64::max);
        let peor = self.resultados.iter().map(|r| r.fisica_peor).fold(0.0, f64::max);
        let ok = prom <= FISICA_PROMEDIO_MS && peor <= FISICA_PEOR_MS;
        let nota = if cfg!(debug_assertions) { " — código sin optimizar: no vale como medida" } else { "" };
        self.anotar(format!(
            "  REQ-AMB-16 (física ≤ {FISICA_PROMEDIO_MS:.0} ms, peor ≤ {FISICA_PEOR_MS:.1} ms): {} \
             (promedio {prom:.2} ms, peor {peor:.2} ms){nota}",
            si_no(ok)
        ));

        let texto = self.informe.join("\n");
        let ruta = ProjectSettings::singleton().globalize_path(ARCHIVO).to_string();
        if let Some(mut f) = FileAccess::open(ARCHIVO, godot::classes::file_access::ModeFlags::WRITE) {
            f.store_string(&texto);
            f.close();
            godot_print!("Guardado en {ruta}");
        }
        godot_print!("PRUEBA DE RENDIMIENTO: terminada");

        if sin_pantalla() {
            self.base().get_tree().quit_ex().exit_code(0).done();
            return;
        }
        // CA-AMB-04: con ventana, el mundo se queda quieto y se muestran los resultados.
        if let Some(mut m) = self.mundo.clone() {
            m.set_process_mode(godot::classes::node::ProcessMode::DISABLED);
        }
        Input::singleton().set_mouse_mode(MouseMode::VISIBLE);
        let mut capa = CanvasLayer::new_alloc();
        capa.set_layer(100);
        let mut fondo = ColorRect::new_alloc();
        fondo.set_color(Color::from_rgba(0.0, 0.0, 0.0, 0.85));
        fondo.set_anchors_preset(control::LayoutPreset::FULL_RECT);
        capa.add_child(&fondo);
        let mut cartel = Label::new_alloc();
        cartel.set_text(&format!("{texto}\n\nGuardado en {ruta}\nCerrá la ventana para salir."));
        cartel.set_position(Vector2::new(40.0, 40.0));
        cartel.add_theme_font_size_override("font_size", 18);
        capa.add_child(&cartel);
        self.base_mut().add_child(&capa);
    }
}

#[godot_api]
impl INode for PruebaRendimiento {
    fn ready(&mut self) {
        // Sin límite de cuadros: se mide cuánto aguanta, no la frecuencia del monitor.
        Engine::singleton().set_max_fps(0);
        DisplayServer::singleton().window_set_vsync_mode(VSyncMode::DISABLED);
        let escena = load::<PackedScene>("res://scenes/main.tscn");
        let mundo = escena.instantiate().expect("instanciar main.tscn");
        self.base_mut().add_child(&mundo);
        self.mundo = Some(mundo);
        self.desde_us = ahora_us();
        self.ultimo_us = self.desde_us;
        let modo = if sin_pantalla() { "sin pantalla: solo procesador" } else { "con ventana: procesador y dibujo" };
        self.anotar(format!("PRUEBA DE RENDIMIENTO ({modo}), {MEDIR_S:.0} s por momento"));
    }

    fn physics_process(&mut self, _delta: f64) {
        if self.midiendo {
            let f = monitor(Monitor::TIME_PHYSICS_PROCESS) * 1000.0;
            self.muestras.fisica_ms.push(f);
            self.peor_fisica = self.peor_fisica.max(f);
        }
    }

    fn process(&mut self, _delta: f64) {
        if self.terminada {
            return;
        }
        let t = ahora_us();
        let cuadro_ms = (t - self.ultimo_us) as f64 / 1000.0;
        self.ultimo_us = t;
        let pasado_s = (t - self.desde_us) as f64 / 1e6;

        if !self.preparado {
            // Un cuadro después de cargar, cuando los nodos ya están listos.
            self.preparado = self.preparar();
            self.desde_us = t;
            return;
        }
        if !self.midiendo {
            if pasado_s >= CALENTAR_S {
                self.midiendo = true;
                self.desde_us = t;
            }
            return;
        }
        self.muestras.cuadros_ms.push(cuadro_ms);
        self.muestras.proceso_ms.push(monitor(Monitor::TIME_PROCESS) * 1000.0);
        self.muestras.dibujos += monitor(Monitor::RENDER_TOTAL_DRAW_CALLS_IN_FRAME);
        self.muestras.primitivas += monitor(Monitor::RENDER_TOTAL_PRIMITIVES_IN_FRAME);
        if pasado_s < MEDIR_S {
            return;
        }
        self.informar_momento();
        self.momento += 1;
        if self.momento >= MOMENTOS.len() {
            self.terminada = true;
            self.cerrar();
            return;
        }
        self.peor_fisica = 0.0;
        self.midiendo = false;
        self.preparado = false;
    }
}
