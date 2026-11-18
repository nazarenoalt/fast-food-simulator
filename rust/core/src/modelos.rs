//! SPEC-014 · Modelos 3D: rutas, piezas con nombre fijo y validación de los datos.
//! Sin Godot: el juego (`rust/game/src/modelos.rs`) carga los `.glb`.

use crate::datos::Catalogo;
use crate::plaza::TipoProp;

/// Piezas del modelo que toman el color de la cocción (guía 6.2). REQ-MOD-05
pub const PIEZAS_COCCION: &[&str] = &["pieza_salchicha", "pieza_carne", "pieza_chorizo"];
/// Pieza que toma el color del carrito (REQ-CAR-09). REQ-MOD-05
pub const PIEZA_PINTURA: &str = "pieza_pintura";
/// Material de la paleta que pinta el juego con el color del carrito (en `pieza_pintura` y
/// en las piezas que lo usan, como las tapas de las bahías).
pub const MATERIAL_PINTURA: &str = "M_PinturaCarrito";
/// Agua y luz piloto del hervidor. REQ-MOD-05
pub const PIEZA_AGUA: &str = "pieza_agua";
pub const PIEZA_PILOTO: &str = "pieza_piloto";
/// Puerta de las bases con interior (gira en Y sobre su bisagra). REQ-MOD-13
pub const PIEZA_PUERTA: &str = "pieza_puerta";
/// Partes que brillan solo de noche (prefijos). REQ-MOD-07. `pieza_luz` cubre también
/// `pieza_luces` (tubos del carro kiosco); `pieza_cartel` son los carteles luminosos.
pub const PIEZAS_LUZ: &[&str] = &["pieza_lampara", "pieza_luz", "pieza_luces", "pieza_lamparitas", "pieza_cartel"];
/// Punto donde una base con luces propias pone su luz nocturna (ej. el carro kiosco). REQ-MOD-07
pub const PUNTO_LUZ: &str = "punto_luz";

/// Modelos de la bandeja de entrega y del pallet (los arma el carrito, no son datos). REQ-MOD-10
pub const MODELO_BANDEJA: &str = "carritos/bandeja_entrega";
pub const MODELO_PALLET: &str = "stock/pallet";

/// "comida/pancho" → "modelos/comida/pancho.glb" (relativo a la carpeta `godot/`). REQ-MOD-01
pub fn ruta_glb(modelo: &str) -> String {
    format!("modelos/{modelo}.glb")
}

/// Todos los modelos que nombran los datos: (archivo, id, modelo). REQ-MOD-02
pub fn modelos_de_datos(cat: &Catalogo) -> Vec<(String, String, String)> {
    let mut v = Vec::new();
    for p in &cat.productos {
        if let Some(m) = &p.modelo {
            v.push(("productos.ron".into(), p.id.clone(), m.clone()));
        }
    }
    for b in &cat.bloques {
        if let Some(m) = &b.modelo {
            v.push(("bloques.ron".into(), b.id.clone(), m.clone()));
        }
    }
    for a in &cat.accesorios {
        if let Some(m) = &a.modelo {
            v.push(("accesorios.ron".into(), a.id.clone(), m.clone()));
        }
    }
    for b in &cat.bases {
        if let Some(m) = &b.modelo {
            v.push((format!("carritos/{}.ron", b.id), b.id.clone(), m.clone()));
        }
    }
    for m in [MODELO_BANDEJA, MODELO_PALLET] {
        v.push(("carrito.rs".into(), m.into(), m.into()));
    }
    for t in [TipoProp::Banco, TipoProp::Farol, TipoProp::Fuente, TipoProp::Arbol] {
        for i in 0..3 {
            v.push(("plaza.rs".into(), format!("{t:?}"), modelo_prop(t, i).into()));
        }
    }
    v.sort();
    v.dedup();
    v
}

/// REQ-MOD-02: mensajes de los modelos que no existen. `existe` recibe la ruta de
/// `ruta_glb` (el juego mira el proyecto de Godot; las pruebas, el disco).
pub fn faltantes(cat: &Catalogo, existe: impl Fn(&str) -> bool) -> Vec<String> {
    modelos_de_datos(cat)
        .into_iter()
        .filter(|(_, _, m)| !existe(&ruta_glb(m)))
        .map(|(archivo, id, m)| format!("{archivo}: \"{id}\" usa el modelo \"{m}\", que no existe ({})", ruta_glb(&m)))
        .collect()
}

/// Modelo de un mueble de la plaza. Los árboles alternan las tres variantes según su
/// número en la distribución, para que no se vean todos iguales. REQ-MOD-11
pub fn modelo_prop(tipo: TipoProp, i: usize) -> &'static str {
    match tipo {
        TipoProp::Banco => "plaza/banco",
        TipoProp::Farol => "plaza/farol",
        TipoProp::Fuente => "plaza/fuente",
        TipoProp::Arbol => ["plaza/arbol_platano_a", "plaza/arbol_platano_b", "plaza/arbol_platano_c"][i % 3],
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::datos::tests::catalogo_real;
    use std::path::PathBuf;

    fn godot() -> PathBuf {
        PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../godot")
    }

    /// Nodos de un `.glb`: (nombre, posición). Lee solo el JSON del archivo.
    fn nodos_glb(ruta: &str) -> Vec<(String, [f32; 3])> {
        let d = std::fs::read(godot().join(ruta)).unwrap();
        let n = u32::from_le_bytes(d[12..16].try_into().unwrap()) as usize;
        let j: serde_json::Value = serde_json::from_slice(&d[20..20 + n]).unwrap();
        j["nodes"]
            .as_array()
            .unwrap()
            .iter()
            .map(|nodo| {
                let t = nodo.get("translation").and_then(|t| t.as_array()).map(|t| {
                    [t[0].as_f64().unwrap() as f32, t[1].as_f64().unwrap() as f32, t[2].as_f64().unwrap() as f32]
                });
                (nodo["name"].as_str().unwrap_or("").to_string(), t.unwrap_or([0.0; 3]))
            })
            .collect()
    }

    #[test]
    fn req_mod_01_ruta_del_modelo() {
        assert_eq!(ruta_glb("comida/pancho"), "modelos/comida/pancho.glb");
        let c = catalogo_real();
        assert_eq!(c.producto("pancho").unwrap().modelo.as_deref(), Some("comida/pancho"));
    }

    #[test]
    fn req_mod_02_todos_los_modelos_existen() {
        let falta = faltantes(&catalogo_real(), |r| godot().join(r).is_file());
        assert!(falta.is_empty(), "faltan modelos:\n{}", falta.join("\n"));
    }

    #[test]
    fn req_mod_02_un_modelo_que_falta_se_informa_con_archivo_e_id() {
        let mut c = catalogo_real();
        c.productos.iter_mut().find(|p| p.id == "salchicha").unwrap().modelo = Some("comida/no_existe".into());
        let falta = faltantes(&c, |r| godot().join(r).is_file());
        assert_eq!(falta.len(), 1);
        assert!(
            falta[0].contains("productos.ron")
                && falta[0].contains("\"salchicha\"")
                && falta[0].contains("comida/no_existe")
        );
    }

    #[test]
    fn req_mod_03_06_foco_corrido_y_sombrilla_rayada_por_superficies() {
        let c = catalogo_real();
        let foco = c.accesorios.iter().find(|a| a.id == "foco_calido").unwrap();
        assert!(foco.pos_modelo[1] > 0.3, "el foco cuelga desde arriba: el modelo sube hasta el punto de enganche");
        let roja = c.accesorios.iter().find(|a| a.id == "sombrilla_roja").unwrap();
        let rayada = c.accesorios.iter().find(|a| a.id == "sombrilla_rayada").unwrap();
        assert_eq!(roja.modelo, rayada.modelo, "un solo modelo para las dos sombrillas");
        let (pieza, colores) = &rayada.superficies[0];
        assert_eq!(pieza, "pieza_pano");
        assert_eq!(colores.len(), 2);
        assert_ne!(colores[0], colores[1]);
    }

    #[test]
    fn req_mod_08_puntos_del_modelo_coinciden_con_los_anclajes() {
        for b in &catalogo_real().bases {
            let Some(m) = &b.modelo else { continue };
            let nodos = nodos_glb(&ruta_glb(m));
            for a in &b.anclajes {
                let nombre = format!("punto_{}", a.id);
                let (_, p) = nodos
                    .iter()
                    .find(|(n, _)| *n == nombre)
                    .unwrap_or_else(|| panic!("{}: falta {nombre} en {m}", b.id));
                let d = (0..3).map(|i| (p[i] - a.pos[i]).abs()).fold(0.0, f32::max);
                assert!(d <= 0.01, "{}: {nombre} está a {d:.3} m del anclaje del .ron", b.id);
            }
        }
    }

    #[test]
    fn req_mod_10_contenido_de_la_etapa_1_con_modelo() {
        let c = catalogo_real();
        for p in ["pan_pancho", "salchicha", "pancho"] {
            assert!(c.producto(p).unwrap().modelo.is_some(), "producto {p}");
        }
        for b in &c.bases {
            assert!(b.modelo.is_some(), "base {}", b.id);
        }
        for a in [
            "hervidor_chico",
            "estante_deposito",
            "sombrilla_roja",
            "sombrilla_rayada",
            "carpa_2x2",
            "telon_panchos",
            "cerco_bajo",
            "foco_calido",
            "pizarra_precios",
            "servilletero",
            "aderecera_tres",
        ] {
            assert!(c.accesorios.iter().find(|x| x.id == a).unwrap().modelo.is_some(), "accesorio {a}");
        }
        for b in ["bolsa_panes_12", "caja_salchichas_12"] {
            assert!(c.bloque(b).unwrap().modelo.is_some(), "bloque {b}");
        }
    }

    #[test]
    fn req_mod_13_kiosco_y_porche_con_modelo() {
        let c = catalogo_real();
        let k = c.bases.iter().find(|b| b.id == "carro_kiosco").unwrap();
        assert_eq!(k.modelo.as_deref(), Some("carritos/carro_kiosco"));
        let nodos = nodos_glb(&ruta_glb("carritos/carro_kiosco"));
        assert!(nodos.iter().any(|(n, _)| n == PIEZA_PUERTA), "el modelo tiene la puerta que se abre");
        let porche = c.accesorios.iter().find(|a| a.id == "porche_nylon").unwrap();
        assert_eq!(porche.modelo.as_deref(), Some("accesorios/porche_nylon"));
    }

    #[test]
    fn req_mod_11_la_plaza_alterna_los_tres_platanos() {
        let arboles: std::collections::BTreeSet<_> = crate::plaza::distribucion()
            .iter()
            .enumerate()
            .filter(|(_, p)| p.tipo == TipoProp::Arbol)
            .map(|(i, _)| modelo_prop(TipoProp::Arbol, i))
            .collect();
        assert_eq!(arboles.len(), 3, "se usan las tres variantes");
        assert_eq!(modelo_prop(TipoProp::Banco, 0), "plaza/banco");
    }

    #[test]
    fn req_mod_12_pancho_con_la_salchicha_hundida() {
        let c = catalogo_real();
        let pancho = c.producto("pancho").unwrap();
        match pancho.colision {
            crate::datos::Colision::Caja { medidas } => {
                assert!((medidas[1] - 0.045).abs() < 1e-6, "mide lo mismo que el pan")
            }
            _ => panic!("colisión de caja"),
        }
        assert_eq!(pancho.altura_aderezos, Some(0.0152));
    }
}
