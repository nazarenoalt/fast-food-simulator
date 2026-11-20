# SPEC-002 · Interacción y agarre

Estado: **Implementada (etapa 2.5: agarre cercano, colocar con la mira; TASK-0250)**

## Objetivo

Tocar el mundo con las manos: agarrar comida, moverla con física real, soltarla,
tirarla, y usar equipos (encender el hervidor, sacar del depósito).

## Requisitos

- **REQ-INT-01** Lo que está bajo la mira a 2,5 m o menos es el "objetivo". Con la mano libre
  la mira es un punto chico; con algo en la mano es un **puntero blanco en cruz**, bien
  visible, que marca dónde va a quedar al colocarlo (REQ-INT-09).
- **REQ-INT-02** Si el objetivo es interactuable, se muestra un cartel con la acción
  (ej. "[Clic] Agarrar salchicha (cruda)", "[E] Encender hervidor").
- **REQ-INT-03** Clic izquierdo sobre un objeto agarrable (comida, paquete o bloque del
  depósito, REQ-DEP-09) lo toma. Queda cerca, abajo a la derecha de la vista, como en la mano:
  0,2 m a la derecha, 0,17 m abajo y 0,35 m + media medida del objeto adelante de los ojos,
  **derecho** (TASK-0265): acostado como sobre una mesa, con su largo cruzado a la vista, la
  parte de arriba (la salchicha del pancho) hacia arriba e inclinado 25° hacia los ojos. Lo que
  se cocina por lados conserva qué cara mira abajo. **No pierde la física**: choca con todo
  menos con el jugador.
- **REQ-INT-04** El objeto agarrado va hacia ese punto con velocidad proporcional a la
  distancia (resorte, ×20) con un tope de 12 m/s, y su giro va hacia el de la cámara igual.
- **REQ-INT-05** Si el objeto agarrado queda trabado a más de 1,5 m del punto donde debería
  estar, se suelta solo.
- **REQ-INT-06** Clic izquierdo con algo en la mano lo **coloca** (REQ-INT-09) donde apunta la
  cruz, a 3 m o menos, sin calcular la distancia (TASK-0260). Si ahí no hay dónde apoyarlo
  (lejos, una pared, el cielo), lo suelta donde está y cae al piso (el cartel dice "Soltar").
  Clic derecho lo tira hacia la mira con un impulso de 4 m/s.
- **REQ-INT-07** La tecla E usa el objetivo. Con la mano libre: enciende/apaga el hervidor
  o saca una unidad de un bloque del depósito (SPEC-004). Con algo en la mano: aderezos y
  repuestos sobre un pomo (SPEC-012); un paquete sobre el hervidor se vuelca (REQ-COC-10).
- **REQ-INT-08** Mientras se sostiene algo, el cartel muestra qué es, su estado de cocción y
  qué hace el clic ahí ("Apoyar", "Poner en el pan", "Guardar en el estante", "Al agua").
  El clic hace siempre lo que dice el cartel (TASK-0263: "Guardar" guarda, no tira al piso).
- **REQ-INT-09** Colocar deja el objeto quieto donde toca la mira: sobre una superficie
  inclinada 50° o menos, parado encima del punto, derecho y girado hacia donde mira el
  jugador. Un paquete con la mira a 0,3 m o menos de un lugar libre del depósito va centrado
  a ese lugar y se guarda (REQ-PRO-06). Con la mira en cualquier parte del hervidor (borde,
  cuba o agua), lo que se cocina en agua va al agua, al primer lugar libre (REQ-COC-10).
- **REQ-INT-10** Con un agregado en la mano (salchicha, chorizo) y la mira en una base que lo
  combina (REQ-ARM-01), colocar lo pone en la zona de encastre de la base, y se arma (REQ-ARM-02).

## Criterios de aceptación

- **CA-INT-01** Agarro una salchicha, la apoyo contra la pared del hervidor y no la atraviesa.
- **CA-INT-02** Tiro un pan y rebota en el piso.
- **CA-INT-03** Con una salchicha en la mano miro el pan de la mesada y hago clic: se arma el pancho.
- **CA-INT-04** Agarro la bolsa de papas del estante, la apoyo en el piso y la vuelvo a guardar.
- **CA-INT-05** Con una salchicha en la mano apunto al borde del hervidor desde 2,5 m y hago
  clic: queda en el agua. Apunto a una pared y hago clic: cae al piso.

## Fuera de alcance

- Rotar el objeto a mano, sostener dos cosas, inventario de bolsillo.

## Notas de diseño

- Se eligió "resorte por velocidad" en vez de pegar el objeto a la cámara: así un objeto
  agarrado no puede atravesar paredes, y se siente físico.
- Colocar con la mira en vez de soltar desde la mano: se sabe dónde va a quedar. El puntero
  en cruz aparece solo con algo en la mano para no ensuciar la pantalla.
