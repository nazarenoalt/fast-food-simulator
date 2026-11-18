//! SPEC-024 · Nodo central de audio: buses, sonidos 2D y 3D, ambiente según la hora.
//! Las reglas viven en `carrito_core::sonido`; acá solo se conectan con el motor.

use std::collections::HashMap;

use carrito_core::azar::Azar;
use carrito_core::sonido::{
    Bus, DefSonido, Enfriador, Entorno, Mezcla, capas_ambiente, elegir_variante, ganancia_distancia, ids, lineal_a_db,
};
use godot::classes::{
    AudioServer, AudioStream, AudioStreamOggVorbis, AudioStreamPlayer, AudioStreamPlayer3D, FileAccess, INode, Input,
    InputEventKey, InputMap, Node3D, ResourceLoader, Time, audio_stream_player_3d::AttenuationModel,
};
use godot::global::Key;
use godot::prelude::*;

use crate::dia_noche::{self, DiaNoche};
use crate::gente::{self, Gente};
use crate::util;

pub const GRUPO: &str = "sonido";
const CARPETA: &str = "res://audio/";
/// Segundos que tarda un fundido de ambiente.
const FUNDIDO_S: f32 = 1.5;

/// Un sonido que dura mientras su dueño lo pide (hervor, chisporroteo...). REQ-SON-08
struct Bucle3D {
    jugador: Gd<AudioStreamPlayer3D>,
    id: String,
}

#[derive(GodotClass)]
#[class(base=Node, init)]
pub struct Sonido {
    base: Base<Node>,
    defs: Vec<DefSonido>,
    mezcla: Mezcla,
    azar: Option<Azar>,
    enfriador: Enfriador,
    ultima_variante: HashMap<String, usize>,
    /// Si cada archivo existe (false = todavía no está, REQ-SON-09). No guarda los recursos.
    existe: HashMap<String, bool>,
    /// Ambiente: un reproductor por capa y su nivel actual (0 a 1).
    ambiente: HashMap<String, (Gd<AudioStreamPlayer>, f32)>,
    disparos_de_un_golpe: Vec<Gd<Node>>,
    bucles: HashMap<(InstanceId, String), Bucle3D>,
    /// Cuántos sonidos se pidieron y no fueron descartados (cuenta aunque falte el archivo).
    disparos: u32,
    faltantes: u32,
    /// Después de `detener_todo` no se vuelve a reproducir nada (cierre del juego).
    detenido: bool,
}

#[godot_api]
impl INode for Sonido {
    fn ready(&mut self) {
        self.base_mut().add_to_group(GRUPO);
        self.azar = Some(Azar::new(24));
        self.cargar_datos();
        self.crear_buses();
        self.registrar_accion();
        self.aplicar_mezcla();
        // Música de fondo, si está el archivo. REQ-SON-08
        self.empezar_capa(ids::MUSICA);
        if let Some((p, _)) = self.ambiente.get_mut(ids::MUSICA) {
            p.set_volume_db(self.defs.iter().find(|d| d.id == ids::MUSICA).map(|d| d.volumen_db).unwrap_or(0.0));
        }
    }

    fn exit_tree(&mut self) {
        // Soltar los recursos de audio antes de que Godot cierre (si no, avisa pérdidas).
        self.detener_todo();
        self.existe.clear();
    }

    fn process(&mut self, delta: f64) {
        // REQ-SON-01: M silencia o reactiva todo.
        if Input::singleton().is_action_just_pressed("silenciar") {
            self.alternar_silencio();
        }
        if self.detenido {
            return;
        }
        let dt = delta as f32;
        self.limpiar_terminados();
        self.actualizar_bucles();
        self.actualizar_ambiente(dt);
    }
}

impl Sonido {
    /// Frena y libera todos los reproductores (al cerrar el juego o en pruebas).
    pub fn detener_todo(&mut self) {
        self.detenido = true;
        for (r, _) in self.ambiente.values_mut() {
            r.stop();
            r.set_stream(Gd::<AudioStream>::null_arg());
        }
        for b in self.bucles.values_mut() {
            b.jugador.stop();
            b.jugador.set_stream(Gd::<AudioStream>::null_arg());
        }
        for n in &mut self.disparos_de_un_golpe {
            if let Ok(mut r) = n.clone().try_cast::<AudioStreamPlayer3D>() {
                r.stop();
                r.set_stream(Gd::<AudioStream>::null_arg());
            } else if let Ok(mut r) = n.clone().try_cast::<AudioStreamPlayer>() {
                r.stop();
                r.set_stream(Gd::<AudioStream>::null_arg());
            }
        }
        self.existe.clear();
        self.ambiente.clear();
        self.bucles.clear();
        self.disparos_de_un_golpe.clear();
    }
}

#[godot_api]
impl Sonido {
    /// Volumen general (0 a 1). REQ-SON-01
    #[func]
    pub fn set_volumen_general(&mut self, v: f32) {
        self.mezcla.general = v.clamp(0.0, 1.0);
        self.aplicar_mezcla();
    }

    /// Volumen de un bus por su nombre ("Ambiente", "Efectos" o "Música"). REQ-SON-01
    #[func]
    pub fn set_volumen_bus(&mut self, bus: GString, v: f32) {
        if let Some(b) = Bus::TODOS.iter().find(|b| bus == b.nombre()) {
            self.mezcla.set_volumen(*b, v);
            self.aplicar_mezcla();
        }
    }

    /// REQ-SON-01
    #[func]
    pub fn alternar_silencio(&mut self) {
        self.mezcla.silenciado = !self.mezcla.silenciado;
        self.aplicar_mezcla();
    }

    /// Dispara un sonido sin posición (interfaz, objetos en la mano). REQ-SON-08
    #[func]
    pub fn reproducir(&mut self, id: GString) {
        self.disparar(&id.to_string(), None);
    }
}

impl Sonido {
    fn cargar_datos(&mut self) {
        let texto = FileAccess::get_file_as_string("res://data/sonidos.ron").to_string();
        match carrito_core::sonido::cargar(&texto) {
            Ok(d) => self.defs = d,
            // REQ-SON-09: sin datos no hay sonido, pero el juego sigue.
            Err(e) => godot_warn!("Sin sonidos: {e}"),
        }
    }

    /// REQ-SON-01: crea los buses Ambiente, Efectos y Música que salen al Master.
    fn crear_buses(&mut self) {
        let mut srv = AudioServer::singleton();
        for bus in Bus::TODOS {
            let nombre = StringName::from(bus.nombre());
            if srv.get_bus_index(&nombre) < 0 {
                let idx = srv.get_bus_count();
                srv.add_bus();
                srv.set_bus_name(idx, bus.nombre());
                srv.set_bus_send(idx, "Master");
            }
        }
    }

    fn aplicar_mezcla(&mut self) {
        let mut srv = AudioServer::singleton();
        srv.set_bus_volume_db(0, self.mezcla.db_master());
        for bus in Bus::TODOS {
            let idx = srv.get_bus_index(&StringName::from(bus.nombre()));
            if idx >= 0 {
                srv.set_bus_volume_db(idx, self.mezcla.db_bus(bus));
            }
        }
    }

    fn registrar_accion(&self) {
        let mut mapa = InputMap::singleton();
        if !mapa.has_action("silenciar") {
            mapa.add_action("silenciar");
            let mut ev = InputEventKey::new_gd();
            ev.set_physical_keycode(Key::M);
            mapa.action_add_event("silenciar", &ev);
        }
    }

    fn def(&self, id: &str) -> Option<&DefSonido> {
        self.defs.iter().find(|d| d.id == id)
    }

    fn ahora(&self) -> f64 {
        Time::singleton().get_ticks_msec() as f64 / 1000.0
    }

    /// Dónde está el oyente (la cámara), si hay.
    fn oyente(&self) -> Option<Vector3> {
        let cam = self.base().get_viewport()?.get_camera_3d()?;
        Some(cam.get_global_position())
    }

    /// REQ-SON-09: carga un archivo de `godot/audio/` si existe; si no, None (sin error).
    /// Godot ya guarda en memoria lo que está en uso, así que acá no se guarda nada.
    fn stream(&mut self, archivo: &str, bucle: bool) -> Option<Gd<AudioStream>> {
        let ruta = format!("{CARPETA}{archivo}");
        let existe = match self.existe.get(archivo) {
            Some(e) => *e,
            None => {
                let e = ResourceLoader::singleton().exists(&ruta);
                if !e {
                    self.faltantes += 1;
                }
                self.existe.insert(archivo.to_string(), e);
                e
            }
        };
        if !existe {
            return None;
        }
        let s = try_load::<AudioStream>(&ruta).ok()?;
        if let Ok(mut ogg) = s.clone().try_cast::<AudioStreamOggVorbis>() {
            ogg.set_loop(bucle);
        }
        Some(s)
    }

    /// Elige variante (REQ-SON-03) y devuelve su stream, si el archivo existe.
    fn elegir_stream(&mut self, def: &DefSonido) -> Option<Gd<AudioStream>> {
        let anterior = self.ultima_variante.get(&def.id).copied();
        let azar = self.azar.as_mut()?;
        let i = elegir_variante(azar, def.archivos.len(), anterior);
        self.ultima_variante.insert(def.id.clone(), i);
        let archivo = def.archivos.get(i)?.clone();
        self.stream(&archivo, def.bucle)
    }

    /// Dispara un sonido de un solo golpe. REQ-SON-03, REQ-SON-04, REQ-SON-08, REQ-SON-09
    fn disparar(&mut self, id: &str, pos: Option<Vector3>) {
        let Some(def) = self.def(id).cloned() else { return };
        if self.detenido {
            return;
        }
        // REQ-SON-04: más allá de la distancia máxima no se reproduce.
        let mut db = def.volumen_db;
        let espacial = def.espacial && pos.is_some();
        if let (true, Some(p)) = (espacial, pos) {
            let d = self.oyente().map(|o| o.distance_to(p)).unwrap_or(0.0);
            let g = ganancia_distancia(d, def.distancia_max);
            if g <= 0.0 {
                return;
            }
            db += lineal_a_db(g);
        }
        // REQ-SON-03: enfriamiento.
        let ahora = self.ahora();
        if !self.enfriador.disparar(id, ahora, def.enfriamiento) {
            return;
        }
        self.disparos += 1;
        // REQ-SON-09: sin archivo (o sin audio) se omite en silencio.
        let Some(stream) = self.elegir_stream(&def) else { return };
        let nodo: Gd<Node> = if let (true, Some(p)) = (espacial, pos) {
            let mut r = AudioStreamPlayer3D::new_alloc();
            r.set_stream(&stream);
            r.set_bus(def.bus.nombre());
            r.set_volume_db(db);
            r.set_attenuation_model(AttenuationModel::DISABLED);
            r.set_position(p);
            r.upcast()
        } else {
            let mut r = AudioStreamPlayer::new_alloc();
            r.set_stream(&stream);
            r.set_bus(def.bus.nombre());
            r.set_volume_db(db);
            r.upcast()
        };
        self.base_mut().add_child(&nodo);
        match nodo.clone().try_cast::<AudioStreamPlayer3D>() {
            Ok(mut r) => r.play(),
            Err(n) => {
                if let Ok(mut r) = n.try_cast::<AudioStreamPlayer>() {
                    r.play()
                }
            }
        }
        self.disparos_de_un_golpe.push(nodo);
    }

    fn limpiar_terminados(&mut self) {
        self.disparos_de_un_golpe.retain_mut(|n| {
            if !n.is_instance_valid() {
                return false;
            }
            let suena = if let Ok(r) = n.clone().try_cast::<AudioStreamPlayer3D>() {
                r.is_playing()
            } else if let Ok(r) = n.clone().try_cast::<AudioStreamPlayer>() {
                r.is_playing()
            } else {
                false
            };
            if !suena {
                n.queue_free();
            }
            suena
        });
    }

    /// Crea (si hay archivo) el reproductor de una capa de ambiente o de la música.
    fn empezar_capa(&mut self, id: &str) {
        if self.ambiente.contains_key(id) {
            return;
        }
        let Some(def) = self.def(id).cloned() else { return };
        let Some(stream) = self.elegir_stream(&def) else { return };
        let mut r = AudioStreamPlayer::new_alloc();
        r.set_stream(&stream);
        r.set_bus(def.bus.nombre());
        r.set_volume_db(-80.0);
        self.base_mut().add_child(&r);
        r.play();
        self.ambiente.insert(id.to_string(), (r, 0.0));
    }

    /// REQ-SON-05, REQ-SON-06, REQ-SON-07: ambiente según hora, gente y clima.
    fn actualizar_ambiente(&mut self, dt: f32) {
        let yo = self.to_gd();
        let Some(dn) = util::unico::<DiaNoche>(&yo, dia_noche::GRUPO) else { return };
        let gente = util::unico::<Gente>(&yo, gente::GRUPO).map(|g| g.bind().cantidad() as u32).unwrap_or(0);
        let entorno = Entorno { minuto: dn.bind().hora() * 60.0, gente, lluvia: 0.0, viento: 0.0 };
        for capa in capas_ambiente(&entorno) {
            if capa.nivel > 0.01 {
                self.empezar_capa(capa.id);
            }
            let db_base = self.def(capa.id).map(|d| d.volumen_db).unwrap_or(0.0);
            if let Some((r, actual)) = self.ambiente.get_mut(capa.id) {
                // Fundido suave hacia el nivel pedido.
                let paso = dt / FUNDIDO_S;
                *actual += (capa.nivel - *actual).clamp(-paso, paso);
                r.set_volume_db(db_base + lineal_a_db(*actual));
            }
        }
    }

    fn actualizar_bucles(&mut self) {
        let oyente = self.oyente();
        self.bucles.retain(|_, b| b.jugador.is_instance_valid());
        let defs = self.defs.clone();
        for b in self.bucles.values_mut() {
            let Some(def) = defs.iter().find(|d| d.id == b.id) else { continue };
            // REQ-SON-04
            let d = oyente.map(|o| o.distance_to(b.jugador.get_global_position())).unwrap_or(0.0);
            let g = ganancia_distancia(d, def.distancia_max);
            b.jugador.set_volume_db(def.volumen_db + lineal_a_db(g));
        }
    }

    /// Para pruebas: cuántos sonidos se dispararon.
    pub fn disparos(&self) -> u32 {
        self.disparos
    }

    /// Para pruebas: cuántos archivos de `godot/audio/` faltan (REQ-SON-09).
    pub fn faltantes(&self) -> u32 {
        self.faltantes
    }

    pub fn silenciado(&self) -> bool {
        self.mezcla.silenciado
    }

    pub fn tiene_sonido(&self, id: &str) -> bool {
        self.def(id).is_some()
    }

    /// REQ-SON-01: los tres buses existen.
    pub fn buses_creados(&self) -> bool {
        let srv = AudioServer::singleton();
        Bus::TODOS.iter().all(|b| srv.get_bus_index(&StringName::from(b.nombre())) >= 0)
    }

    pub fn volumen_bus(&self, bus: Bus) -> f32 {
        self.mezcla.volumen(bus)
    }

    /// Enciende o apaga un sonido continuo 3D pegado a `dueno` (hervor, chisporroteo). REQ-SON-08
    pub fn bucle_en(&mut self, id: &str, dueno: &Gd<Node3D>, activo: bool) {
        let clave = (dueno.instance_id(), id.to_string());
        if !activo {
            if let Some(mut b) = self.bucles.remove(&clave).filter(|b| b.jugador.is_instance_valid()) {
                b.jugador.queue_free();
            }
            return;
        }
        if self.bucles.contains_key(&clave) {
            return;
        }
        let Some(def) = self.def(id).cloned() else { return };
        self.disparos += 1;
        let Some(stream) = self.elegir_stream(&def) else { return };
        let mut r = AudioStreamPlayer3D::new_alloc();
        r.set_stream(&stream);
        r.set_bus(def.bus.nombre());
        r.set_volume_db(def.volumen_db);
        r.set_attenuation_model(AttenuationModel::DISABLED);
        dueno.clone().add_child(&r);
        r.play();
        self.bucles.insert(clave, Bucle3D { jugador: r, id: id.to_string() });
    }
}

/// Dispara un sonido sin posición desde cualquier nodo del mundo. REQ-SON-08
pub fn sonar(desde: &Gd<impl Inherits<Node>>, id: &str) {
    if let Some(mut s) = util::unico::<Sonido>(desde, GRUPO) {
        s.bind_mut().disparar(id, None);
    }
}

/// Dispara un sonido que sale de `pos` (global). REQ-SON-04, REQ-SON-08
pub fn sonar_en(desde: &Gd<impl Inherits<Node>>, id: &str, pos: Vector3) {
    if let Some(mut s) = util::unico::<Sonido>(desde, GRUPO) {
        s.bind_mut().disparar(id, Some(pos));
    }
}

/// Enciende o apaga un sonido continuo pegado a `dueno`. REQ-SON-08
pub fn bucle(dueno: &Gd<Node3D>, id: &str, activo: bool) {
    if let Some(mut s) = util::unico::<Sonido>(dueno, GRUPO) {
        s.bind_mut().bucle_en(id, dueno, activo);
    }
}
