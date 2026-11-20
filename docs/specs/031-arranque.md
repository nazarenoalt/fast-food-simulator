# SPEC-031 · Arranque de la partida

Estado: **Aprobada (TASK-0250)**

## Objetivo

Empezar de a poco: un solo producto a elección, el carrito armado para ese producto y una
primera semana tranquila, para aprender a jugar antes de que se llene de gente.

## Requisitos

### Elegir con qué arrancar (TASK-0267)
- **REQ-ARR-01** Al empezar la partida se abre un panel en el medio de la pantalla: "¿Con qué
  arrancás?" con 4 botones: Pancho, Hamburguesa, Choripán y Papas fritas. El mouse queda libre
  y el reloj quieto (nadie se mueve) hasta elegir. Cuando haya menú (SPEC-022) pasa ahí.
- **REQ-ARR-02** El carrito inicial es la base común de `godot/data/carrito_jugador.ron` (base,
  color, heladera, estante, sombrilla, foco, telón y cartel de cerrado) más lo del producto
  elegido, en `godot/data/arranque.ron`:

  | Producto | Equipo | Estante |
  |---|---|---|
  | Pancho | hervidor + aderecera | 2 bolsas de pan, 2 cajas de salchichas |
  | Hamburguesa | plancha + aderecera | 2 cajas de hamburguesas |
  | Choripán | parrilla + aderecera | chorizos, pan de choripán, bolsa de carbón |
  | Papas fritas | freidora + tabla de papas | bolsa de papas de 5 kg, pack de cajitas |

  Los demás equipos se compran en la tienda (SPEC-017). La caja arranca con $120 (REQ-ECO-01).
- **REQ-ARR-03** El cartel de cerrado viene puesto en el anclaje `cartel` y arranca colgado:
  el puesto empieza cerrado (REQ-CLI-12, REQ-CLI-13) (TASK-0261).
- **REQ-ARR-04** La prueba de humo no muestra el panel y arranca con los cuatro equipos.

### Primera semana tranquila (TASK-0264)
- **REQ-ARR-05** La primera semana la cantidad de clientes (REQ-CLI-01) va subiendo:

  | Día | Lun 1 | Mar 2 | Mié 3 | Jue 4 | Vie 5 | Desde el día 6 |
  |---|---|---|---|---|---|---|
  | Clientes | ×0,3 | ×0,45 | ×0,6 | ×0,75 | ×0,9 | ×1 |
  | Lugares en la fila | 3 | 4 | 5 | 6 | 6 | 6 |

  La gente de la plaza (REQ-RUT-01) no cambia. Con la fila llena no llegan más (REQ-CLI-03);
  la tecla C la respeta igual. Los eventos esperan a la segunda semana (REQ-EVE-10).

## Criterios de aceptación

- **CA-ARR-01** Arranco, elijo Choripán: el carrito tiene parrilla y aderecera, sin hervidor ni
  plancha, y en el estante hay chorizos, pan y carbón. Los clientes solo piden choripán.
- **CA-ARR-02** El lunes nunca hay más de 3 clientes en la fila; el sábado puede haber 6.
- **CA-ARR-03** Al empezar, el cartel de cerrado está colgado y no llega nadie hasta sacarlo.

## Fuera de alcance

- Modo "Testing" (eventos desde el día 1 y mucha plata): llega con el menú (TASK-0756).
- Dificultad (TASK-0755) y tutorial guiado (TASK-0802).

## Notas de diseño

- Un producto al principio y +15% de clientes por producto nuevo (REQ-CLI-01): comprar
  equipos hace crecer el puesto (decisión del dueño).
- La rampa toca solo a los clientes: la plaza se ve viva desde el primer día.
