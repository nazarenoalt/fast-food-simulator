# SPEC-000 · Proceso y convenciones

Estado: **Aprobada**

## Cómo trabajamos (spec-driven development)

1. **Primero la spec.** Ninguna funcionalidad se programa sin una spec en `docs/specs/`
   que diga *qué* tiene que pasar, con requisitos numerados.
2. **Después la prueba.** Cada requisito que se pueda probar sin abrir el juego tiene un
   test en Rust (`rust/core`) cuyo nombre o comentario cita su ID (ej. `REQ-COC-03`).
3. **Recién ahí el código.** El código que cumple un requisito lo cita con un comentario
   `// REQ-XXX-NN`.
4. **Trazabilidad automática.** `cargo test` corre `tests/trazabilidad.rs`, que falla si
   algún requisito de las specs no aparece citado en ningún lugar del código Rust.
5. **Prueba de humo.** `tools/prueba_humo.sh` abre el juego sin pantalla y verifica los
   criterios de aceptación de integración (cocinar, sacar del depósito, armar un pancho).
6. Cambiar una regla del juego = cambiar primero la spec, después el test, después el código.
7. **Docs al día.** `rust/core/tests/docs.rs` falla si una spec no está en la tabla de áreas,
   si el ROADMAP tiene IDs repetidos o estados inválidos, si hay enlaces rotos o si algún
   documento pasa su presupuesto de tamaño (ver [CLAUDE.md](../../CLAUDE.md)).
8. **Verificación local.** `tools/verificar.sh` corre todo lo anterior (formato, lints, tests
   y prueba de humo). La corre el dueño de la feature antes de abrir o actualizar el PR y
   pega su resultado en la descripción; la CI de GitHub solo revisa las convenciones.

Ramas, PRs y commits: ver [CLAUDE.md](../../CLAUDE.md). El estado de cada etapa vive solo en el
[ROADMAP](../ROADMAP.md).

## Formato de una spec

```
# SPEC-NNN · Título
Estado: Borrador | Aprobada | Implementada
## Objetivo            ← para qué existe, en 2-3 líneas
## Requisitos          ← REQ-ÁREA-NN, una regla verificable cada uno
## Criterios de aceptación  ← CA-ÁREA-NN, cómo se comprueba jugando
## Fuera de alcance    ← lo que explícitamente NO entra (todavía)
## Notas de diseño     ← decisiones y por qué
```

## Áreas (prefijos de IDs)

| Prefijo | Spec |
|---|---|
| JUG | 001 Jugador |
| INT | 002 Interacción y agarre |
| COC | 003 Cocción |
| DEP | 004 Depósito con comida visible |
| ARM | 005 Armado de comida |
| CAR | 006 Carrito modular |
| DIA | 007 Día y noche |
| MUN | 008 Mundo (plaza) |
| CLI | 009 Clientes |
| ECO | 010 Economía |
| PRO | 011 Proveedor |
| ADE | 012 Aderezos |
| AMB | 013 Ambientación |
| PLA | 014 Plancha |
| PAR | 015 Parrilla con carbón y pan tostado |
| HEL | 016 Heladera y cadena de frío |
| TIE | 017 Tienda y modo armado |
| SON | 024 Sonido |
| MOD | 025 Modelos 3D |

## Convenciones de código

- Nombres del dominio en castellano (`Salchicha`, `Hervidor`, `Anclaje`); la API de Godot
  y de Rust queda como es.
- `rust/core`: reglas puras, sin Godot, 100% testeables.
- `rust/game`: nodos de Godot que usan `core`. Nada de reglas de juego acá adentro.
- Contenido (carritos, accesorios, productos, bloques de stock) en archivos de datos
  `.ron` dentro de `godot/data/`. Agregar un carrito nuevo no requiere tocar código.
- Unidades: metros, kilogramos, segundos, grados Celsius.
