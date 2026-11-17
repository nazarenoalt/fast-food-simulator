# SPEC-015 · Parrilla con carbón y pan tostado

Estado: **Borrador**

## Objetivo

Una parrilla de carbón para el choripán: el fuego depende del carbón, que se gasta y hay
que reponer. El pan se tuesta en la misma parrilla.

## Requisitos

### Parrilla y carbón
- **REQ-PAR-01** La parrilla es un accesorio del carrito (datos `.ron`) con una cantidad de
  carbón en kg (máximo 3 kg). Se carga con bolsas de carbón (producto con `repone`, como los
  pomos de SPEC-012) y se enciende con E cuando tiene carbón.
- **REQ-PAR-02** Encendida, el carbón se gasta 0,5 kg por hora de juego y las brasas se
  calientan 3 °C por segundo hasta una temperatura máxima que depende del carbón que queda:
  `T_max = 20 + 300 × min(1, carbón / 1 kg)`. Sin carbón se apaga sola.
- **REQ-PAR-03** Apagada o sin carbón, la parrilla se enfría hacia el ambiente. Se ve el
  resplandor de las brasas según su temperatura y el cartel muestra carbón y temperatura.
- **REQ-PAR-04** Todo alimento apoyado en la parrilla toma su temperatura como entorno, igual
  que en la plancha (REQ-PLA-03): el lado de abajo.

### Chorizo
- **REQ-PAR-05** El chorizo se cocina como la hamburguesa, por lados (REQ-PLA-04 y 05), con
  sus propios valores. A 250 °C cada lado queda Cocido entre 60 s y 150 s.

### Pan tostado
- **REQ-PAR-06** El pan de choripán tiene un avance de **tostado** por cada cara, con las
  mismas fórmulas que la cocción pero con sus propios valores. Estados: **Blando**, **Tostado**,
  **Quemado**. Cada cara se ve del color de su avance.
- **REQ-PAR-07** El choripán se arma por encastre (SPEC-005) con un chorizo cocido y un pan
  tostado de al menos una cara. Con el pan blando o quemado o el chorizo crudo, el cliente
  lo rechaza (REQ-CLI-08).

## Criterios de aceptación

- **CA-PAR-01** Cargo carbón, enciendo, y el cartel muestra la temperatura subiendo.
- **CA-PAR-02** Dejo la parrilla prendida un rato largo: el carbón baja y las brasas se apagan.
- **CA-PAR-03** Armo un choripán con pan tostado y chorizo cocido y me lo aceptan.

## Fuera de alcance

- Soplar las brasas, chispas, parrilla de varias alturas, panes de otros tipos.

## Notas de diseño

- Valores iniciales: chorizo k = 0,05; T_min = 60 °C; velocidad = 0,0012; punto = 10; pasado = 22.
  Pan: k = 0,15; T_min = 90 °C; velocidad = 0,0020; tostado = 4; quemado = 15.
