//! SPEC-032 · Escena de medición de rendimiento (TASK-0255).
//!
//! `res://scenes/rendimiento.tscn` (la abre `tools/rendimiento.sh`, REQ-REN-01): carga el juego,
//! lo pone siempre en el mismo momento (REQ-REN-02), espera y junta el tiempo de cada cuadro
//! (REQ-REN-03); las cuentas están en `carrito_core::rendimiento` (REQ-REN-05). Al terminar
//! imprime la línea `RENDIMIENTO: ...` y se cierra (REQ-REN-04). La meta (REQ-REN-06) se mira
//! en la PC del dueño: acá no hay nada que comparar.
//!
//! Para probar la escena sin esperar 70 s: `RENDIMIENTO_ESPERA` y `RENDIMIENTO_MEDICION`
//! (segundos) acortan los tiempos.

use carrito_core::rendimiento::{self as cuentas, Etapa};
use godot::classes::display_server::VSyncMode;
use godot::classes::performance::Monitor;
use godot::classes::{DisplayServer, Engine, INode, Node, Os, PackedScene, Performance, Time};
use godot::prelude::*;

use crate::dia_noche::DiaNoche;
use crate::gente::Gente;
use crate::peaton::Peaton;
use crate::transito::Autos;

/// REQ-REN-02: sábado de la segunda semana (día 13, con feria) a las 13:00.
const DIA: u32 = 13;
const MINUTO: f64 = 13.0 * 60.0;
/// REQ-REN-02: la fila llena.
const FILA_LLENA: usize = 6;
/// Cuadros que se espera después de mover el reloj, para que la gente lea la hora nueva.
const CUADROS_PREPARAR: u32 = 3;

#[derive(GodotClass)]
#[class(base=Node, init)]
pub struct Rendimiento {
    base: Base<Node>,
    mundo: Option<Gd<Node>>,
    cuadro: u32,
    /// Microsegundos del cuadro anterior y segundos desde que quedó armada la escena.
    ultimo_us: Option<u64>,
    segundos: f64,
    espera: f64,
    medicion: f64,
    tiempos: Vec<f64>,
    dibujos: f64,
    terminado: bool,
}

/// Segundos de una variable de entorno, o `defecto`.
fn segundos_de(variable: &str, defecto: f64) -> f64 {
    let os = Os::singleton();
    if !os.has_environment(variable) {
        return defecto;
    }
    os.get_environment(variable).to_string().trim().parse::<f64>().ok().filter(|s| *s >= 0.0).unwrap_or(defecto)
}

fn contar<T: GodotClass + Inherits<Node>>(raiz: &Gd<Node>) -> usize {
    let mut n = 0;
    let mut pila = vec![raiz.clone()];
    while let Some(nodo) = pila.pop() {
        for h in nodo.get_children().iter_shared() {
            pila.push(h);
        }
        if nodo.try_cast::<T>().is_ok() {
            n += 1;
        }
    }
    n
}

fn buscar<T: GodotClass + Inherits<Node>>(raiz: &Gd<Node>) -> Option<Gd<T>> {
    let mut pila = vec![raiz.clone()];
    while let Some(nodo) = pila.pop() {
        for h in nodo.get_children().iter_shared() {
            pila.push(h);
        }
        if let Ok(t) = nodo.try_cast::<T>() {
            return Some(t);
        }
    }
    None
}

#[godot_api]
impl INode for Rendimiento {
    fn ready(&mut self) {
        // REQ-REN-01: sin vsync ni tope de cuadros (además de --disable-vsync en el script).
        DisplayServer::singleton().window_set_vsync_mode(VSyncMode::DISABLED);
        Engine::singleton().set_max_fps(0);
        // REQ-REN-03
        self.espera = segundos_de("RENDIMIENTO_ESPERA", cuentas::SEGUNDOS_ESPERA);
        self.medicion = segundos_de("RENDIMIENTO_MEDICION", cuentas::SEGUNDOS_MEDICION);
        let escena = load::<PackedScene>("res://scenes/main.tscn");
        let mundo = escena.instantiate().expect("instanciar main.tscn");
        self.base_mut().add_child(&mundo);
        self.mundo = Some(mundo);
        godot_print!("RENDIMIENTO: armando la escena (espera {} s, mide {} s)", self.espera, self.medicion);
    }

    fn process(&mut self, _delta: f64) {
        if self.terminado {
            return;
        }
        let Some(mundo) = self.mundo.clone() else { return };
        self.cuadro += 1;
        let gente = buscar::<Gente>(&mundo);
        if self.cuadro == 1 {
            // REQ-REN-02: sábado 13:00 de la segunda semana: la feria está armada.
            if let Some(mut dn) = buscar::<DiaNoche>(&mundo) {
                dn.bind_mut().set_dia(DIA);
                dn.bind_mut().set_minuto(MINUTO);
            }
            return;
        }
        if self.cuadro <= CUADROS_PREPARAR {
            return;
        }
        // REQ-REN-02: la plaza tan llena como la quiere la agenda con feria, y la fila llena
        // (si alguien se va de la fila, llega otro, para que sea siempre igual).
        if let Some(mut g) = gente {
            if self.cuadro == CUADROS_PREPARAR + 1 {
                let faltan = g.bind().objetivo_gente().saturating_sub(g.bind().cantidad());
                g.bind_mut().probar_presentes(faltan);
            }
            if g.bind().largo_fila() < FILA_LLENA {
                g.bind_mut().forzar_cliente();
            }
        }

        // REQ-REN-03: tiempo real de cada cuadro (sin el suavizado del delta).
        let ahora = Time::singleton().get_ticks_usec();
        let Some(antes) = self.ultimo_us.replace(ahora) else { return };
        let dt = (ahora - antes) as f64 / 1e6;
        self.segundos += dt;
        match cuentas::etapa(self.segundos, self.espera, self.medicion) {
            Etapa::Esperando => {}
            Etapa::Midiendo => {
                self.tiempos.push(dt);
                self.dibujos += Performance::singleton().get_monitor(Monitor::RENDER_TOTAL_DRAW_CALLS_IN_FRAME);
            }
            Etapa::Terminada => self.terminar(&mundo),
        }
    }
}

impl Rendimiento {
    /// REQ-REN-04: imprime la línea y cierra el juego.
    fn terminar(&mut self, mundo: &Gd<Node>) {
        self.terminado = true;
        let personas = contar::<Peaton>(mundo);
        let autos = buscar::<Autos>(mundo).map(|a| a.bind().posiciones().len()).unwrap_or(0);
        let dibujos =
            if self.tiempos.is_empty() { 0 } else { (self.dibujos / self.tiempos.len() as f64).round() as u64 };
        let codigo = match cuentas::resumir(&self.tiempos) {
            Some(r) => {
                godot_print!("{}", cuentas::linea(&r, dibujos, personas, autos));
                0
            }
            None => {
                godot_print!("RENDIMIENTO: no se midió ningún cuadro");
                1
            }
        };
        self.base().get_tree().quit_ex().exit_code(codigo).done();
    }
}
