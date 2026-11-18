# SPEC-014 · Modelos 3D

Estado: **Implementada (etapa 1)**

## Objetivo

Que el juego dibuje los modelos 3D hechos con la guía de modelado (`docs/arte/`) en lugar de
las piezas simples (cajas, cilindros). Los datos dicen qué modelo usa cada cosa; el resto del
juego (física, cocción, anclajes, depósito) sigue funcionando igual. Es lo que la nota de
diseño de SPEC-006 dejó previsto ("el campo de forma podrá apuntar a un `.glb`").

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
- **REQ-MOD-04** Colisión: los productos siguen usando la colisión del dato (`colision`), no la
  del modelo. Los accesorios, las bases y el mobiliario de la plaza usan las piezas
  `-colonly` del modelo (guía 6.1). El hervidor sigue armando por código la colisión de su
  batea (REQ-COC-08), porque la comida tiene que poder entrar.
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

### Contenido de la etapa 1
- **REQ-MOD-10** Usan modelo: pan de pancho, salchicha y pancho; las tres bases de carrito;
  el hervidor, el estante, las dos sombrillas, la carpa, el telón, el cerco, el foco, la
  pizarra, el servilletero y la aderecera; la bolsa de panes y la bandeja de salchichas;
  la bandeja de entrega y el pallet.
- **REQ-MOD-11** La plaza usa los modelos de banco, farol y fuente, y los tres plátanos
  (`arbol_platano_a/b/c`), alternados según su lugar para que no se vean todos iguales.
- **REQ-MOD-12** En el pancho con modelo la salchicha va hundida entre las mitades del pan:
  la colisión del pancho mide lo mismo que el pan (0,17 × 0,045 × 0,055) y los aderezos se
  dibujan a la altura que dice el dato (`altura_aderezos`, 0,0152 m en el pancho).

## Criterios de aceptación

- **CA-MOD-01** Abro el juego: el carrito es el modelo de la barra chica, pintado del color
  de `carrito_jugador.ron`, con sus accesorios modelados en los anclajes.
- **CA-MOD-02** Cocino una salchicha y la pongo en el pan: el pancho muestra la salchicha
  hundida, del color de su cocción.
- **CA-MOD-03** De noche se prenden la lamparita del foco y los faroles; de día están apagados.
- **CA-MOD-04** Borro un `.glb` y abro el juego: avisa qué modelo falta y se ve la pieza simple.

## Fuera de alcance (próximas etapas)

- Personajes (peatones y clientes, con esqueleto y animaciones), palomas y perro.
- Ciudad: fachadas, autos, nubes.
- Alacenas bajo mesada (bahías), techos y toldos, food truck, tráiler y carro kiosco
  (necesitan anclajes nuevos).
- Pomos y repuestos de aderezo, chorrito de aderezo, comida y equipos de la etapa 4.

## Notas de diseño

- Las rutas de modelo van sin extensión ni `res://` (`"comida/pancho"`): el juego arma
  `res://modelos/comida/pancho.glb`. Así los datos no dependen de Godot.
- La forma simple (`forma`) queda en los datos como respaldo (REQ-MOD-09) y para las pruebas
  sin Godot.
- El modelo de cada mueble de la plaza está en el código (`plaza.rs`), porque la plaza todavía
  no es un archivo de datos.
- Las piezas y puntos que el código busca están documentados en la guía de modelado (6.2) y en
  la columna "Notas" de `docs/arte/lista-de-modelos.md`.
