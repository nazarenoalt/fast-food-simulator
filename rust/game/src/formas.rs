//! Convierte piezas simples (`carrito_core::forma::Pieza`) en mallas y colisiones de Godot.

use carrito_core::forma::{Pieza, TipoPieza};
use godot::builtin::EulerOrder;
use godot::classes::base_material_3d::{Feature, Transparency};
use godot::classes::{
    BoxMesh, BoxShape3D, CapsuleMesh, CapsuleShape3D, CollisionShape3D, CylinderMesh, CylinderShape3D, Mesh,
    MeshInstance3D, Node3D, Shape3D, SphereMesh, SphereShape3D, StandardMaterial3D, StaticBody3D,
};
use godot::prelude::*;

/// Capa física de los objetos sueltos (comida y paquetes). Las zonas que los detectan
/// (agua del hervidor, bandeja, lugares del depósito, encastre) solo miran esta capa.
pub const CAPA_OBJETOS: u32 = 1 << 1;

/// Capa de lo que solo se usa con la mira y no choca con nada (el cartel de cerrado). El rayo
/// del jugador la mira además de la capa 1. REQ-CLI-13
pub const CAPA_USABLES: u32 = 1 << 2;

/// Zona que detecta solo comida y paquetes.
pub fn zona_objetos() -> Gd<godot::classes::Area3D> {
    let mut z = godot::classes::Area3D::new_alloc();
    z.set_collision_layer(0);
    z.set_collision_mask(CAPA_OBJETOS);
    z.set_monitorable(false);
    z
}

pub fn v3(a: [f32; 3]) -> Vector3 {
    Vector3::new(a[0], a[1], a[2])
}

pub fn color(c: [f32; 3]) -> Color {
    Color::from_rgb(c[0], c[1], c[2])
}

pub fn material(c: [f32; 3], alfa: f32, metal: bool, emision: f32) -> Gd<StandardMaterial3D> {
    let mut m = StandardMaterial3D::new_gd();
    m.set_albedo(Color::from_rgba(c[0], c[1], c[2], alfa));
    if alfa < 1.0 {
        m.set_transparency(Transparency::ALPHA);
    }
    if metal {
        m.set_metallic(0.6);
        m.set_roughness(0.35);
    } else {
        m.set_roughness(0.75);
    }
    if emision > 0.0 {
        m.set_feature(Feature::EMISSION, true);
        m.set_emission(color(c));
        m.set_emission_energy_multiplier(emision);
    }
    m
}

pub fn malla(tipo: TipoPieza, medidas: [f32; 3]) -> Gd<Mesh> {
    let [a, b, c] = medidas;
    match tipo {
        TipoPieza::Caja => {
            let mut m = BoxMesh::new_gd();
            m.set_size(Vector3::new(a, b, c));
            m.upcast()
        }
        TipoPieza::Cilindro | TipoPieza::Cono => {
            let mut m = CylinderMesh::new_gd();
            m.set_bottom_radius(a);
            m.set_top_radius(if tipo == TipoPieza::Cono { 0.0 } else { a });
            m.set_height(b);
            m.set_radial_segments(if a > 0.3 { 32 } else { 16 });
            m.upcast()
        }
        TipoPieza::Esfera => {
            let mut m = SphereMesh::new_gd();
            m.set_radius(a);
            m.set_height(2.0 * a);
            m.set_radial_segments(16);
            m.set_rings(8);
            m.upcast()
        }
        TipoPieza::Capsula => {
            let mut m = CapsuleMesh::new_gd();
            m.set_radius(a);
            m.set_height(b.max(2.0 * a));
            m.set_radial_segments(12);
            m.set_rings(4);
            m.upcast()
        }
    }
}

/// Posición + giro (grados, orden YXZ) + escala de una pieza.
pub fn transform_pieza(p: &Pieza) -> Transform3D {
    let rot = Vector3::new(p.rot[0].to_radians(), p.rot[1].to_radians(), p.rot[2].to_radians());
    let basis = Basis::from_euler(EulerOrder::YXZ, rot).scaled(v3(p.escala));
    Transform3D::new(basis, v3(p.pos))
}

pub fn instancia_malla(malla: Gd<Mesh>, mat: Gd<StandardMaterial3D>) -> Gd<MeshInstance3D> {
    let mut mi = MeshInstance3D::new_alloc();
    mi.set_mesh(&malla);
    mi.set_material_override(&mat);
    mi
}

/// Malla visual de una pieza, ya ubicada.
pub fn visual_pieza(p: &Pieza) -> Gd<MeshInstance3D> {
    let mut mi = instancia_malla(malla(p.tipo, p.medidas), material(p.color, p.alfa, p.metal, p.emision));
    mi.set_transform(transform_pieza(p));
    mi
}

pub fn forma_colision(tipo: TipoPieza, medidas: [f32; 3], escala: [f32; 3]) -> Gd<Shape3D> {
    let [a, b, c] = medidas;
    match tipo {
        TipoPieza::Caja => {
            let mut s = BoxShape3D::new_gd();
            s.set_size(Vector3::new(a * escala[0], b * escala[1], c * escala[2]));
            s.upcast()
        }
        // Los conos colisionan como cilindros (alcanza para mobiliario).
        TipoPieza::Cilindro | TipoPieza::Cono => {
            let mut s = CylinderShape3D::new_gd();
            s.set_radius(a);
            s.set_height(b);
            s.upcast()
        }
        TipoPieza::Esfera => {
            let mut s = SphereShape3D::new_gd();
            s.set_radius(a);
            s.upcast()
        }
        TipoPieza::Capsula => {
            let mut s = CapsuleShape3D::new_gd();
            s.set_radius(a);
            s.set_height(b.max(2.0 * a));
            s.upcast()
        }
    }
}

pub fn nodo_colision(forma: Gd<Shape3D>, t: Transform3D) -> Gd<CollisionShape3D> {
    let mut cs = CollisionShape3D::new_alloc();
    cs.set_shape(&forma);
    cs.set_transform(t);
    cs
}

/// Agrega las piezas como hijos de `padre`. Las piezas con colisión van dentro de un
/// `StaticBody3D` hijo (se crea solo si hace falta).
pub fn construir(padre: &mut Gd<Node3D>, piezas: &[Pieza]) {
    let mut cuerpo: Option<Gd<StaticBody3D>> = None;
    for p in piezas {
        padre.add_child(&visual_pieza(p));
        if p.colision {
            let cuerpo = cuerpo.get_or_insert_with(|| {
                let c = StaticBody3D::new_alloc();
                padre.add_child(&c);
                c
            });
            // La escala se aplica a las medidas (las formas de colisión no se escalan bien).
            let sin_escala = Pieza { escala: [1.0; 3], ..p.clone() };
            cuerpo.add_child(&nodo_colision(forma_colision(p.tipo, p.medidas, p.escala), transform_pieza(&sin_escala)));
        }
    }
}

/// Caja simple con colisión (atajo para piso, muebles, etc.).
pub fn caja_solida(padre: &mut Gd<Node3D>, medidas: [f32; 3], pos: [f32; 3], c: [f32; 3], metal: bool) {
    construir(
        padre,
        &[Pieza {
            tipo: TipoPieza::Caja,
            medidas,
            pos,
            rot: [0.0; 3],
            escala: [1.0; 3],
            color: c,
            alfa: 1.0,
            metal,
            emision: 0.0,
            colision: true,
            tinte_coccion: false,
            tinte_lado: None,
        }],
    );
}

/// Pieza sin colisión (atajo).
pub fn pieza(tipo: TipoPieza, medidas: [f32; 3], pos: [f32; 3], c: [f32; 3]) -> Pieza {
    Pieza {
        tipo,
        medidas,
        pos,
        rot: [0.0; 3],
        escala: [1.0; 3],
        color: c,
        alfa: 1.0,
        metal: false,
        emision: 0.0,
        colision: false,
        tinte_coccion: false,
        tinte_lado: None,
    }
}
