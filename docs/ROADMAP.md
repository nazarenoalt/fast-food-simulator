# Roadmap

Única fuente del estado del proyecto. Estados: ⬜ pendiente · 🔄 en curso · ✅ hecha.
Un PR = una etapa (o porción). Rama `tipo/TASK-N00-slug`; las filas `N0x` son su checklist.
Cada etapa abre con sus specs (SPEC-000) y cierra con docs al día. Formato en [CLAUDE.md](../CLAUDE.md).

## Mantenimiento
| ID | Tarea | Spec | Estado |
|---|---|---|---|
| 0001 | Proceso, CLAUDE.md, roadmap, CI de PRs y docs (`chore (docs)`) | 000 | 🔄 |
| 0002 | Dejar `cargo clippy` sin advertencias (la CI falla si aparece una) | — | ✅ |
| 0003 | Git LFS para modelos `.glb`, fuentes `.blend` e imágenes de arte | — | ✅ |

## Hechas
| ID | Tarea | Spec | Estado |
|---|---|---|---|
| 0100 | Etapa 1 · Prototipo: jugador, agarre, cocción, depósito, armado, carrito modular, día/noche, plaza | 001, 002, 003, 004, 005, 006, 007, 008 | ✅ |
| 0200 | Etapa 2 · Clientes con fila, caja y reputación, proveedor, aderezos, ciudad viva | 009, 010, 011, 012, 013 | ✅ |
| 0290 | Builds descargables Win/Mac/Linux (acción Builds) | — | ✅ |

## Etapa 2.5 · Prueba de juego (`fix (balance)`) · PR TASK-0250
| ID | Tarea | Spec | Estado |
|---|---|---|---|
| 0251 | Jugarlo y anotar fricciones (hoja de hallazgos en el PR) | — | ⬜ |
| 0252 | Ajustar sensibilidad, agarre y salto | 001, 002 | ⬜ |
| 0253 | Ajustar tiempos de cocción y paciencia | 003, 009 | ⬜ |
| 0254 | Ajustar precios y clientes por hora | 009, 010 | ⬜ |
| 0255 | Rendimiento (FPS) con ciudad y fila llena | 013 | ⬜ |

## Etapa 3 · Plancha y parrilla (`feat (cocina)`) · PR TASK-0300
| ID | Tarea | Spec | Estado |
|---|---|---|---|
| 0301 | Escribir specs 014 Plancha, 015 Parrilla, 016 Heladera | 014, 015, 016 | ✅ |
| 0302 | Plancha: hamburguesa se cocina por lados | 014 | ✅ |
| 0303 | Parrilla: choripán y carbón que se gasta | 015 | ✅ |
| 0304 | Pan tostado | 015 | ✅ |
| 0305 | Heladera y cadena de frío (la comida se echa a perder) | 016 | ✅ |
| 0306 | Aderezos nuevos: papas pay, chimichurri | 012 | ✅ |
| 0307 | Clientes piden hamburguesa y choripán (menú de varios productos) | 009 | ✅ |
| 0308 | Datos `.ron` y prueba de humo ampliada | — | ✅ |

## Etapa 3.5 · Papas fritas (`feat (cocina)`) · PR TASK-0350
| ID | Tarea | Spec | Estado |
|---|---|---|---|
| 0351 | Escribir spec 026 Papas fritas y la puerta en la 006 | 026, 006 | ✅ |
| 0352 | Modelar papas (4 estados), cajita y bolsas de arpillera de 2 y 5 kg | 026 | ✅ |
| 0353 | Modelar freidora (simple y doble), colador, pelapapas, cuchillo y cartel de cerrado (anclaje `cartel` adelante) | 026, 006 | ✅ |
| 0354 | Función Surtido y datos `.ron` con modelo | 026 | ✅ |
| 0355 | Puerta que se abre y cierra en el carro grande (y el kiosco) | 006 | ✅ |
| 0356 | Pelar y cortar papas con pelapapas y cuchillo | — | ⬜ |
| 0357 | Freír en aceite a ~180 °C con el colador | — | ⬜ |
| 0358 | Vender papas en cajita; el cartel de cerrado frena a los clientes | — | ⬜ |

## Etapa 4 · Carritos y mejoras (`feat (carrito)`) · PR TASK-0400
| ID | Tarea | Spec | Estado |
|---|---|---|---|
| 0401 | Escribir spec 006 v2 y 017 Tienda | 006, 017 | ✅ |
| 0402 | Tienda de accesorios dentro del juego (modo armado, inventario y venta) | 017 | ✅ |
| 0403 | Colocar y mover accesorios en los anclajes; techos, telones y mobiliario nuevos | 006, 017 | ✅ |
| 0404 | Cambiar estilos y colores | 006, 017 | ✅ |
| 0405 | Bases de carrito nuevas (cambiar de base ya; faltan food truck, tráiler, alacenas, toldos y guirnaldas) | 006, 017 | 🔄 |
| 0406 | Carro con interior caminable | 006 | ⬜ |
| 0407 | Logo del carrito: elegir entre varios diseños y escribirle tu texto | 006 | ⬜ |

## Etapa 5 · Plaza con rutinas (`feat (mundo)`) · PR TASK-0500
| ID | Tarea | Spec | Estado |
|---|---|---|---|
| 0501 | Escribir specs 018 Rutinas y 019 Eventos | 018, 019 | ⬜ |
| 0502 | Agenda por hora para los NPCs | 018 | ⬜ |
| 0503 | Oficinistas al mediodía, familias a la tarde, salida nocturna | 018 | ⬜ |
| 0504 | Clientes habituales que recuerdan la atención | 018 | ⬜ |
| 0505 | Eventos: feria y partido | 019 | ⬜ |

## Etapa 6a · Precios y cobro (`feat (economia)`) · PR TASK-0600
| ID | Tarea | Spec | Estado |
|---|---|---|---|
| 0601 | Escribir spec 020 Precios | 020 | ⬜ |
| 0602 | Elegir precios; la demanda reacciona | 020 | ⬜ |
| 0603 | Cobrar con billetes y dar vuelto | 020 | ⬜ |

## Etapa 6b · Gastos y progresión (`feat (economia)`) · PR TASK-0650
| ID | Tarea | Spec | Estado |
|---|---|---|---|
| 0651 | Escribir spec 021 Gastos | 021 | ⬜ |
| 0652 | Gastos fijos: permiso, gas | 021 | ⬜ |
| 0653 | Inspección de higiene | 021 | ⬜ |
| 0654 | Objetivos y progresión | 021 | ⬜ |

## Etapa 7a · Sonido y arte (`feat (ambientacion)`) · PR TASK-0700
| ID | Tarea | Spec | Estado |
|---|---|---|---|
| 0701 | Sonido y música | 013, 024 | 🔄 |
| 0702 | Modelos de Blender (`.glb`) reemplazan las piezas simples (carritos, comida, plaza y kiosco ya; faltan personajes, ciudad y equipos) | 006, 013, 025 | 🔄 |
| 0703 | Animaciones | 013 | ⬜ |

## Etapa 7b · Persistencia y clima (`feat (mundo)`) · PR TASK-0750
| ID | Tarea | Spec | Estado |
|---|---|---|---|
| 0751 | Escribir specs 022 Guardado y 023 Clima | 022, 023 | ⬜ |
| 0752 | Guardado de partida | 022 | ⬜ |
| 0753 | Menú y opciones | 022 | ⬜ |
| 0754 | Clima: lluvia y viento | 023 | ⬜ |
