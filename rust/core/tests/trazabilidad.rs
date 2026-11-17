//! SPEC-000: cada requisito de `docs/specs/` tiene que estar citado en el código Rust,
//! ya sea como `REQ-XXX-NN` en un comentario o como nombre de test `req_xxx_nn_...`
//! (un test puede cubrir varios: `req_car_01_02_...`).

use std::collections::BTreeSet;
use std::fs;
use std::path::{Path, PathBuf};

fn raiz() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..")
}

/// IDs definidos en las specs: líneas con `**REQ-XXX-NN**`.
fn requisitos_de_specs() -> BTreeSet<String> {
    let mut ids = BTreeSet::new();
    for e in fs::read_dir(raiz().join("docs/specs")).unwrap() {
        let texto = fs::read_to_string(e.unwrap().path()).unwrap();
        for parte in texto.split("**REQ-").skip(1) {
            if let Some(fin) = parte.find("**") {
                ids.insert(format!("REQ-{}", &parte[..fin]));
            }
        }
    }
    ids
}

fn archivos_rs(dir: &Path, salida: &mut Vec<PathBuf>) {
    for e in fs::read_dir(dir).unwrap() {
        let p = e.unwrap().path();
        if p.is_dir() {
            if p.file_name().is_some_and(|n| n != "target") {
                archivos_rs(&p, salida);
            }
        } else if p.extension().is_some_and(|x| x == "rs") {
            salida.push(p);
        }
    }
}

/// IDs citados en el código.
fn requisitos_citados() -> BTreeSet<String> {
    let mut archivos = Vec::new();
    archivos_rs(&raiz().join("rust"), &mut archivos);
    let mut ids = BTreeSet::new();
    for a in archivos {
        if a.ends_with("trazabilidad.rs") {
            continue;
        }
        let texto = fs::read_to_string(&a).unwrap();
        // Forma 1: REQ-XXX-NN
        for parte in texto.split("REQ-").skip(1) {
            let id: String = parte.chars().take_while(|c| c.is_ascii_alphanumeric() || *c == '-').collect();
            ids.insert(format!("REQ-{}", id.trim_end_matches('-')));
        }
        // Forma 2: fn req_xxx_nn_mm_descripcion
        for parte in texto.split("fn req_").skip(1) {
            let mut trozos = parte.split('_');
            let Some(area) = trozos.next() else { continue };
            for t in trozos {
                if t.len() == 2 && t.chars().all(|c| c.is_ascii_digit()) {
                    ids.insert(format!("REQ-{}-{}", area.to_uppercase(), t));
                } else {
                    break;
                }
            }
        }
    }
    ids
}

#[test]
fn todos_los_requisitos_estan_citados_en_el_codigo() {
    let specs = requisitos_de_specs();
    assert!(specs.len() > 30, "se leyeron muy pocos requisitos: {specs:?}");
    let citados = requisitos_citados();
    let faltan: Vec<_> = specs.difference(&citados).collect();
    assert!(faltan.is_empty(), "Requisitos sin implementar/citar en el código: {faltan:?}");
}

#[test]
fn no_se_citan_requisitos_que_no_existen() {
    let specs = requisitos_de_specs();
    let sobran: Vec<_> = requisitos_citados().into_iter().filter(|id| !specs.contains(id)).collect();
    assert!(sobran.is_empty(), "El código cita requisitos que no están en ninguna spec: {sobran:?}");
}
