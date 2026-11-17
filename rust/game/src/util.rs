//! Atajos para encontrar los nodos "únicos" del juego por su grupo.

use godot::prelude::*;

/// Primer nodo del grupo, ya convertido a su clase.
pub fn unico<T: GodotClass + Inherits<Node>>(desde: &Gd<impl Inherits<Node>>, grupo: &str) -> Option<Gd<T>> {
    let nodo: Gd<Node> = desde.clone().upcast();
    let arbol = nodo.get_tree_or_null()?;
    arbol.get_first_node_in_group(grupo)?.try_cast::<T>().ok()
}

/// Todos los nodos del grupo de esa clase.
pub fn todos<T: GodotClass + Inherits<Node>>(desde: &Gd<impl Inherits<Node>>, grupo: &str) -> Vec<Gd<T>> {
    let nodo: Gd<Node> = desde.clone().upcast();
    let Some(arbol) = nodo.get_tree_or_null() else { return Vec::new() };
    arbol.get_nodes_in_group(grupo).iter_shared().filter_map(|n| n.try_cast::<T>().ok()).collect()
}
