# SPEC-011 · Proveedor

Estado: **Implementada (etapa 2)**

## Objetivo

Reponer lo que se acaba: pedir mercadería, esperar que llegue y acomodarla a mano en el
depósito.

## Requisitos

- **REQ-PRO-01** Con Tab se abre el panel del proveedor: lista de bloques de
  `bloques.ron` con nombre, unidades y precio, un botón "Comprar" en cada uno, la caja
  actual y los pedidos en camino con su hora de llegada. Con el panel abierto el mouse
  queda libre.
- **REQ-PRO-02** Comprar resta el precio de la caja (SPEC-010) y crea un pedido.
- **REQ-PRO-03** Horario del proveedor de 8:00 a 20:00. Un pedido hecho en horario llega
  60 minutos de juego después (si eso pasa las 20:00, llega igual). Un pedido hecho fuera
  de horario llega a las 9:00 (del mismo día si es de madrugada, del siguiente si es de noche).
- **REQ-PRO-04** Al llegar, cada bloque aparece como **paquete** físico sobre un pallet en
  la vereda, al costado del carrito, con un aviso "Llegó tu pedido".
- **REQ-PRO-05** Un paquete se agarra y se lleva como cualquier objeto (SPEC-002).
- **REQ-PRO-06** Si un paquete suelto queda dentro de un lugar **libre** del depósito, se
  acomoda solo: pasa a ser un bloque de stock (SPEC-004) en ese lugar. En un lugar ocupado
  no entra.

## Criterios de aceptación

- **CA-PRO-01** A las 10:00 compro una bolsa de panes; a las 11:00 aparece en el pallet; la
  llevo a un lugar libre del estante y queda guardada con sus 12 panes visibles.

## Fuera de alcance

- Varios proveedores, precios que cambian, envío más rápido pagando más, vencimiento.
