//! SPEC-029 · Freidora: cubas de aceite que fríen lo que tienen adentro, y sus coladores.
//! Las reglas (aceite, colador, alturas, en qué se convierte la papa) están en
//! `carrito_core::freidora`.

use carrito_core::carrito::{CubaFreidora, ObjetoInicial};
use carrito_core::datos::Colision;
use carrito_core::freidora::{self as reglas, Aceite, NoEntra};
use carrito_core::sonido::ids;
use godot::classes::base_material_3d::Feature;
use godot::classes::rigid_body_3d::FreezeMode;
use godot::classes::{Area3D, BoxShape3D, INode3D, Node, Node3D, RigidBody3D, StandardMaterial3D};
use godot::prelude::*;

use crate::comida::Comida;
use crate::datos::catalogo;
use crate::{formas, modelos};

/// Grupos de las freidoras y de los coladores (para encontrarlos desde el jugador).
pub const GRUPO: &str = "freidoras";
pub const GRUPO_COLADORES: &str = "coladores";
/// Piezas del modelo: el aceite y la luz piloto de cada cuba (REQ-PAP-05).
const PIEZA_ACEITE: &str = "pieza_aceite";
/// Velocidad con la que el colador baja o sube (m/s). REQ-FRE-08
const VEL_COLADOR: f32 = 0.4;
/// Cuánto más arriba de su lugar se acepta un colador como «puesto en la cuba» (m).
const MARGEN_PUESTO: f32 = 0.1;

/// Medidas del canasto del colador (su caja de colisión). REQ-FRE-07
pub fn canasto() -> [f32; 3] {
    match catalogo().producto(reglas::COLADOR).map(|p| &p.colision) {
        Some(Colision::Caja { medidas }) => *medidas,
        _ => [0.19, 0.095, 0.27],
    }
}

struct Cuba {
    def: CubaFreidora,
    aceite: Aceite,
    /// Volumen de aceite: lo que está adentro toma su temperatura. REQ-FRE-06
    zona: Option<Gd<Area3D>>,
    piloto: Option<Gd<StandardMaterial3D>>,
    /// Altura (relativa a la freidora) y giro del colador arriba, como lo trae (REQ-FRE-08).
    arriba: f32,
    rot_y: f32,
    /// El colador puesto en esta cuba, y si está bajado.
    colador: Option<Gd<Comida>>,
    abajo: bool,
}

#[derive(GodotClass)]
#[class(base=Node3D, no_init)]
pub struct Freidora {
    base: Base<Node3D>,
    cubas: Vec<Cuba>,
    modelo: Option<String>,
    pos_modelo: [f32; 3],
}

impl Freidora {
    pub fn crear(
        cubas: &[CubaFreidora],
        objetos: &[ObjetoInicial],
        modelo: Option<String>,
        pos_modelo: [f32; 3],
    ) -> Gd<Self> {
        let [_, alto_canasto, _] = canasto();
        let coladores: Vec<&ObjetoInicial> = objetos.iter().filter(|o| o.producto == reglas::COLADOR).collect();
        let cubas = cubas
            .iter()
            .enumerate()
            .map(|(i, c)| {
                let (arriba, rot_y) = match coladores.get(i) {
                    Some(o) => (o.pos[1], o.rot_y),
                    None => (c.centro[1] + c.interior[1] + alto_canasto / 2.0 + 0.01, 0.0),
                };
                Cuba {
                    def: c.clone(),
                    aceite: Aceite::default(),
                    zona: None,
                    piloto: None,
                    arriba,
                    rot_y,
                    colador: None,
                    abajo: false,
                }
            })
            .collect();
        Gd::from_init_fn(|base| Self { base, cubas, modelo, pos_modelo })
    }

    /// Cuba más cercana a un punto (global). REQ-FRE-05
    fn cuba_en(&self, punto: Vector3) -> usize {
        let local = self.base().get_global_transform().affine_inverse() * punto;
        let dist = |c: &Cuba| (c.def.centro[0] - local.x).abs();
        (0..self.cubas.len()).min_by(|a, b| dist(&self.cubas[*a]).total_cmp(&dist(&self.cubas[*b]))).unwrap_or(0)
    }

    /// REQ-FRE-05: E sobre una cuba la enciende o la apaga (la que está bajo la mira).
    pub fn alternar_en(&mut self, punto: Vector3) {
        let i = self.cuba_en(punto);
        self.alternar(i);
    }

    pub fn alternar(&mut self, i: usize) {
        let Some(c) = self.cubas.get_mut(i) else { return };
        c.aceite.alternar();
        Self::actualizar_piloto(c);
        let yo = self.to_gd().upcast::<Node3D>();
        crate::sonido::sonar_en(&yo, ids::PLANCHA_INTERRUPTOR, yo.get_global_position());
    }

    /// Texto del cartel de la cuba bajo la mira. REQ-FRE-05
    pub fn cartel(&self, punto: Vector3) -> String {
        let i = self.cuba_en(punto);
        let n = (self.cubas.len() > 1).then_some(i + 1);
        self.cubas[i].aceite.cartel(n)
    }

    /// Solo para pruebas.
    pub fn temperatura(&self, i: usize) -> f32 {
        self.cubas[i].aceite.temp
    }

    pub fn encendida(&self, i: usize) -> bool {
        self.cubas[i].aceite.encendida
    }

    pub fn set_temperatura(&mut self, i: usize, t: f32) {
        self.cubas[i].aceite.temp = t;
    }

    pub fn cantidad_cubas(&self) -> usize {
        self.cubas.len()
    }

    /// El colador puesto en la cuba `i` y si está bajado.
    pub fn colador(&self, i: usize) -> Option<(Gd<Comida>, bool)> {
        let c = self.cubas.get(i)?;
        c.colador.clone().filter(|x| x.is_instance_valid()).map(|x| (x, c.abajo))
    }

    /// REQ-FRE-08: si el colador está puesto en una cuba de esta freidora, lo baja o lo sube.
    /// Devuelve si quedó bajado (o `None` si no está acá).
    pub fn alternar_colador(&mut self, colador: &Gd<Comida>) -> Option<bool> {
        let c = self.cubas.iter_mut().find(|c| c.colador.as_ref() == Some(colador))?;
        c.abajo = !c.abajo;
        Some(c.abajo)
    }

    /// Si el colador está puesto acá: si está bajado.
    pub fn estado_colador(&self, colador: &Gd<Comida>) -> Option<bool> {
        self.cubas.iter().find(|c| c.colador.as_ref() == Some(colador)).map(|c| c.abajo)
    }

    fn actualizar_piloto(c: &mut Cuba) {
        let on = c.aceite.encendida;
        if let Some(m) = &mut c.piloto {
            // REQ-FRE-05: luz piloto roja de cada cuba.
            m.set_emission_energy_multiplier(if on { 4.0 } else { 0.0 });
            m.set_albedo(if on { Color::from_rgb(1.0, 0.1, 0.05) } else { Color::from_rgb(0.25, 0.05, 0.05) });
        }
    }

    /// Índice de la cuba cuyo centro está más cerca en X de esta pieza del modelo.
    fn cuba_de_pieza(&self, pieza: &Gd<Node3D>) -> usize {
        let p = self.base().get_global_transform().affine_inverse() * pieza.get_global_position();
        let dist = |c: &Cuba| (c.def.centro[0] - p.x).abs();
        (0..self.cubas.len()).min_by(|a, b| dist(&self.cubas[*a]).total_cmp(&dist(&self.cubas[*b]))).unwrap_or(0)
    }

    /// Dónde va el colador de la cuba `i` (global), arriba o bajado. REQ-FRE-08
    fn lugar_colador(&self, i: usize) -> Transform3D {
        let c = &self.cubas[i];
        let y = reglas::altura_colador(&c.def, canasto(), c.arriba, c.abajo);
        let local = Transform3D::new(
            Basis::from_axis_angle(Vector3::UP, c.rot_y.to_radians()),
            Vector3::new(c.def.centro[0], y, c.def.centro[2]),
        );
        let t = self.base().get_global_transform();
        Transform3D::new(t.basis.orthonormalized(), t.origin) * local
    }

    /// REQ-FRE-08: un colador suelto (que nadie sostiene) adentro de la cuba `i`.
    fn colador_suelto_en(&self, i: usize, tomados: &[Gd<Comida>]) -> Option<Gd<Comida>> {
        let c = &self.cubas[i];
        let inversa = self.base().get_global_transform().affine_inverse();
        let [w, _, d] = c.def.interior;
        self.base()
            .get_tree()
            .get_nodes_in_group(GRUPO_COLADORES)
            .iter_shared()
            .filter_map(|n| n.get_parent()?.try_cast::<Comida>().ok())
            .filter(|x| !x.bind().sostenida && !x.is_queued_for_deletion() && !tomados.contains(x))
            .find(|x| {
                let p = inversa * x.get_global_position();
                (p.x - c.def.centro[0]).abs() < w / 2.0
                    && (p.z - c.def.centro[2]).abs() < d / 2.0
                    && p.y > c.def.centro[1] - 0.02
                    && p.y < c.arriba + MARGEN_PUESTO
            })
    }

    /// REQ-FRE-08: pone, mueve o suelta el colador de cada cuba.
    fn atender_coladores(&mut self, dt: f32) {
        // Coladores puestos en alguna freidora (para no tomar uno dos veces).
        let tomados: Vec<Gd<Comida>> = self
            .base()
            .get_tree()
            .get_nodes_in_group(GRUPO)
            .iter_shared()
            .filter_map(|n| n.try_cast::<Freidora>().ok())
            .filter(|f| *f != self.to_gd())
            .flat_map(|f| f.bind().cubas.iter().filter_map(|c| c.colador.clone()).collect::<Vec<_>>())
            .collect();
        for i in 0..self.cubas.len() {
            // Lo agarró el jugador (o desapareció): queda libre.
            if let Some(mut col) = self.cubas[i].colador.clone() {
                if !col.is_instance_valid() || col.is_queued_for_deletion() {
                    self.cubas[i].colador = None;
                } else if col.bind().sostenida {
                    col.set_freeze_enabled(false);
                    self.cubas[i].colador = None;
                }
            }
            if self.cubas[i].colador.is_none()
                && let Some(mut col) = self.colador_suelto_en(i, &tomados)
            {
                // Puesto en la cuba: queda quieto, arriba (REQ-FRE-08: arranca arriba).
                col.set_freeze_mode(FreezeMode::KINEMATIC);
                col.set_freeze_enabled(true);
                col.set_linear_velocity(Vector3::ZERO);
                col.set_angular_velocity(Vector3::ZERO);
                self.cubas[i].colador = Some(col);
                self.cubas[i].abajo = false;
            }
            let Some(mut col) = self.cubas[i].colador.clone() else { continue };
            // Va hacia su lugar (arriba o abajo) a velocidad fija; el giro, directo.
            let destino = self.lugar_colador(i);
            let actual = col.get_global_position();
            let d = destino.origin - actual;
            let paso = VEL_COLADOR * dt;
            let pos = if d.length() <= paso { destino.origin } else { actual + d.normalized() * paso };
            col.set_global_transform(Transform3D::new(destino.basis, pos));
        }
    }
}

#[godot_api]
impl INode3D for Freidora {
    fn ready(&mut self) {
        let mut yo = self.to_gd().upcast::<Node3D>();
        yo.add_to_group(GRUPO);
        // REQ-MOD-04/05: el modelo (con su cuba hueca, su aceite y sus pilotos) o piezas simples.
        let modelo = self.modelo.clone().and_then(|m| modelos::agregar(&mut yo, &m));
        if let Some(m) = &modelo {
            m.clone().set_position(formas::v3(self.pos_modelo));
            for piloto in modelos::buscar_prefijos(m, &[carrito_core::modelos::PIEZA_PILOTO]) {
                let i = self.cuba_de_pieza(&piloto);
                if self.cubas[i].piloto.is_some() {
                    continue;
                }
                if let Some((_, mut mat)) = modelos::materiales_propios(&piloto).into_iter().next() {
                    mat.set_feature(Feature::EMISSION, true);
                    mat.set_emission(Color::from_rgb(1.0, 0.1, 0.05));
                    self.cubas[i].piloto = Some(mat);
                }
            }
        }
        let tiene_aceite = modelo.as_ref().is_some_and(|m| !modelos::buscar_prefijos(m, &[PIEZA_ACEITE]).is_empty());
        for i in 0..self.cubas.len() {
            let def = self.cubas[i].def.clone();
            let (centro, medidas) = reglas::volumen_aceite(&def);
            if modelo.is_none() {
                // Sin modelo: una cuba de acero con su perilla y su piloto (piezas simples).
                let [w, h, d] = def.interior;
                let [x, y, z] = def.centro;
                formas::caja_solida(&mut yo, [w + 0.02, 0.01, d + 0.02], [x, y - 0.005, z], [0.8, 0.8, 0.82], true);
                for (m, p) in [
                    ([w + 0.02, h + 0.04, 0.01], [x, y + (h + 0.04) / 2.0, z + d / 2.0 + 0.005]),
                    ([w + 0.02, h + 0.04, 0.01], [x, y + (h + 0.04) / 2.0, z - d / 2.0 - 0.005]),
                    ([0.01, h + 0.04, d], [x + w / 2.0 + 0.005, y + (h + 0.04) / 2.0, z]),
                    ([0.01, h + 0.04, d], [x - w / 2.0 - 0.005, y + (h + 0.04) / 2.0, z]),
                ] {
                    formas::caja_solida(&mut yo, m, p, [0.8, 0.8, 0.82], true);
                }
                let piloto_mat = formas::material([1.0, 0.1, 0.05], 1.0, false, 0.01);
                let mut piloto = formas::instancia_malla(
                    formas::malla(carrito_core::forma::TipoPieza::Esfera, [0.008, 0.0, 0.0]),
                    piloto_mat.clone(),
                );
                piloto.set_position(Vector3::new(x, y + h, z + d / 2.0 + 0.02));
                yo.add_child(&piloto);
                self.cubas[i].piloto = Some(piloto_mat);
            }
            if !tiene_aceite {
                let mat = formas::material([0.85, 0.65, 0.2], 0.7, false, 0.0);
                let mut aceite =
                    formas::instancia_malla(formas::malla(carrito_core::forma::TipoPieza::Caja, medidas), mat);
                aceite.set_position(formas::v3(centro));
                yo.add_child(&aceite);
            }
            // REQ-FRE-06: el volumen de aceite (zona que calienta).
            let mut zona = formas::zona_objetos();
            let mut s = BoxShape3D::new_gd();
            s.set_size(formas::v3(medidas));
            zona.add_child(&formas::nodo_colision(s.upcast(), Transform3D::IDENTITY));
            zona.set_position(formas::v3(centro));
            yo.add_child(&zona);
            self.cubas[i].zona = Some(zona);
            Self::actualizar_piloto(&mut self.cubas[i]);
        }
    }

    fn physics_process(&mut self, delta: f64) {
        let dt = delta as f32;
        for c in &mut self.cubas {
            // REQ-FRE-04
            c.aceite.paso(dt);
            // REQ-FRE-06: todo alimento dentro del aceite toma su temperatura.
            let temp = c.aceite.temp;
            if let Some(zona) = &c.zona {
                for cuerpo in zona.get_overlapping_bodies().iter_shared() {
                    if let Ok(mut comida) = cuerpo.try_cast::<Comida>() {
                        comida.bind_mut().exponer(temp);
                    }
                }
            }
        }
        self.atender_coladores(dt);
    }
}

/// REQ-FRE-07: lo que tiene adentro un colador. Es hijo de la comida que hace de colador y
/// lleva sus porciones quietas en su lugar del canasto: se mueven con él.
#[derive(GodotClass)]
#[class(base=Node, init)]
pub struct Colador {
    base: Base<Node>,
    contenido: Vec<Gd<Comida>>,
}

impl Colador {
    /// Agrega el contenido a un colador recién creado (lo llama la comida en su `ready`).
    pub fn preparar(comida: &mut Gd<RigidBody3D>, producto: &str) {
        if producto == reglas::COLADOR {
            let mut c = Colador::new_alloc();
            c.add_to_group(GRUPO_COLADORES);
            comida.add_child(&c);
        }
    }

    /// El colador de esta comida (si es un colador).
    pub fn de(comida: &Gd<Comida>) -> Option<Gd<Colador>> {
        comida.get_children().iter_shared().find_map(|n| n.try_cast::<Colador>().ok())
    }

    /// El colador en el que está esta comida (si la tiene adentro alguno).
    pub fn que_contiene(comida: &Gd<Comida>) -> Option<Gd<Colador>> {
        let arbol = comida.get_tree();
        arbol
            .get_nodes_in_group(GRUPO_COLADORES)
            .iter_shared()
            .filter_map(|n| n.try_cast::<Colador>().ok())
            .find(|c| c.bind().contenido.contains(comida))
    }

    pub fn porciones(&self) -> usize {
        self.contenido.len()
    }

    /// Solo para pruebas.
    pub fn contenido(&self) -> Vec<Gd<Comida>> {
        self.contenido.clone()
    }

    /// REQ-FRE-07: si se puede meter este producto.
    pub fn puede_meter(&self, producto: &str) -> Result<(), NoEntra> {
        reglas::puede_meter(producto, self.contenido.len())
    }

    fn colador(&self) -> Option<Gd<Comida>> {
        self.base().get_parent()?.try_cast::<Comida>().ok()
    }

    /// REQ-FRE-07: deja la porción adentro, quieta en su lugar del canasto.
    pub fn meter(&mut self, mut comida: Gd<Comida>) -> Result<(), NoEntra> {
        let producto = comida.bind().producto().to_string();
        self.puede_meter(&producto)?;
        let Some(colador) = self.colador() else { return Err(NoEntra::NoVa) };
        comida.set_freeze_mode(FreezeMode::KINEMATIC);
        comida.set_freeze_enabled(true);
        comida.add_collision_exception_with(&colador);
        self.contenido.push(comida);
        self.acomodar();
        Ok(())
    }

    /// Pone cada porción en su lugar del canasto (siguen al colador).
    fn acomodar(&mut self) {
        let Some(colador) = self.colador() else { return };
        let t = colador.get_global_transform();
        let t = Transform3D::new(t.basis.orthonormalized(), t.origin);
        let canasto = canasto();
        for (i, c) in self.contenido.iter_mut().enumerate() {
            let (alto, _, _) = c.bind().medidas();
            let p = reglas::lugar_en_colador(i, canasto, alto * 2.0);
            c.set_global_transform(t * Transform3D::new(Basis::IDENTITY, formas::v3(p)));
        }
    }
}

#[godot_api]
impl INode for Colador {
    fn physics_process(&mut self, _delta: f64) {
        // Las que agarró el jugador (o desaparecieron) salen del colador y vuelven a la física.
        let colador = self.colador();
        self.contenido.retain_mut(|c| {
            if !c.is_instance_valid() || c.is_queued_for_deletion() {
                return false;
            }
            if c.bind().sostenida {
                c.set_freeze_enabled(false);
                if let Some(col) = &colador {
                    c.remove_collision_exception_with(col);
                }
                return false;
            }
            true
        });
        self.acomodar();
    }
}

/// REQ-FRE-08: el colador al que apunta la mira: el colador mismo o el que tiene adentro
/// esta comida (mirando las papas también se baja y se sube).
fn colador_apuntado(comida: &Gd<Comida>) -> Option<Gd<Comida>> {
    if es_colador(comida) {
        return Some(comida.clone());
    }
    Colador::que_contiene(comida)?.bind().colador()
}

/// REQ-FRE-08: la freidora donde está puesto este colador, y si está bajado.
pub fn freidora_de(colador: &Gd<Comida>) -> Option<(Gd<Freidora>, bool)> {
    colador.get_tree().get_nodes_in_group(GRUPO).iter_shared().filter_map(|n| n.try_cast::<Freidora>().ok()).find_map(
        |f| {
            let abajo = f.bind().estado_colador(colador)?;
            Some((f, abajo))
        },
    )
}

/// REQ-FRE-08: texto para el cartel del colador (o de lo que tiene adentro) si está puesto en
/// una cuba.
pub fn cartel_colador(apuntado: &Gd<Comida>) -> Option<String> {
    let colador = colador_apuntado(apuntado)?;
    let (_, abajo) = freidora_de(&colador)?;
    let porciones = Colador::de(&colador).map(|c| c.bind().porciones()).unwrap_or(0);
    let accion = if abajo { "Subir el colador" } else { "Bajar el colador al aceite" };
    Some(format!("[E] {accion} ({porciones}/{} porciones)", reglas::PORCIONES_COLADOR))
}

/// REQ-FRE-08: E sobre un colador puesto en una cuba (o sobre lo que tiene adentro) lo baja o
/// lo sube. Devuelve false si no apunta a un colador puesto.
pub fn alternar_colador(apuntado: &Gd<Comida>) -> bool {
    let Some(colador) = colador_apuntado(apuntado) else { return false };
    let Some((mut f, _)) = freidora_de(&colador) else { return false };
    f.bind_mut().alternar_colador(&colador);
    let pos = colador.get_global_position();
    crate::sonido::sonar_en(&f, ids::SOLTAR, pos);
    true
}

/// Para el árbol de nodos: la comida es un colador.
pub fn es_colador(comida: &Gd<Comida>) -> bool {
    comida.bind().producto() == reglas::COLADOR
}

/// REQ-FRE-07: si colocar `mano` donde toca la mira (`tocado`) la mete en un colador: el
/// colador (`Ok`) o por qué no entra (`Err`, ej. lleno). `None` si no apunta a un colador o
/// no son papas.
pub fn colador_destino(
    mano: &Gd<Comida>,
    tocado: Option<Gd<godot::classes::Object>>,
) -> Option<Result<Gd<Colador>, NoEntra>> {
    let producto = mano.bind().producto().to_string();
    if !reglas::va_al_colador(&producto) {
        return None;
    }
    let comida = tocado?.try_cast::<Comida>().ok()?;
    let colador = if es_colador(&comida) { Colador::de(&comida) } else { Colador::que_contiene(&comida) }?;
    let r = colador.bind().puede_meter(&producto);
    Some(r.map(|_| colador))
}
