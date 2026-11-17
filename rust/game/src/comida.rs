//! Un alimento suelto en el mundo: objeto físico agarrable que se cocina y se arma.
//! SPEC-002 (agarre), SPEC-003 (cocción), SPEC-005 (armado).

use carrito_core::TEMP_AMBIENTE;
use carrito_core::armado;
use carrito_core::coccion::{EstadoCoccion, PerfilCoccion};
use carrito_core::datos::{Colision, DefProducto};
use carrito_core::lados::CoccionLados;
use carrito_core::plancha::{entorno_por_lados, lado_abajo};
use godot::classes::{
    Area3D, BoxShape3D, CapsuleShape3D, Engine, IRigidBody3D, MeshInstance3D, PhysicsMaterial, RigidBody3D,
    StandardMaterial3D,
};
use godot::prelude::*;

use crate::datos::catalogo;
use crate::formas;

#[derive(GodotClass)]
#[class(base=RigidBody3D, no_init)]
pub struct Comida {
    base: Base<RigidBody3D>,
    def: DefProducto,
    /// Perfil y estado de cocción (propio, o heredado si es un armado como el pancho).
    coccion: Option<(PerfilCoccion, EstadoCoccion)>,
    /// REQ-PLA-04: si se cocina por lados (hamburguesa), el estado de cada lado.
    lados: Option<CoccionLados>,
    /// Si sigue cocinándose (un pancho armado no).
    cocina: bool,
    /// Texto extra, ej. "salchicha cocida" en un pancho.
    detalle: Option<String>,
    /// Lo tiene el jugador en la mano.
    pub sostenida: bool,
    /// Ya se usó en un armado (está por desaparecer).
    consumida: bool,
    /// Temperatura del entorno que le dio una fuente de calor, y en qué cuadro.
    entorno: Option<(f32, u64)>,
    tintes: Vec<Gd<StandardMaterial3D>>,
    /// Materiales que tiñe cada lado (REQ-PLA-05).
    tintes_lado: [Vec<Gd<StandardMaterial3D>>; 2],
    /// Aderezos puestos (SPEC-012) y su dibujo.
    aderezos: Vec<String>,
    dibujo_aderezos: Option<Gd<godot::classes::Node3D>>,
    zona_encastre: Option<Gd<Area3D>>,
}

#[godot_api]
impl Comida {
    /// Crea un alimento desde Godot (escenas, herramientas): `Comida.nueva("salchicha")`.
    #[func]
    fn nueva(producto: GString) -> Gd<Self> {
        Self::crear(&producto.to_string())
    }
}

impl Comida {
    pub fn crear(producto: &str) -> Gd<Self> {
        let def = catalogo().producto(producto).unwrap_or_else(|| panic!("producto inexistente: {producto}")).clone();
        let coccion = def.coccion.clone().map(|p| (p, EstadoCoccion::default()));
        let cocina = coccion.is_some();
        let lados = if def.por_lados { Some(CoccionLados::default()) } else { None };
        Gd::from_init_fn(|base| Self {
            base,
            def,
            coccion,
            lados,
            cocina,
            detalle: None,
            sostenida: false,
            consumida: false,
            entorno: None,
            tintes: Vec::new(),
            tintes_lado: [Vec::new(), Vec::new()],
            aderezos: Vec::new(),
            dibujo_aderezos: None,
            zona_encastre: None,
        })
    }

    pub fn producto(&self) -> &str {
        &self.def.id
    }

    pub fn punto(&self) -> Option<carrito_core::coccion::Punto> {
        // REQ-PLA-05: el más grave de los dos lados.
        if let (Some((p, _)), Some(l)) = (&self.coccion, &self.lados) {
            return Some(l.punto(p));
        }
        self.coccion.as_ref().map(|(p, e)| e.punto(p))
    }

    /// REQ-PLA-04
    pub fn por_lados(&self) -> bool {
        self.lados.is_some()
    }

    /// Qué lado (0 o 1) mira hacia abajo ahora. REQ-PLA-07
    fn lado_abajo(&self) -> usize {
        lado_abajo(self.base().get_global_transform().basis.col_b().y)
    }

    /// REQ-PLA-07: la da vuelta en el lugar (medio giro sobre su eje X) y la levanta un poquito.
    pub fn dar_vuelta(&mut self) {
        if self.lados.is_none() {
            return;
        }
        let t = self.base().get_global_transform();
        let giro = Basis::from_axis_angle(t.basis.col_a().normalized(), std::f32::consts::PI);
        let nueva = Transform3D::new(giro * t.basis, t.origin + Vector3::new(0.0, 0.02, 0.0));
        let mut yo = self.to_gd();
        yo.set_global_transform(nueva);
        yo.set_linear_velocity(Vector3::ZERO);
        yo.set_angular_velocity(Vector3::ZERO);
    }

    /// Solo para pruebas: estado de cada lado.
    pub fn estado_lados(&self) -> Option<CoccionLados> {
        self.lados
    }

    /// Nombre para mostrar con su estado. REQ-INT-08
    pub fn descripcion(&self) -> String {
        let mut s = capitalizar(&self.def.nombre);
        if let Some(d) = &self.detalle {
            s += &format!(" ({d})");
        } else if let (Some((p, _)), Some(l)) = (&self.coccion, &self.lados) {
            s += &format!(" ({})", l.descripcion(p, self.lado_abajo()));
        } else if let Some((p, e)) = &self.coccion {
            s += &format!(" ({}, {:.0} °C)", e.punto(p).nombre(), e.temp);
        }
        // REQ-ADE-03 / CA-ADE-01: el cartel lista los aderezos.
        if !self.aderezos.is_empty() {
            let nombres: Vec<String> = self
                .aderezos
                .iter()
                .map(|a| catalogo().aderezo(a).map(|d| d.nombre.clone()).unwrap_or_default())
                .collect();
            s += &format!(" con {}", carrito_core::aderezos::enumerar(&nombres));
        }
        s
    }

    pub fn admite_aderezos(&self) -> bool {
        self.def.admite_aderezos
    }

    pub fn aderezos(&self) -> &[String] {
        &self.aderezos
    }

    /// Si es un repuesto, qué aderezo repone. REQ-ADE-05
    pub fn repone(&self) -> Option<&str> {
        self.def.repone.as_deref()
    }

    /// Si es una bolsa de carbón, cuántos kg trae. REQ-PAR-01
    pub fn carbon(&self) -> Option<f32> {
        self.def.carbon
    }

    /// REQ-ADE-03: guarda los aderezos y los dibuja en zigzag.
    pub fn set_aderezos(&mut self, aderezos: Vec<String>) {
        self.aderezos = aderezos;
        self.dibujar_aderezos();
    }

    /// Lo que ve el cliente al recibirlo. REQ-CLI-08
    pub fn entregado(&self) -> carrito_core::clientes::Entregado {
        carrito_core::clientes::Entregado {
            producto: self.def.id.clone(),
            punto: self.punto(),
            aderezos: self.aderezos.clone(),
        }
    }

    /// Solo para pruebas: deja la parte cocinable con este avance de cocción.
    pub fn forzar_avance(&mut self, avance: f32) {
        if let Some(l) = &mut self.lados {
            for e in &mut l.lados {
                e.avance = avance;
                e.temp = 70.0;
            }
        } else if let Some((_, e)) = &mut self.coccion {
            e.avance = avance;
            e.temp = 70.0;
        }
        self.actualizar_color();
    }

    fn dibujar_aderezos(&mut self) {
        if let Some(mut viejo) = self.dibujo_aderezos.take() {
            viejo.queue_free();
        }
        if self.aderezos.is_empty() {
            return;
        }
        let mut nodo = godot::classes::Node3D::new_alloc();
        for (k, id) in self.aderezos.iter().enumerate() {
            let color = catalogo().aderezo(id).map(|a| a.color).unwrap_or([1.0; 3]);
            // Zigzag: palitos finos alternando el ángulo, un poco más arriba cada aderezo.
            for i in 0..6 {
                let mut p = formas::pieza(
                    carrito_core::forma::TipoPieza::Caja,
                    [0.03, 0.004, 0.005],
                    [-0.0625 + i as f32 * 0.025, 0.037 + k as f32 * 0.003, 0.0],
                    color,
                );
                p.rot = [0.0, if i % 2 == 0 { 35.0 } else { -35.0 }, 0.0];
                nodo.add_child(&formas::visual_pieza(&p));
            }
        }
        self.base_mut().add_child(&nodo);
        self.dibujo_aderezos = Some(nodo);
    }

    pub fn detalle(&self) -> Option<&str> {
        self.detalle.as_deref()
    }

    /// Una fuente de calor avisa que este cuadro el alimento está a `temp`. REQ-COC-08
    pub fn exponer(&mut self, temp: f32) {
        self.entorno = Some((temp, Engine::singleton().get_physics_frames()));
    }

    /// Solo para pruebas: fuerza el estado de cocción.
    pub fn estado_coccion(&self) -> Option<EstadoCoccion> {
        self.coccion.as_ref().map(|(_, e)| *e)
    }

    fn actualizar_color(&mut self) {
        // REQ-PLA-05: cada mitad toma el color de su propio lado.
        if let (Some((p, _)), Some(l)) = (&self.coccion, &self.lados) {
            for (i, mats) in self.tintes_lado.iter_mut().enumerate() {
                let c = formas::color(l.color(p, i));
                for m in mats {
                    m.set_albedo(c);
                }
            }
            return;
        }
        if let Some((p, e)) = &self.coccion {
            let c = formas::color(e.color(p));
            for m in &mut self.tintes {
                m.set_albedo(c);
            }
        }
    }

    /// REQ-ARM-02: si una pieza agregable suelta está en la zona de encastre, se arma.
    fn intentar_encastre(&mut self) {
        if self.sostenida || self.consumida {
            return;
        }
        let Some(zona) = &self.zona_encastre else { return };
        let yo = self.base().instance_id();
        for cuerpo in zona.get_overlapping_bodies().iter_shared() {
            if cuerpo.instance_id() == yo {
                continue;
            }
            let Ok(mut otra) = cuerpo.try_cast::<Comida>() else { continue };
            let (resultado, heredado, nombre_agregado) = {
                let o = otra.bind();
                if o.sostenida || o.consumida {
                    continue;
                }
                // REQ-ARM-04: si no hay regla, no pasa nada.
                let Some(r) = armado::combinar(&catalogo().combinaciones, &self.def.id, &o.def.id) else {
                    continue;
                };
                (r.to_string(), o.coccion.clone(), o.def.nombre.clone())
            };

            let mut nueva = Comida::crear(&resultado);
            {
                let mut n = nueva.bind_mut();
                // REQ-ARM-03: guarda el estado de la salchicha y deja de cocinarse.
                if let Some((p, e)) = &heredado {
                    n.detalle = Some(format!("{nombre_agregado} {}", e.punto(p).nombre()));
                }
                n.coccion = heredado;
                n.cocina = false;
            }
            let t = self.base().get_global_transform();
            nueva.set_transform(t);
            if let Some(mut padre) = self.base().get_parent() {
                padre.add_child(&nueva);
            }
            nueva.set_global_transform(t);

            self.consumida = true;
            otra.bind_mut().consumida = true;
            otra.queue_free();
            self.base_mut().queue_free();
            return;
        }
    }
}

#[godot_api]
impl IRigidBody3D for Comida {
    fn ready(&mut self) {
        let def = self.def.clone();
        let mut yo = self.to_gd();

        // REQ-ARM-05 (masa de los datos: el pancho pesa lo que el pan + la salchicha).
        yo.set_mass(def.masa);
        // Objetos chicos: detección continua para que no atraviesen paredes finas.
        yo.set_use_continuous_collision_detection(true);
        yo.set_collision_layer(1 | formas::CAPA_OBJETOS);
        yo.set_angular_damp(2.0);
        let mut mat = PhysicsMaterial::new_gd();
        mat.set_friction(0.9);
        mat.set_bounce(0.15);
        yo.set_physics_material_override(&mat);

        // Forma visual. Las piezas con tinte de cocción tienen su propio material.
        for p in &def.forma {
            let mi: Gd<MeshInstance3D> = formas::visual_pieza(p);
            if p.tinte_coccion {
                if let Some(m) = mi.get_material_override() {
                    self.tintes.push(m.cast::<StandardMaterial3D>());
                }
            }
            if let Some(lado) = p.tinte_lado.filter(|l| *l < 2) {
                if let Some(m) = mi.get_material_override() {
                    self.tintes_lado[lado].push(m.cast::<StandardMaterial3D>());
                }
            }
            yo.add_child(&mi);
        }

        // Colisión.
        match def.colision {
            Colision::Caja { medidas } => {
                let mut s = BoxShape3D::new_gd();
                s.set_size(formas::v3(medidas));
                yo.add_child(&formas::nodo_colision(s.upcast(), Transform3D::IDENTITY));
            }
            Colision::Capsula { radio, largo } => {
                let mut s = CapsuleShape3D::new_gd();
                s.set_radius(radio);
                s.set_height(largo);
                // Acostada sobre X.
                let t =
                    Transform3D::new(Basis::from_axis_angle(Vector3::BACK, std::f32::consts::FRAC_PI_2), Vector3::ZERO);
                yo.add_child(&formas::nodo_colision(s.upcast(), t));
            }
        }

        // REQ-ARM-02: zona de encastre arriba de los productos que son base de una combinación.
        if armado::es_base(&catalogo().combinaciones, &def.id) {
            let alto = match def.colision {
                Colision::Caja { medidas } => medidas[1],
                Colision::Capsula { radio, .. } => radio * 2.0,
            };
            let mut zona = formas::zona_objetos();
            let mut s = BoxShape3D::new_gd();
            s.set_size(Vector3::new(0.16, 0.06, 0.06));
            zona.add_child(&formas::nodo_colision(s.upcast(), Transform3D::IDENTITY));
            zona.set_position(Vector3::new(0.0, alto / 2.0 + 0.025, 0.0));
            yo.add_child(&zona);
            self.zona_encastre = Some(zona);
        }

        self.actualizar_color();
    }

    fn physics_process(&mut self, delta: f64) {
        let dt = delta as f32;
        if self.cocina {
            // REQ-COC-02: fuera de toda fuente, el entorno es el ambiente.
            let cuadro = Engine::singleton().get_physics_frames();
            let t_entorno = match self.entorno {
                Some((t, f)) if cuadro.saturating_sub(f) <= 1 => t,
                _ => TEMP_AMBIENTE,
            };
            let abajo = self.lado_abajo();
            if let (Some((p, _)), Some(l)) = (&self.coccion, &mut self.lados) {
                // REQ-PLA-03: solo el lado de abajo toma la temperatura de la fuente.
                let fuente = (t_entorno != TEMP_AMBIENTE).then_some(t_entorno);
                let (t_abajo, t_arriba) = entorno_por_lados(fuente);
                l.paso(p, abajo, t_abajo, t_arriba, dt);
            } else if let Some((p, e)) = &mut self.coccion {
                e.paso(p, t_entorno, dt);
            }
            // REQ-COC-06
            self.actualizar_color();
        }
        self.intentar_encastre();
    }
}

fn capitalizar(s: &str) -> String {
    let mut c = s.chars();
    match c.next() {
        Some(f) => f.to_uppercase().collect::<String>() + c.as_str(),
        None => String::new(),
    }
}
