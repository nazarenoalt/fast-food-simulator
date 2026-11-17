//! SPEC-006 · Construye el carrito del jugador a partir de los datos.

use carrito_core::carrito::{BaseCarrito, CarritoArmado, Funcion, armar};
use carrito_core::clientes::SEPARACION_FILA;
use carrito_core::forma::TipoPieza;
use godot::classes::base_material_3d::BillboardMode;
use godot::classes::{Area3D, BoxShape3D, INode3D, Label3D, Node3D};
use godot::prelude::*;

use crate::aderecera;
use crate::bloque_stock::BloqueStock;
use crate::comida::Comida;
use crate::datos::catalogo;
use crate::formas;
use crate::hervidor::Hervidor;
use crate::lugar_deposito::LugarDeposito;
use crate::luz::LuzNocturna;

const ACERO: [f32; 3] = [0.82, 0.83, 0.85];
pub const GRUPO: &str = "carrito";

#[derive(GodotClass)]
#[class(base=Node3D, init)]
pub struct Carrito {
    base: Base<Node3D>,
    /// Si está vacío, usa la config del jugador (`res://data/carrito_jugador.ron`).
    #[export]
    base_forzada: GString,
    base_def: Option<BaseCarrito>,
    bandeja: Option<Gd<Area3D>>,
}

impl Carrito {
    /// REQ-CAR-10: lugar `i` de la fila (global). La fila sigue hacia +X de la base.
    pub fn posicion_fila(&self, i: usize) -> Vector3 {
        let f = self.base_def.as_ref().map(|b| b.fila).unwrap_or([0.0, 0.0, 1.0]);
        let local = Vector3::new(f[0] + i as f32 * SEPARACION_FILA, f[1], f[2]);
        self.base().get_global_transform() * local
    }

    /// Hacia dónde mira un cliente en la fila (hacia el carrito).
    pub fn mirada_fila(&self) -> Vector3 {
        -self.base().get_global_transform().basis.col_c()
    }

    /// Centro de la bandeja de entrega (global).
    pub fn pos_bandeja(&self) -> Vector3 {
        let e = self.base_def.as_ref().map(|b| b.entrega).unwrap_or([0.0, 1.0, 0.0]);
        self.base().get_global_transform() * Vector3::new(e[0], e[1], e[2])
    }

    /// Dónde deja los paquetes el proveedor: un pallet al costado, del lado del vendedor.
    pub fn pos_pallet(&self) -> Vector3 {
        let ancho = self.base_def.as_ref().map(|b| b.ancho).unwrap_or(1.6);
        self.base().get_global_transform() * Vector3::new(ancho / 2.0 + 1.35, 0.12, -1.0)
    }

    /// REQ-CLI-07: comida suelta (que nadie sostiene) apoyada en la bandeja.
    pub fn comida_en_bandeja(&self) -> Vec<Gd<Comida>> {
        let Some(b) = &self.bandeja else { return Vec::new() };
        b.get_overlapping_bodies()
            .iter_shared()
            .filter_map(|c| c.try_cast::<Comida>().ok())
            .filter(|c| !c.bind().sostenida && !c.is_queued_for_deletion())
            .collect()
    }

    /// Aderezos que el carrito tiene (para los pedidos). REQ-CLI-04
    pub fn aderezos_disponibles(&self) -> Vec<String> {
        let yo = self.to_gd();
        crate::util::todos::<aderecera::Pomo>(&yo, aderecera::GRUPO)
            .iter()
            .map(|p| p.bind().aderezo().to_string())
            .collect()
    }

    /// REQ-CLI-07: bandeja roja sobre el mostrador con su zona de entrega.
    fn construir_bandeja(&mut self, b: &BaseCarrito) {
        let mut yo = self.to_gd().upcast::<Node3D>();
        let pos = formas::v3(b.entrega);
        let mut bandeja = Node3D::new_alloc();
        bandeja.set_name("BandejaEntrega");
        bandeja.set_position(pos);
        yo.add_child(&bandeja);
        formas::construir(
            &mut bandeja,
            &[
                formas::pieza(TipoPieza::Caja, [0.3, 0.008, 0.22], [0.0, 0.004, 0.0], [0.8, 0.12, 0.1]),
                formas::pieza(TipoPieza::Caja, [0.3, 0.02, 0.008], [0.0, 0.01, 0.11], [0.8, 0.12, 0.1]),
                formas::pieza(TipoPieza::Caja, [0.3, 0.02, 0.008], [0.0, 0.01, -0.11], [0.8, 0.12, 0.1]),
            ],
        );
        let mut zona = formas::zona_objetos();
        let mut s = BoxShape3D::new_gd();
        s.set_size(Vector3::new(0.3, 0.14, 0.22));
        zona.add_child(&formas::nodo_colision(s.upcast(), Transform3D::IDENTITY));
        zona.set_position(Vector3::new(0.0, 0.07, 0.0));
        zona.set_monitorable(false);
        bandeja.add_child(&zona);
        self.bandeja = Some(zona);

        // Pallet del proveedor.
        let pallet_local = Vector3::new(b.ancho / 2.0 + 1.35, 0.0, -1.0);
        let mut pallet = Node3D::new_alloc();
        pallet.set_name("Pallet");
        pallet.set_position(pallet_local);
        yo.add_child(&pallet);
        let madera = [0.62, 0.48, 0.3];
        let mut piezas = vec![formas::pieza(TipoPieza::Caja, [0.8, 0.03, 0.6], [0.0, 0.105, 0.0], madera)];
        for x in [-0.35, 0.0, 0.35] {
            piezas.push(formas::pieza(TipoPieza::Caja, [0.1, 0.09, 0.6], [x, 0.045, 0.0], [0.5, 0.38, 0.24]));
        }
        for p in &mut piezas {
            p.colision = true;
        }
        formas::construir(&mut pallet, &piezas);
    }

    fn construir_base(&mut self, armado: &CarritoArmado) {
        let b = &armado.base;
        let mut yo = self.to_gd().upcast::<Node3D>();
        let suelo = if b.ruedas { 0.18 } else { 0.02 };
        let alto_cuerpo = b.alto_mostrador - 0.04 - suelo;

        // Mueble (color = estilo, REQ-CAR-09).
        formas::caja_solida(
            &mut yo,
            [b.ancho, alto_cuerpo, b.profundidad],
            [0.0, suelo + alto_cuerpo / 2.0, 0.0],
            armado.color,
            false,
        );
        // Mesada de acero, un poco más grande que el mueble.
        formas::caja_solida(
            &mut yo,
            [b.ancho + 0.04, 0.04, b.profundidad + 0.06],
            [0.0, b.alto_mostrador - 0.02, 0.02],
            ACERO,
            true,
        );
        // Zócalo y ruedas.
        if b.ruedas {
            let r = 0.15;
            for &sx in &[-1.0_f32, 1.0] {
                for &sz in &[-1.0_f32, 1.0] {
                    let mut rueda = formas::pieza(
                        TipoPieza::Cilindro,
                        [r, 0.06, 0.0],
                        [sx * (b.ancho / 2.0 - 0.3), r, sz * (b.profundidad / 2.0 + 0.03)],
                        [0.12, 0.12, 0.12],
                    );
                    rueda.rot = [90.0, 0.0, 0.0];
                    yo.add_child(&formas::visual_pieza(&rueda));
                }
            }
            // Manija para empujarlo.
            let mut manija = formas::pieza(
                TipoPieza::Cilindro,
                [0.015, b.profundidad * 0.8, 0.0],
                [-b.ancho / 2.0 - 0.15, b.alto_mostrador - 0.1, 0.0],
                ACERO,
            );
            manija.rot = [90.0, 0.0, 0.0];
            manija.metal = true;
            yo.add_child(&formas::visual_pieza(&manija));
        }
    }

    fn construir_accesorios(&mut self, armado: &CarritoArmado) {
        let mut yo = self.to_gd().upcast::<Node3D>();
        for c in &armado.colocados {
            // REQ-CAR-03: el accesorio se ubica en la posición y giro del anclaje.
            let mut nodo = Node3D::new_alloc();
            nodo.set_name(&format!("{}_{}", c.anclaje.id, c.accesorio.id));
            nodo.set_position(formas::v3(c.anclaje.pos));
            nodo.set_rotation_degrees(Vector3::new(0.0, c.anclaje.rot_y, 0.0));
            yo.add_child(&nodo);

            formas::construir(&mut nodo, &c.accesorio.forma);

            // REQ-CAR-05: función del accesorio.
            match &c.accesorio.funcion {
                Some(Funcion::Hervidor { interior }) => {
                    nodo.add_child(&Hervidor::crear(*interior));
                }
                Some(Funcion::Deposito { lugares }) => {
                    // REQ-DEP-07: cada lugar es un nodo que guarda a lo sumo un bloque.
                    for (i, lugar) in lugares.iter().enumerate() {
                        let mut l = LugarDeposito::new_alloc();
                        l.set_position(formas::v3(*lugar));
                        nodo.add_child(&l);
                        if let Some(Some(id)) = c.stock.get(i) {
                            let def = catalogo().bloque(id).expect("bloque validado").clone();
                            l.add_child(&BloqueStock::crear(def));
                        }
                    }
                }
                Some(Funcion::Aderezos { tipos, separacion }) => {
                    aderecera::construir(&mut nodo, tipos, *separacion);
                }
                Some(Funcion::Luz { pos, color, energia, alcance }) => {
                    // REQ-CAR-06: se prende de noche (grupo luces_noche).
                    let mut luz = LuzNocturna::crear(*color, *energia, *alcance, 0.035, true);
                    luz.set_position(formas::v3(*pos));
                    nodo.add_child(&luz);
                }
                None => {}
            }
        }
    }

    /// REQ-CAR-08: muestra el error arriba del carrito, en rojo, además de la consola.
    fn mostrar_error(&mut self, mensaje: &str) {
        godot_error!("Carrito: {mensaje}");
        let mut l = Label3D::new_alloc();
        l.set_text(&format!("ERROR EN EL CARRITO\n{mensaje}"));
        l.set_modulate(Color::from_rgb(1.0, 0.2, 0.2));
        l.set_billboard_mode(BillboardMode::ENABLED);
        l.set_font_size(48);
        l.set_pixel_size(0.003);
        l.set_position(Vector3::new(0.0, 2.6, 0.0));
        l.add_to_group("errores_carrito");
        self.base_mut().add_child(&l);
    }
}

#[godot_api]
impl INode3D for Carrito {
    fn ready(&mut self) {
        self.base_mut().add_to_group(GRUPO);
        let cat = catalogo();
        let mut config = cat.carrito_jugador.clone();
        if !self.base_forzada.is_empty() {
            config.base = self.base_forzada.to_string();
        }
        // REQ-CAR-07, REQ-CAR-08
        match armar(&config, &cat.bases, &cat.accesorios, &cat.ids_bloques()) {
            Ok(armado) => {
                self.construir_base(&armado);
                self.construir_bandeja(&armado.base);
                self.construir_accesorios(&armado);
                self.base_def = Some(armado.base.clone());
            }
            Err(e) => {
                // Se dibuja al menos la base (si existe) para que se vea dónde está el problema.
                let mensaje = e.to_string();
                let base_sola = carrito_core::carrito::ConfigCarrito {
                    accesorios: Default::default(),
                    stock: Default::default(),
                    ..config
                };
                if let Ok(a) = armar(&base_sola, &cat.bases, &cat.accesorios, &cat.ids_bloques()) {
                    self.construir_base(&a);
                    self.base_def = Some(a.base.clone());
                }
                self.mostrar_error(&mensaje);
            }
        }
    }
}
