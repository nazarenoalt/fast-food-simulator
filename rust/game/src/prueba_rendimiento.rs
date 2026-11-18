//! Prueba de rendimiento (TASK-0255): carga el juego con la plaza en su hora más
//! poblada y la fila llena, y mide cuánto tarda cada cuadro. Sin pantalla mide solo el
//! procesador (física y lógica); con ventana mide también el dibujo (FPS reales).
//! Uso: `tools/prueba_rendimiento.sh` (ver el script).

use godot::classes::display_server::VSyncMode;
use godot::classes::performance::Monitor;
use godot::classes::{DisplayServer, Engine, INode, Performance, Time};
use godot::prelude::*;

use crate::dia_noche::{self, DiaNoche};
use crate::gente::{self, Gente};
use crate::util;

/// Momentos que se miden: (nombre, minuto del día).
/// 13:00 tiene la mayor cantidad de gente (REQ-AMB-04); 20:30 suma las luces de la noche.
const MOMENTOS: [(&str, f64); 2] = [("mediodía 13:00", 13.0 * 60.0), ("anochecer 20:30", 20.5 * 60.0)];
const CALENTAR_S: f64 = 3.0;
const MEDIR_S: f64 = 10.0;
/// Tiempo de un paso de física a 60 por segundo.
const PASO_FISICA_MS: f64 = 1000.0 / 60.0;

#[derive(Default)]
struct Muestras {
    cuadros_ms: Vec<f64>,
    fisica_ms: Vec<f64>,
    proceso_ms: Vec<f64>,
    dibujos: f64,
    primitivas: f64,
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
    muestras: Muestras,
    peor_fisica: f64,
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

impl PruebaRendimiento {
    fn mundo(&self) -> Gd<Node> {
        self.mundo.clone().expect("mundo cargado")
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

    fn informar(&self) {
        let m = &self.muestras;
        let mundo = self.mundo();
        let (personas, fila) = util::unico::<Gente>(&mundo, gente::GRUPO)
            .map(|g| (g.bind().cantidad(), g.bind().largo_fila()))
            .unwrap_or_default();
        let n = m.cuadros_ms.len().max(1) as f64;
        let prom = promedio(&m.cuadros_ms);
        godot_print!("── {} ──", MOMENTOS[self.momento].0);
        godot_print!("  personas {personas} (fila {fila}), nodos {}", monitor(Monitor::OBJECT_NODE_COUNT));
        // Sin pantalla Godot duerme ~6,9 ms por cuadro a propósito: ese número no dice nada.
        if !sin_pantalla() {
            godot_print!(
                "  cuadro: promedio {prom:.2} ms ({:.0} FPS), 99 % debajo de {:.2} ms, peor {:.2} ms",
                if prom > 0.0 { 1000.0 / prom } else { 0.0 },
                percentil(&m.cuadros_ms, 0.99),
                percentil(&m.cuadros_ms, 1.0),
            );
        }
        godot_print!(
            "  física por paso: promedio {:.2} ms, peor {:.2} ms (límite {PASO_FISICA_MS:.1} ms)",
            promedio(&m.fisica_ms),
            self.peor_fisica,
        );
        godot_print!("  lógica por cuadro: promedio {:.2} ms", promedio(&m.proceso_ms));
        if m.dibujos > 0.0 {
            godot_print!(
                "  dibujo: {:.0} llamadas y {:.0} mil triángulos por cuadro",
                m.dibujos / n,
                m.primitivas / n / 1000.0
            );
        }
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
        godot_print!("PRUEBA DE RENDIMIENTO ({modo})");
    }

    fn physics_process(&mut self, _delta: f64) {
        if self.midiendo {
            let f = monitor(Monitor::TIME_PHYSICS_PROCESS) * 1000.0;
            self.muestras.fisica_ms.push(f);
            self.peor_fisica = self.peor_fisica.max(f);
        }
    }

    fn process(&mut self, _delta: f64) {
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
        self.informar();
        self.momento += 1;
        if self.momento >= MOMENTOS.len() {
            godot_print!("PRUEBA DE RENDIMIENTO: terminada");
            self.base().get_tree().quit_ex().exit_code(0).done();
            return;
        }
        self.muestras = Muestras::default();
        self.peor_fisica = 0.0;
        self.midiendo = false;
        self.preparado = false;
    }
}
