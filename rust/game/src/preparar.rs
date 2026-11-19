//! SPEC-029 · Pelar y cortar en el juego: conecta la tecla E y el cartel del jugador con las
//! reglas de `carrito_core::preparar`. Las reglas no van acá.

use carrito_core::preparar::Pasada;
use godot::prelude::*;

use crate::comida::Comida;
use crate::datos::catalogo;

/// REQ-FRE-01..03: E con `en_mano` (el producto que hay en la mano) sobre `objetivo`.
/// Devuelve true si el objetivo se prepara a mano (aunque sin la herramienta no pase nada).
pub fn usar(en_mano: Option<&str>, mut objetivo: Gd<Comida>) -> bool {
    if objetivo.is_queued_for_deletion() {
        return false;
    }
    let pasada = {
        let c = objetivo.bind();
        let Some(prep) = c.preparacion() else { return false };
        prep.pasar(c.pasadas, en_mano, c.sostenida)
    };
    match pasada {
        Pasada::Nada => {}
        Pasada::Avanza(hechas) => objetivo.bind_mut().pasadas = hechas,
        Pasada::Lista(resultado) => reemplazar(objetivo, &resultado),
    }
    true
}

/// REQ-FRE-01, REQ-FRE-03: lo que se agrega al cartel al mirar `objetivo` con `en_mano`
/// (" · [E] Pelar papa (1/3)" o " · Necesitás el pelapapas"); vacío si no se prepara.
pub fn cartel(en_mano: Option<&str>, objetivo: &Gd<Comida>) -> String {
    let c = objetivo.bind();
    let Some(prep) = c.preparacion().filter(|_| !c.sostenida) else { return String::new() };
    let nombre = catalogo().producto(&prep.herramienta).map(|d| d.nombre.as_str()).unwrap_or(&prep.herramienta);
    format!(" · {}", prep.cartel(c.pasadas, en_mano, nombre))
}

/// REQ-FRE-01, REQ-FRE-02: el producto preparado ocupa el lugar del anterior, con el mismo giro
/// y apoyado a la misma altura (la base queda donde estaba).
fn reemplazar(mut vieja: Gd<Comida>, producto: &str) {
    let mut t = vieja.get_global_transform();
    let Some(def) = catalogo().producto(producto) else { return };
    let (media_altura, _, _) = crate::comida::medidas_de(def);
    let (media_altura_vieja, _, _) = vieja.bind().medidas();
    t.origin -= t.basis.col_b().normalized() * (media_altura_vieja - media_altura);
    let temp = vieja.bind().temperatura();
    let mut nueva = Comida::crear(producto);
    if let Some(temp) = temp {
        nueva.bind_mut().fijar_temperatura(temp);
    }
    if let Some(mut padre) = vieja.get_parent() {
        padre.add_child(&nueva);
    }
    nueva.set_global_transform(t);
    vieja.queue_free();
}
