# SPEC-030 · Clientes habituales

Estado: **Implementada (etapa 5)**

## Objetivo

Que atender bien tenga memoria: algunos clientes contentos vuelven todos los días, con
nombre y "lo de siempre", y dejan de venir si los atendés mal.

## Requisitos

- **REQ-HAB-01** Hay hasta 8 habituales; la partida empieza sin ninguno. Un cliente común
  que puso 4,5 estrellas o más tiene 25% de chance de volverse habitual (si hay lugar).
  Recibe un nombre de `godot/data/habituales.ron` que no use otro habitual, y se queda con
  su cara, su ropa y su perfil (queda afuera de REQ-AMB-16).
- **REQ-HAB-02** Su "lo de siempre" es el pedido de esa visita y su hora de costumbre, la
  hora a la que pidió.
- **REQ-HAB-03** Una vez por día llega caminando desde el borde, cerca de su hora (±1 h,
  sorteado cada día), además de los clientes de REQ-CLI-01. Respeta la fila llena y el
  cartel de cerrado: si no puede sumarse, se va y no cuenta como visita.
- **REQ-HAB-04** Pide lo de siempre si el producto está en el menú (con los aderezos que haya
  disponibles); si no, pide como cualquier cliente, sin enojarse.
- **REQ-HAB-05** El globo muestra su nombre: "Marta: lo de siempre (pancho con mostaza)".
  Con memoria buena (REQ-HAB-06) saluda al llegar: "¡Hola! ¿Lo de siempre?".
- **REQ-HAB-06** Recuerda sus últimas 3 visitas (estrellas; irse enojado cuenta 1). Promedio
  4 o más: viene todos los días y tiene paciencia ×1,25. Entre 2,5 y 4: viene la mitad de
  los días (al azar). Menos de 2,5: no vuelve más y libera su lugar.
- **REQ-HAB-07** Los habituales no se guardan al cerrar el juego (guardado: etapa 7b).

## Criterios de aceptación

- **CA-HAB-01** Atiendo bien a varios clientes; alguno vuelve al día siguiente cerca de la
  misma hora, con su nombre en el globo, y pide lo mismo.
- **CA-HAB-02** Lo dejo irse enojado dos veces seguidas y no vuelve más.

## Fuera de alcance

- Habituales que traen amigos, charlas, pedidos de varios productos, regalos.

## Notas de diseño

- Nacen de clientes contentos (decisión del dueño): la plaza se va poblando de caras
  conocidas a medida que el puesto atiende bien.
