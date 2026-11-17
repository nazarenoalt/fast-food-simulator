# SPEC-004 · Depósito con comida visible

Estado: **Implementada (etapa 1)**

## Objetivo

El depósito muestra la mercadería real: si quedan 7 panes, se ven 7 panes. El jugador
mira el estante y sabe qué le falta sin abrir menús.

## Requisitos

- **REQ-DEP-01** El stock se guarda en **bloques**: un bloque es un paquete de N unidades de
  un mismo producto (ej. "bolsa de 12 panes de pancho", "caja de 12 salchichas").
  Los tipos de bloque se definen en `godot/data/bloques.ron`.
- **REQ-DEP-02** Cada bloque ordena sus unidades en una grilla (columnas × filas × capas)
  y cada unidad restante se dibuja como un objeto 3D real en su lugar dentro del paquete.
- **REQ-DEP-03** La cantidad de unidades visibles es siempre igual a las unidades restantes.
- **REQ-DEP-04** Sacar una unidad saca la "última" de la grilla (de arriba hacia abajo, de
  atrás hacia adelante), para que el paquete se vacíe de forma natural.
- **REQ-DEP-05** Al sacar una unidad con E, aparece como objeto físico (SPEC-002) en la mano
  del jugador.
- **REQ-DEP-06** El paquete se dibuja (bolsa transparente o bandeja de cartón). Cuando un
  bloque queda vacío, el paquete desaparece y el lugar queda libre.
- **REQ-DEP-07** Un depósito tiene un número fijo de lugares para bloques (definido por su
  accesorio). No se puede poner un bloque en un lugar ocupado.
- **REQ-DEP-08** Al mirar un bloque el cartel dice qué es y cuántas unidades quedan
  (ej. "[E] Sacar pan de pancho (7/12)").

## Criterios de aceptación

- **CA-DEP-01** Saco 3 panes de la bolsa de 12: se ven 9 dentro de la bolsa.
- **CA-DEP-02** Saco las 12 salchichas: la caja desaparece del estante.

## Fuera de alcance (próximas etapas)

- Comprar bloques nuevos (llegan por el proveedor), devolver unidades al paquete,
  vencimiento, cadena de frío (heladera), bloques de bloques (ej. "fardo de 6 bolsas").

## Notas de diseño

- Las unidades del paquete **no** tienen física mientras están guardadas (solo dibujo):
  así un depósito lleno no hace lento el juego. Recién al sacarlas se vuelven objetos físicos.
