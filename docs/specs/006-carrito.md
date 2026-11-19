# SPEC-006 · Carrito modular

Estado: **Implementada (etapa 1: modelo de datos + barra chica)**

## Objetivo

Los carritos se arman como un juego de bloques: una **base** de cierto tamaño con
**anclajes** (lugares donde enganchar cosas) y **accesorios** que se enganchan en ellos.
La cantidad de tipos de carrito no está decidida, así que agregar uno tiene que ser solo
agregar un archivo de datos.

## Requisitos

### Bases
- **REQ-CAR-01** Una base se define en un archivo `godot/data/carritos/*.ron` con: id,
  nombre, medidas (ancho, profundidad, alto del mostrador), color, si tiene ruedas, y su
  lista de anclajes. Agregar un `.ron` nuevo agrega una base nueva sin tocar código.
- **REQ-CAR-02** Etapa 1 trae tres bases de distinto tamaño: barra chica, barra mediana y
  carro grande. Después se suma el **carro kiosco** (REQ-CAR-12).
- **REQ-CAR-03** Cada anclaje tiene id, posición y giro relativos a la base, y la lista de
  categorías de accesorio que acepta.

### Accesorios
- **REQ-CAR-04** Categorías de accesorio: Decoración, Equipamiento, Cerco, Carpa, Telón,
  Cocina, Depósito, Sombrilla, Luz, Porche (cerramiento para comer al costado del carro) y
  Cartel (colgante, SPEC-026); Techo, Toldo, Alacena y Guirnalda en SPEC-027.
- **REQ-CAR-05** Un accesorio se define en `godot/data/accesorios.ron` con id, nombre,
  categoría, precio, forma visual (lista de piezas simples: caja, cilindro, esfera, cono,
  con medidas, posición y color) y opcionalmente una **función**: Hervidor, Depósito
  (con cantidad de lugares para bloques), Luz (color, potencia, alcance) o Aderezos
  (qué pomos tiene, SPEC-012).
- **REQ-CAR-06** Las luces de accesorios se prenden de noche y se apagan de día (SPEC-007).

### Configuración del carrito del jugador
- **REQ-CAR-07** El carrito del jugador es: una base + qué accesorio va en cada anclaje +
  el stock inicial de sus depósitos (`godot/data/carrito_jugador.ron`).
- **REQ-CAR-08** Validación al cargar: el anclaje existe en la base, la categoría del
  accesorio está permitida en ese anclaje, un anclaje tiene como máximo un accesorio, y el
  accesorio existe. Si algo falla, se informa el error exacto (qué anclaje, qué accesorio).
- **REQ-CAR-09** Estilo: la configuración puede cambiar el color de la base sin cambiar la base.
- **REQ-CAR-10** Cada base define dónde va su bandeja de entrega sobre el mostrador
  (SPEC-009) y dónde se paran los clientes para hacer fila.
- **REQ-CAR-11** Una base puede definir además, relativos a ella: dónde aparece el jugador
  (`jugador`, si no, el lugar de la escena), dónde deja el proveedor el pallet (`pallet`, si
  no, al costado del carrito) y cuántos grados se abre la puerta de su modelo (`puerta`) y si
  arranca abierta (`puerta_abierta`, SPEC-025).
- **REQ-CAR-12** El **carro kiosco** (carro de chorizos de esquina) es una base con interior:
  el vendedor trabaja adentro, sobre un piso a 0,15 m, detrás de una vitrina con ventana de
  atención; trae techo y cartel propios (no tiene anclajes de sombrilla ni de carpa) y un
  anclaje al costado para el porche de nylon.
- **REQ-CAR-13** Mirando la puerta de una base con `puerta`, E la abre o la cierra: la
  `pieza_puerta` gira con su colisión sobre la bisagra hasta `puerta` grados (o vuelve a 0) en
  0,5 s y suena `carrito_puerta`, que no es el de la heladera (SPEC-024). El carro grande tiene
  puerta en el lugar de la garrafa; el kiosco, atrás.

## Criterios de aceptación

- **CA-CAR-01** Cambio `base` a `"carro_grande"` en `carrito_jugador.ron`, abro el juego y
  aparece el carrito grande con sus accesorios en los nuevos anclajes.
- **CA-CAR-02** Pongo una sombrilla en un anclaje de mostrador: el juego avisa el error.
- **CA-CAR-03** Con `base: "carro_kiosco"` el jugador arranca adentro del kiosco, detrás de la
  ventana, y puede salir por la puerta, que está abierta.
- **CA-CAR-04** Con el carro grande, miro la puerta de la garrafa y aprieto E: se abre; otra
  vez E: se cierra.

## Fuera de alcance (próximas etapas)

- Las vitrinas del kiosco como depósito. Food truck, tráiler y alacenas: [SPEC-027](027-ampliaciones.md).

## Notas de diseño

- Comprar, poner, mover, guardar y vender accesorios y bases desde el juego: [SPEC-017](017-tienda.md).

- Las formas de los accesorios son piezas simples (cajas, cilindros) hasta tener modelos de
  Blender. Desde SPEC-025, bases y accesorios pueden usar un modelo `.glb` (`modelo`), y la
  forma simple queda de respaldo.
