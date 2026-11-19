# SPEC-028 · Logo del carrito

Estado: **Implementada (etapa 4)**

## Objetivo

Ponerle nombre al puesto: elegir un logo entre varios diseños, escribirle el texto y decidir
en qué lugares del carrito se ve. Es gratis, como la paleta de colores (SPEC-017).

## Requisitos

### Diseños
- **REQ-LOG-01** Los diseños están en `godot/data/logos.ron`: id, nombre, fondo, marcos (de
  afuera hacia adentro), forma (rectángulo, u óvalo con su relleno), figura opcional
  (`godot/logos/<figura>.png`), color del texto, sombra opcional, si va en mayúsculas, guardas
  de filete y subrayado. Son seis: Óvalo, Filete, Pancho, Hamburguesa, Estrella y Pizarrón.
  Solo usan colores de la paleta (guía de arte 4.5) y sus figuras existen.
- **REQ-LOG-02** El logo se acomoda a cada lugar. **Largo** (3 o más veces más ancho que alto):
  la figura a la izquierda y el texto a la derecha; las guardas, a los costados del texto.
  **Chico**: la figura arriba y el texto abajo, sin guardas. El texto va en un renglón y se
  achica hasta entrar.

### Texto
- **REQ-LOG-03** El texto tiene de 1 a 18 caracteres (se recortan los espacios de las puntas):
  letras (con tilde, ü y ñ), números, espacio y `. , ' - & !`. Si no cumple, se rechaza con
  aviso y queda el anterior.
- **REQ-LOG-04** Tipografía: DejaVu Sans Bold (`godot/fuentes/`, licencia libre), la misma de
  los carteles pintados, dibujada sin suavizado.

### Lugares
- **REQ-LOG-05** Bases y accesorios pueden traer `logos`: lugares con nombre (el que ve el
  jugador; varios pueden compartirlo), posición, giro (grados) y tamaño (ancho, alto) relativos
  a la base o al accesorio, y si brilla de noche. Ahí va una **calcomanía**: una lámina 2 mm
  delante de la superficie, con el logo dibujado por el juego.
- **REQ-LOG-06** Traen lugares: las marquesinas (el cartel entero) y el cartel luminoso (el
  frente), que brillan de noche; el kiosco ("Óvalos": los 5 óvalos del cartel corrido, que
  brillan); el food truck ("Costados": el del lado de la puerta y abajo de la ventana;
  "Atrás") y el tráiler ("Costado" del lado de la puerta y "Atrás"); las barras y el carro
  grande ("Costados": los dos del cuerpo, abajo de la mesada). Los telones no.

### Panel
- **REQ-LOG-07** El panel del carrito (REQ-TIE-07) suma **Logo**, gratis: los diseños para
  elegir, un cuadro para escribir el texto (Enter o "Aplicar"), una casilla por lugar del carrito
  actual (prendido o apagado) y "Sacar logo". Mientras se escribe, las teclas no mueven al
  jugador ni cierran el panel.
- **REQ-LOG-08** El logo se ve al instante en los lugares prendidos y se acomoda solo al poner,
  mover o sacar accesorios o al cambiar de base. Un lugar arranca prendido; uno apagado sigue
  apagado aunque cambien el diseño o el texto.
- **REQ-LOG-09** Sin logo, el carrito se ve como antes ("PANCHOS", "Lo de Tito").
- **REQ-LOG-10** `carrito_jugador.ron` puede traer `logo: Some((diseno: …, texto: …))` (y
  `apagados`); al cargar se revisan el diseño y el texto, con el error exacto.

## Criterios de aceptación

- **CA-LOG-01** En el panel elijo Estrella y escribo "Panchos El Tano": la marquesina y los
  costados del carrito muestran la estrella con ese texto.
- **CA-LOG-02** Escribo 19 letras, o un `@`: se rechaza con aviso y queda el texto anterior.
- **CA-LOG-03** Apago "Costados": queda solo en la marquesina. Saco la marquesina: su lugar
  desaparece de la lista; la vuelvo a poner y vuelve con el logo.
- **CA-LOG-04** De noche brilla el logo de la marquesina; el de los costados, no.

## Fuera de alcance

- Guardar el logo entre partidas (SPEC-022, etapa 7b), dos renglones, colores propios del logo
  y logos en los telones.

## Notas de diseño

- Decisiones del dueño: seis diseños, gratis, 18 caracteres, la tipografía de los carteles, y
  el jugador elige en qué lugares se ve.
- Calcomanía en lugar de una `pieza_` en blanco: no hay que rehacer modelos y tapa el cartel
  fijo, que vuelve a verse al sacar el logo.
- Las figuras salen de `tools/logos/figuras.py` (Pillow, sin suavizado, colores de la paleta).
