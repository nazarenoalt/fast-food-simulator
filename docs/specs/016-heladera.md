# SPEC-016 · Heladera y cadena de frío

Estado: **Implementada (etapa 3: heladera)**

## Objetivo

La carne cruda se echa a perder si no se la mantiene fría. Una heladera en el carrito la
conserva; el jugador tiene que guardarla y no dejarla al sol.

## Requisitos

- **REQ-HEL-01** La heladera es un accesorio del carrito (datos `.ron`). Su interior está a
  4 °C mientras está cerrada y enchufada. Se abre y cierra con E. Tiene lugares para guardar
  paquetes como el depósito (SPEC-004) y sitio para comida suelta. Cerrada, la puerta tapa lo
  que hay adentro. (Por ahora siempre está enchufada: no hay forma de desenchufarla.)
- **REQ-HEL-02** Cerrada y enchufada, su temperatura interior se acerca a 4 °C; con la puerta
  abierta o desenchufada se acerca a la del ambiente, más lento (constante 3 veces menor).
- **REQ-HEL-03** Todo alimento perecedero (hamburguesa, chorizo cruda) tiene **frescura** de
  100% a 0%. Mientras su temperatura está entre 8 °C y 60 °C la frescura baja `(T − 8) × 0,02 % por
  segundo`; por debajo de 8 °C no baja, y por encima de 60 °C (bien cocinado) tampoco. La
  frescura nunca sube; lo cocido ya no la pierde (REQ-HEL-08). (Sin el tope de 60 °C la carne se echaría a perder cocinándose.)
- **REQ-HEL-04** Frescura menor a 40%: se ve verdosa y el cartel avisa. En 0% está **Echada
  a perder**: definitivo, y se rechaza al entregarla (REQ-CLI-08).
- **REQ-HEL-05** La comida guardada en la heladera usa su temperatura interior como entorno,
  igual que el hervidor usa la del agua (REQ-COC-08). La cocción sigue sus reglas propias.
- **REQ-HEL-06** Los paquetes del proveedor (SPEC-011) de carne vienen a 4 °C. Se pueden
  guardar en la heladera o en el estante, donde se calientan hasta el ambiente.
- **REQ-HEL-07** Cocinar no restaura frescura: servir carne con frescura menor a 40%
  descuenta 1 estrella aunque esté bien cocida.
- **REQ-HEL-08** Las comidas listas no se echan a perder: los armados (pancho, choripán) no son
  perecederos (el choripán guarda fija la frescura del chorizo) y una carne sin ningún lado
  crudo deja de perder frescura aunque se enfríe.

## Criterios de aceptación

- **CA-HEL-01** Guardo una hamburguesa cruda en la heladera cerrada: tras varias horas de
  juego sigue con 100%.
- **CA-HEL-02** La dejo al sol del mediodía: se pone verdosa y al final se echa a perder.
- **CA-HEL-03** Dejo la puerta abierta: el interior sube y el cartel lo muestra.
- **CA-HEL-04** Dejo un pancho o una hamburguesa cocida toda la tarde al sol: no se pudren.

## Fuera de alcance

- Freezer, electricidad como recurso con costo, hielo, olores. El gas y la luz llegan con
  SPEC-021.

## Notas de diseño

- Constantes: la heladera enfría con k = 0,01 1/s (abierta, 0,0033 1/s). Un paquete se acerca a la
  temperatura de su entorno con k = 0,002 1/s.
- Mismo modelo de calor que SPEC-003: la heladera solo define la temperatura del entorno.
- El ambiente de la plaza depende del día/noche (SPEC-007); un valor fijo de 20 °C alcanza
  para esta etapa.
