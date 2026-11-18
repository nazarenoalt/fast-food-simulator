//! SPEC-006 · Construye el carrito del jugador a partir de los datos.

use std::collections::BTreeMap;

use carrito_core::carrito::{Accesorio, BaseCarrito, CarritoArmado, Colocado, ConfigCarrito, Funcion, armar};
use carrito_core::clientes::SEPARACION_FILA;
use carrito_core::forma::TipoPieza;
use godot::classes::base_material_3d::BillboardMode;
use godot::classes::{Area3D, BoxShape3D, INode3D, Label3D, Node3D};
use godot::prelude::*;

use crate::aderecera;
use crate::bloque_stock::BloqueStock;
use crate::comida::Comida;
use crate::datos::catalogo;
use crate::heladera::Heladera;
use crate::hervidor::Hervidor;
use crate::lugar_deposito::LugarDeposito;
use crate::luz::LuzNocturna;
use crate::parrilla::Parrilla;
use crate::plancha::Plancha;
use crate::puerta::PuertaCarrito;
use crate::{formas, modelos};

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
    /// Funciones de los accesorios colocados (REQ-CLI-04: qué se puede cocinar).
    funciones: Vec<&'static str>,
    /// Lo que se dibuja de la base (cuerpo, bandeja y pallet): se rehace al cambiar de base.
    raiz_base: Option<Gd<Node3D>>,
    /// anclaje → accesorio puesto y su nodo (REQ-TIE-02..05: se cambian de a uno).
    puestos: BTreeMap<String, (Accesorio, Gd<Node3D>)>,
    color: [f32; 3],
    /// Si está, se usa en lugar de la config del jugador (la prueba de humo arma así un
    /// segundo carrito).
    config_forzada: Option<ConfigCarrito>,
}

impl Carrito {
    /// Un carrito con una config propia (no la del jugador). Se llama antes de agregarlo.
    pub fn forzar_config(&mut self, config: ConfigCarrito) {
        self.config_forzada = Some(config);
    }

    /// REQ-CAR-13: la puerta de la base, si tiene.
    pub fn puerta(&self) -> Option<Gd<PuertaCarrito>> {
        self.base().find_child_ex("Puerta").recursive(true).owned(false).done()?.try_cast::<PuertaCarrito>().ok()
    }

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

    /// Dónde deja los paquetes el proveedor: el pallet (REQ-CAR-11).
    pub fn pos_pallet(&self) -> Vector3 {
        let p = self.base_def.as_ref().map(|b| b.lugar_pallet()).unwrap_or([0.8 + 1.35, 0.0, -1.0]);
        self.base().get_global_transform() * Vector3::new(p[0], p[1] + 0.12, p[2])
    }

    /// REQ-CAR-11: dónde aparece el jugador, si la base lo define (en coordenadas del mundo).
    pub fn posicion_jugador(&self) -> Option<Vector3> {
        let p = self.base_def.as_ref()?.jugador?;
        Some(self.base().get_global_transform() * formas::v3(p))
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
    /// REQ-CLI-04: productos que se pueden pedir en este carrito, con los aderezos que admiten.
    pub fn menu(&self) -> Vec<carrito_core::clientes::ItemMenu> {
        crate::datos::catalogo().menu_para(&self.funciones)
    }

    pub fn aderezos_disponibles(&self) -> Vec<String> {
        let yo = self.to_gd();
        crate::util::todos::<aderecera::Pomo>(&yo, aderecera::GRUPO)
            .iter()
            .map(|p| p.bind().aderezo().to_string())
            .collect()
    }

    /// REQ-CLI-07: bandeja roja sobre el mostrador con su zona de entrega.
    fn construir_bandeja(&mut self, b: &BaseCarrito) {
        let mut yo = self.raiz_base.clone().expect("base construida");
        let pos = formas::v3(b.entrega);
        let mut bandeja = Node3D::new_alloc();
        bandeja.set_name("BandejaEntrega");
        bandeja.set_position(pos);
        yo.add_child(&bandeja);
        // REQ-MOD-10: modelo de la bandeja (con colisión del piso), o las piezas simples.
        if modelos::agregar(&mut bandeja, carrito_core::modelos::MODELO_BANDEJA).is_none() {
            formas::construir(
                &mut bandeja,
                &[
                    formas::pieza(TipoPieza::Caja, [0.3, 0.008, 0.22], [0.0, 0.004, 0.0], [0.8, 0.12, 0.1]),
                    formas::pieza(TipoPieza::Caja, [0.3, 0.02, 0.008], [0.0, 0.01, 0.11], [0.8, 0.12, 0.1]),
                    formas::pieza(TipoPieza::Caja, [0.3, 0.02, 0.008], [0.0, 0.01, -0.11], [0.8, 0.12, 0.1]),
                ],
            );
        }
        let mut zona = formas::zona_objetos();
        let mut s = BoxShape3D::new_gd();
        s.set_size(Vector3::new(0.3, 0.14, 0.22));
        zona.add_child(&formas::nodo_colision(s.upcast(), Transform3D::IDENTITY));
        zona.set_position(Vector3::new(0.0, 0.07, 0.0));
        zona.set_monitorable(false);
        bandeja.add_child(&zona);
        self.bandeja = Some(zona);

        // Pallet del proveedor. REQ-CAR-11
        let pallet_local = formas::v3(b.lugar_pallet());
        let mut pallet = Node3D::new_alloc();
        pallet.set_name("Pallet");
        pallet.set_position(pallet_local);
        yo.add_child(&pallet);
        // REQ-MOD-10: modelo del pallet, o las piezas simples.
        if modelos::agregar(&mut pallet, carrito_core::modelos::MODELO_PALLET).is_some() {
            return;
        }
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
        if let Some(mut vieja) = self.raiz_base.take() {
            vieja.queue_free();
        }
        let mut yo = Node3D::new_alloc();
        yo.set_name("Base");
        self.base_mut().add_child(&yo);
        self.raiz_base = Some(yo.clone());
        self.color = armado.color;
        // REQ-MOD-01: el modelo de la base, con su colisión (-colonly, REQ-MOD-04) y el
        // cuerpo pintado del color elegido (REQ-MOD-05, REQ-CAR-09).
        if let Some(mut m) = b.modelo.as_deref().and_then(|m| modelos::agregar(&mut yo, m)) {
            modelos::pintar_material(&m, carrito_core::modelos::MATERIAL_PINTURA, armado.color);
            // REQ-MOD-07: si la base trae su punto_luz (luces propias), ahí va su luz de noche.
            if let Some(p) = modelos::buscar(&m, carrito_core::modelos::PUNTO_LUZ) {
                let mut luz = LuzNocturna::crear([1.0, 0.8, 0.55], 2.0, 7.0, 0.03, true);
                luz.set_position(p.get_position());
                m.add_child(&luz);
            }
            // REQ-CAR-11 / REQ-MOD-13 / REQ-CAR-13: la puerta del modelo arranca abierta o
            // cerrada según la base, y E la abre o la cierra.
            if let (Some(grados), Some(pieza)) = (b.puerta, modelos::buscar(&m, carrito_core::modelos::PIEZA_PUERTA)) {
                PuertaCarrito::envolver(pieza, grados, b.puerta_abierta);
            }
            return;
        }
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
        for c in &armado.colocados {
            self.construir_accesorio(c);
        }
        self.actualizar_funciones();
    }

    /// Un accesorio en su anclaje, con su función. REQ-CAR-03, REQ-CAR-05
    fn construir_accesorio(&mut self, c: &Colocado) {
        let mut yo = self.to_gd().upcast::<Node3D>();
        let color = self.color;
        {
            // REQ-CAR-03: el accesorio se ubica en la posición y giro del anclaje.
            let mut nodo = Node3D::new_alloc();
            nodo.set_name(&format!("{}_{}", c.anclaje.id, c.accesorio.id));
            nodo.set_position(formas::v3(c.anclaje.pos));
            nodo.set_rotation_degrees(Vector3::new(0.0, c.anclaje.rot_y, 0.0));
            yo.add_child(&nodo);

            // REQ-MOD-01: el modelo del accesorio (corrido con pos_modelo, REQ-MOD-03) o sus
            // piezas simples. El hervidor arma su propio dibujo (usa el agua y el piloto).
            let es_hervidor = matches!(c.accesorio.funcion, Some(Funcion::Hervidor { .. }));
            if !es_hervidor {
                let modelo = c.accesorio.modelo.as_deref().and_then(|m| modelos::agregar(&mut nodo, m));
                match modelo {
                    Some(mut m) => {
                        m.set_position(formas::v3(c.accesorio.pos_modelo));
                        // REQ-TIE-08: las partes pintadas del accesorio siguen el color del carrito.
                        modelos::pintar_material(&m, carrito_core::modelos::MATERIAL_PINTURA, color);
                        // REQ-MOD-06: colores por superficie (ej. la sombrilla rayada).
                        for (pieza, colores) in &c.accesorio.superficies {
                            if let Some(p) = modelos::buscar(&m, pieza) {
                                modelos::pintar_superficies(&p, colores);
                            }
                        }
                    }
                    None => formas::construir(&mut nodo, &c.accesorio.forma),
                }
            }

            // REQ-CAR-05: función del accesorio.
            match &c.accesorio.funcion {
                Some(Funcion::Hervidor { interior }) => {
                    nodo.add_child(&Hervidor::crear(*interior, c.accesorio.modelo.clone()));
                }
                Some(Funcion::Plancha { superficie }) => {
                    // REQ-PLA-01
                    nodo.add_child(&Plancha::crear(*superficie));
                }
                Some(Funcion::Parrilla { superficie }) => {
                    // REQ-PAR-01
                    nodo.add_child(&Parrilla::crear(*superficie));
                }
                Some(Funcion::Heladera { interior, lugares }) => {
                    // REQ-HEL-01
                    nodo.add_child(&Heladera::crear(*interior, lugares.clone()));
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
                Some(Funcion::Surtido { objetos }) => {
                    // REQ-PAP-06: objetos sueltos apoyados en el accesorio (el colador en la
                    // freidora, el cuchillo en la tabla); se agarran como cualquier comida.
                    for o in objetos {
                        let mut c = Comida::crear(&o.producto);
                        c.set_position(formas::v3(o.pos));
                        c.set_rotation_degrees(Vector3::new(0.0, o.rot_y, 0.0));
                        nodo.add_child(&c);
                    }
                }
                Some(Funcion::Luz { pos, color, energia, alcance }) => {
                    // REQ-CAR-06: se prende de noche (grupo luces_noche).
                    let mut luz = LuzNocturna::crear(*color, *energia, *alcance, 0.035, true);
                    luz.set_position(formas::v3(*pos));
                    nodo.add_child(&luz);
                }
                None => {}
            }
            self.puestos.insert(c.anclaje.id.clone(), (c.accesorio.clone(), nodo));
        }
    }

    /// REQ-CLI-04 / REQ-TIE-06: lo que se puede cocinar sale de lo que está puesto ahora.
    fn actualizar_funciones(&mut self) {
        self.funciones = self.puestos.values().filter_map(|(a, _)| a.funcion.as_ref()).map(|f| f.nombre()).collect();
    }

    fn anclaje_def(&self, id: &str) -> Option<carrito_core::carrito::Anclaje> {
        self.base_def.as_ref()?.anclaje(id).cloned()
    }

    fn ubicar(nodo: &mut Gd<Node3D>, a: &carrito_core::carrito::Anclaje) {
        nodo.set_position(formas::v3(a.pos));
        nodo.set_rotation_degrees(Vector3::new(0.0, a.rot_y, 0.0));
    }

    // ── Modo armado (SPEC-017) ─────────────────────────────────────

    /// La base actual.
    pub fn base_actual(&self) -> Option<&BaseCarrito> {
        self.base_def.as_ref()
    }

    /// anclaje → id del accesorio puesto.
    pub fn accesorios_puestos(&self) -> BTreeMap<String, String> {
        self.puestos.iter().map(|(k, (a, _))| (k.clone(), a.id.clone())).collect()
    }

    pub fn color(&self) -> [f32; 3] {
        self.color
    }

    /// Anclajes de la base con su posición en el mundo. REQ-TIE-01
    pub fn anclajes_globales(&self) -> Vec<(String, Vector3)> {
        let t = self.base().get_global_transform();
        let Some(b) = &self.base_def else { return Vec::new() };
        b.anclajes.iter().map(|a| (a.id.clone(), t * formas::v3(a.pos))).collect()
    }

    /// REQ-TIE-05: el depósito de ese anclaje tiene algún bloque.
    pub fn deposito_con_bloques(&self, anclaje: &str) -> bool {
        let Some((_, nodo)) = self.puestos.get(anclaje) else { return false };
        nodo.get_children()
            .iter_shared()
            .filter_map(|n| n.try_cast::<LugarDeposito>().ok())
            .any(|l| l.get_child_count() > 0)
    }

    /// Anclajes con un depósito que tiene bloques. REQ-TIE-10
    pub fn anclajes_con_bloques(&self) -> Vec<String> {
        self.puestos.keys().filter(|a| self.deposito_con_bloques(a)).cloned().collect()
    }

    /// REQ-TIE-02, REQ-TIE-03: pone un accesorio nuevo (si había otro, lo saca).
    pub fn poner(&mut self, anclaje: &str, accesorio: &Accesorio) {
        self.quitar(anclaje);
        let Some(a) = self.anclaje_def(anclaje) else { return };
        self.construir_accesorio(&Colocado { anclaje: a, accesorio: accesorio.clone(), stock: Vec::new() });
        self.actualizar_funciones();
    }

    /// REQ-TIE-05: saca el accesorio del anclaje (queda guardado en el inventario).
    pub fn quitar(&mut self, anclaje: &str) {
        if let Some((_, mut nodo)) = self.puestos.remove(anclaje) {
            nodo.queue_free();
        }
        self.actualizar_funciones();
    }

    /// REQ-TIE-04: mueve el mismo nodo (con todo su estado); si el destino está ocupado, intercambia.
    pub fn mover(&mut self, desde: &str, hasta: &str) {
        let (Some(a_desde), Some(a_hasta)) = (self.anclaje_def(desde), self.anclaje_def(hasta)) else { return };
        let Some(mut uno) = self.puestos.remove(desde) else { return };
        if let Some(mut otro) = self.puestos.remove(hasta) {
            Self::ubicar(&mut otro.1, &a_desde);
            otro.1.set_name(&format!("{}_{}", desde, otro.0.id));
            self.puestos.insert(desde.to_string(), otro);
        }
        Self::ubicar(&mut uno.1, &a_hasta);
        uno.1.set_name(&format!("{}_{}", hasta, uno.0.id));
        self.puestos.insert(hasta.to_string(), uno);
    }

    /// REQ-TIE-08: pinta la base y las partes pintadas de los accesorios.
    pub fn pintar(&mut self, color: [f32; 3]) {
        self.color = color;
        if let Some(r) = &self.raiz_base {
            modelos::pintar_material(r, carrito_core::modelos::MATERIAL_PINTURA, color);
        }
        for (_, nodo) in self.puestos.values() {
            modelos::pintar_material(nodo, carrito_core::modelos::MATERIAL_PINTURA, color);
        }
    }

    /// REQ-TIE-10: rehace la base; los accesorios de `pasan` van a su anclaje en la base nueva y
    /// el resto se saca (el inventario ya los guardó).
    pub fn cambiar_base(&mut self, armado: &CarritoArmado, pasan: &[String]) {
        self.construir_base(armado);
        self.base_def = Some(armado.base.clone());
        self.construir_bandeja(&armado.base);
        let viejos: Vec<String> = self.puestos.keys().cloned().collect();
        for anc in viejos {
            match (pasan.contains(&anc), armado.base.anclaje(&anc).cloned()) {
                (true, Some(a)) => {
                    if let Some((_, nodo)) = self.puestos.get_mut(&anc) {
                        Self::ubicar(nodo, &a);
                    }
                }
                _ => self.quitar(&anc),
            }
        }
        self.pintar(armado.color);
        self.actualizar_funciones();
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
        modelos::revisar_faltantes(); // REQ-MOD-02
        let cat = catalogo();
        let mut config = self.config_forzada.take().unwrap_or_else(|| cat.carrito_jugador.clone());
        if !self.base_forzada.is_empty() {
            config.base = self.base_forzada.to_string();
        }
        // REQ-CAR-07, REQ-CAR-08
        match armar(&config, &cat.bases, &cat.accesorios, &cat.ids_bloques()) {
            Ok(armado) => {
                self.construir_base(&armado);
                self.construir_bandeja(&armado.base);
                self.base_def = Some(armado.base.clone());
                self.construir_accesorios(&armado);
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
