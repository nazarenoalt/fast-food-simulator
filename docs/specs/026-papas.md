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
- **REQ-PAP-03** Papas crudas en bolsa de arpillera blanda (abultada, boca fruncida y atada
  hacia el vendedor): bloques `bolsa_papas_2kg` (12 papas, 2 × 3 × 2) y `bolsa_papas_5kg`
  (24 papas, 2 × 4 × 3), modelo `stock/<id>`. Los dos entran en un lugar del estante.

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
- **REQ-PAP-07** El `cartel_cerrado` (categoría Cartel) es un tablero con «CERRADO» de los dos
  lados (textura `T_cartel_cerrado`) colgado en V de un cordón desde un clavo: el origen es
  el punto de donde cuelga, la cara que se lee mira a +Z y no choca. Cada base tiene un
  anclaje `cartel` que solo acepta Cartel, **adelante** (lo ven los clientes): centrado, en el
  canto del mostrador (en el kiosco, el de la repisa de afuera), delante del telón.

## Criterios de aceptación

- **CA-PAP-01** Pongo `freidora_doble`, `tabla_papas` y `cartel_cerrado` (en `cartel`) en
  `carrito_jugador.ron`: se ven, los coladores quedan dentro de la freidora y puedo agarrar el
  cuchillo.
- **CA-PAP-02** Compro una bolsa de papas de 5 kg en el proveedor y la guardo en el estante.

## Fuera de alcance

- Pelar, cortar y freír (aceite a ~180 °C), llenar la cajita y vender papas.
- Que el cartel de cerrado frene a los clientes.

## Notas de diseño

- Colores nuevos de la paleta: `M_PapaCascara`, `M_PapaPulpa`, `M_PapaFrita` y `M_Aceite`
  (guía de modelado v1.12) y `M_Arpillera` (v1.13).
- La cajita llena (para entregar) queda para la etapa de vender papas.
- Bolsa de 5 kg: 25 papas exactas no forman una grilla que entre (a lo ancho entran 2):
  van 24 (≈ 4,8 kg). La de 2 kg lleva 12. Las papas de adentro no se ven (bolsa cerrada).
- Cartel: categoría propia para que no caiga en un mostrador ni una pizarra en el canto.
  Va adelante y no en una puerta: las dos puertas (garrafa, kiosco) dan al vendedor.
- Surtido reutiliza los productos: los utensilios no son objetos especiales.
- Modelos y hojas de revisión: `docs/arte/lista-de-modelos.md` (etapa 4).
