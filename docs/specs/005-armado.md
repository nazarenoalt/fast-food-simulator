# SPEC-005 · Armado de comida

Estado: **Implementada (etapa 1: pancho)**

## Objetivo

Combinar ingredientes sueltos en un producto terminado, de forma física y sin menús.

## Requisitos

- **REQ-ARM-01** Las combinaciones válidas se definen como reglas
  `base + agregado → resultado` (etapa 1: `pan de pancho + salchicha → pancho`).
- **REQ-ARM-02** El pan tiene una zona de encastre sobre su parte de arriba. Si una salchicha
  **que nadie está sosteniendo** queda dentro de esa zona, se encastra: ambos se reemplazan
  por un pancho en la posición del pan.
- **REQ-ARM-03** El pancho guarda el estado de cocción que tenía la salchicha en el momento
  del encastre (y su color), y deja de cocinarse.
- **REQ-ARM-04** Combinaciones no válidas (ej. salchicha + salchicha) no hacen nada.
- **REQ-ARM-05** El pancho es un objeto agarrable más, con masa = suma de las masas.

## Criterios de aceptación

- **CA-ARM-01** Dejo un pan sobre el mostrador, suelto una salchicha cocida encima: se forma
  un pancho que puedo agarrar, y el cartel dice "Pancho (salchicha cocida)".

## Fuera de alcance (próximas etapas)

- Aderezos (mostaza, ketchup, mayonesa, papas pay), servilleta, entregar al cliente,
  hamburguesa y choripán.

## Notas de diseño

- Encastre en vez de física pura: meter una salchicha dentro de un pan solo con física
  queda tembloroso y frustrante. Al caer y al tirarlos sí son objetos físicos reales.
