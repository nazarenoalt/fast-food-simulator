//! SPEC-024 (REQ-SON-10): ningún archivo de audio entra sin su crédito.

use std::fs;
use std::path::PathBuf;

fn raiz() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..")
}

#[test]
fn req_son_10_todo_archivo_de_audio_tiene_credito() {
    let creditos = fs::read_to_string(raiz().join("godot/audio/CREDITOS.md")).expect("falta godot/audio/CREDITOS.md");
    for e in fs::read_dir(raiz().join("godot/audio")).unwrap() {
        let p = e.unwrap().path();
        if p.extension().is_some_and(|x| x == "ogg") {
            let nombre = p.file_name().unwrap().to_string_lossy().into_owned();
            // Tiene que estar en la tabla "Archivos en uso" (antes de "Archivos que faltan"), con 4 columnas.
            let en_uso = creditos.split("## Archivos que faltan").next().unwrap();
            let fila = en_uso.lines().find(|l| l.contains(&format!("`{nombre}`")));
            let fila = fila.unwrap_or_else(|| panic!("{nombre} no figura en CREDITOS.md (archivos en uso)"));
            let celdas: Vec<&str> = fila.split('|').map(str::trim).filter(|c| !c.is_empty()).collect();
            assert!(
                celdas.len() >= 4 && celdas.iter().all(|c| !c.is_empty()),
                "{nombre}: faltan autor, enlace o licencia"
            );
            let lic = celdas[3].to_uppercase();
            assert!(
                lic.starts_with("CC0") || lic.starts_with("CC-BY") || lic.starts_with("CC BY"),
                "{nombre}: licencia no permitida ({lic})"
            );
            assert!(celdas[2].starts_with("http"), "{nombre}: el enlace de origen tiene que ser una URL");
        }
    }
}
