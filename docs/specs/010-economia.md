# SPEC-010 · Economía

Estado: **Implementada (etapa 2)**

## Objetivo

La plata que entra y sale, y la fama del puesto, para que vender bien tenga sentido.

## Requisitos

- **REQ-ECO-01** Caja: la partida arranca con $120. Se suma lo cobrado (precio + propina)
  y se resta lo comprado al proveedor.
- **REQ-ECO-02** No se puede gastar más de lo que hay en la caja: la compra se rechaza con un
  aviso.
- **REQ-ECO-03** Precio de venta de cada producto en `productos.ron` (pancho: $10, hamburguesa:
  $14, choripán: $12, con los aderezos incluidos; valores a ajustar en la etapa 2.5).
- **REQ-ECO-07** Unidad de la plata: **1 pancho básico = $10**. Todos los precios del juego
  (productos, stock, accesorios y bases) se piensan en esa escala.
- **REQ-ECO-04** Reputación de 0 a 5 estrellas; arranca en 3. Con cada cliente se acerca un
  10% a las estrellas que dio: `rep = rep + (estrellas − rep) × 0,1`.
- **REQ-ECO-05** Estadísticas del día: ventas, ingresos, gastos, clientes atendidos y
  perdidos. Al pasar las 00:00 se muestra el resumen del día que terminó y se reinician.
- **REQ-ECO-06** La pantalla muestra siempre la caja y la reputación.

## Criterios de aceptación

- **CA-ECO-01** Vendo un pancho: la caja sube $10 más la propina.
- **CA-ECO-02** Con $4 en la caja intento comprar una bolsa de panes y no me deja.

## Fuera de alcance

- Impuestos, alquiler del lugar, préstamos.
- Descartado por el dueño (TASK-0006): elegir precios (son los de REQ-ECO-03), billetes y
  vuelto, caja registradora, permisos, gas, inspección de higiene y suciedad.
- Objetivos y campañas: postergados (ver el [ROADMAP](../ROADMAP.md)).
