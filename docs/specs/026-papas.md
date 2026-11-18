# SPEC-026 · Papas fritas (contenido y modelos)

Estado: **Implementada (contenido: se ven, se agarran y se ubican; pelar, cortar y freír vienen después)**

## Objetivo

Tener, como datos con su modelo 3D (guía de modelado), todo lo que hace falta para vender
papas fritas: las papas en cada estado, sus envases, los utensilios, la freidora y un cartel de
cerrado. Agregarlos no toca la cocción: freír llega en otra etapa (ROADMAP).

## Requisitos

### Comida y envases (`productos.ron`, `bloques.ron`)
- **REQ-PAP-01** Existen `papa_cruda`, `papa_pelada`, `papa_cortada` y `papas_fritas`, cada
  uno con modelo `comida/<id>`, colisión y masa, y se distinguen a simple vista: cáscara marrón
  con ojos; pelada clara y facetada; bastones crudos pálidos y rectos; bastones dorados y
  torcidos. Todavía no se venden ni se cocinan.
- **REQ-PAP-02** Existe `cajita_papas` (cajita de cartón vacía, modelo `comida/cajita_papas`) y
  el bloque `pack_cajitas` para guardarlas en el depósito.
- **REQ-PAP-03** Existe el bloque `bolsa_papas` (papas crudas en bolsa de papel con ventana,
  modelo `stock/bolsa_papas`). Como todo bloque, se compra en el proveedor y entra en un lugar
  del estante.

### Utensilios (`productos.ron`)
- **REQ-PAP-04** Existen `pelapapas`, `cuchillo` y `colador_freidora` con modelo `cocina/<id>`:
  se agarran y se sueltan como cualquier objeto; no se venden ni se cocinan.

### Accesorios (`accesorios.ron`)
- **REQ-PAP-05** La `freidora` (Cocina) es angosta y profunda: dos entran en la porción de
  mesada más chica (la menor distancia entre anclajes de mostrador de las bases). La
  `freidora_doble` son dos cubas en un mueble y ocupa un solo anclaje. La cuba es hueca
  (`-colonly`) para que el colador quede adentro; el aceite es `pieza_aceite` y la perilla y la
  `pieza_piloto` miran al vendedor.
- **REQ-PAP-06** Función **Surtido**: un accesorio trae objetos sueltos ya apoyados (producto,
  posición y giro en Y relativos al accesorio). La freidora trae su colador (la doble, dos) y la
  `tabla_papas` (Equipamiento) trae el cuchillo, el pelapapas y una papa. Si un producto no
  existe, la carga falla con el id del accesorio y el del producto.
- **REQ-PAP-07** El `cartel_cerrado` (Decoración) es colgante: un tablero que cuelga de cadenas
  desde el brazo de un pie que se apoya en el mostrador, con «CERRADO» pintado de los dos lados
  (textura `T_cartel_cerrado`). Va en cualquier anclaje de mostrador que acepte Decoración.

## Criterios de aceptación

- **CA-PAP-01** Pongo `freidora_doble`, `tabla_papas` y `cartel_cerrado` en
  `carrito_jugador.ron`: se ven, los coladores quedan dentro de la freidora y puedo agarrar el
  cuchillo.
- **CA-PAP-02** Compro una bolsa de papas en el proveedor y la guardo en el estante.

## Fuera de alcance

- Pelar, cortar y freír (aceite a ~180 °C), llenar la cajita y vender papas.
- Que el cartel de cerrado frene a los clientes.

## Notas de diseño

- Colores nuevos de la paleta: `M_PapaCascara`, `M_PapaPulpa`, `M_PapaFrita` y `M_Aceite`
  (guía de modelado v1.12).
- Surtido reutiliza los productos: los utensilios no son objetos especiales.
- Modelos y hojas de revisión: `docs/arte/lista-de-modelos.md` (etapa 4).
