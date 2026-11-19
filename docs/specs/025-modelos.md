# SPEC-025 · Modelos 3D

Estado: **Implementada (etapa 1)**

## Objetivo

Que el juego dibuje los modelos 3D hechos con la guía de modelado (`docs/arte/`) en lugar de
las piezas simples. Los datos dicen qué modelo usa cada cosa; el resto (física, cocción,
anclajes, depósito) sigue igual.

## Requisitos

### Datos
- **REQ-MOD-01** Productos (`productos.ron`), accesorios (`accesorios.ron`), bases de carrito
  (`carritos/*.ron`) y bloques de stock (`bloques.ron`) pueden tener un campo opcional
  `modelo: "familia/id"`, que apunta a `godot/modelos/familia/id.glb`. Si lo tienen, se dibuja
  ese modelo en vez de las piezas simples (`forma`, o el empaque dibujado por código en los
  bloques). Sin `modelo`, todo sigue como antes.
- **REQ-MOD-02** Todo `modelo` nombrado en los datos existe en disco. Si falta uno, al
  arrancar se informa qué archivo de datos, qué id y qué modelo.
- **REQ-MOD-03** Un accesorio puede correr su modelo respecto del anclaje con
  `pos_modelo: (x, y, z)` (ej. el foco, que en el modelo cuelga desde arriba).

### Cómo se usa el modelo
- **REQ-MOD-04** Colisión: los productos usan la del dato (`colision`). Los accesorios, las
  bases y el mobiliario de la plaza usan las piezas `-colonly` del modelo (guía 6.1). El
  hervidor arma por código la de su batea (REQ-COC-08): la comida tiene que poder entrar.
- **REQ-MOD-05** Piezas que el código cambia, buscadas por nombre (guía 6.2):
  - `pieza_salchicha` toma el color de la cocción (reemplaza a `tinte_coccion`, REQ-COC-06).
  - `pieza_pintura` toma el color del carrito (REQ-CAR-09).
  - En el hervidor, `pieza_agua` muestra el agua (se aclara con la temperatura) y
    `pieza_piloto` se enciende con el hervidor (REQ-COC-09).
- **REQ-MOD-06** Un accesorio puede dar colores por superficie a una pieza de su modelo con
  `superficies: [("pieza_x", [color0, color1, ...])]`. Así la sombrilla roja y la rayada usan el
  mismo modelo (guía 4.2, regla 5).
- **REQ-MOD-07** Las partes del modelo que brillan (`pieza_lampara`, `pieza_luz`,
  `pieza_lamparitas`) se prenden solo de noche, junto con las luces (REQ-DIA-06).
- **REQ-MOD-08** Los *Empties* `punto_<anclaje>` del modelo de una base están en la misma
  posición (±1 cm) que los anclajes de su `.ron`.
- **REQ-MOD-09** Si un modelo no se puede cargar en el juego, se dibujan las piezas simples
  y se avisa en la consola: el juego no se rompe.

### Contenido

- **REQ-MOD-10** Usan modelo: pan de pancho, salchicha y pancho; las tres bases; el hervidor,
  el estante, las sombrillas, la carpa, el telón, el cerco, el foco, la pizarra, el
  servilletero y la aderecera; la bolsa de panes, la bandeja de salchichas, la bandeja de
  entrega y el pallet.
- **REQ-MOD-11** La plaza usa los modelos de banco, farol y fuente, y los tres plátanos
  (`arbol_platano_a/b/c`), alternados según su lugar.
- **REQ-MOD-12** En el pancho con modelo la salchicha va hundida entre las mitades: su colisión
  mide lo mismo que el pan (0,17 × 0,045 × 0,055) y los aderezos van a la altura del dato
  `altura_aderezos` (0,0152 m).
- **REQ-MOD-13** El carro kiosco (REQ-CAR-12) y el porche de nylon usan su modelo; la puerta
  del kiosco arranca abierta (REQ-CAR-11) y gira `pieza_puerta` sobre su bisagra.
- **REQ-MOD-14** Las alacenas, los toldos, las guirnaldas, el food truck y el tráiler usan su
  modelo (SPEC-027).

## Criterios de aceptación

- **CA-MOD-01** Abro el juego: el carrito es el modelo de la barra chica, del color de
  `carrito_jugador.ron`, con sus accesorios modelados.
- **CA-MOD-02** Armo un pancho: muestra la salchicha hundida, del color de su cocción.
- **CA-MOD-03** De noche se prenden la lamparita del foco y los faroles; de día no.
- **CA-MOD-04** Borro un `.glb`: el juego avisa qué modelo falta y dibuja la pieza simple.

## Fuera de alcance (próximas etapas)

- Personajes (con esqueleto y animaciones), palomas y perro.
- Ciudad: fachadas, autos, nubes.
- Pomos y repuestos de aderezo, chorrito de aderezo, comida y equipos de la etapa 4.

## Notas de diseño

- Las rutas de modelo van sin extensión ni `res://` (`"comida/pancho"`): el juego arma
  `res://modelos/comida/pancho.glb`. Así los datos no dependen de Godot.
- La forma simple (`forma`) queda como respaldo (REQ-MOD-09) y para pruebas sin Godot.
- El modelo de cada mueble de la plaza está en `plaza.rs` (la plaza todavía no es de datos).
- Las piezas y puntos que el código busca: guía de modelado (6.2) y `docs/arte/lista-de-modelos.md`.
