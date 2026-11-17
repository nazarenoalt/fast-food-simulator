# SPEC-009 · Clientes

Estado: **Implementada (etapa 2)**

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
  carrito puede cocinar: pancho (con hervidor), hamburguesa (con plancha) y choripán (con
  parrilla). Cada uno tiene la misma chance.
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
  - Otro producto, salchicha o chorizo crudos o quemados, pan del choripán blando o quemado
    (SPEC-015), carne echada a perder (SPEC-016) → lo **rechaza**: queda en la bandeja, dice por
    qué y pierde 20 s de paciencia.
  - Si lo acepta: estrellas = 5 − 1 por aderezo pedido que falta − 0,5 por aderezo que no
    pidió − 1,5 si la salchicha está pasada − hasta 1,5 según cuánta paciencia gastó.
    Mínimo 1, máximo 5.
- **REQ-CLI-09** Si lo acepta paga el precio del producto más una propina de hasta 20%
  (0% con 3 estrellas o menos, 20% con 5), y se va comiendo.
- **REQ-CLI-10** Cada cliente atendido o perdido actualiza la reputación (SPEC-010) y se
  muestra un aviso con el resultado (ej. "+$2.750 · ★★★★☆").
- **REQ-CLI-11** (Para probar) La tecla C trae un cliente a la fila al instante.

## Criterios de aceptación

- **CA-CLI-01** A las 13:00 llega un cliente, pide, le apoyo el pancho correcto en la
  bandeja, paga y la caja sube.
- **CA-CLI-02** Si no lo atiendo, se va enojado y la reputación baja.

## Fuera de alcance

- Cobrar con billetes y dar vuelto, pedidos de varios productos, clientes habituales.
