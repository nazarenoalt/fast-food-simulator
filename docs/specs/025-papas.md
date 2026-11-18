# SPEC-025 · Papas y utensilios (modelado)

Estado: **Implementada (solo modelado: se ven, se agarran y se ubican; freír y pelar vienen después)**

## Objetivo

Tener en el juego, como contenido de datos, todo lo necesario para las papas fritas:
la freidora, su colador, las papas en cada estado, sus envases y los utensilios de cocina.
Agregarlos no requiere tocar la lógica de cocción: esa llega en una etapa posterior (ROADMAP).

## Requisitos

### Comida y envases (`productos.ron`, `bloques.ron`)
- **REQ-PAP-01** Existen los productos `papa_cruda_sin_pelar`, `papa_pelada`, `papa_cortada` y
  `papas_fritas`. Cada uno tiene forma, colisión y masa, y se distingue de los otros a simple
  vista (color y forma).
- **REQ-PAP-02** Existe el producto `cajita_papas` (envase de cartón abierto) y el bloque
  `pack_cajitas` para guardarlas en el depósito.
- **REQ-PAP-03** Existe el bloque `bolsa_papas` (bolsa de papas crudas sin pelar) con empaque
  Bolsa. Como todo bloque, se compra en el proveedor y se guarda en un depósito.

### Utensilios (`productos.ron`)
- **REQ-PAP-04** Existen `pelapapas`, `cuchillo` y `colador_freidora` como objetos que se
  agarran y se sueltan como cualquier producto (no se venden ni se cocinan).

### Accesorios de carrito (`accesorios.ron`)
- **REQ-PAP-05** La `freidora` es un accesorio de categoría Cocina: cuba de acero con aceite,
  perilla y luz piloto. Sus paredes tienen colisión para que el colador quede adentro.
- **REQ-PAP-06** Función **Surtido**: un accesorio puede traer objetos sueltos ya apoyados
  (producto, posición y giro relativos). La freidora trae su colador; la `tabla_de_cortar`
  (Equipamiento) trae cuchillo, pelapapas y una papa. Si el producto no existe, error de carga.
- **REQ-PAP-07** Función **Cartel**: un accesorio puede mostrar un texto sobre un tablero.
  El `cartel_cerrado` (Decoración) dice «CERRADO» y se lee de frente.
- **REQ-PAP-08** Cada base tiene un anclaje para Decoración donde cabe el cartel, y la
  freidora y la tabla se pueden ubicar en algún anclaje de cada base.

## Criterios de aceptación

- **CA-PAP-01** Pongo `freidora`, `tabla_de_cortar` y `cartel_cerrado` en `carrito_jugador.ron`:
  se ven en el carrito, el colador está dentro de la freidora y puedo agarrar el cuchillo.
- **CA-PAP-02** Compro una bolsa de papas en el proveedor y la guardo en el estante.

## Fuera de alcance

- Pelar, cortar y freír (cocción en aceite a ~180 °C), llenar la cajita, vender papas.
- Que el cartel de cerrado frene a los clientes (ver ROADMAP).

## Notas de diseño

- Surtido reutiliza los productos existentes: no hay objetos especiales para utensilios.
- Los modelos son piezas simples; los `.glb` los reemplazan en la etapa de arte (SPEC-013).
