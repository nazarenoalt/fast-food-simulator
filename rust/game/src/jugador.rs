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
use crate::cartel::CartelCerrado;
use crate::comida::{self, Comida};
use crate::datos::catalogo;
use crate::formas;
use crate::freidora::{self, Colador, Freidora};
use crate::heladera::Heladera;
use crate::hervidor::Hervidor;
use crate::hud::{self, Hud};
use crate::lugar_deposito::{self, LugarDeposito};
use crate::paquete::Paquete;
use crate::parrilla::Parrilla;
use crate::plancha::Plancha;
use crate::preparar;
use crate::puerta::PuertaCarrito;
use crate::sonido;
use crate::tienda;
use carrito_core::agarre;
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
const RESORTE: f32 = 20.0; // REQ-INT-04
const VEL_MAX_MANO: f32 = 12.0; // REQ-INT-04
/// REQ-INT-04: qué tan rápido gira hacia el giro de la cámara (1/s) y tope (rad/s).
const RESORTE_GIRO: f32 = 15.0;
const GIRO_MAX_MANO: f32 = 20.0;
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
    Cartel(Gd<CartelCerrado>),
    Freidora(Gd<Freidora>), // REQ-FRE-05
}

/// REQ-INT-08/09/10: qué pasa al colocar lo que tenés en la mano donde apunta la mira.
enum Colocacion {
    Apoyar,
    Pared,
    /// Sobre una base de armado (nombre de la base).
    Armar(String),
    Guardar,
    /// REQ-FRE-07: papas adentro del colador, o apoyadas como siempre si está lleno.
    Colador(Gd<Colador>),
    ColadorLleno,
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
    /// REQ-INT-03: lo agarrado estaba dado vuelta (se respeta al sostenerlo y al colocarlo).
    volteado: bool,
    /// REQ-INT-09: rayo de la cámara a un lugar del depósito (para ver que no haya nada en medio).
    rayo_lugar: Option<Gd<RayCast3D>>,
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
        Self {
            base,
            camara: None,
            rayo: None,
            mano: None,
            segundos_en_mano: 0.0,
            volteado: false,
            rayo_lugar: None,
            pitch,
            gravedad: 9.8,
            paso_m: 0.0,
        }
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
        rayo.set_collision_mask(1 | formas::CAPA_USABLES); // REQ-CLI-13: también el cartel
        let yo = self.to_gd();
        rayo.add_exception(&yo);
        camara.add_child(&rayo);
        let mut rayo_lugar = RayCast3D::new_alloc();
        rayo_lugar.add_exception(&yo);
        rayo_lugar.set_enabled(false);
        camara.add_child(&rayo_lugar);

        self.camara = Some(camara);
        self.rayo = Some(rayo);
        self.rayo_lugar = Some(rayo_lugar);
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
        } else if input.is_action_just_pressed("saltar") && !armado::escribiendo() {
            v.y = VEL_SALTO;
        }

        // REQ-JUG-01: WASD relativo a hacia dónde mira; REQ-JUG-03: correr con Shift.
        // REQ-LOG-07: mientras se escribe el nombre del puesto, las teclas no lo mueven.
        let ejes = if armado::escribiendo() {
            Vector2::ZERO
        } else {
            input.get_vector("izquierda", "derecha", "adelante", "atras")
        };
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

    /// Solo para pruebas: gira el cuerpo y la cámara para que la mira apunte a `punto`.
    pub fn apuntar_a(&mut self, punto: Vector3) {
        let ojos = self.base().get_global_position() + Vector3::new(0.0, ALTO_OJOS, 0.0);
        let d = punto - ojos;
        let horizontal = Vector2::new(d.x, d.z).length();
        self.base_mut().set_global_rotation(Vector3::new(0.0, (-d.x).atan2(-d.z), 0.0));
        self.pitch = d.y.atan2(horizontal).clamp(-85f32.to_radians(), 85f32.to_radians());
        let p = self.pitch;
        if let Some(c) = &mut self.camara {
            c.set_rotation(Vector3::new(p, 0.0, 0.0));
        }
    }

    /// Lo que tiene en la mano (para pruebas).
    pub fn en_mano(&self) -> Option<Gd<RigidBody3D>> {
        self.mano.clone().filter(|c| c.is_instance_valid())
    }

    /// REQ-INT-01
    pub fn objetivo(&mut self) -> Option<Objetivo> {
        let rayo = self.rayo.as_mut()?;
        rayo.force_raycast_update();
        if !rayo.is_colliding() {
            return None;
        }
        let mut nodo: Option<Gd<Node>> = rayo.get_collider()?.try_cast::<Node>().ok();
        let punto = rayo.get_collision_point();
        // El objeto puede ser el cuerpo físico o un hijo de un equipo: se sube hasta 4 niveles.
        for _ in 0..4 {
            let n = nodo?;
            let n = match n.try_cast::<Comida>() {
                // REQ-FRE-08: en un colador, la porción de papas que mira.
                Ok(c) => return Some(Objetivo::Comida(freidora::agarrable_en(c, punto))),
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
            let n = match n.try_cast::<CartelCerrado>() {
                Ok(c) => return Some(Objetivo::Cartel(c)),
                Err(n) => n,
            };
            let n = match n.try_cast::<Freidora>() {
                Ok(f) => return Some(Objetivo::Freidora(f)),
                Err(n) => n,
            };
            nodo = n.get_parent();
        }
        None
    }

    /// Punto donde toca la mira (el del último objetivo). REQ-FRE-05
    fn punto_mira(&self) -> Option<Vector3> {
        self.rayo.as_ref().filter(|r| r.is_colliding()).map(|r| r.get_collision_point())
    }

    /// REQ-INT-03, REQ-INT-06 (y REQ-CLI-13): agarrar, colocar o usar el cartel.
    pub fn clic_izquierdo(&mut self) {
        if self.mano.is_some() {
            // REQ-INT-06: colocar donde apunta la mira.
            self.colocar();
            return;
        }
        // REQ-INT-03, REQ-PRO-05: agarrar comida o paquetes; REQ-DEP-09: o levantar un bloque.
        match self.objetivo() {
            Some(Objetivo::Comida(c)) => self.agarrar(c.upcast()),
            Some(Objetivo::Paquete(p)) => self.agarrar(p.upcast()),
            Some(Objetivo::Bloque(b)) => self.levantar(b),
            // REQ-CLI-13: con la mano libre, el clic saca o cuelga el cartel, igual que E.
            Some(Objetivo::Cartel(mut c)) => c.bind_mut().alternar(),
            _ => {}
        }
    }

    /// REQ-DEP-09: el bloque del depósito pasa a ser un paquete en la mano, con lo que le queda.
    pub fn levantar(&mut self, mut bloque: Gd<BloqueStock>) {
        if bloque.is_queued_for_deletion() {
            return;
        }
        let (def, restantes, temp) = {
            let b = bloque.bind();
            (b.def().clone(), b.restantes(), b.temperatura())
        };
        let alto = def.tamano()[1];
        let t = bloque.get_global_transform();
        // El bloque se dibuja con la base en su origen; el paquete está centrado.
        let t = Transform3D::new(t.basis.orthonormalized(), t.origin + t.basis.col_b().normalized() * (alto / 2.0));
        bloque.queue_free();
        let mut p = Paquete::crear_con(def, restantes, temp);
        if let Some(mut padre) = self.base().get_parent() {
            padre.add_child(&p);
        }
        p.set_global_transform(t);
        self.agarrar(p.upcast());
    }

    /// REQ-INT-03, REQ-INT-09: (media altura, medio ancho, media medida mayor) de lo agarrable.
    fn medidas(cuerpo: &Gd<RigidBody3D>) -> (f32, f32, f32) {
        if let Ok(c) = cuerpo.clone().try_cast::<Comida>() {
            return c.bind().medidas();
        }
        if let Ok(p) = cuerpo.clone().try_cast::<Paquete>() {
            let [x, y, z] = p.bind().def().tamano();
            return (y / 2.0, x.max(z) / 2.0, x.max(y).max(z) / 2.0);
        }
        (0.05, 0.05, 0.05)
    }

    /// Giro con el que queda lo colocado: derecho, mirando hacia donde mira el jugador
    /// (y dado vuelta si lo estaba). REQ-INT-09
    fn giro_colocado(&self) -> Basis {
        let giro = self.base().get_global_transform().basis.orthonormalized();
        if self.volteado { giro * Basis::from_axis_angle(Vector3::RIGHT, std::f32::consts::PI) } else { giro }
    }

    /// REQ-INT-09, REQ-INT-10: dónde y cómo quedaría lo que tenés en la mano si hacés clic.
    fn destino_colocar(&mut self) -> Option<(Transform3D, Colocacion)> {
        let mano = self.mano.clone().filter(|c| c.is_instance_valid())?;
        let rayo = self.rayo.as_mut()?;
        // REQ-CLI-13: colocar no ve la zona del cartel de cerrado (es solo para usarlo).
        rayo.set_collision_mask(1);
        rayo.force_raycast_update();
        let choque =
            rayo.is_colliding().then(|| (rayo.get_collision_point(), rayo.get_collision_normal(), rayo.get_collider()));
        rayo.set_collision_mask(1 | formas::CAPA_USABLES);
        let (punto, normal, tocado) = choque?;
        let v3 = |v: Vector3| [v.x, v.y, v.z];

        // REQ-FRE-07: papas sobre un colador van adentro (lleno, se apoyan como siempre).
        let colador =
            mano.clone().try_cast::<Comida>().ok().and_then(|c| freidora::colador_destino(&c, tocado.clone()));
        if let Some(Ok(col)) = colador {
            // El origen es donde toca la mira: la porción va al lugar libre más cercano.
            return Some((Transform3D::new(Basis::IDENTITY, punto), Colocacion::Colador(col)));
        }
        let lleno = colador.is_some();

        // REQ-INT-10: un agregado sobre su base va a la zona de encastre.
        if let Ok(comida) = mano.clone().try_cast::<Comida>()
            && let Some(base) = tocado.and_then(|o| o.try_cast::<Comida>().ok())
        {
            let producto = comida.bind().producto().to_string();
            if let Some(pos) = base.bind().encastre_para(&producto) {
                let t = Transform3D::new(base.get_global_transform().basis.orthonormalized(), pos);
                return Some((t, Colocacion::Armar(base.bind().nombre().to_string())));
            }
        }
        let (media_altura, medio_ancho, _) = Self::medidas(&mano);

        // REQ-INT-09: un paquete cerca de un lugar libre (y a la vista) va centrado ahí.
        if mano.clone().try_cast::<Paquete>().is_ok() {
            let libres: Vec<Gd<LugarDeposito>> = self
                .base()
                .get_tree()
                .get_nodes_in_group(lugar_deposito::GRUPO)
                .iter_shared()
                .filter_map(|n| n.try_cast::<LugarDeposito>().ok())
                .filter(|l| !l.bind().ocupado())
                .collect();
            let posiciones: Vec<[f32; 3]> = libres.iter().map(|l| v3(l.get_global_position())).collect();
            if let Some(i) = agarre::lugar_cercano(v3(punto), &posiciones)
                && self.a_la_vista(&libres[i])
            {
                let tl = libres[i].get_global_transform();
                let b = tl.basis.orthonormalized();
                let t = Transform3D::new(b, tl.origin + b.col_b() * (media_altura + agarre::HOLGURA));
                return Some((t, Colocacion::Guardar));
            }
        }

        let c = agarre::centro_colocado(v3(punto), v3(normal), media_altura, medio_ancho);
        let como = if lleno {
            Colocacion::ColadorLleno
        } else if agarre::es_apoyo(v3(normal)) {
            Colocacion::Apoyar
        } else {
            Colocacion::Pared
        };
        Some((Transform3D::new(self.giro_colocado(), Vector3::new(c[0], c[1], c[2])), como))
    }

    /// REQ-INT-09: no hay nada entre los ojos y el lugar (una puerta cerrada, un cajón).
    fn a_la_vista(&mut self, lugar: &Gd<LugarDeposito>) -> bool {
        let destino = lugar.bind().centro_zona();
        let (Some(camara), Some(rayo)) = (&self.camara, &mut self.rayo_lugar) else { return false };
        let local = camara.get_global_transform().affine_inverse() * destino;
        rayo.set_target_position(local);
        rayo.force_raycast_update();
        !rayo.is_colliding() || rayo.get_collision_point().distance_to(destino) < 0.15
    }

    /// REQ-INT-06, REQ-INT-09, REQ-INT-10: deja lo de la mano donde apunta la mira (o lo suelta).
    pub fn colocar(&mut self) {
        let destino = self.destino_colocar();
        let Some(mut c) = self.soltar() else { return };
        // REQ-FRE-07: adentro del colador.
        if let Some((t, Colocacion::Colador(col))) = &destino
            && let Ok(papa) = c.clone().try_cast::<Comida>()
        {
            if let Err(e) = col.clone().bind_mut().meter(papa, Some(t.origin)) {
                hud::avisar(&self.to_gd(), e.mensaje());
            }
            return;
        }
        if let Some((t, _)) = destino {
            c.set_global_transform(t);
            c.set_linear_velocity(Vector3::ZERO);
            c.set_angular_velocity(Vector3::ZERO);
        }
    }

    /// REQ-COC-10: vuelca todas las unidades del paquete de la mano en el agua del hervidor.
    pub fn volcar(&mut self, hervidor: &Gd<Hervidor>) {
        let Some(paquete) = self.mano.clone().and_then(|m| m.try_cast::<Paquete>().ok()) else { return };
        let (producto, n, temp) = {
            let p = paquete.bind();
            (p.def().producto.clone(), p.restantes(), p.temp)
        };
        let yo = self.to_gd();
        if !Comida::va_al_hervidor(&producto) {
            hud::avisar(&yo, "Eso no se cocina en el agua");
            return;
        }
        let Some(mut padre) = self.base().get_parent() else { return };
        let Some(def) = catalogo().producto(&producto) else { return };
        let (media_altura, medio_ancho, _) = comida::medidas_de(def);
        for t in hervidor.bind().lugares_volcado(n, medio_ancho * 2.0, media_altura * 2.0) {
            let mut c = Comida::crear(&producto);
            c.bind_mut().fijar_temperatura(temp);
            padre.add_child(&c);
            c.set_global_transform(t);
        }
        if let Some(mut p) = self.soltar_en_silencio() {
            p.queue_free();
        }
        sonido::sonar_en(&yo, ids::SOLTAR, hervidor.get_global_position());
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
        // REQ-INT-03: no choca con el jugador (va pegado a la cámara).
        let yo = self.to_gd().upcast::<Node>();
        c.add_collision_exception_with(&yo);
        self.volteado = c.get_global_transform().basis.col_b().y < 0.0;
        if let Some(r) = &mut self.rayo {
            r.add_exception(&c);
        }
        if let Some(r) = &mut self.rayo_lugar {
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
        let yo = self.to_gd().upcast::<Node>();
        c.remove_collision_exception_with(&yo);
        if let Some(r) = &mut self.rayo {
            r.remove_exception(&c);
        }
        if let Some(r) = &mut self.rayo_lugar {
            r.remove_exception(&c);
        }
        Some(c)
    }

    /// REQ-INT-06: tirar hacia adelante.
    fn tirar(&mut self) {
        // REQ-INT-06: hacia donde apunta la mira (lo de la mano está corrido a la derecha).
        let mut direccion = self.adelante();
        if let (Some(rayo), Some(c)) = (&mut self.rayo, &self.mano)
            && c.is_instance_valid()
        {
            rayo.force_raycast_update();
            if rayo.is_colliding() {
                let d = rayo.get_collision_point() - c.get_global_position();
                if d.length() > 0.05 {
                    direccion = d.normalized();
                }
            }
        }
        if let Some(mut c) = self.soltar_en_silencio() {
            c.set_linear_velocity(direccion * VEL_TIRO);
            // REQ-SON-08
            sonido::sonar(&self.to_gd(), ids::TIRAR);
        }
    }

    fn adelante(&self) -> Vector3 {
        self.camara.as_ref().map(|c| -c.get_global_transform().basis.col_c()).unwrap_or(Vector3::FORWARD)
    }

    fn paquete_en_mano(&self) -> Option<Gd<Paquete>> {
        self.mano.as_ref().filter(|c| c.is_instance_valid()).and_then(|c| c.clone().try_cast::<Paquete>().ok())
    }

    fn comida_en_mano(&self) -> Option<Gd<Comida>> {
        self.mano.as_ref().filter(|c| c.is_instance_valid()).and_then(|c| c.clone().try_cast::<Comida>().ok())
    }

    /// REQ-INT-07: E usa el objetivo.
    pub fn usar(&mut self) {
        let yo = self.to_gd();
        if self.mano.is_some() {
            // REQ-COC-10: un paquete sobre el hervidor se vuelca en el agua.
            if self.paquete_en_mano().is_some() {
                if let Some(Objetivo::Hervidor(h)) = self.objetivo() {
                    self.volcar(&h);
                }
                return;
            }
            // Con comida en la mano: pomos de aderezo (SPEC-012) y carbón en la parrilla.
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
            // REQ-FRE-01..03: pelar o cortar con la herramienta de la mano.
            let herramienta = comida.bind().producto().to_string();
            if let Some(Objetivo::Comida(c)) = self.objetivo()
                && preparar::usar(Some(&herramienta), c)
            {
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
            // REQ-FRE-05: la cuba bajo la mira.
            Some(Objetivo::Freidora(mut f)) => {
                if let Some(p) = self.punto_mira() {
                    f.bind_mut().alternar_en(p);
                }
            }
            // REQ-FRE-08: E sobre un colador puesto en una cuba lo baja o lo sube.
            Some(Objetivo::Comida(c)) if freidora::alternar_colador(&c) => {}
            // REQ-PLA-01
            Some(Objetivo::Plancha(mut p)) => p.bind_mut().alternar(),
            // REQ-HEL-01
            Some(Objetivo::Heladera(mut h)) => h.bind_mut().alternar(),
            // REQ-CAR-13
            Some(Objetivo::Puerta(mut p)) => p.bind_mut().alternar(),
            // REQ-CLI-13
            Some(Objetivo::Cartel(mut c)) => c.bind_mut().alternar(),
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
        let mut c = c.clone();
        // REQ-INT-03: abajo a la derecha de la vista, cerca.
        let (_, _, medio) = Self::medidas(&c);
        let [x, y, z] = agarre::punto_mano(medio);
        let destino = t * Vector3::new(x, y, z);
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
        // REQ-INT-04: el giro va hacia el de la cámara (dado vuelta si lo estaba), como resorte.
        let mut objetivo = t.basis.orthonormalized();
        if self.volteado {
            objetivo = objetivo * Basis::from_axis_angle(Vector3::RIGHT, std::f32::consts::PI);
        }
        let actual = c.get_global_transform().basis.orthonormalized().get_quaternion();
        let mut q = (objetivo.get_quaternion() * actual.inverse()).normalized();
        if q.w < 0.0 {
            q = -q; // el camino corto
        }
        let angulo = q.get_angle();
        let w = if angulo > 1e-3 {
            q.get_axis().normalized() * (angulo * RESORTE_GIRO).min(GIRO_MAX_MANO)
        } else {
            Vector3::ZERO
        };
        c.set_angular_velocity(w);
    }

    /// REQ-INT-02, REQ-INT-08
    fn actualizar_cartel(&mut self) {
        let en_mano = self.mano.clone().filter(|c| c.is_instance_valid() && !c.is_queued_for_deletion());
        // REQ-INT-08: qué hace el clic con lo que tenés en la mano, ahí donde apuntás.
        let clic = match en_mano.as_ref().and_then(|_| self.destino_colocar()) {
            None => "[Clic] Soltar".to_string(),
            Some((_, Colocacion::Apoyar)) => "[Clic] Apoyar acá".to_string(),
            Some((_, Colocacion::Pared)) => "[Clic] Dejar acá".to_string(),
            Some((_, Colocacion::Armar(base))) => format!("[Clic] Poner en el {base}"),
            Some((_, Colocacion::Guardar)) => "[Clic] Guardar en el estante".to_string(),
            Some((_, Colocacion::Colador(_))) => "[Clic] Poner en el colador".to_string(),
            Some((_, Colocacion::ColadorLleno)) => "[Clic] Apoyar acá (el colador está lleno)".to_string(),
        };
        let mano_ocupada = en_mano.is_some();
        let objetivo = self.objetivo();
        let texto = if let Some(m) = en_mano {
            if let Ok(c) = m.clone().try_cast::<Comida>() {
                let c = c.bind();
                let mut t = format!("{}\n{} · [Clic der.] Tirar", c.descripcion(), clic);
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
                if let Some(Objetivo::Comida(o)) = &objetivo {
                    t += &preparar::cartel(Some(c.producto()), o); // REQ-FRE-01..03
                }
                t
            } else if let Ok(p) = m.try_cast::<Paquete>() {
                let p = p.bind();
                let mut t = format!("{}\n{} · [Clic der.] Tirar", p.descripcion(), clic);
                // REQ-COC-10
                if let Some(Objetivo::Hervidor(_)) = &objetivo
                    && Comida::va_al_hervidor(&p.def().producto)
                {
                    let nombre = catalogo().producto(&p.def().producto).map(|d| d.nombre.clone()).unwrap_or_default();
                    t += &format!(" · [E] Echar al agua ({} × {nombre})", p.restantes());
                }
                t
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
                    t += &preparar::cartel(None, &c); // REQ-FRE-03: sin la herramienta
                    // REQ-FRE-08
                    if let Some(e) = freidora::cartel_colador(&c) {
                        t += &format!(" · {e}");
                    }
                    t
                }
                Some(Objetivo::Hervidor(h)) => h.bind().cartel(),
                Some(Objetivo::Plancha(p)) => p.bind().cartel(),
                Some(Objetivo::Parrilla(p)) => p.bind().cartel(),
                Some(Objetivo::Heladera(h)) => h.bind().cartel(),
                Some(Objetivo::Puerta(p)) => p.bind().cartel(),
                Some(Objetivo::Cartel(c)) => c.bind().cartel(),
                Some(Objetivo::Freidora(f)) => self.punto_mira().map(|p| f.bind().cartel(p)).unwrap_or_default(),
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
            h.bind_mut().set_mano_ocupada(mano_ocupada); // REQ-INT-01
        }
    }
}
