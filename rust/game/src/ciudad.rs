//! SPEC-013 · Edificios alrededor de la plaza, veredas, sendas peatonales y faroles de enfrente.

use carrito_core::ciudad::{self, ALTO_PB, ALTO_PISO, Edificio, SENDAS};
use carrito_core::forma::TipoPieza;
use carrito_core::plaza;
use godot::classes::multi_mesh::TransformFormat;
use godot::classes::{INode3D, MultiMesh, MultiMeshInstance3D, Node3D, QuadMesh, StandardMaterial3D};
use godot::prelude::*;

use crate::luz::LuzNocturna;
use crate::{formas, nocturno};

const VIDRIO: [f32; 3] = [0.16, 0.2, 0.25];
const LUZ_VENTANA: [f32; 3] = [1.0, 0.82, 0.5];
const VEREDA: [f32; 3] = [0.48, 0.48, 0.47];

#[derive(GodotClass)]
#[class(base=Node3D, init)]
pub struct Ciudad {
    base: Base<Node3D>,
}

fn transform_edificio(e: &Edificio) -> Transform3D {
    Transform3D::new(Basis::from_axis_angle(Vector3::UP, e.rot_y.to_radians()), Vector3::new(e.x, 0.0, e.z))
}

fn ventanas(mesh: &Gd<QuadMesh>, mat: Gd<StandardMaterial3D>, ts: &[Transform3D]) -> Gd<MultiMeshInstance3D> {
    let mut mm = MultiMesh::new_gd();
    mm.set_transform_format(TransformFormat::TRANSFORM_3D);
    mm.set_mesh(mesh);
    mm.set_instance_count(ts.len() as i32);
    for (i, t) in ts.iter().enumerate() {
        mm.set_instance_transform(i as i32, *t);
    }
    let mut mmi = MultiMeshInstance3D::new_alloc();
    mmi.set_multimesh(&mm);
    mmi.set_material_override(&mat);
    mmi
}

impl Ciudad {
    /// REQ-AMB-01: un edificio con cornisa, puerta y, si tiene local, vidriera y toldo.
    fn edificio(&mut self, e: &Edificio, prendibles: &mut Vec<Transform3D>, oscuras: &mut Vec<Transform3D>) {
        let mut nodo = Node3D::new_alloc();
        nodo.set_transform(transform_edificio(e));
        self.base_mut().add_child(&nodo);
        let alto = e.alto();
        let frente = e.fondo / 2.0;
        formas::caja_solida(&mut nodo, [e.ancho, alto, e.fondo], [0.0, alto / 2.0, 0.0], e.color, false);
        let claro = carrito_core::coccion::mezclar(e.color, [1.0, 1.0, 1.0], 0.35);
        let oscuro = carrito_core::coccion::mezclar(e.color, [0.0, 0.0, 0.0], 0.3);
        let mut piezas = vec![
            formas::pieza(TipoPieza::Caja, [e.ancho + 0.1, 0.35, e.fondo + 0.1], [0.0, alto + 0.17, 0.0], claro),
            // Zócalo y línea entre planta baja y pisos.
            formas::pieza(TipoPieza::Caja, [e.ancho, 0.5, 0.06], [0.0, 0.25, frente + 0.03], oscuro),
            formas::pieza(TipoPieza::Caja, [e.ancho, 0.18, 0.12], [0.0, ALTO_PB, frente + 0.06], claro),
        ];
        // Puerta.
        let x_puerta = -e.ancho / 2.0 + 1.2;
        piezas.push(formas::pieza(TipoPieza::Caja, [1.1, 2.2, 0.06], [x_puerta, 1.1, frente + 0.03], [0.3, 0.2, 0.14]));
        nodo.add_child(&formas::visual_pieza(&piezas[0]));
        for p in &piezas[1..] {
            nodo.add_child(&formas::visual_pieza(p));
        }
        if let Some(t) = e.toldo {
            // Local: vidriera que brilla de noche y toldo inclinado.
            let ancho_vid = (e.ancho - 3.0).max(1.5);
            let mut vid = formas::instancia_malla(
                formas::malla(TipoPieza::Caja, [ancho_vid, 2.1, 0.05]),
                nocturno::material(VIDRIO, [1.0, 0.92, 0.75], 1.6),
            );
            vid.set_position(Vector3::new(0.9, 1.45, frente + 0.03));
            nodo.add_child(&vid);
            let mut toldo = formas::pieza(TipoPieza::Caja, [ancho_vid + 0.6, 0.05, 1.3], [0.9, 2.95, frente + 0.6], t);
            toldo.rot = [-18.0, 0.0, 0.0];
            nodo.add_child(&formas::visual_pieza(&toldo));
        }

        // REQ-AMB-02: ventanas de los pisos de arriba (las que se prenden van aparte).
        let t = transform_edificio(e);
        let paso = e.ancho / e.columnas as f32;
        for piso in 0..(e.pisos - 1) {
            for c in 0..e.columnas {
                let local = Vector3::new(
                    -e.ancho / 2.0 + paso * (c as f32 + 0.5),
                    ALTO_PB + piso as f32 * ALTO_PISO + 1.5,
                    frente + 0.03,
                );
                let i = (piso * e.columnas + c) as usize;
                let tv = t * Transform3D::new(Basis::IDENTITY, local);
                if e.encendidas.get(i).copied().unwrap_or(false) {
                    prendibles.push(tv);
                } else {
                    oscuras.push(tv);
                }
            }
        }
    }
}

#[godot_api]
impl INode3D for Ciudad {
    fn ready(&mut self) {
        let mut prendibles = Vec::new();
        let mut oscuras = Vec::new();
        // REQ-AMB-03: siempre la misma ciudad.
        for e in ciudad::edificios() {
            self.edificio(&e, &mut prendibles, &mut oscuras);
        }
        let mut quad = QuadMesh::new_gd();
        quad.set_size(Vector2::new(1.1, 1.4));
        let mut vidrio = formas::material(VIDRIO, 1.0, false, 0.0);
        vidrio.set_metallic(0.4);
        vidrio.set_roughness(0.15);
        let mi = ventanas(&quad, vidrio, &oscuras);
        self.base_mut().add_child(&mi);
        let mi = ventanas(&quad, nocturno::material(VIDRIO, LUZ_VENTANA, 2.2), &prendibles);
        self.base_mut().add_child(&mi);

        // Veredas de enfrente, laterales y sur.
        let mut yo = self.to_gd().upcast::<Node3D>();
        let sup = |yo: &mut Gd<Node3D>, ancho: f32, largo: f32, x: f32, z: f32, c: [f32; 3]| {
            yo.add_child(&formas::visual_pieza(&formas::pieza(
                TipoPieza::Caja,
                [ancho, 0.01, largo],
                [x, 0.006, z],
                c,
            )));
        };
        sup(&mut yo, 120.0, 4.0, 0.0, ciudad::Z_VEREDA_ENFRENTE, VEREDA);
        sup(&mut yo, 4.0, 52.0, ciudad::X_FACHADA_ESTE - 2.0, 5.0, VEREDA);
        sup(&mut yo, 4.0, 52.0, -ciudad::X_FACHADA_ESTE + 2.0, 5.0, VEREDA);
        sup(&mut yo, 90.0, 4.0, 0.0, ciudad::Z_FACHADA_SUR - 2.0, VEREDA);
        yo.add_child(&formas::visual_pieza(&formas::pieza(
            TipoPieza::Caja,
            [120.0, 0.12, 0.2],
            [0.0, 0.06, plaza::Z_CALLE - plaza::ANCHO_CALLE / 2.0],
            [0.75, 0.75, 0.72],
        )));

        // REQ-AMB-08: sendas peatonales (rayas blancas).
        for x in SENDAS {
            let mut z = plaza::Z_CALLE - plaza::ANCHO_CALLE / 2.0 + 0.5;
            while z < plaza::Z_CALLE + plaza::ANCHO_CALLE / 2.0 {
                yo.add_child(&formas::visual_pieza(&formas::pieza(
                    TipoPieza::Caja,
                    [3.0, 0.01, 0.5],
                    [x, 0.009, z],
                    [0.92, 0.92, 0.9],
                )));
                z += 1.0;
            }
        }

        // Faroles de la vereda de enfrente.
        let mut x = -50.0;
        while x <= 50.0 {
            let mut nodo = Node3D::new_alloc();
            nodo.set_position(Vector3::new(x, 0.0, ciudad::Z_VEREDA_ENFRENTE + 1.5));
            yo.add_child(&nodo);
            let mut poste = formas::pieza(TipoPieza::Cilindro, [0.07, 3.6, 0.0], [0.0, 1.8, 0.0], [0.15, 0.16, 0.15]);
            poste.colision = true;
            formas::construir(&mut nodo, &[poste]);
            let mut luz = LuzNocturna::crear([1.0, 0.82, 0.55], 3.0, 12.0, 0.12, false);
            luz.set_position(Vector3::new(0.0, 3.62, 0.0));
            nodo.add_child(&luz);
            x += 20.0;
        }
    }
}
