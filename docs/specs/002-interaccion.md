# SPEC-002 · Interacción y agarre

Estado: **Implementada (etapa 1)**

## Objetivo

Tocar el mundo con las manos: agarrar comida, moverla con física real, soltarla,
tirarla, y usar equipos (encender el hervidor, sacar del depósito).

## Requisitos

- **REQ-INT-01** Una mira (punto) en el centro de la pantalla. Lo que está bajo la mira a
  2,5 m o menos es el "objetivo".
- **REQ-INT-02** Si el objetivo es interactuable, se muestra un cartel con la acción
  (ej. "[Clic] Agarrar salchicha (cruda)", "[E] Encender hervidor").
- **REQ-INT-03** Clic izquierdo sobre un objeto agarrable (comida o paquete) lo toma. El objeto queda flotando
  1 m delante de la cámara **sin perder la física**: sigue chocando con todo.
- **REQ-INT-04** El objeto agarrado se mueve hacia ese punto con velocidad proporcional a la
  distancia (como un resorte), con un tope de 8 m/s, y se le frena el giro.
- **REQ-INT-05** Si el objeto agarrado queda trabado a más de 1,5 m del punto donde debería
  estar, se suelta solo.
- **REQ-INT-06** Clic izquierdo con algo en la mano lo suelta (cae por gravedad).
  Clic derecho lo tira hacia adelante con un impulso de 4 m/s.
- **REQ-INT-07** La tecla E usa el objetivo. Con la mano libre: enciende/apaga el hervidor
  o saca una unidad de un bloque del depósito (SPEC-004). Con algo en la mano: si el
  objetivo es un pomo de aderezo, le pone aderezo a lo que sostenés o lo recarga si
  sostenés un repuesto (SPEC-012).
- **REQ-INT-08** Mientras se sostiene algo, el cartel muestra qué es y su estado de cocción.

## Criterios de aceptación

- **CA-INT-01** Agarro una salchicha, la apoyo contra la pared del hervidor y no la atraviesa.
- **CA-INT-02** Tiro un pan y rebota en el piso.

## Fuera de alcance

- Rotar el objeto a mano, sostener dos cosas, inventario de bolsillo.

## Notas de diseño

- Se eligió "resorte por velocidad" en vez de pegar el objeto a la cámara: así un objeto
  agarrado no puede atravesar paredes, y se siente físico.
