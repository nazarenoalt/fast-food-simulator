# SPEC-027 · Ampliaciones del carrito

Estado: **Implementada (etapa 4, segunda parte)**

## Objetivo

Más carritos y más cosas para ponerles desde el modo armado (SPEC-017): food truck, tráiler,
alacenas bajo mesada, toldos y guirnaldas. Modelos en SPEC-025 y `docs/arte/lista-de-modelos.md`.

## Requisitos

### Food truck y tráiler
- **REQ-AMP-01** Dos bases nuevas con interior: **food truck** ($7.200, 5.000 triángulos por
  excepción) y **tráiler** ($5.200). Piso de adentro a 0,50 m con un escalón a 0,25, mesada de
  la ventana y mesada de atrás a 1,45, puerta del lado del vendedor (100°, arranca cerrada,
  REQ-CAR-13). La tapa de la ventana queda abierta, fija, como alero.
- **REQ-AMP-02** El jugador arranca **afuera, adelante** (del lado de los clientes); entra
  dando la vuelta y abriendo la puerta. Los clientes hacen fila afuera, frente a la ventana, y
  el proveedor deja el pallet afuera, del lado de la puerta.
- **REQ-AMP-03** Su anclaje `cartel` (REQ-PAP-07) va en el canto de la repisa de afuera; el
  cartel luminoso va arriba del techo, en `cartel_techo` (Decoración).

### Alacenas bajo mesada
- **REQ-AMP-04** Categoría nueva **Alacena**, que solo aceptan los anclajes `bahia_N`, en el
  `punto_bahia_N` de cada modelo: 2 en la barra chica, 3 en la mediana, 4 en el carro grande
  y en el kiosco, 3 en el food truck y 2 en el tráiler. Con una alacena puesta, la base
  esconde su `pieza_tapa_bahia_N`; al sacarla, vuelve.
- **REQ-AMP-05** Las alacenas son depósitos (SPEC-004): abierta ($100, 6 lugares), de puertas
  ($160, 4), de cajones ($180, 6) y mixta ($200, 5). Cada lugar está en el `punto_lugar_N`
  de su modelo.
- **REQ-AMP-06** Mirando una puerta o un cajón de alacena, E lo abre o lo cierra en 0,5 s
  (como la puerta del carrito). Las puertas giran 100° hacia afuera; los cajones salen 0,32 m
  hacia el vendedor llevando lo que tienen adentro. Arrancan cerrados.

### Toldos, techos y guirnaldas
- **REQ-AMP-07** Categoría nueva **Toldo** y anclaje `toldo`: en las barras y el carro grande,
  en el mismo punto que `frente` (el telón queda debajo); en el food truck y el tráiler, en la
  pared de la ventana, con la lona debajo de la tapa abierta. Toldo de frente ($50/60/80),
  rayado ($100/130/170) y enrollable ($140/180/230), en tres tamaños (REQ-TIE-11). Al food
  truck y al tráiler les entran el rayado y el enrollable medianos.
- **REQ-AMP-08** El food truck y el tráiler tienen además un anclaje `carpa` (Carpa) adelante,
  sobre la fila, que no choca con la tapa abierta.
- **REQ-AMP-09** Categoría nueva **Techo** para los techos y las marquesinas (REQ-TIE-12); la
  carpa sigue en Carpa. El anclaje `techo` acepta las dos.
- **REQ-AMP-10** Un anclaje puede pedir una categoría puesta en el carrito (`requiere`). El
  anclaje `guirnalda` (0; 2,08; profundidad/2), de las barras y el carro grande, pide Techo:
  sin techo no se ve ni se usa. Si se saca el techo (o no pasa a la base nueva), la guirnalda
  se guarda sola, con aviso. Guirnaldas ($50/65/90, tres tamaños) que se prenden de noche.
- **REQ-AMP-11** Un accesorio puede chocar con categorías (`choca_con`): no se pone si en el
  carrito hay algo de esas categorías, ni al revés (aviso: "choca con X: sacalo primero").
  Las sombrillas chocan con Techo; el toldo rayado y el enrollable, con Carpa; el toldo de
  frente, con Cartel (lo taparía). El carrito del `.ron` del jugador no puede traer choques.

## Criterios de aceptación

- **CA-AMP-01** Compro el food truck: arranco adelante, doy la vuelta, abro la puerta con E,
  subo el escalón y atiendo por la ventana.
- **CA-AMP-02** Pongo una alacena de cajones en una bahía: la tapa desaparece; abro un cajón
  con una bolsa de panes adentro y la bolsa sale con el cajón.
- **CA-AMP-03** Sin techo, el anclaje de la guirnalda no aparece; pongo un techo y aparece;
  pongo la guirnalda y saco el techo: la guirnalda va al inventario.
- **CA-AMP-04** Con una carpa puesta, el toldo rayado avisa que choca; el de frente entra.

## Fuera de alcance

- Cerrar la tapa de la ventana, estirar techos y toldos a cualquier ancho, las vitrinas del
  kiosco como depósito. Optimizar triángulos de los modelos (sesión aparte).

## Notas de diseño

- Decisiones del dueño: precios en escala pancho = $10 (REQ-ECO-07); toldo o carpa en el food
  truck aunque la ventana esté abierta, uno u otro; la sombrilla no va con techo.
