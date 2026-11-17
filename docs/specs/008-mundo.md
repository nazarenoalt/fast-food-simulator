# SPEC-008 · Mundo: la plaza

Estado: **Implementada (etapa 1: versión mínima)**

## Objetivo

Un lugar para que exista el carrito: una vereda frente a una plaza con espacio para
caminar, donde después vivirán los NPCs.

## Requisitos

- **REQ-MUN-01** Terreno de 120 × 120 m con piso con colisión.
- **REQ-MUN-02** Plaza cuadrada de 40 × 40 m con caminos, fuente en el centro, bancos,
  árboles y faroles. Los faroles pertenecen al grupo `luces_noche`.
- **REQ-MUN-03** Una calle y una vereda a lo largo de un lado de la plaza; el carrito está
  sobre la vereda, con el mostrador mirando a la plaza.
- **REQ-MUN-04** Todo el mobiliario tiene colisión (bancos, troncos, fuente, faroles).
- **REQ-MUN-05** La distribución de la plaza es fija y repetible (misma plaza en cada partida).

## Criterios de aceptación

- **CA-MUN-01** Desde el carrito veo la fuente y los árboles de la plaza.

## Fuera de alcance (próximas etapas)

- NPCs y sus actividades, edificios alrededor, autos, modelos 3D definitivos, pasto con viento.
