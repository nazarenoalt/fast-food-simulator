# Carrito: guía rápida (leer primero)

Simulador 3D de carrito de comida: Godot 4.7 + Rust (godot-rust). Se desarrolla con
specs primero ([SPEC-000](docs/specs/000-proceso.md)). Qué sigue: [ROADMAP](docs/ROADMAP.md).

## Mapa (leé solo lo de tu tarea)
- `docs/ROADMAP.md`: etapas y tareas `TASK-NNNN` con su estado. **Única fuente del estado.**
- `docs/specs/NNN-*.md`: reglas por área (`REQ-ÁREA-NN`). Tabla de áreas en SPEC-000.
- `rust/core/`: reglas puras, sin Godot, con tests. Acá va toda la lógica.
- `rust/game/`: nodos Godot que usan `core`. Sin reglas de juego.
- `godot/data/*.ron`: contenido (productos, carritos, accesorios). Sin tocar código.
- `docs/jugar.md`: controles y guía para jugar. `README.md`: portada para humanos.
- No leer: `docs/capturas/`, `rust/Cargo.lock`, `rust/target/` (bloqueado en `.claude/settings.json`).

## Comandos
```bash
cd rust && cargo fmt --check && cargo clippy --all-targets && cargo test
GODOT=/ruta/godot tools/prueba_humo.sh   # humo en el motor
```
Modelos `.glb`/`.blend` e imágenes de `docs/arte/` van en Git LFS (`git lfs install` antes de clonar).
`cargo test` incluye trazabilidad specs↔código y validación de docs (`rust/core/tests/`).

## Flujo de trabajo (obligatorio)
1. **Spec → test → código.** Cambiar una regla = spec primero. Citar `REQ-XXX-NN` en el código.
2. **Un PR por etapa** (o porción grande de etapa) del ROADMAP, no por arreglo suelto.
   Cada PR sale de `main` actualizado y vuelve a `main` con squash.
3. **Rama:** `tipo/TASK-0000-slug-en-minusculas` (ej. `feat/TASK-0300-plancha-parrilla`).
   El ID es el del PR en el ROADMAP (`TASK-N00`); las subtareas `TASK-N0x` van en la descripción.
4. **Título del PR y commits:** `tipo (modulo): descripción` (ej. `feat (cocina): plancha y parrilla`).
   - Tipos: `feat fix docs refactor test chore ci perf`.
   - Módulo: área de la spec en minúscula (`jugador interaccion coccion deposito armado carrito
     dia-noche mundo clientes economia proveedor aderezos ambientacion`) o `docs ci build tools datos`.
5. **Antes de mergear:** actualizar en el mismo PR el ROADMAP (⬜→✅), las specs tocadas y
   `docs/jugar.md` si cambian controles. La CI falla si algo queda desfasado.
6. No duplicar estado ni listas en otros archivos: enlazar al ROADMAP/specs.

## Presupuesto de contexto (lo vigila `rust/core/tests/docs.rs`)
CLAUDE.md ≤ 5 KB · cada spec ≤ 4,5 KB · ROADMAP ≤ 9 KB. Si algo crece, partir la spec o resumir.
Código: castellano para el dominio, unidades SI, `cargo fmt` (ver `rust/rustfmt.toml`).
