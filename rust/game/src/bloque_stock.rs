//! SPEC-004 · Un bloque de stock en el depósito, con sus unidades visibles.

use carrito_core::deposito::{Bloque, DefBloque, Empaque};
use carrito_core::forma::TipoPieza;
use godot::classes::{BoxShape3D, INode3D, Node3D, StaticBody3D};
use godot::prelude::*;

use crate::datos::catalogo;
use crate::{formas, modelos};

#[derive(GodotClass)]
#[class(base=Node3D, no_init)]
pub struct BloqueStock {
    base: Base<Node3D>,
    bloque: Bloque,
    /// Un nodo por unidad, en el mismo orden que la grilla.
    unidades: Vec<Gd<Node3D>>,
    /// Temperatura del paquete (°C). REQ-HEL-06
    temp: f32,
}

impl BloqueStock {
    pub fn crear(def: DefBloque) -> Gd<Self> {
        let temp = temp_inicial(&def);
        Self::crear_con_temp(def, temp)
    }

    pub fn crear_con_temp(def: DefBloque, temp: f32) -> Gd<Self> {
        Gd::from_init_fn(|base| Self { base, bloque: Bloque::lleno(def), unidades: Vec::new(), temp })
    }

    /// REQ-HEL-06
    pub fn temperatura(&self) -> f32 {
        self.temp
    }

    pub fn restantes(&self) -> u32 {
        self.bloque.restantes
    }

    pub fn empaque(&self) -> Empaque {
        self.bloque.def.empaque
    }

    pub fn producto(&self) -> &str {
        &self.bloque.def.producto
    }

    /// Unidades dibujadas (para pruebas). REQ-DEP-03
    pub fn unidades_visibles(&self) -> usize {
        self.unidades.len()
    }

    /// REQ-DEP-08
    pub fn cartel(&self) -> String {
        let nombre = catalogo().producto(&self.bloque.def.producto).map(|p| p.nombre.as_str()).unwrap_or("?");
        format!(
            "[E] Sacar {nombre} ({}/{}) — {}",
            self.bloque.restantes,
            self.bloque.def.capacidad(),
            self.bloque.def.nombre
        )
    }

    /// Saca una unidad. Devuelve el producto y dónde estaba (para que aparezca ahí). REQ-DEP-04
    pub fn sacar(&mut self) -> Option<(String, Vector3)> {
        let producto = self.bloque.sacar()?.to_string();
        // REQ-DEP-03: se deja de dibujar exactamente la unidad sacada (la última).
        let mut nodo = self.unidades.pop()?;
        let pos = nodo.get_global_position();
        nodo.queue_free();
        // REQ-DEP-06: bloque vacío → desaparece el paquete y el lugar queda libre.
        if self.bloque.vacio() {
            self.base_mut().queue_free();
        }
        Some((producto, pos))
    }
}

/// REQ-HEL-06: la carne viene de la distribuidora a 4 °C; lo demás, a temperatura ambiente.
pub fn temp_inicial(def: &DefBloque) -> f32 {
    let perecedero = catalogo().producto(&def.producto).is_some_and(|p| p.perecedero);
    if perecedero { carrito_core::heladera::TEMP_INTERIOR } else { carrito_core::TEMP_AMBIENTE }
}

/// Dibuja las unidades restantes y el paquete de un bloque como hijos de `padre`.
/// Devuelve los nodos de las unidades, en el orden de la grilla. REQ-DEP-02, REQ-DEP-06
pub fn construir_visual(padre: &mut Gd<Node3D>, def: &DefBloque, restantes: u32) -> Vec<Gd<Node3D>> {
    let producto = catalogo().producto(&def.producto).expect("producto del bloque").clone();
    let [tx, ty, tz] = def.tamano();
    let mut unidades = Vec::new();

    // REQ-DEP-02: cada unidad restante es un objeto 3D real en su lugar (sin física).
    for i in 0..restantes {
        let mut unidad = Node3D::new_alloc();
        unidad.add_child(&modelos::visual_producto(&producto).0); // SPEC-025
        unidad.set_position(formas::v3(def.posicion_unidad(i)));
        padre.add_child(&unidad);
        unidades.push(unidad);
    }

    // REQ-DEP-06: el paquete (REQ-MOD-01: su modelo, si tiene).
    if let Some(m) = &def.modelo
        && modelos::agregar(padre, m).is_some()
    {
        return unidades;
    }
    let c = def.color_empaque;
    match def.empaque {
        Empaque::Bolsa => {
            let mut bolsa = formas::pieza(TipoPieza::Caja, [tx + 0.01, ty + 0.01, tz + 0.01], [0.0, ty / 2.0, 0.0], c);
            bolsa.alfa = 0.22;
            padre.add_child(&formas::visual_pieza(&bolsa));
            let nudo = formas::pieza(TipoPieza::Esfera, [0.02, 0.0, 0.0], [0.0, ty / 2.0, -tz / 2.0 - 0.015], c);
            padre.add_child(&formas::visual_pieza(&nudo));
        }
        Empaque::Bandeja => {
            let alto = (ty * 0.45).max(0.015);
            let e = 0.004;
            for (m, p) in [
                ([tx + 2.0 * e, e, tz + 2.0 * e], [0.0, -e / 2.0, 0.0]),
                ([tx + 2.0 * e, alto, e], [0.0, alto / 2.0, tz / 2.0 + e / 2.0]),
                ([tx + 2.0 * e, alto, e], [0.0, alto / 2.0, -tz / 2.0 - e / 2.0]),
                ([e, alto, tz], [tx / 2.0 + e / 2.0, alto / 2.0, 0.0]),
                ([e, alto, tz], [-tx / 2.0 - e / 2.0, alto / 2.0, 0.0]),
            ] {
                padre.add_child(&formas::visual_pieza(&formas::pieza(TipoPieza::Caja, m, p, c)));
            }
            let mut film = formas::pieza(
                TipoPieza::Caja,
                [tx + 0.008, ty + 0.004, tz + 0.008],
                [0.0, ty / 2.0, 0.0],
                [0.95, 0.95, 1.0],
            );
            film.alfa = 0.15;
            padre.add_child(&formas::visual_pieza(&film));
        }
    }
    unidades
}

#[godot_api]
impl INode3D for BloqueStock {
    fn physics_process(&mut self, delta: f64) {
        // REQ-HEL-06: dentro de la heladera toma su temperatura; en el estante, la del ambiente.
        // El bloque cuelga de un LugarDeposito, y ese de la heladera.
        let entorno = self
            .base()
            .get_parent()
            .and_then(|l| l.get_parent())
            .and_then(|h| h.try_cast::<crate::heladera::Heladera>().ok())
            .map(|h| h.bind().temperatura())
            .unwrap_or(carrito_core::TEMP_AMBIENTE);
        self.temp =
            carrito_core::heladera::acercar(self.temp, entorno, carrito_core::heladera::K_PAQUETE, delta as f32);
    }

    fn ready(&mut self) {
        let def = self.bloque.def.clone();
        let [tx, ty, tz] = def.tamano();
        let mut yo = self.to_gd().upcast::<Node3D>();
        self.unidades = construir_visual(&mut yo, &def, self.bloque.restantes);

        // Cuerpo para que la mira lo detecte y se pueda apoyar cosas encima.
        let mut cuerpo = StaticBody3D::new_alloc();
        let mut s = BoxShape3D::new_gd();
        s.set_size(Vector3::new(tx + 0.01, ty + 0.01, tz + 0.01));
        cuerpo.add_child(&formas::nodo_colision(
            s.upcast(),
            Transform3D::new(Basis::IDENTITY, Vector3::new(0.0, ty / 2.0, 0.0)),
        ));
        yo.add_child(&cuerpo);
    }
}
