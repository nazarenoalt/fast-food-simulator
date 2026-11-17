//! Lee el contenido de `res://data/` una sola vez y lo deja disponible para todos los nodos.

use std::sync::OnceLock;

use carrito_core::datos::{Catalogo, cargar_catalogo};
use godot::classes::{DirAccess, FileAccess};
use godot::prelude::*;

static CATALOGO: OnceLock<Catalogo> = OnceLock::new();

fn leer(ruta: &str) -> String {
    let texto = FileAccess::get_file_as_string(ruta).to_string();
    if texto.is_empty() {
        godot_error!("No se pudo leer {ruta}");
    }
    texto
}

pub fn catalogo() -> &'static Catalogo {
    CATALOGO.get_or_init(|| {
        // REQ-CAR-01: cada archivo de res://data/carritos/ es una base.
        let mut bases = Vec::new();
        for nombre in DirAccess::get_files_at("res://data/carritos").as_slice() {
            let nombre = nombre.to_string();
            if nombre.ends_with(".ron") {
                let texto = leer(&format!("res://data/carritos/{nombre}"));
                bases.push((nombre, texto));
            }
        }
        match cargar_catalogo(
            &leer("res://data/productos.ron"),
            &leer("res://data/bloques.ron"),
            &leer("res://data/accesorios.ron"),
            &bases,
            &leer("res://data/carrito_jugador.ron"),
            &leer("res://data/aderezos.ron"),
        ) {
            Ok(c) => c,
            Err(e) => {
                godot_error!("Error en los datos del juego: {e}");
                panic!("Error en los datos del juego: {e}");
            }
        }
    })
}
