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
  carro grande.
- **REQ-CAR-03** Cada anclaje tiene id, posición y giro relativos a la base, y la lista de
  categorías de accesorio que acepta.

### Accesorios
- **REQ-CAR-04** Categorías de accesorio: Decoración, Equipamiento, Cerco, Carpa, Telón,
  Cocina, Depósito, Sombrilla, Luz.
- **REQ-CAR-05** Un accesorio se define en `godot/data/accesorios.ron` con id, nombre,
  categoría, precio, forma visual (lista de piezas simples: caja, cilindro, esfera, cono,
  con medidas, posición y color) y opcionalmente una **función**: Hervidor, Depósito
  (con cantidad de lugares para bloques) o Luz (color, potencia, alcance).
- **REQ-CAR-06** Las luces de accesorios se prenden de noche y se apagan de día (SPEC-007).

### Configuración del carrito del jugador
- **REQ-CAR-07** El carrito del jugador es: una base + qué accesorio va en cada anclaje +
  el stock inicial de sus depósitos (`godot/data/carrito_jugador.ron`).
- **REQ-CAR-08** Validación al cargar: el anclaje existe en la base, la categoría del
  accesorio está permitida en ese anclaje, un anclaje tiene como máximo un accesorio, y el
  accesorio existe. Si algo falla, se informa el error exacto (qué anclaje, qué accesorio).
- **REQ-CAR-09** Estilo: la configuración puede cambiar el color de la base sin cambiar la base.

## Criterios de aceptación

- **CA-CAR-01** Cambio `base` a `"carro_grande"` en `carrito_jugador.ron`, abro el juego y
  aparece el carrito grande con sus accesorios en los nuevos anclajes.
- **CA-CAR-02** Pongo una sombrilla en un anclaje de mostrador: el juego avisa el error.

## Fuera de alcance (próximas etapas)

- Comprar y colocar accesorios desde el juego, carritos con interior caminable,
  remolque, modelos 3D definitivos (hoy son piezas simples).

## Notas de diseño

- Las formas de los accesorios son piezas simples (cajas, cilindros) hasta tener modelos de
  Blender. El campo de forma podrá apuntar a un `.glb` más adelante sin cambiar el resto.
