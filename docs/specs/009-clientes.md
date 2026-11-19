# SPEC-009 · Clientes

Estado: **Implementada (etapa 2; papas y cartel: etapa 3.5)**

## Objetivo

Personas que llegan al carrito, hacen fila, piden, esperan, reciben su comida (o se cansan
y se van) y juzgan lo que les diste.

## Requisitos

### Llegada
- **REQ-CLI-01** La cantidad esperada de clientes por hora de juego depende de la hora:
  casi nadie de 0 a 7, picos al mediodía (12–14) y a la noche (20–22). Se multiplica por un
  factor de reputación (SPEC-010): con 0 estrellas viene el 40%, con 5 estrellas el 160%.
- **REQ-CLI-02** Los clientes llegan caminando desde los extremos de la vereda o desde la
  plaza, siguiendo los caminos (SPEC-013).
- **REQ-CLI-03** Fila: hasta 6 lugares en la vereda, frente al carrito. Si está llena no
  llegan más clientes. Cuando alguien se va, los de atrás avanzan.

### Pedido
- **REQ-CLI-04** Cuando el primero de la fila llega a su lugar, pide: un producto del menú y
  entre 0 y 2 aderezos entre los que ese producto admite (SPEC-012) y el carrito tiene
  disponibles. Un 25% lo pide sin aderezos. El **menú** son los productos con precio que el
  carrito puede cocinar: pancho (con hervidor), hamburguesa (con plancha), choripán (con
  parrilla) y papas en cajita (con freidora, SPEC-029). Cada uno tiene la misma chance.
- **REQ-CLI-05** El pedido se muestra en un globo sobre su cabeza (ej. "Pancho con
  mostaza y ketchup"). El color del globo muestra la paciencia: verde, amarillo, rojo.
- **REQ-CLI-06** Paciencia: 100 s desde que pide. Mientras espera en la fila (sin pedir
  todavía) la paciencia baja a la mitad de velocidad. Con paciencia 0 se va enojado
  (1 estrella, no paga).

### Entrega
- **REQ-CLI-07** El carrito tiene una **bandeja de entrega** sobre el mostrador. Un producto
  que nadie sostiene apoyado en la bandeja se le entrega al primero de la fila que esté
  esperando.
- **REQ-CLI-08** Evaluación de lo entregado:
  - Otro producto, salchicha, chorizo o papas crudos o quemados, pan del choripán blando o quemado
    (SPEC-015), carne echada a perder (SPEC-016) → lo **rechaza**: queda en la bandeja, dice por
    qué y pierde 20 s de paciencia.
  - Si lo acepta: estrellas = 5 − 1 por aderezo pedido que falta − 0,5 por aderezo que no
    pidió − 1,5 si la salchicha o las papas están pasadas − hasta 1,5 según cuánta paciencia gastó.
    Mínimo 1, máximo 5.
- **REQ-CLI-09** Si lo acepta paga el precio del producto más una propina de hasta 20%
  (0% con 3 estrellas o menos, 20% con 5), y se va comiendo.
- **REQ-CLI-10** Cada cliente atendido o perdido actualiza la reputación (SPEC-010) y se
  muestra un aviso con el resultado (ej. "+$12 · ★★★★☆").
- **REQ-CLI-11** (Para probar) La tecla C trae un cliente a la fila al instante.

### Cartel de cerrado
- **REQ-CLI-12** Con el `cartel_cerrado` (REQ-PAP-07) colgado no se suman clientes nuevos a la
  fila; los que ya están se quedan y se atienden. Sin cartel, o descolgado, está abierto. La
  tecla C trae clientes igual.
- **REQ-CLI-13** Clic con la mano libre, o E con o sin algo en la mano, en el frente del
  carrito, donde cuelga el cartel (se hace desde la vereda): colgado, lo saca y desaparece
  (abierto); sin cartel a la vista, lo vuelve a colgar (cerrado). Arranca colgado. Sin
  `cartel_cerrado` puesto no se puede cerrar.

## Criterios de aceptación

- **CA-CLI-01** A las 13:00 llega un cliente, pide, le apoyo el pancho correcto en la
  bandeja, paga y la caja sube.
- **CA-CLI-02** Si no lo atiendo, se va enojado y la reputación baja.

## Fuera de alcance

- Cobrar con billetes y dar vuelto, pedidos de varios productos, clientes habituales.
