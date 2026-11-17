# SPEC-007 · Día y noche

Estado: **Implementada (etapa 1)**

## Objetivo

Que la plaza cambie con la hora: amanecer, mediodía, atardecer y noche con faroles prendidos.
Más adelante la hora va a manejar a los NPCs y los horarios de venta.

## Requisitos

- **REQ-DIA-01** Hay un reloj de juego (minuto del día 0–1439 y número de día). Por defecto
  1 minuto de juego = 1 segundo real (un día dura 24 minutos reales). La partida arranca a
  las 17:00 del día 1.
- **REQ-DIA-02** Al pasar de 23:59 a 00:00 el contador de días suma uno.
- **REQ-DIA-03** El sol sale a las 6:30 y se pone a las 19:30. Durante el día su altura sigue
  un arco que llega a 60° al mediodía solar; de noche está bajo el horizonte.
  El sol recorre el cielo de este a oeste.
- **REQ-DIA-04** La intensidad y el color del sol cambian con su altura: cálido (anaranjado)
  cerca del horizonte, blanco arriba, apagado bajo el horizonte.
- **REQ-DIA-05** El cielo y la luz ambiente se oscurecen de noche; queda una luz de luna
  azulada tenue para que se pueda ver.
- **REQ-DIA-06** "Es de noche" (luces encendidas) cuando el sol está a menos de 3° sobre el
  horizonte. Todos los nodos del grupo `luces_noche` se prenden de noche y se apagan de día.
- **REQ-DIA-07** La tecla T alterna velocidad ×1 / ×30 (para probar), y la hora se ve en pantalla.

## Criterios de aceptación

- **CA-DIA-01** Empiezo a las 17:00, aprieto T, y en menos de un minuto real veo el
  atardecer anaranjado y los faroles de la plaza y la luz del carrito prendiéndose.

## Fuera de alcance

- Estaciones del año, clima (lluvia, nubes), sombras de nubes.
