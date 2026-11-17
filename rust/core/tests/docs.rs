//! SPEC-000 (punto 7): la documentación no se puede desfasar ni crecer sin control.

use std::collections::BTreeSet;
use std::fs;
use std::path::{Path, PathBuf};

fn raiz() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..")
}

fn leer(ruta: &str) -> String {
    fs::read_to_string(raiz().join(ruta)).unwrap_or_else(|e| panic!("no se pudo leer {ruta}: {e}"))
}

/// Números de las specs que existen como archivo (`014-plancha.md` → "014"), sin la 000.
fn specs_existentes() -> BTreeSet<String> {
    let mut ids = BTreeSet::new();
    for e in fs::read_dir(raiz().join("docs/specs")).unwrap() {
        let nombre = e.unwrap().file_name().to_string_lossy().into_owned();
        if nombre.ends_with(".md") && nombre != "000-proceso.md" {
            ids.insert(nombre[..3].to_string());
        }
    }
    ids
}

#[test]
fn presupuesto_de_tamano() {
    let limites = [("CLAUDE.md", 5_000), ("docs/ROADMAP.md", 9_000), ("README.md", 6_000)];
    for (ruta, max) in limites {
        let n = leer(ruta).len();
        assert!(n <= max, "{ruta} pesa {n} bytes (máximo {max}): resumir o partir");
    }
    for n in specs_existentes() {
        let ruta = fs::read_dir(raiz().join("docs/specs"))
            .unwrap()
            .map(|e| e.unwrap().path())
            .find(|p| p.file_name().unwrap().to_string_lossy().starts_with(&n))
            .unwrap();
        let bytes = fs::metadata(&ruta).unwrap().len();
        assert!(bytes <= 4_500, "{} pesa {bytes} bytes (máximo 4500): partir la spec", ruta.display());
    }
}

#[test]
fn cada_spec_tiene_estado_valido_y_esta_en_la_tabla_de_areas() {
    let proceso = leer("docs/specs/000-proceso.md");
    for e in fs::read_dir(raiz().join("docs/specs")).unwrap() {
        let p = e.unwrap().path();
        let nombre = p.file_name().unwrap().to_string_lossy().into_owned();
        let texto = fs::read_to_string(&p).unwrap();
        let estado = texto
            .lines()
            .find_map(|l| l.strip_prefix("Estado: "))
            .unwrap_or_else(|| panic!("{nombre}: falta la línea `Estado:`"));
        let estado = estado.trim_start_matches('*');
        assert!(
            ["Borrador", "Aprobada", "Implementada"].iter().any(|v| estado.starts_with(v)),
            "{nombre}: estado inválido `{estado}`"
        );
        if nombre != "000-proceso.md" {
            // fila de la tabla: `| JUG | 001 Jugador |`
            let fila = format!("| {} ", &nombre[..3]);
            assert!(
                proceso.lines().any(|l| l.starts_with("| ") && l.contains(&fila)),
                "{nombre}: no está en la tabla de áreas de SPEC-000"
            );
        }
    }
}

#[test]
fn roadmap_ids_unicos_estados_validos_y_specs_reales() {
    let specs = specs_existentes();
    let mut ids = BTreeSet::new();
    let mut filas = 0;
    for linea in leer("docs/ROADMAP.md").lines() {
        let celdas: Vec<&str> = linea.split('|').map(str::trim).collect();
        // `| 0301 | Tarea | 014, 015 | ⬜ |` → ["", id, tarea, spec, estado, ""]
        if celdas.len() != 6 || celdas[1].len() != 4 || !celdas[1].chars().all(|c| c.is_ascii_digit()) {
            continue;
        }
        filas += 1;
        assert!(ids.insert(celdas[1].to_string()), "ID repetido en el ROADMAP: TASK-{}", celdas[1]);
        assert!(["⬜", "🔄", "✅"].contains(&celdas[4]), "TASK-{}: estado inválido `{}`", celdas[1], celdas[4]);
        if celdas[4] == "✅" && celdas[3] != "—" {
            for s in celdas[3].split(',').map(str::trim) {
                assert!(specs.contains(s), "TASK-{} está ✅ pero la spec {s} no existe", celdas[1]);
            }
        }
    }
    assert!(filas >= 30, "se leyeron muy pocas tareas del ROADMAP ({filas})");
}

fn markdowns(dir: &Path, salida: &mut Vec<PathBuf>) {
    for e in fs::read_dir(dir).unwrap() {
        let p = e.unwrap().path();
        let nombre = p.file_name().unwrap().to_string_lossy().into_owned();
        if p.is_dir() {
            if !["target", ".git", ".godot", "node_modules"].contains(&nombre.as_str()) {
                markdowns(&p, salida);
            }
        } else if nombre.ends_with(".md") {
            salida.push(p);
        }
    }
}

#[test]
fn los_enlaces_relativos_de_los_md_existen() {
    let mut archivos = Vec::new();
    markdowns(&raiz(), &mut archivos);
    assert!(archivos.len() >= 5);
    let mut rotos = Vec::new();
    for a in archivos {
        let texto = fs::read_to_string(&a).unwrap();
        for parte in texto.split("](").skip(1) {
            let Some(fin) = parte.find(')') else { continue };
            let destino = parte[..fin].split('#').next().unwrap_or("");
            if destino.is_empty() || destino.contains("://") || destino.starts_with("mailto:") {
                continue;
            }
            if !a.parent().unwrap().join(destino).exists() {
                rotos.push(format!("{} → {destino}", a.strip_prefix(raiz()).unwrap().display()));
            }
        }
    }
    assert!(rotos.is_empty(), "enlaces rotos: {rotos:?}");
}
