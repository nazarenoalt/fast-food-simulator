//! SPEC-027 · Ampliaciones del carrito: food truck, tráiler, alacenas, toldos y guirnaldas.
//! Las reglas de poner y sacar están en `tienda.rs` (requisitos y choques) y `carrito.rs`
//! (categorías y validación); acá van las medidas de las alacenas y los tests de la spec.

/// REQ-AMP-06: grados que gira la puerta de una alacena (hacia afuera, como la del carrito).
pub const APERTURA_PUERTA_ALACENA: f32 = 100.0;
/// REQ-AMP-06: metros que sale un cajón hacia el vendedor (−Z de la alacena).
pub const SALIDA_CAJON: f32 = 0.32;
/// REQ-AMP-04: lo que tapa una bahía vacía (`pieza_tapa_bahia_<n>`), en el modelo de la base.
pub const PIEZA_TAPA_BAHIA: &str = "pieza_tapa_bahia_";
/// REQ-AMP-06: puertas (`pieza_puerta_<n>`) y cajones (`pieza_cajon_<n>`) de una alacena.
pub const PIEZA_PUERTA_ALACENA: &str = "pieza_puerta_";
pub const PIEZA_CAJON: &str = "pieza_cajon_";
/// REQ-AMP-05: lugar `n` (desde 1) de un depósito con modelo.
pub const PUNTO_LUGAR: &str = "punto_lugar_";

/// REQ-AMP-04: número de bahía de un anclaje `bahia_<n>`.
pub fn bahia(anclaje: &str) -> Option<u32> {
    anclaje.strip_prefix("bahia_")?.parse().ok()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::carrito::{BaseCarrito, Categoria, ErrorCarrito, Funcion, armar};
    use crate::datos::Catalogo;
    use crate::datos::tests::catalogo_real;
    use crate::economia::Caja;
    use crate::puerta::Puerta;
    use crate::tienda::{Armado, ErrorArmado, Origen, entra};

    fn base<'a>(c: &'a Catalogo, id: &str) -> &'a BaseCarrito {
        c.bases.iter().find(|b| b.id == id).unwrap_or_else(|| panic!("falta la base {id}"))
    }

    fn rica() -> Caja {
        Caja { saldo: 1e9 }
    }

    /// Un carrito armado en la base dada, sin accesorios.
    fn vacio(c: &Catalogo, base: &str) -> Armado {
        let mut a = Armado::desde_config(&c.carrito_jugador, &c.bases);
        a.base = base.into();
        a.accesorios.clear();
        a
    }

    #[test]
    fn req_amp_01_food_truck_y_trailer() {
        let c = catalogo_real();
        for (id, precio) in [("food_truck", 7200.0), ("trailer", 5200.0)] {
            let b = base(&c, id);
            assert_eq!(b.precio, precio, "{id}");
            assert_eq!(b.modelo.as_deref(), Some(format!("carritos/{id}").as_str()));
            // Mesadas a 0,95 del piso de adentro (0,50): 1,45 desde la calle.
            assert!((b.alto_mostrador - 1.45).abs() < 1e-6, "{id}");
            assert_eq!((b.puerta, b.puerta_abierta), (Some(100.0), false), "{id}: puerta cerrada");
            for a in ["mostrador_izq", "mostrador_centro", "mostrador_der", "atras_izq", "atras_der"] {
                assert!((b.anclaje(a).unwrap().pos[1] - 1.45).abs() < 1e-6, "{id}: {a}");
            }
            // Sin techo ni sombrilla: la tapa de la ventana es su alero.
            assert!(b.anclaje("techo").is_none() && b.anclaje("sombra").is_none(), "{id}");
        }
    }

    #[test]
    fn req_amp_02_el_jugador_arranca_afuera_adelante() {
        let c = catalogo_real();
        for id in ["food_truck", "trailer"] {
            let b = base(&c, id);
            let j = b.jugador.expect("dónde arranca");
            assert!(j[1].abs() < 1e-6 && j[2] > b.profundidad / 2.0, "{id}: afuera, del lado de los clientes");
            // El pallet, afuera del lado de la puerta (−Z).
            assert!(b.lugar_pallet()[2] < -b.profundidad / 2.0, "{id}: pallet atrás");
        }
    }

    #[test]
    fn req_amp_03_cartel_en_la_repisa_y_luminoso_arriba() {
        let c = catalogo_real();
        let luminoso = c.accesorios.iter().find(|a| a.id == "cartel_luminoso").unwrap();
        for id in ["food_truck", "trailer"] {
            let b = base(&c, id);
            let cartel = b.anclaje("cartel").unwrap();
            assert_eq!(cartel.categorias, vec![Categoria::Cartel]);
            assert!(cartel.pos[1] < b.alto_mostrador, "{id}: en el canto de la repisa");
            let techo = b.anclaje("cartel_techo").unwrap();
            assert!(techo.pos[1] > 2.5 && entra(luminoso, b, techo), "{id}: el luminoso va arriba");
        }
    }

    #[test]
    fn req_amp_04_bahias_por_base_solo_para_alacenas() {
        let c = catalogo_real();
        let esperadas = [
            ("barra_chica", 2),
            ("barra_mediana", 3),
            ("carro_grande", 4),
            ("carro_kiosco", 4),
            ("food_truck", 3),
            ("trailer", 2),
        ];
        for (id, n) in esperadas {
            let b = base(&c, id);
            let bahias: Vec<_> = b.anclajes.iter().filter(|a| bahia(&a.id).is_some()).collect();
            assert_eq!(bahias.len(), n, "{id}");
            for (i, a) in bahias.iter().enumerate() {
                assert_eq!(bahia(&a.id), Some(i as u32 + 1));
                assert_eq!(a.categorias, vec![Categoria::Alacena], "{id}: {}", a.id);
            }
            // Ningún otro anclaje acepta alacenas.
            assert!(
                b.anclajes.iter().all(|a| bahia(&a.id).is_some() || !a.categorias.contains(&Categoria::Alacena)),
                "{id}"
            );
        }
        assert_eq!(bahia("bahia_3"), Some(3));
        assert_eq!(bahia("techo"), None);
    }

    #[test]
    fn req_amp_05_alacenas_son_depositos() {
        let c = catalogo_real();
        for (id, precio, lugares) in [
            ("alacena_abierta", 100.0, 6),
            ("alacena_puertas", 160.0, 4),
            ("alacena_cajones", 180.0, 6),
            ("alacena_mixta", 200.0, 5),
        ] {
            let a = c.accesorios.iter().find(|a| a.id == id).unwrap();
            assert_eq!((a.categoria, a.precio), (Categoria::Alacena, precio), "{id}");
            let Some(Funcion::Deposito { lugares: l }) = &a.funcion else { panic!("{id}: no es depósito") };
            assert_eq!(l.len(), lugares, "{id}");
            // Cada lugar coincide con su punto_lugar_N del modelo (±1 cm, con el cajón cerrado).
            let puntos = lugares_glb(a.modelo.as_deref().unwrap());
            assert_eq!(puntos.len(), lugares, "{id}: punto_lugar en el modelo");
            for (i, p) in l.iter().enumerate() {
                let m = puntos[i];
                let d = (0..3).map(|k| (p[k] - m[k]).abs()).fold(0.0, f32::max);
                assert!(d <= 0.01, "{id}: lugar {} está a {d:.3} m de su punto", i + 1);
            }
        }
    }

    /// punto_lugar_N del modelo, en orden, relativos a la raíz (sumando el cajón si son hijos).
    fn lugares_glb(modelo: &str) -> Vec<[f32; 3]> {
        let ruta = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join(format!("../../godot/modelos/{modelo}.glb"));
        let d = std::fs::read(ruta).unwrap();
        let n = u32::from_le_bytes(d[12..16].try_into().unwrap()) as usize;
        let j: serde_json::Value = serde_json::from_slice(&d[20..20 + n]).unwrap();
        let nodos = j["nodes"].as_array().unwrap();
        let t = |i: usize| -> [f32; 3] {
            let v = nodos[i].get("translation").and_then(|t| t.as_array());
            v.map(|v| [0, 1, 2].map(|k| v[k].as_f64().unwrap() as f32)).unwrap_or([0.0; 3])
        };
        let padre =
            |i: usize| nodos.iter().position(|p| p["children"].as_array().is_some_and(|c| c.contains(&i.into())));
        let mut v: Vec<(u32, [f32; 3])> = Vec::new();
        for (i, nodo) in nodos.iter().enumerate() {
            let Some(num) = nodo["name"].as_str().and_then(|s| s.strip_prefix(PUNTO_LUGAR)) else { continue };
            let mut p = t(i);
            if let Some(q) = padre(i).filter(|&q| nodos[q]["name"].as_str().is_some_and(|s| s.starts_with(PIEZA_CAJON)))
            {
                let tq = t(q);
                p = [0, 1, 2].map(|k| p[k] + tq[k]);
            }
            v.push((num.parse().unwrap(), p));
        }
        v.sort_by_key(|x| x.0);
        v.into_iter().map(|x| x.1).collect()
    }

    #[test]
    fn req_amp_06_puertas_y_cajones_de_alacena() {
        // Arrancan cerrados; E abre: la puerta gira 100° y el cajón sale 0,32 m en 0,5 s.
        for (apertura, nombre) in [(APERTURA_PUERTA_ALACENA, "puerta"), (SALIDA_CAJON, "cajón")] {
            let mut h = Puerta::nueva(apertura, false);
            assert_eq!(h.angulo(), 0.0, "{nombre}");
            h.alternar();
            h.paso(0.25);
            assert!((h.angulo() - apertura / 2.0).abs() < 1e-4, "{nombre}: a mitad de camino");
            h.paso(0.25);
            assert!((h.angulo() - apertura).abs() < 1e-5, "{nombre}: abierto en 0,5 s");
        }
        assert_eq!(APERTURA_PUERTA_ALACENA, 100.0);
        assert_eq!(SALIDA_CAJON, 0.32);
    }

    #[test]
    fn req_amp_07_toldos_en_su_anclaje() {
        let c = catalogo_real();
        for id in ["barra_chica", "barra_mediana", "carro_grande"] {
            let b = base(&c, id);
            let (t, f) = (b.anclaje("toldo").unwrap(), b.anclaje("frente").unwrap());
            assert_eq!(t.pos, f.pos, "{id}: el toldo va en el punto del frente");
            assert_eq!(t.categorias, vec![Categoria::Toldo]);
        }
        let toldos: Vec<_> = c.accesorios.iter().filter(|a| a.categoria == Categoria::Toldo).collect();
        assert_eq!(toldos.len(), 9);
        for (base_id, tam) in [("barra_chica", "chico"), ("barra_mediana", "mediano"), ("carro_grande", "grande")] {
            let b = base(&c, base_id);
            for t in ["toldo_frente", "toldo_rayado", "toldo_enrollable"] {
                let a = toldos.iter().find(|a| a.id == format!("{t}_{tam}")).unwrap();
                assert!(entra(a, b, b.anclaje("toldo").unwrap()), "{} en {base_id}", a.id);
            }
        }
        // Food truck y tráiler: rayado y enrollable medianos; el de frente no.
        for id in ["food_truck", "trailer"] {
            let b = base(&c, id);
            let anc = b.anclaje("toldo").unwrap();
            let entran: Vec<_> = toldos.iter().filter(|a| entra(a, b, anc)).map(|a| a.id.as_str()).collect();
            assert_eq!(entran, vec!["toldo_rayado_mediano", "toldo_enrollable_mediano"], "{id}");
        }
    }

    #[test]
    fn req_amp_08_carpa_adelante_en_food_truck_y_trailer() {
        let c = catalogo_real();
        let carpa = c.accesorios.iter().find(|a| a.id == "carpa_2x2").unwrap();
        for id in ["food_truck", "trailer"] {
            let b = base(&c, id);
            let anc = b.anclaje("carpa").unwrap();
            assert!(entra(carpa, b, anc), "{id}");
            // La carpa (1,9 m de fondo) empieza más allá de la fila, que queda bajo la tapa.
            assert!(anc.pos[2] - 0.95 > b.fila[2] + 0.1, "{id}: la carpa no tapa la fila ni la tapa");
        }
    }

    #[test]
    fn req_amp_09_techos_aparte_de_la_carpa() {
        let c = catalogo_real();
        for a in c.accesorios.iter().filter(|a| a.id.starts_with("techo_") || a.id.starts_with("marquesina_")) {
            assert_eq!(a.categoria, Categoria::Techo, "{}", a.id);
        }
        assert_eq!(c.accesorios.iter().find(|a| a.id == "carpa_2x2").unwrap().categoria, Categoria::Carpa);
        for b in c.bases.iter().filter(|b| b.anclaje("techo").is_some()) {
            assert_eq!(b.anclaje("techo").unwrap().categorias, vec![Categoria::Carpa, Categoria::Techo], "{}", b.id);
        }
    }

    #[test]
    fn req_amp_10_guirnalda_solo_con_techo() {
        let c = catalogo_real();
        for (id, tam) in [("barra_chica", "chico"), ("barra_mediana", "mediano"), ("carro_grande", "grande")] {
            let b = base(&c, id);
            let g = b.anclaje("guirnalda").unwrap();
            assert_eq!(g.requiere, Some(Categoria::Techo));
            assert!((g.pos[1] - 2.08).abs() < 1e-6 && (g.pos[2] - b.profundidad / 2.0).abs() < 1e-6, "{id}");
            let acc = c.accesorios.iter().find(|a| a.id == format!("guirnalda_luces_{tam}")).unwrap();
            assert!(entra(acc, b, g) && matches!(acc.funcion, Some(Funcion::Luz { .. })), "{id}");
        }
        // Sin techo no se ve ni se usa.
        let mut a = vacio(&c, "barra_mediana");
        assert!(!a.anclaje_disponible("guirnalda", &c));
        assert!(a.opciones("guirnalda", &c).is_empty());
        let e = a.poner("guirnalda", "guirnalda_luces_mediano", Origen::Tienda, false, &mut rica(), &c);
        assert_eq!(e, Err(ErrorArmado::FaltaRequisito(Categoria::Techo)));
        // Una carpa no alcanza: no tiene los caños donde se agarra.
        a.poner("techo", "carpa_2x2", Origen::Tienda, false, &mut rica(), &c).unwrap();
        assert!(!a.anclaje_disponible("guirnalda", &c));
        // Con techo aparece.
        a.poner("techo", "techo_plano_mediano", Origen::Tienda, false, &mut rica(), &c).unwrap();
        assert!(a.anclaje_disponible("guirnalda", &c));
        assert!(!a.opciones("guirnalda", &c).is_empty());
        a.poner("guirnalda", "guirnalda_luces_mediano", Origen::Tienda, false, &mut rica(), &c).unwrap();
        assert!(a.soltar_sin_requisito(&c).is_empty());
        // Saco el techo: la guirnalda se guarda sola.
        a.guardar("techo", false).unwrap();
        assert_eq!(a.soltar_sin_requisito(&c), vec![("guirnalda".to_string(), "guirnalda_luces_mediano".to_string())]);
        assert!(a.inventario.accesorios.contains(&"guirnalda_luces_mediano".to_string()));
        // Cambiar el techo por la carpa también la guarda.
        a.poner("techo", "techo_plano_mediano", Origen::Guardado, false, &mut rica(), &c).unwrap();
        a.poner("guirnalda", "guirnalda_luces_mediano", Origen::Guardado, false, &mut rica(), &c).unwrap();
        a.poner("techo", "carpa_2x2", Origen::Guardado, false, &mut rica(), &c).unwrap();
        assert_eq!(a.soltar_sin_requisito(&c).len(), 1);
        // Cambiar de base: el techo mediano no pasa a la barra chica, la guirnalda tampoco.
        a.poner("techo", "techo_plano_mediano", Origen::Guardado, false, &mut rica(), &c).unwrap();
        a.poner("guirnalda", "guirnalda_luces_mediano", Origen::Guardado, false, &mut rica(), &c).unwrap();
        let r = a.cambiar_base("barra_chica", &mut rica(), &c, &[]).unwrap();
        assert!(r.guardados.iter().any(|(anc, _)| anc == "guirnalda") && !r.pasan.contains(&"guirnalda".into()));
        assert!(!a.accesorios.contains_key("guirnalda"));
        // El carrito del .ron no puede traer una guirnalda sin techo.
        let mut cfg = c.carrito_jugador.clone();
        cfg.accesorios.insert("guirnalda".into(), "guirnalda_luces_mediano".into());
        let e = armar(&cfg, &c.bases, &c.accesorios, &[]).unwrap_err();
        assert_eq!(e, ErrorCarrito::FaltaRequisito { anclaje: "guirnalda".into(), categoria: Categoria::Techo });
    }

    #[test]
    fn req_amp_11_choques() {
        let c = catalogo_real();
        let acc = |id: &str| c.accesorios.iter().find(|a| a.id == id).unwrap().clone();
        assert!(acc("sombrilla_roja").choca(&acc("techo_curvo_mediano")));
        assert!(acc("techo_curvo_mediano").choca(&acc("sombrilla_rayada")), "vale para los dos lados");
        assert!(acc("toldo_rayado_mediano").choca(&acc("carpa_2x2")));
        assert!(acc("toldo_enrollable_grande").choca(&acc("carpa_2x2")));
        assert!(!acc("toldo_frente_mediano").choca(&acc("carpa_2x2")));
        assert!(acc("toldo_frente_mediano").choca(&acc("cartel_cerrado")));
        assert!(!acc("toldo_rayado_mediano").choca(&acc("techo_plano_mediano")), "toldo y techo conviven");
        // En el modo armado: el carrito del jugador trae sombrilla, así que el techo choca.
        let mut a = Armado::desde_config(&c.carrito_jugador, &c.bases);
        assert!(a.accesorios.contains_key("sombra"));
        let e = a.poner("techo", "techo_plano_mediano", Origen::Tienda, false, &mut rica(), &c).unwrap_err();
        assert!(matches!(&e, ErrorArmado::Choca { con, .. } if con == "Sombrilla roja"), "{e:?}");
        assert!(e.to_string().contains("sacalo primero"));
        a.guardar("sombra", false).unwrap();
        a.poner("techo", "techo_plano_mediano", Origen::Tienda, false, &mut rica(), &c).unwrap();
        // Food truck: toldo o carpa, no los dos.
        let mut f = vacio(&c, "food_truck");
        f.poner("carpa", "carpa_2x2", Origen::Tienda, false, &mut rica(), &c).unwrap();
        let e = f.poner("toldo", "toldo_rayado_mediano", Origen::Tienda, false, &mut rica(), &c);
        assert!(matches!(e, Err(ErrorArmado::Choca { .. })));
        f.guardar("carpa", false).unwrap();
        f.poner("toldo", "toldo_rayado_mediano", Origen::Tienda, false, &mut rica(), &c).unwrap();
        // Cambiar un accesorio por otro en el mismo anclaje no choca consigo mismo.
        f.poner("toldo", "toldo_enrollable_mediano", Origen::Tienda, false, &mut rica(), &c).unwrap();
        // El .ron del jugador no puede traer choques.
        let mut cfg = c.carrito_jugador.clone();
        cfg.accesorios.insert("techo".into(), "techo_plano_mediano".into());
        let e = armar(&cfg, &c.bases, &c.accesorios, &[]).unwrap_err();
        assert!(matches!(e, ErrorCarrito::Choque { .. }), "{e:?}");
        assert!(armar(&c.carrito_jugador, &c.bases, &c.accesorios, &bloques(&c)).is_ok());
    }

    fn bloques(c: &Catalogo) -> Vec<String> {
        c.bloques.iter().map(|b| b.id.clone()).collect()
    }
}
