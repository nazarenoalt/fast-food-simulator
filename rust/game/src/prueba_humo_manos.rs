//! Prueba de humo de la etapa 2.5 · agente B: REQ-INT-03, REQ-INT-06, REQ-INT-08, REQ-INT-09, REQ-JUG-02, REQ-JUG-04, REQ-JUG-10. (TASK-0250)

use carrito_core::agarre::{self, AccionClic};
use carrito_core::movimiento;
use godot::classes::{Input, Node, Object, RayCast3D};
use godot::prelude::*;

use super::{PruebaHumo, todos};
use crate::bloque_stock::BloqueStock;
use crate::comida::{self, Comida};
use crate::datos::catalogo;
use crate::heladera::Heladera;
use crate::hervidor::Hervidor;
use crate::jugador::Jugador;
use crate::lugar_deposito::LugarDeposito;
use crate::paquete::Paquete;

/// CA-INT-05: desde cuánto se apunta al hervidor (m, de los ojos al punto).
const DESDE_HERVIDOR: f32 = 2.5;
/// REQ-JUG-05: alto de los ojos.
const OJOS: f32 = 1.65;
/// Cuadros que camina antes de medir la velocidad de crucero.
const CUADROS_CAMINANDO: u32 = 90;
/// Cuadros después de soltar la tecla (0,25 s: ya frenó y la cámara volvió al centro).
const CUADROS_FRENANDO: u32 = 15;

// Lugares de `notas5`.
const N_POS: usize = 0; // x, y, z del jugador al empezar
const N_GIRO: usize = 3; // giro del jugador al empezar
const N_A: usize = 4; // números de cada fase
const N_B: usize = 5;
const N_C: usize = 6;
const N_ID: usize = 7; // id de un objeto (dos mitades)
const N_TOTAL: usize = 9;

/// Lo que toca un rayo de `desde` a `hasta`, sin contar al jugador: punto, normal y objeto.
fn rayo(mundo: &Gd<Node>, j: &Gd<Jugador>, desde: Vector3, hasta: Vector3) -> Option<(Vector3, Vector3, Gd<Object>)> {
    let mut r = RayCast3D::new_alloc();
    mundo.clone().add_child(&r);
    r.add_exception(j);
    r.set_global_position(desde);
    r.set_target_position(hasta - desde);
    r.force_raycast_update();
    let res = if r.is_colliding() {
        r.get_collider().map(|o| (r.get_collision_point(), r.get_collision_normal(), o))
    } else {
        None
    };
    r.queue_free();
    res
}

/// Piso donde pararse en (x, z), por debajo de `techo`: el primer apoyo bajando.
fn piso(mundo: &Gd<Node>, j: &Gd<Jugador>, x: f32, z: f32, techo: f32) -> Option<f32> {
    let (p, n, _) = rayo(mundo, j, Vector3::new(x, techo, z), Vector3::new(x, techo - 4.0, z))?;
    (n.y > 0.7).then_some(p.y)
}

/// Pone al jugador parado en `pie` mirando a `punto`, si entra ahí (no está dentro de algo).
fn pararse(j: &mut Gd<Jugador>, pie: Vector3, punto: Vector3) -> bool {
    let t = Transform3D::new(Basis::IDENTITY, pie + Vector3::new(0.0, 0.02, 0.0));
    if j.test_move(t, Vector3::new(0.0, 0.05, 0.0)) || j.test_move(t, Vector3::new(0.1, 0.0, 0.0)) {
        return false;
    }
    j.set_global_position(t.origin);
    j.set_velocity(Vector3::ZERO);
    j.bind_mut().apuntar_a(punto);
    true
}

/// Busca dónde pararse para que el clic haga `quiero` apuntando a alguno de los `puntos`:
/// prueba vueltas alrededor de `centro` a las distancias `radios` (los ojos a `desde` del punto
/// si `desde` > 0). Deja al jugador ahí y devuelve el punto al que apunta.
fn buscar_lugar(
    mundo: &Gd<Node>,
    j: &mut Gd<Jugador>,
    centro: Vector3,
    puntos: &[Vector3],
    desde: f32,
    quiero: &AccionClic,
) -> Option<Vector3> {
    for radio in [0.8f32, 1.1, 1.4, 1.8, 2.2] {
        for k in 0..24 {
            let a = k as f32 * std::f32::consts::TAU / 24.0;
            let dir = Vector3::new(a.cos(), 0.0, a.sin());
            for &punto in puntos {
                let mut r = radio;
                let mut pie = None;
                // Con `desde`, el radio se ajusta para que los ojos queden a esa distancia.
                for _ in 0..4 {
                    let x = centro.x + dir.x * r;
                    let z = centro.z + dir.z * r;
                    pie = None;
                    let Some(y) = piso(mundo, j, x, z, punto.y + 0.6) else { break };
                    if y > punto.y - 0.05 {
                        break; // eso es una mesada o un estante, no el piso
                    }
                    pie = Some(Vector3::new(x, y, z));
                    let dy = y + OJOS - punto.y;
                    if desde <= 0.0 || desde <= dy.abs() {
                        break;
                    }
                    r = (desde * desde - dy * dy).sqrt();
                }
                let Some(pie) = pie else { continue };
                let ojos = pie + Vector3::new(0.0, OJOS, 0.0);
                if desde > 0.0 && ((ojos - punto).length() - desde).abs() > 0.15 {
                    continue;
                }
                if pararse(j, pie, punto) && j.bind_mut().accion_clic().as_ref() == Some(quiero) {
                    return Some(punto);
                }
            }
        }
    }
    None
}

/// Busca, alrededor de `centro`, dónde pararse con una pared a menos de 3 m a la vista (que
/// no sea del hervidor: el clic tiene que decir "Soltar"). Deja al jugador ahí, mirándola.
fn buscar_pared(mundo: &Gd<Node>, j: &mut Gd<Jugador>, centro: Vector3) -> Option<Vector3> {
    for radio in [1.0f32, 1.5, 2.0, 2.5, 3.0] {
        for k in 0..12 {
            let a = k as f32 * std::f32::consts::TAU / 12.0;
            let (x, z) = (centro.x + a.cos() * radio, centro.z + a.sin() * radio);
            let Some(y) = piso(mundo, j, x, z, centro.y + 0.3) else { continue };
            let ojos = Vector3::new(x, y + OJOS, z);
            for m in 0..24 {
                let b = m as f32 * std::f32::consts::TAU / 24.0;
                let hasta = ojos + Vector3::new(b.cos(), -0.15, b.sin()) * 2.6;
                let Some((p, n, _)) = rayo(mundo, j, ojos, hasta) else { continue };
                if n.y.abs() > 0.3 || (p - ojos).length() < 0.8 {
                    continue;
                }
                if pararse(j, Vector3::new(x, y, z), p) && j.bind_mut().accion_clic() == Some(AccionClic::Soltar) {
                    return Some(p);
                }
            }
        }
    }
    None
}

fn guardar_id(notas: &mut [f64], id: InstanceId) {
    let v = id.to_i64() as u64;
    notas[N_ID] = (v >> 32) as f64;
    notas[N_ID + 1] = (v & 0xffff_ffff) as f64;
}

fn leer_id<T: GodotClass + Inherits<Object>>(notas: &[f64]) -> Option<Gd<T>> {
    let v = ((notas[N_ID] as u64) << 32) | notas[N_ID + 1] as u64;
    let id = InstanceId::try_from_i64(v as i64)?;
    Gd::<Object>::try_from_instance_id(id).ok()?.try_cast::<T>().ok()
}

/// Lleva lo que tiene en la mano a la mano (después de mover al jugador lejos).
fn a_la_mano(j: &Gd<Jugador>) {
    if let Some(mut m) = j.bind().en_mano() {
        let [x, y, z] = agarre::punto_mano(0.08);
        m.set_global_position(j.bind().vista() * Vector3::new(x, y, z));
        m.set_linear_velocity(Vector3::ZERO);
    }
}

/// Clic izquierdo como el del mouse: fuera del paso de física (al final del cuadro).
fn clic(j: &mut Gd<Jugador>) {
    j.run_deferred(|j| j.clic_izquierdo());
}

fn horizontal(v: Vector3) -> f32 {
    Vector2::new(v.x, v.z).length()
}

impl PruebaHumo {
    /// Se llama cada cuadro hasta que devuelve true. Camina (arranque, frenado, balanceo y
    /// salto), coloca una salchicha en el hervidor desde 2,5 m, la suelta contra una pared,
    /// guarda un paquete en el estante con el clic y vuelca una caja de salchichas. Deja al
    /// jugador donde estaba (no toca día ni hora).
    pub(super) fn chequear_manos(&mut self) -> bool {
        if self.cuadro < self.cuadro5 {
            return false;
        }
        let mundo = self.mundo();
        let (Some(mut j), Some(h)) = (todos::<Jugador>(&mundo).pop(), todos::<Hervidor>(&mundo).pop()) else {
            self.chequear(false, "REQ-INT-06 hay jugador y hervidor");
            return true;
        };
        if self.notas5.len() < N_TOTAL {
            self.notas5.resize(N_TOTAL, 0.0);
        }
        let mut input = Input::singleton();
        match self.fase5 {
            0 => {
                let p = j.get_global_position();
                self.notas5[N_POS..N_POS + 3].copy_from_slice(&[p.x as f64, p.y as f64, p.z as f64]);
                self.notas5[N_GIRO] = j.get_global_rotation().y as f64;
                if let Some(mut viejo) = j.bind_mut().soltar() {
                    viejo.queue_free();
                }
                // REQ-JUG-10: un lugar de la plaza con 3 m libres para caminar.
                let mut listo = false;
                'busca: for (x, z) in [(0.0, -14.0), (8.0, -8.0), (-8.0, -8.0), (8.0, 8.0), (-8.0, 8.0), (0.0, 14.0)] {
                    for k in 0..8 {
                        let a = k as f32 * std::f32::consts::TAU / 8.0;
                        let dir = Vector3::new(a.cos(), 0.0, a.sin());
                        let Some(y) = piso(&mundo, &j, x, z, 3.0) else { continue };
                        let pie = Vector3::new(x, y + 0.05, z);
                        let t = Transform3D::new(Basis::IDENTITY, pie);
                        if j.test_move(t, Vector3::new(0.0, 0.05, 0.0)) || j.test_move(t, dir * 6.0) {
                            continue;
                        }
                        j.set_global_position(pie);
                        j.set_velocity(Vector3::ZERO);
                        j.bind_mut().apuntar_a(pie + dir * 5.0 + Vector3::new(0.0, OJOS, 0.0));
                        listo = true;
                        break 'busca;
                    }
                }
                self.chequear(listo, "REQ-JUG-10 hay un lugar libre en la plaza para caminar 6 m");
                self.fase5 = if listo { 1 } else { 5 };
                self.cuadro5 = self.cuadro + 30;
                false
            }
            1 => {
                self.chequear(j.is_on_floor(), "REQ-JUG-10 el jugador está parado en el piso");
                input.action_press("adelante");
                self.notas5[N_A] = 0.0; // cuadros caminando
                self.notas5[N_B] = 0.0; // balanceo más alto
                self.notas5[N_C] = 0.0; // balanceo más bajo
                self.fase5 = 2;
                false
            }
            2 => {
                let v = horizontal(j.get_velocity());
                let n = self.notas5[N_A] as u32;
                if n == 0 {
                    // El primer cuadro con la tecla apretada ya pasó: 12 m/s² × 1/60 s = 0,2 m/s.
                    self.chequear(
                        v > 0.05 && v < 1.0,
                        &format!("REQ-JUG-10 arranca de a poco: {v:.2} m/s en el primer cuadro (no 3,5)"),
                    );
                }
                if n >= 30 {
                    let y = (j.bind().alto_camara() - OJOS) as f64;
                    self.notas5[N_B] = self.notas5[N_B].max(y);
                    self.notas5[N_C] = self.notas5[N_C].min(y);
                }
                self.notas5[N_A] += 1.0;
                if n + 1 >= CUADROS_CAMINANDO {
                    self.chequear(
                        (v - 3.5).abs() < 0.15,
                        &format!("REQ-JUG-10 en {CUADROS_CAMINANDO} cuadros llega a 3,5 m/s ({v:.2})"),
                    );
                    let (alto, bajo) = (self.notas5[N_B], self.notas5[N_C]);
                    self.chequear(
                        alto > 0.012 && alto < 0.022 && bajo < -0.012 && bajo > -0.022,
                        &format!("REQ-JUG-10 la cámara se balancea 2 cm al caminar ({bajo:.3} a {alto:.3} m)"),
                    );
                    input.action_release("adelante");
                    self.notas5[N_A] = 0.0;
                    self.fase5 = 3;
                }
                false
            }
            3 => {
                let v = horizontal(j.get_velocity());
                let n = self.notas5[N_A] as u32;
                if n == 0 {
                    self.chequear(v > 2.5, &format!("REQ-JUG-10 frena suave: {v:.2} m/s un cuadro después de soltar"));
                }
                self.notas5[N_A] += 1.0;
                if n + 1 >= CUADROS_FRENANDO {
                    let y = j.bind().alto_camara() - OJOS;
                    self.chequear(
                        v < 0.05 && y.abs() < 0.001,
                        &format!("REQ-JUG-10 en 0,25 s frenó ({v:.2} m/s) y la cámara volvió al centro ({y:.4} m)"),
                    );
                    // REQ-JUG-04: salto.
                    input.action_press("saltar");
                    self.notas5[N_A] = j.get_global_position().y as f64;
                    self.notas5[N_B] = self.notas5[N_A];
                    self.notas5[N_C] = 0.0;
                    self.fase5 = 4;
                }
                false
            }
            4 => {
                input.action_release("saltar");
                let y = j.get_global_position().y as f64;
                self.notas5[N_B] = self.notas5[N_B].max(y);
                self.notas5[N_C] += 1.0;
                if self.notas5[N_C] >= 60.0 {
                    let sube = self.notas5[N_B] - self.notas5[N_A];
                    self.chequear(
                        (0.5..0.7).contains(&sube),
                        &format!(
                            "REQ-JUG-04 el salto sube ~0,6 m ({sube:.2} m, sale a {} m/s); REQ-JUG-02 mira a {} rad/px",
                            movimiento::VEL_SALTO,
                            movimiento::SENSIBILIDAD
                        ),
                    );
                    self.fase5 = 5;
                }
                false
            }
            5 => {
                // CA-INT-05: una salchicha en la mano, apuntando al hervidor desde ~2,5 m.
                let s = self.agregar_comida("salchicha", j.get_global_position() + Vector3::new(0.0, 1.4, 0.0));
                j.bind_mut().agarrar(s.clone().upcast());
                let t = h.get_global_transform();
                let arriba = t.basis.col_b().normalized();
                // Primero el borde (cerca y arriba de las paredes); si no, cualquier parte.
                let puntos: Vec<Vector3> = [0.19f32, 0.15, 0.1].iter().map(|&alto| t.origin + arriba * alto).collect();
                let encontrado = buscar_lugar(&mundo, &mut j, t.origin, &puntos, DESDE_HERVIDOR, &AccionClic::AlAgua);
                self.chequear(
                    encontrado.is_some(),
                    "REQ-INT-09 con la salchicha en la mano, la cruz en el hervidor ofrece \"Al agua\"",
                );
                a_la_mano(&j);
                guardar_id(&mut self.notas5, s.instance_id());
                self.notas5[N_A] = Self::salchichas_en_hervidor(&mundo).len() as f64;
                self.notas5[N_B] = encontrado.map(|p| (p - j.bind().vista().origin).length()).unwrap_or(0.0) as f64;
                // Se espera que la mano y el jugador se acomoden.
                self.fase5 = if encontrado.is_some() { 6 } else { 8 };
                self.cuadro5 = self.cuadro + 30;
                false
            }
            6 => {
                // REQ-INT-03: derecha en la mano: cruzada a la vista, arriba e inclinada 25°.
                let vista = j.bind().vista();
                if let Some(s) = leer_id::<Comida>(&self.notas5) {
                    let b = s.get_global_transform().basis.orthonormalized();
                    let local = vista.basis.orthonormalized().transposed();
                    let (x, y) = (local * b.col_a(), local * b.col_b());
                    let grados = y.z.atan2(y.y).to_degrees();
                    self.chequear(
                        x.x > 0.95 && y.y > 0.8 && (grados - agarre::INCLINACION_MANO).abs() < 6.0,
                        &format!(
                            "REQ-INT-03 la salchicha en la mano va cruzada ({:.2}), derecha ({:.2}) e inclinada {grados:.0}° hacia los ojos",
                            x.x, y.y
                        ),
                    );
                }
                // Por si se movió al asentarse: vuelve a apuntar y hace clic (como el mouse).
                let t = h.get_global_transform();
                let arriba = t.basis.col_b().normalized();
                let puntos: Vec<Vector3> = [0.19f32, 0.15, 0.1].iter().map(|&a| t.origin + arriba * a).collect();
                let ok = puntos.iter().any(|&p| {
                    j.bind_mut().apuntar_a(p);
                    j.bind_mut().accion_clic() == Some(AccionClic::AlAgua)
                });
                let d = self.notas5[N_B];
                self.chequear(
                    ok,
                    &format!("REQ-INT-08 el cartel dice \"{}\" (a {d:.2} m)", AccionClic::AlAgua.cartel()),
                );
                clic(&mut j);
                self.fase5 = 7;
                self.cuadro5 = self.cuadro + 40;
                false
            }
            7 => {
                let antes = self.notas5[N_A] as usize;
                let ahora = Self::salchichas_en_hervidor(&mundo);
                let s = leer_id::<Comida>(&self.notas5);
                let dentro = s.as_ref().is_some_and(|s| ahora.iter().any(|c| c.instance_id() == s.instance_id()));
                self.chequear(
                    dentro && j.bind().en_mano().is_none(),
                    &format!(
                        "CA-INT-05 apunto al hervidor desde {:.1} m, hago clic y la salchicha queda en el agua ({antes} → {})",
                        self.notas5[N_B],
                        ahora.len()
                    ),
                );
                if let Some(mut s) = s {
                    s.queue_free();
                }
                self.fase5 = 8;
                false
            }
            8 => {
                // CA-INT-05 / REQ-INT-06: con la cruz en una pared, el clic la suelta y cae.
                let mut s = self.agregar_comida("salchicha", j.get_global_position() + Vector3::new(0.0, 1.4, 0.0));
                s.set_linear_velocity(Vector3::ZERO);
                j.bind_mut().agarrar(s.clone().upcast());
                guardar_id(&mut self.notas5, s.instance_id());
                // Primero, el cielo: nada a 3 m.
                let ojos = j.bind().vista().origin;
                j.bind_mut().apuntar_a(ojos + Vector3::new(0.3, 10.0, 0.0));
                let cielo = j.bind_mut().accion_clic();
                self.chequear(
                    cielo == Some(AccionClic::Soltar),
                    &format!("REQ-INT-06 con la cruz en el cielo el cartel dice \"[Clic] Soltar\" ({cielo:?})"),
                );
                // Una pared a menos de 3 m: se la busca parándose alrededor del carrito.
                let pared = buscar_pared(&mundo, &mut j, h.get_global_position());
                a_la_mano(&j);
                self.chequear(pared.is_some(), "REQ-INT-06 hay una pared cerca para probar");
                self.notas5[N_A] = pared.map(|p| p.y).unwrap_or(0.0) as f64;
                self.notas5[N_B] = pared.map(|p| p.x).unwrap_or(0.0) as f64;
                self.notas5[N_C] = pared.map(|p| p.z).unwrap_or(0.0) as f64;
                self.fase5 = if pared.is_some() { 9 } else { 11 };
                self.cuadro5 = self.cuadro + 20;
                false
            }
            9 => {
                let n = &self.notas5;
                let pared = Vector3::new(n[N_B] as f32, n[N_A] as f32, n[N_C] as f32);
                j.bind_mut().apuntar_a(pared);
                let accion = j.bind_mut().accion_clic();
                self.chequear(
                    accion == Some(AccionClic::Soltar),
                    &format!("REQ-INT-08 con la cruz en la pared el cartel dice \"[Clic] Soltar\" ({accion:?})"),
                );
                let y = leer_id::<Comida>(&self.notas5).map(|s| s.get_global_position().y).unwrap_or(0.0);
                self.notas5[N_A] = y as f64;
                clic(&mut j);
                self.fase5 = 10;
                self.cuadro5 = self.cuadro + 45;
                false
            }
            10 => {
                let antes = self.notas5[N_A] as f32;
                let s = leer_id::<Comida>(&self.notas5);
                let y = s.as_ref().map(|s| s.get_global_position().y).unwrap_or(antes);
                self.chequear(
                    j.bind().en_mano().is_none() && y < antes - 0.2,
                    &format!("CA-INT-05 apunto a la pared, hago clic y la salchicha cae (de {antes:.2} a {y:.2} m)"),
                );
                if let Some(mut s) = s {
                    s.queue_free();
                }
                self.fase5 = 11;
                false
            }
            11 => {
                // REQ-INT-08 (TASK-0263): un paquete con la cruz en un lugar libre del estante: el
                // clic lo guarda (no lo tira al piso). Se levanta uno del depósito del carrito.
                let bloques: Vec<Gd<BloqueStock>> = todos::<BloqueStock>(&mundo)
                    .into_iter()
                    .filter(|b| !b.is_queued_for_deletion() && b.bind().restantes() > 0)
                    .filter(|b| {
                        let mut n = b.get_parent();
                        for _ in 0..6 {
                            let Some(p) = n else { return true };
                            if p.clone().try_cast::<Heladera>().is_ok() {
                                return false;
                            }
                            n = p.get_parent();
                        }
                        true
                    })
                    .collect();
                let mut listo = false;
                for b in bloques {
                    let Some(lugar) = b.get_parent().and_then(|p| p.try_cast::<LugarDeposito>().ok()) else { continue };
                    let n = b.bind().restantes();
                    let base = lugar.get_global_position();
                    j.bind_mut().levantar(b);
                    let puntos = [base + Vector3::new(0.0, 0.01, 0.0)];
                    if buscar_lugar(&mundo, &mut j, base, &puntos, 0.0, &AccionClic::Guardar).is_some() {
                        a_la_mano(&j);
                        guardar_id(&mut self.notas5, lugar.instance_id());
                        self.notas5[N_A] = n as f64;
                        self.notas5[N_B] = base.x as f64;
                        self.notas5[N_C] = base.z as f64;
                        listo = true;
                        break;
                    }
                    // Desde ningún lado se ve: se devuelve el paquete a su lugar y se prueba otro.
                    if let Some(mut p) = j.bind_mut().soltar() {
                        p.set_global_transform(Transform3D::new(lugar.get_global_basis(), lugar.bind().centro_zona()));
                        p.set_linear_velocity(Vector3::ZERO);
                    }
                }
                self.chequear(
                    listo,
                    "REQ-INT-09 con un paquete, la cruz en un lugar libre del estante ofrece guardarlo",
                );
                self.fase5 = if listo { 12 } else { 14 };
                self.cuadro5 = self.cuadro + 150; // quieto en la mano un rato, como quien apunta tranquilo
                false
            }
            12 => {
                let Some(lugar) = leer_id::<LugarDeposito>(&self.notas5) else {
                    self.fase5 = 14;
                    return false;
                };
                j.bind_mut().apuntar_a(lugar.get_global_position() + Vector3::new(0.0, 0.01, 0.0));
                let accion = j.bind_mut().accion_clic();
                self.chequear(
                    accion == Some(AccionClic::Guardar),
                    &format!("REQ-INT-08 el cartel dice \"{}\" ({accion:?})", AccionClic::Guardar.cartel()),
                );
                clic(&mut j);
                self.fase5 = 13;
                self.cuadro5 = self.cuadro + 40;
                false
            }
            13 => {
                let n = self.notas5[N_A] as u32;
                let lugar = leer_id::<LugarDeposito>(&self.notas5);
                let guardado = lugar.as_ref().and_then(|l| l.bind().bloque()).map(|b| b.bind().restantes());
                self.chequear(
                    guardado == Some(n) && j.bind().en_mano().is_none(),
                    &format!(
                        "REQ-INT-08 / CA-INT-04 clic con \"Guardar en el estante\": el paquete se guarda con sus {n} unidades ({guardado:?})"
                    ),
                );
                if guardado.is_none() {
                    // No quedó en el estante: se lo devuelve para no romper lo que sigue.
                    if let (Some(l), Some(mut p)) = (lugar, todos::<Paquete>(&mundo).pop()) {
                        p.set_global_transform(Transform3D::new(l.get_global_basis(), l.bind().centro_zona()));
                        p.set_linear_velocity(Vector3::ZERO);
                    }
                }
                self.fase5 = 14;
                false
            }
            14 => {
                // REQ-COC-10: volcar una caja de 12 salchichas: van al agua las que entran.
                let def = catalogo().bloque("caja_salchichas_12").expect("caja de salchichas").clone();
                let mut caja = Paquete::crear(def);
                mundo.clone().add_child(&caja);
                caja.set_global_position(j.get_global_position() + Vector3::new(0.0, 1.4, 0.0));
                j.bind_mut().agarrar(caja.clone().upcast());
                let def = catalogo().producto("salchicha").expect("salchicha");
                let (media_altura, medio_ancho, _) = comida::medidas_de(def);
                let libres = h.bind().lugares_libres(medio_ancho * 2.0, media_altura * 2.0).len();
                let (al_agua, sobran) = agarre::repartir_volcado(12, libres);
                let antes: Vec<InstanceId> = todos::<Comida>(&mundo).iter().map(|c| c.instance_id()).collect();
                j.bind_mut().volcar(&h);
                let nuevas: Vec<Gd<Comida>> = todos::<Comida>(&mundo)
                    .into_iter()
                    .filter(|c| c.bind().producto() == "salchicha" && !antes.contains(&c.instance_id()))
                    .collect();
                let en_mano = j.bind().en_mano().and_then(|m| m.try_cast::<Paquete>().ok());
                let queda = en_mano.as_ref().map(|p| p.bind().restantes());
                let ok = nuevas.len() as u32 == al_agua
                    && if sobran == 0 {
                        caja.is_queued_for_deletion() && queda.is_none()
                    } else {
                        queda == Some(sobran)
                    };
                self.chequear(
                    ok,
                    &format!(
                        "REQ-COC-10 vuelco 12 con {libres} lugares libres: {} al agua y {queda:?} quedan en la mano",
                        nuevas.len()
                    ),
                );
                for mut c in nuevas {
                    c.queue_free();
                }
                if let Some(mut p) = j.bind_mut().soltar() {
                    p.queue_free();
                }
                // Deja al jugador donde estaba.
                let n = &self.notas5;
                j.set_global_position(Vector3::new(n[N_POS] as f32, n[N_POS + 1] as f32, n[N_POS + 2] as f32));
                j.set_global_rotation(Vector3::new(0.0, n[N_GIRO] as f32, 0.0));
                j.set_velocity(Vector3::ZERO);
                true
            }
            _ => true,
        }
    }
}
