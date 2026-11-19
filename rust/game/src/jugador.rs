//! SPEC-001 (jugador) y SPEC-002 (interacción y agarre).

use godot::classes::input::MouseMode;
use godot::classes::{
    Camera3D, CapsuleShape3D, CharacterBody3D, ICharacterBody3D, Input, InputEvent, InputEventKey,
    InputEventMouseButton, InputEventMouseMotion, InputMap, KinematicCollision3D, Node, ProjectSettings, RayCast3D,
    RigidBody3D,
};
use godot::global::{Key, MouseButton};
use godot::prelude::*;

use crate::aderecera::Pomo;
use crate::armado;
use crate::bloque_stock::BloqueStock;
use crate::comida::Comida;
use crate::formas;
use crate::heladera::Heladera;
use crate::hervidor::Hervidor;
use crate::hud::{self, Hud};
use crate::paquete::Paquete;
use crate::parrilla::Parrilla;
use crate::plancha::Plancha;
use crate::puerta::PuertaCarrito;
use crate::sonido;
use crate::tienda;
use carrito_core::deposito::Empaque;
use carrito_core::sonido::ids;

const VEL_CAMINAR: f32 = 3.5; // REQ-JUG-03
const VEL_CORRER: f32 = 6.0; // REQ-JUG-03
const VEL_SALTO: f32 = 4.5;
const ALTO: f32 = 1.75; // REQ-JUG-05
const RADIO: f32 = 0.3; // REQ-JUG-05
const ALTO_OJOS: f32 = 1.65; // REQ-JUG-05
/// REQ-JUG-09: escalón más alto que se sube caminando.
const ESCALON_MAX: f32 = 0.30;
const ALCANCE: f32 = 2.5; // REQ-INT-01
const DIST_MANO: f32 = 1.0; // REQ-INT-03
const RESORTE: f32 = 12.0; // REQ-INT-04
const VEL_MAX_MANO: f32 = 8.0; // REQ-INT-04
const DIST_TRABADO: f32 = 1.5; // REQ-INT-05
const VEL_TIRO: f32 = 4.0; // REQ-INT-06
const SENSIBILIDAD: f32 = 0.0025;
/// Metros entre paso y paso. REQ-SON-08
const LARGO_PASO: f32 = 1.6;

/// Lo que está bajo la mira.
pub enum Objetivo {
    Comida(Gd<Comida>),
    Hervidor(Gd<Hervidor>),
    Plancha(Gd<Plancha>),
    Parrilla(Gd<Parrilla>),
    Heladera(Gd<Heladera>),
    Bloque(Gd<BloqueStock>),
    Paquete(Gd<Paquete>),
    Pomo(Gd<Pomo>),
    Puerta(Gd<PuertaCarrito>),
}

#[derive(GodotClass)]
#[class(base=CharacterBody3D)]
pub struct Jugador {
    base: Base<CharacterBody3D>,
    camara: Option<Gd<Camera3D>>,
    rayo: Option<Gd<RayCast3D>>,
    /// Lo que tiene en la mano: comida o paquete (REQ-INT-03).
    mano: Option<Gd<RigidBody3D>>,
    segundos_en_mano: f32,
    pitch: f32,
    gravedad: f32,
    /// Metros caminados desde el último paso que sonó. REQ-SON-08
    paso_m: f32,
}

fn registrar_acciones() {
    let mut mapa = InputMap::singleton();
    for (accion, tecla) in [
        ("adelante", Key::W),
        ("atras", Key::S),
        ("izquierda", Key::A),
        ("derecha", Key::D),
        ("saltar", Key::SPACE),
        ("correr", Key::SHIFT),
        ("usar", Key::E),
        ("tiempo_rapido", Key::T),
        ("tienda", Key::TAB),
        ("armado", Key::B), // REQ-TIE-01
        ("traer_cliente", Key::C),
    ] {
        if !mapa.has_action(accion) {
            mapa.add_action(accion);
            let mut ev = InputEventKey::new_gd();
            ev.set_physical_keycode(tecla);
            mapa.action_add_event(accion, &ev);
        }
    }
}

#[godot_api]
impl ICharacterBody3D for Jugador {
    fn init(base: Base<CharacterBody3D>) -> Self {
        // Arranca mirando un poco hacia abajo, para ver el mostrador.
        let pitch = -18f32.to_radians();
        Self { base, camara: None, rayo: None, mano: None, segundos_en_mano: 0.0, pitch, gravedad: 9.8, paso_m: 0.0 }
    }

    fn ready(&mut self) {
        registrar_acciones();
        self.base_mut().add_to_group("jugador");
        self.gravedad =
            ProjectSettings::singleton().get_setting("physics/3d/default_gravity").try_to::<f64>().unwrap_or(9.8)
                as f32;

        // REQ-JUG-08 / REQ-CAR-11: si la base dice dónde aparece el jugador (ej. adentro del
        // carro kiosco), se lo pone ahí; si no, queda donde lo dejó la escena.
        let tree = self.base().get_tree();
        if let Some(c) = tree.get_first_node_in_group(crate::carrito::GRUPO)
            && let Some(p) = c.try_cast::<crate::carrito::Carrito>().ok().and_then(|c| c.bind().posicion_jugador())
        {
            self.base_mut().set_global_position(p);
        }

        // REQ-JUG-05: cápsula de 1,75 m y radio 0,3; ojos a 1,65 m.
        let mut forma = CapsuleShape3D::new_gd();
        forma.set_radius(RADIO);
        forma.set_height(ALTO);
        let col = formas::nodo_colision(
            forma.upcast(),
            Transform3D::new(Basis::IDENTITY, Vector3::new(0.0, ALTO / 2.0, 0.0)),
        );
        self.base_mut().add_child(&col);

        let mut camara = Camera3D::new_alloc();
        camara.set_position(Vector3::new(0.0, ALTO_OJOS, 0.0));
        camara.set_rotation(Vector3::new(self.pitch, 0.0, 0.0));
        camara.set_fov(75.0);
        camara.set_near(0.03);
        self.base_mut().add_child(&camara);
        camara.make_current();

        // REQ-INT-01: lo que está a 2,5 m o menos bajo la mira.
        let mut rayo = RayCast3D::new_alloc();
        rayo.set_target_position(Vector3::new(0.0, 0.0, -ALCANCE));
        let yo = self.to_gd();
        rayo.add_exception(&yo);
        camara.add_child(&rayo);

        self.camara = Some(camara);
        self.rayo = Some(rayo);
        Input::singleton().set_mouse_mode(MouseMode::CAPTURED);
    }

    fn unhandled_input(&mut self, event: Gd<InputEvent>) {
        let mut input = Input::singleton();
        let capturado = input.get_mouse_mode() == MouseMode::CAPTURED;

        if let Ok(mov) = event.clone().try_cast::<InputEventMouseMotion>() {
            if capturado {
                // REQ-JUG-02: mirar con el mouse, vertical limitado a ±85°.
                let r = mov.get_relative();
                self.base_mut().rotate_y(-r.x * SENSIBILIDAD);
                self.pitch = (self.pitch - r.y * SENSIBILIDAD).clamp(-85f32.to_radians(), 85f32.to_radians());
                let p = self.pitch;
                if let Some(c) = &mut self.camara {
                    c.set_rotation(Vector3::new(p, 0.0, 0.0));
                }
            }
        } else if let Ok(boton) = event.clone().try_cast::<InputEventMouseButton>() {
            if !boton.is_pressed() {
                return;
            }
            // REQ-JUG-07: clic captura el mouse (salvo con el panel del proveedor abierto).
            if !capturado {
                if tienda::abierta() || armado::menu_abierto() {
                    return;
                }
                input.set_mouse_mode(MouseMode::CAPTURED);
                return;
            }
            // REQ-TIE-01: en el modo armado los clics son del modo armado.
            if armado::activo() {
                return;
            }
            match boton.get_button_index() {
                MouseButton::LEFT => self.clic_izquierdo(),
                MouseButton::RIGHT => self.tirar(),
                _ => {}
            }
        } else if let Ok(tecla) = event.try_cast::<InputEventKey>() {
            // REQ-JUG-07: Esc libera el mouse.
            if tecla.is_pressed() && tecla.get_keycode() == Key::ESCAPE {
                input.set_mouse_mode(MouseMode::VISIBLE);
            }
        }
    }

    fn physics_process(&mut self, delta: f64) {
        let dt = delta as f32;
        self.mover(dt);
        // REQ-TIE-01: en el modo armado no se usa nada y el cartel es del modo armado.
        if armado::activo() {
            self.actualizar_mano(dt);
            return;
        }
        if Input::singleton().is_action_just_pressed("usar") {
            self.usar();
        }
        self.actualizar_mano(dt);
        self.actualizar_cartel();
    }
}

impl Jugador {
    /// REQ-JUG-09: prueba subir `ESCALON_MAX`, avanzar y bajar hasta apoyar. Si arriba hay techo,
    /// si sigue chocando (es una pared) o si no hay piso, no hace nada.
    fn subir_escalon(&mut self, avance: Vector3) {
        let t = self.base().get_global_transform();
        let arriba = Vector3::UP * ESCALON_MAX;
        if self.base_mut().test_move(t, arriba) {
            return;
        }
        // Avanza lo suficiente para apoyar arriba del borde (no en la punta), sin pasar el radio.
        let paso = avance.normalized() * avance.length().max(RADIO * 0.66);
        let t_arriba = t.translated(arriba);
        if self.base_mut().test_move(t_arriba, paso) {
            return;
        }
        let t_adelante = t_arriba.translated(paso);
        let col = KinematicCollision3D::new_gd();
        if !self.base_mut().test_move_ex(t_adelante, -arriba).collision(&col).done() {
            return;
        }
        let bajada = col.get_travel();
        if (arriba + bajada).y < 0.02 || col.get_normal().y < 0.7 {
            return;
        }
        self.base_mut().set_global_position(t_adelante.origin + bajada);
    }

    fn mover(&mut self, dt: f32) {
        let input = Input::singleton();
        let mut v = self.base().get_velocity();

        // REQ-JUG-04: gravedad del proyecto; salto solo apoyado.
        if !self.base().is_on_floor() {
            v.y -= self.gravedad * dt;
        } else if input.is_action_just_pressed("saltar") {
            v.y = VEL_SALTO;
        }

        // REQ-JUG-01: WASD relativo a hacia dónde mira; REQ-JUG-03: correr con Shift.
        let ejes = input.get_vector("izquierda", "derecha", "adelante", "atras");
        let basis = self.base().get_global_transform().basis;
        let mut dir = basis * Vector3::new(ejes.x, 0.0, ejes.y);
        dir.y = 0.0;
        let vel = if input.is_action_pressed("correr") { VEL_CORRER } else { VEL_CAMINAR };
        if dir.length() > 0.01 {
            let dir = dir.normalized();
            v.x = dir.x * vel;
            v.z = dir.z * vel;
        } else {
            v.x = 0.0;
            v.z = 0.0;
        }
        let apoyado = self.base().is_on_floor();
        self.base_mut().set_velocity(v);
        self.base_mut().move_and_slide();
        // REQ-JUG-09: si choca de frente con un borde bajo (escalón), sube a ese nivel.
        if apoyado && self.base().is_on_wall() && dir.length() > 0.01 {
            self.subir_escalon(Vector3::new(v.x, 0.0, v.z) * dt);
        }

        // REQ-SON-08: un paso cada tanto caminado, solo apoyado en el piso.
        let horizontal = Vector2::new(v.x, v.z).length();
        if self.base().is_on_floor() && horizontal > 0.5 {
            self.paso_m += horizontal * dt;
            if self.paso_m >= LARGO_PASO {
                self.paso_m = 0.0;
                sonido::sonar(&self.to_gd(), ids::PASOS_JUGADOR);
            }
        } else if horizontal <= 0.5 {
            self.paso_m = LARGO_PASO * 0.6;
        }

        // REQ-JUG-06: empuja suavemente los objetos con física que toca.
        let n = self.base().get_slide_collision_count();
        for i in 0..n {
            let Some(choque) = self.base_mut().get_slide_collision(i) else { continue };
            let Some(obj) = choque.get_collider() else { continue };
            if let Ok(mut cuerpo) = obj.try_cast::<RigidBody3D>() {
                let normal = choque.get_normal();
                let impulso = -normal * cuerpo.get_mass() * 0.6;
                cuerpo.apply_central_impulse(Vector3::new(impulso.x, 0.0, impulso.z));
            }
        }
    }

    /// REQ-INT-01
    pub fn objetivo(&mut self) -> Option<Objetivo> {
        let rayo = self.rayo.as_mut()?;
        rayo.force_raycast_update();
        if !rayo.is_colliding() {
            return None;
        }
        let mut nodo: Option<Gd<Node>> = rayo.get_collider()?.try_cast::<Node>().ok();
        // El objeto puede ser el cuerpo físico o un hijo de un equipo: se sube hasta 4 niveles.
        for _ in 0..4 {
            let n = nodo?;
            let n = match n.try_cast::<Comida>() {
                Ok(c) => return Some(Objetivo::Comida(c)),
                Err(n) => n,
            };
            let n = match n.try_cast::<Hervidor>() {
                Ok(h) => return Some(Objetivo::Hervidor(h)),
                Err(n) => n,
            };
            let n = match n.try_cast::<Plancha>() {
                Ok(p) => return Some(Objetivo::Plancha(p)),
                Err(n) => n,
            };
            let n = match n.try_cast::<Parrilla>() {
                Ok(p) => return Some(Objetivo::Parrilla(p)),
                Err(n) => n,
            };
            let n = match n.try_cast::<Heladera>() {
                Ok(h) => return Some(Objetivo::Heladera(h)),
                Err(n) => n,
            };
            let n = match n.try_cast::<BloqueStock>() {
                Ok(b) => return Some(Objetivo::Bloque(b)),
                Err(n) => n,
            };
            let n = match n.try_cast::<Paquete>() {
                Ok(p) => return Some(Objetivo::Paquete(p)),
                Err(n) => n,
            };
            let n = match n.try_cast::<Pomo>() {
                Ok(p) => return Some(Objetivo::Pomo(p)),
                Err(n) => n,
            };
            let n = match n.try_cast::<PuertaCarrito>() {
                Ok(p) => return Some(Objetivo::Puerta(p)),
                Err(n) => n,
            };
            nodo = n.get_parent();
        }
        None
    }

    fn clic_izquierdo(&mut self) {
        if self.mano.is_some() {
            // REQ-INT-06: soltar.
            self.soltar();
            return;
        }
        // REQ-INT-03, REQ-PRO-05: agarrar comida o paquetes.
        match self.objetivo() {
            Some(Objetivo::Comida(c)) => self.agarrar(c.upcast()),
            Some(Objetivo::Paquete(p)) => self.agarrar(p.upcast()),
            _ => {}
        }
    }

    fn marcar(cuerpo: &Gd<RigidBody3D>, sostenido: bool) {
        if let Ok(mut c) = cuerpo.clone().try_cast::<Comida>() {
            c.bind_mut().sostenida = sostenido;
        } else if let Ok(mut p) = cuerpo.clone().try_cast::<Paquete>() {
            p.bind_mut().sostenido = sostenido;
        }
    }

    pub fn agarrar(&mut self, mut c: Gd<RigidBody3D>) {
        Self::marcar(&c, true);
        c.set_gravity_scale(0.0);
        if let Some(r) = &mut self.rayo {
            r.add_exception(&c);
        }
        self.segundos_en_mano = 0.0;
        self.mano = Some(c);
        // REQ-SON-08
        sonido::sonar(&self.to_gd(), ids::AGARRAR);
    }

    pub fn soltar(&mut self) -> Option<Gd<RigidBody3D>> {
        let c = self.soltar_en_silencio()?;
        // REQ-SON-08
        sonido::sonar(&self.to_gd(), ids::SOLTAR);
        Some(c)
    }

    fn soltar_en_silencio(&mut self) -> Option<Gd<RigidBody3D>> {
        let mut c = self.mano.take()?;
        if !c.is_instance_valid() {
            return None;
        }
        Self::marcar(&c, false);
        c.set_gravity_scale(1.0);
        if let Some(r) = &mut self.rayo {
            r.remove_exception(&c);
        }
        Some(c)
    }

    /// REQ-INT-06: tirar hacia adelante.
    fn tirar(&mut self) {
        let adelante = self.adelante();
        if let Some(mut c) = self.soltar_en_silencio() {
            c.set_linear_velocity(adelante * VEL_TIRO);
            // REQ-SON-08
            sonido::sonar(&self.to_gd(), ids::TIRAR);
        }
    }

    fn adelante(&self) -> Vector3 {
        self.camara.as_ref().map(|c| -c.get_global_transform().basis.col_c()).unwrap_or(Vector3::FORWARD)
    }

    fn comida_en_mano(&self) -> Option<Gd<Comida>> {
        self.mano.as_ref().filter(|c| c.is_instance_valid()).and_then(|c| c.clone().try_cast::<Comida>().ok())
    }

    /// REQ-INT-07: E usa el objetivo.
    pub fn usar(&mut self) {
        let yo = self.to_gd();
        if self.mano.is_some() {
            // Con algo en la mano, solo se usan los pomos de aderezo (SPEC-012).
            let Some(mut comida) = self.comida_en_mano() else { return };
            // REQ-PAR-01: una bolsa de carbón en la mano se vuelca en la parrilla.
            let carbon = comida.bind().carbon();
            if let (Some(kg), Some(Objetivo::Parrilla(mut parrilla))) = (carbon, self.objetivo()) {
                match parrilla.bind_mut().cargar(kg) {
                    Ok(()) => {
                        self.soltar();
                        comida.queue_free();
                    }
                    Err(e) => hud::avisar(&yo, e.mensaje()),
                }
                return;
            }
            let Some(Objetivo::Pomo(mut pomo)) = self.objetivo() else { return };
            let repone = comida.bind().repone().map(str::to_string);
            let resultado = match repone {
                // REQ-ADE-05: recargar con un repuesto (que se gasta).
                Some(a) => pomo.bind_mut().recargar(&a).map(|_| {
                    self.soltar();
                    comida.queue_free();
                }),
                // REQ-ADE-03
                None => pomo.bind_mut().aplicar(&mut comida),
            };
            if let Err(e) = resultado {
                hud::avisar(&yo, e.mensaje());
            }
            return;
        }
        match self.objetivo() {
            Some(Objetivo::Hervidor(mut h)) => h.bind_mut().alternar(),
            // REQ-PLA-01
            Some(Objetivo::Plancha(mut p)) => p.bind_mut().alternar(),
            // REQ-HEL-01
            Some(Objetivo::Heladera(mut h)) => h.bind_mut().alternar(),
            // REQ-CAR-13
            Some(Objetivo::Puerta(mut p)) => p.bind_mut().alternar(),
            // REQ-PAR-01
            Some(Objetivo::Parrilla(mut p)) => {
                if let Err(e) = p.bind_mut().usar() {
                    hud::avisar(&yo, e.mensaje());
                }
            }
            // REQ-PLA-07: E sobre una hamburguesa suelta la da vuelta.
            Some(Objetivo::Comida(mut c)) if c.bind().por_lados() => c.bind_mut().dar_vuelta(),
            Some(Objetivo::Bloque(mut b)) => {
                // REQ-HEL-06: lo que sale del paquete conserva la temperatura del paquete.
                let temp = b.bind().temperatura();
                let empaque = b.bind().empaque();
                let sacado = b.bind_mut().sacar();
                if let Some((producto, pos)) = sacado {
                    // REQ-SON-08: bolsa o caja de cartón según el empaque.
                    let id = if empaque == Empaque::Bolsa { ids::SACAR_BOLSA } else { ids::SACAR_CAJA };
                    sonido::sonar_en(&self.to_gd(), id, pos);
                    // REQ-DEP-05: aparece como objeto físico en la mano.
                    let mut c = Comida::crear(&producto);
                    c.bind_mut().fijar_temperatura(temp);
                    c.set_position(pos);
                    if let Some(mut padre) = self.base().get_parent() {
                        padre.add_child(&c);
                    }
                    c.set_global_position(pos);
                    self.agarrar(c.upcast());
                }
            }
            _ => {}
        }
    }

    /// REQ-INT-03, REQ-INT-04, REQ-INT-05
    fn actualizar_mano(&mut self, dt: f32) {
        let Some(c) = &self.mano else { return };
        if !c.is_instance_valid() || c.is_queued_for_deletion() {
            self.mano = None;
            return;
        }
        let Some(camara) = &self.camara else { return };
        let t = camara.get_global_transform();
        let destino = t.origin - t.basis.col_c() * DIST_MANO;
        let mut c = c.clone();
        let diferencia = destino - c.get_global_position();

        self.segundos_en_mano += dt;
        if self.segundos_en_mano > 0.5 && diferencia.length() > DIST_TRABADO {
            self.soltar();
            return;
        }
        let mut v = diferencia * RESORTE;
        if v.length() > VEL_MAX_MANO {
            v = v.normalized() * VEL_MAX_MANO;
        }
        c.set_linear_velocity(v);
        let giro = c.get_angular_velocity();
        c.set_angular_velocity(giro * 0.8);
    }

    /// REQ-INT-02, REQ-INT-08
    fn actualizar_cartel(&mut self) {
        let en_mano = self.mano.clone().filter(|c| c.is_instance_valid() && !c.is_queued_for_deletion());
        let objetivo = self.objetivo();
        let texto = if let Some(m) = en_mano {
            if let Ok(c) = m.clone().try_cast::<Comida>() {
                let c = c.bind();
                let mut t = format!("{}\n[Clic] Soltar · [Clic der.] Tirar", c.descripcion());
                if let (Some(_), Some(Objetivo::Parrilla(_))) = (c.carbon(), &objetivo) {
                    t += " · [E] Cargar carbón en la parrilla";
                }
                if let Some(Objetivo::Pomo(p)) = &objetivo {
                    let p = p.bind();
                    if c.repone().is_some() {
                        t += &format!(" · [E] Recargar {}", p.cartel());
                    } else if c.admite_aderezos() {
                        t += &format!(" · [E] Poner {}", p.cartel());
                    }
                }
                t
            } else if let Ok(p) = m.try_cast::<Paquete>() {
                format!(
                    "{}\nDejalo en un lugar libre del estante · [Clic] Soltar · [Clic der.] Tirar",
                    p.bind().descripcion()
                )
            } else {
                String::new()
            }
        } else {
            match objetivo {
                Some(Objetivo::Comida(c)) => {
                    let mut t = format!("[Clic] Agarrar {}", c.bind().descripcion().to_lowercase());
                    if c.bind().por_lados() {
                        t += " · [E] Dar vuelta";
                    }
                    t
                }
                Some(Objetivo::Hervidor(h)) => h.bind().cartel(),
                Some(Objetivo::Plancha(p)) => p.bind().cartel(),
                Some(Objetivo::Parrilla(p)) => p.bind().cartel(),
                Some(Objetivo::Heladera(h)) => h.bind().cartel(),
                Some(Objetivo::Puerta(p)) => p.bind().cartel(),
                Some(Objetivo::Bloque(b)) => b.bind().cartel(),
                Some(Objetivo::Paquete(p)) => format!("[Clic] Agarrar {}", p.bind().descripcion().to_lowercase()),
                Some(Objetivo::Pomo(p)) => format!("{} — agarrá un pancho y apretá E para ponerle", p.bind().cartel()),
                None => String::new(),
            }
        };
        let arbol = self.base().get_tree();
        if let Some(n) = arbol.get_first_node_in_group(hud::GRUPO)
            && let Ok(mut h) = n.try_cast::<Hud>()
        {
            h.bind_mut().set_cartel(&texto);
        }
    }
}
