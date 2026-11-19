//! SPEC-025 · Carga los modelos 3D (`.glb`) y toca las piezas que el código cambia.
//! Las reglas (rutas, nombres de piezas, validación) están en `carrito_core::modelos`.

use std::cell::RefCell;
use std::collections::HashMap;

use carrito_core::datos::DefProducto;
use carrito_core::modelos::{self as reglas, ruta_glb};
use godot::classes::base_material_3d::{EmissionOperator, Feature, TextureParam};
use godot::classes::{MeshInstance3D, Node, Node3D, PackedScene, ResourceLoader, StandardMaterial3D};
use godot::prelude::*;

use crate::datos::catalogo;
use crate::{formas, nocturno};

thread_local! {
    static ESCENAS: RefCell<HashMap<String, Option<Gd<PackedScene>>>> = RefCell::new(HashMap::new());
}

/// Suelta las escenas guardadas al cerrar el juego.
pub fn limpiar() {
    ESCENAS.with(|c| c.borrow_mut().clear());
}

fn ruta_res(modelo: &str) -> String {
    format!("res://{}", ruta_glb(modelo))
}

/// REQ-MOD-02: avisa en la consola qué modelos nombrados en los datos no existen.
pub fn revisar_faltantes() {
    for m in reglas::faltantes(catalogo(), |r| ResourceLoader::singleton().exists(&format!("res://{r}"))) {
        godot_error!("REQ-MOD-02: {m}");
    }
}

/// Instancia un modelo (REQ-MOD-01). Si no se puede cargar devuelve `None` y avisa, para
/// que quien llama use las piezas simples (REQ-MOD-09).
pub fn instanciar(modelo: &str) -> Option<Gd<Node3D>> {
    let escena = ESCENAS.with(|c| {
        c.borrow_mut()
            .entry(modelo.to_string())
            .or_insert_with(|| {
                let ruta = ruta_res(modelo);
                if !ResourceLoader::singleton().exists(&ruta) {
                    godot_warn!("REQ-MOD-09: no está el modelo {ruta}: se usan las piezas simples");
                    return None;
                }
                match godot::tools::try_load::<PackedScene>(&ruta) {
                    Ok(e) => Some(e),
                    Err(err) => {
                        godot_warn!("REQ-MOD-09: no se pudo cargar {ruta} ({err}): se usan las piezas simples");
                        None
                    }
                }
            })
            .clone()
    })?;
    let nodo = escena.instantiate()?;
    match nodo.try_cast::<Node3D>() {
        Ok(n) => Some(n),
        Err(mut otro) => {
            godot_warn!("REQ-MOD-09: {modelo} no es un nodo 3D");
            otro.queue_free();
            None
        }
    }
}

/// Instancia el modelo y lo agrega como hijo de `padre`. Prende de noche sus luces.
pub fn agregar(padre: &mut Gd<Node3D>, modelo: &str) -> Option<Gd<Node3D>> {
    let m = instanciar(modelo)?;
    padre.add_child(&m);
    luces_de_noche(&m);
    Some(m)
}

/// Primer nodo 3D con ese nombre adentro del modelo.
pub fn buscar(raiz: &Gd<Node3D>, nombre: &str) -> Option<Gd<Node3D>> {
    raiz.find_child_ex(nombre).recursive(true).owned(false).done()?.try_cast::<Node3D>().ok()
}

fn juntar(nodo: &Gd<Node>, prefijos: &[&str], salida: &mut Vec<Gd<Node3D>>) {
    let nombre = nodo.get_name().to_string();
    if prefijos.iter().any(|p| nombre.starts_with(p))
        && let Ok(n) = nodo.clone().try_cast::<Node3D>()
    {
        salida.push(n);
    }
    for hijo in nodo.get_children().iter_shared() {
        juntar(&hijo, prefijos, salida);
    }
}

/// Todos los nodos 3D cuyo nombre empieza con alguno de los prefijos.
pub fn buscar_prefijos(raiz: &Gd<Node3D>, prefijos: &[&str]) -> Vec<Gd<Node3D>> {
    let mut v = Vec::new();
    juntar(&raiz.clone().upcast(), prefijos, &mut v);
    v
}

fn mallas(nodo: &Gd<Node3D>) -> Vec<Gd<MeshInstance3D>> {
    let mut v = Vec::new();
    let mut pila: Vec<Gd<Node>> = vec![nodo.clone().upcast()];
    while let Some(n) = pila.pop() {
        if let Ok(mi) = n.clone().try_cast::<MeshInstance3D>() {
            v.push(mi);
        }
        pila.extend(n.get_children().iter_shared());
    }
    v
}

/// Copia propia del material de cada superficie de la pieza (para cambiarle el color sin
/// tocar a los demás objetos que usan el mismo modelo). Devuelve (superficie, material).
pub fn materiales_propios(pieza: &Gd<Node3D>) -> Vec<(i32, Gd<StandardMaterial3D>)> {
    let mut v = Vec::new();
    for mut mi in mallas(pieza) {
        for s in 0..mi.get_surface_override_material_count() {
            let Some(mat) = mi.get_active_material(s) else { continue };
            let copia = mat.duplicate_resource();
            let Ok(copia) = copia.try_cast::<StandardMaterial3D>() else { continue };
            mi.set_surface_override_material(s, &copia);
            v.push((s, copia));
        }
    }
    v
}

fn con_alfa(m: &Gd<StandardMaterial3D>, c: [f32; 3]) -> Color {
    Color::from_rgba(c[0], c[1], c[2], m.get_albedo().a)
}

/// Pinta, en todo el modelo, las superficies cuyo material se llama `material` (ej. la
/// pintura del carrito: `pieza_pintura` y las tapas de las bahías, sin tocar los tiradores).
/// REQ-MOD-05
pub fn pintar_material(raiz: &Gd<Node3D>, material: &str, c: [f32; 3]) {
    for mut mi in mallas(raiz) {
        for s in 0..mi.get_surface_override_material_count() {
            let Some(mat) = mi.get_active_material(s) else { continue };
            if !mat.get_name().to_string().starts_with(material) {
                continue;
            }
            let copia = mat.duplicate_resource();
            let Ok(mut copia) = copia.try_cast::<StandardMaterial3D>() else { continue };
            let color = con_alfa(&copia, c);
            copia.set_albedo(color);
            mi.set_surface_override_material(s, &copia);
        }
    }
}

/// Un color por superficie. REQ-MOD-06
pub fn pintar_superficies(pieza: &Gd<Node3D>, colores: &[[f32; 3]]) {
    for (s, mut m) in materiales_propios(pieza) {
        if let Some(c) = colores.get(s as usize) {
            let color = con_alfa(&m, *c);
            m.set_albedo(color);
        }
    }
}

/// REQ-MOD-07: las partes que brillan (`pieza_lampara`, `pieza_luz`, …) se prenden solo de noche.
pub fn luces_de_noche(raiz: &Gd<Node3D>) {
    for pieza in buscar_prefijos(raiz, reglas::PIEZAS_LUZ) {
        for (_, mut m) in materiales_propios(&pieza) {
            let energia = if m.get_feature(Feature::EMISSION) {
                m.get_emission_energy_multiplier().max(1.0)
            } else {
                // Un cartel sin brillo propio: de noche brilla con su mismo dibujo (REQ-MOD-07).
                let albedo = m.get_albedo();
                m.set_emission(albedo);
                if let Some(t) = m.get_texture(TextureParam::ALBEDO) {
                    m.set_texture(TextureParam::EMISSION, &t);
                    // Color × dibujo, como el albedo. Con el operador por defecto (sumar) brillaría
                    // color + dibujo: casi blanco, con los colores lavados.
                    m.set_emission_operator(EmissionOperator::MULTIPLY);
                }
                0.8
            };
            nocturno::registrar(m, energia);
        }
    }
}

/// Materiales que toman el color de la cocción.
pub type Tintes = Vec<Gd<StandardMaterial3D>>;

/// Dibujo de un producto: su modelo, o sus piezas simples si no tiene o no carga.
/// Devuelve el nodo, los tintes de todo el producto y los de cada lado (REQ-MOD-05, REQ-COC-06).
pub fn visual_producto(def: &DefProducto) -> (Gd<Node3D>, Tintes, [Tintes; 2]) {
    if let Some(m) = def.modelo.as_deref().and_then(instanciar) {
        let mut tintes = Vec::new();
        for pieza in buscar_prefijos(&m, reglas::PIEZAS_COCCION) {
            tintes.extend(materiales_propios(&pieza).into_iter().map(|(_, mat)| mat));
        }
        // REQ-FRE-09: un modelo de una sola pieza que se cocina entero (las papas) toma todo
        // el color de la cocción.
        if tintes.is_empty() && def.coccion.is_some() && !def.por_lados {
            tintes.extend(materiales_propios(&m).into_iter().map(|(_, mat)| mat));
        }
        return (m, tintes, [Vec::new(), Vec::new()]);
    }
    let mut nodo = Node3D::new_alloc();
    let mut tintes = Vec::new();
    let mut tintes_lado = [Vec::new(), Vec::new()];
    for p in &def.forma {
        let mi = formas::visual_pieza(p);
        if p.tinte_coccion
            && let Some(mat) = mi.get_material_override()
        {
            tintes.push(mat.cast::<StandardMaterial3D>());
        }
        // REQ-PLA-05: cada cara toma el color de su lado.
        if let Some(lado) = p.tinte_lado.filter(|l| *l < 2)
            && let Some(mat) = mi.get_material_override()
        {
            tintes_lado[lado].push(mat.cast::<StandardMaterial3D>());
        }
        nodo.add_child(&mi);
    }
    (nodo, tintes, tintes_lado)
}
