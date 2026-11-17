# Carrito

Simulador de carrito de comida rápida (panchos, hamburguesas, choripanes) en 3D con
física real, frente a una plaza. Hecho con **Godot 4.7** y **Rust** (godot-rust 0.5).

> Estado: **etapa 1 (prototipo)**: moverse, agarrar comida con física, sacar del
> depósito, hervir salchichas, armar panchos, carrito modular por datos, día y noche.
> Ver [`docs/hoja-de-ruta.md`](docs/hoja-de-ruta.md).

| | |
|---|---|
| ![Vista del jugador](docs/capturas/1_vista_jugador.png) | ![Depósito con comida visible](docs/capturas/2_deposito.png) |
| ![Hervidor y panchos](docs/capturas/3_cocinando.png) | ![Noche](docs/capturas/5_noche.png) |

*(Capturas con el renderizador de compatibilidad; en Godot con Vulkan se ve mejor.)*

## Cómo se trabaja: specs primero

Este proyecto sigue *spec-driven development* ([SPEC-000](docs/specs/000-proceso.md)):

1. Toda funcionalidad empieza como una spec en [`docs/specs/`](docs/specs/) con requisitos
   numerados (`REQ-COC-03`) y criterios de aceptación (`CA-COC-01`).
2. Cada requisito tiene un test o, si depende de Godot, un comentario `// REQ-...` en el
   código que lo cumple.
3. `cargo test` incluye un test de **trazabilidad** que falla si algún requisito no está
   citado en el código (o si el código cita uno que no existe).
4. `tools/prueba_humo.sh` abre el juego sin pantalla y verifica los criterios de aceptación
   de integración (cocinar, sacar del depósito, armar un pancho, luces de noche).

## Requisitos

- [Rust](https://rustup.rs) 1.94 o más nuevo.
- [Godot 4.7](https://godotengine.org/download) (versión estándar, no la de .NET).

## Compilar y jugar

```bash
cd rust
cargo build
```

Después abrí `godot/project.godot` con Godot y apretá **F5** (o "Ejecutar proyecto").
La primera vez Godot tarda un poco en importar el proyecto.

Cada vez que cambies código Rust, volvé a correr `cargo build`; Godot recarga la librería.

### Controles

| Tecla | Acción |
|---|---|
| W A S D | Moverse |
| Mouse | Mirar |
| Shift | Correr |
| Espacio | Saltar |
| Clic izquierdo | Agarrar / soltar |
| Clic derecho | Tirar lo que tenés en la mano |
| E | Usar (prender el hervidor, sacar del depósito) |
| T | Tiempo ×30 (para ver el atardecer rápido) |
| Esc | Soltar el mouse |

**Para hacer un pancho:** E sobre el hervidor para prenderlo → E sobre el paquete de
salchichas del estante → soltá la salchicha en el agua → esperá que esté cocida
(el cartel lo dice y cambia de color) → sacá un pan de la bolsa y dejalo en la mesada →
soltá la salchicha encima.

## Tests

```bash
cd rust && cargo test                          # reglas + trazabilidad
GODOT=/ruta/a/godot tools/prueba_humo.sh       # prueba de humo en el motor
```

## Estructura

```
docs/specs/        ← las specs (qué tiene que pasar)
docs/arte/         ← guía de modelado 3D, paleta y lista de modelos a hacer
rust/core/         ← reglas puras, sin Godot: cocción, depósito, carrito, reloj, plaza
rust/game/         ← nodos de Godot en Rust: jugador, comida, hervidor, carrito, HUD…
godot/data/        ← contenido en archivos .ron: productos, bloques, accesorios, carritos
godot/scenes/      ← escena principal y escena de prueba de humo
tools/             ← scripts (prueba de humo)
```

### Agregar contenido sin tocar código

- **Un carrito nuevo:** copiá un archivo de `godot/data/carritos/` y cambiale id, medidas
  y anclajes.
- **Un accesorio:** agregalo en `godot/data/accesorios.ron` (categoría, forma, función).
- **Cambiar tu carrito:** editá `godot/data/carrito_jugador.ron` (base, color, qué va en
  cada anclaje y el stock inicial). Si algo no encaja, el juego muestra el error arriba
  del carrito.

## Notas técnicas

- Física: **Jolt** (incluida en Godot). Las unidades guardadas en el depósito no tienen
  física hasta que se sacan, para que un depósito lleno no haga lento el juego.
- Los modelos son piezas simples (cajas, cilindros) definidas en los datos; se van a
  reemplazar por modelos de Blender (`.glb`) más adelante, siguiendo la
  [guía de modelado 3D](docs/arte/guia-modelado-3d.md) y la [lista de modelos](docs/arte/lista-de-modelos.md). Cuando haya modelos, conviene
  activar Git LFS para los archivos pesados.
- Al exportar el juego, agregá `data/*.ron` en "Filtros para exportar archivos que no son
  recursos", para que se incluyan los datos.
