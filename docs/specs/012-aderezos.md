# SPEC-012 · Aderezos

Estado: **Implementada (etapa 2)**

## Objetivo

Ponerle aderezos a la comida con pomos que se gastan y se recargan.

## Requisitos

- **REQ-ADE-01** Los aderezos se definen en `godot/data/aderezos.ron`: id, nombre, color y
  usos por pomo lleno. Etapa 2: mostaza, ketchup y mayonesa (40 usos cada uno).
- **REQ-ADE-02** El accesorio **aderecera** (categoría Equipamiento) tiene un pomo por cada
  aderezo que lista. Cada pomo muestra cuánto le queda (nivel visible).
- **REQ-ADE-03** Con un producto que admite aderezos en la mano, mirar un pomo y apretar E
  le pone ese aderezo (gasta 1 uso). Se ve como una línea en zigzag del color del aderezo.
- **REQ-ADE-04** No se puede poner dos veces el mismo aderezo, ni usar un pomo vacío.
- **REQ-ADE-05** Los repuestos (ej. "repuesto de mostaza") se compran al proveedor como
  cualquier bloque. Con un repuesto en la mano, mirar el pomo de ese aderezo y apretar E lo
  llena y el repuesto se gasta.
- **REQ-ADE-06** El cartel del pomo dice el aderezo y los usos (ej. "Mostaza (32/40)").

## Criterios de aceptación

- **CA-ADE-01** Armo un pancho, le pongo mostaza y ketchup; el cartel del pancho los lista y
  los pomos bajan 1 uso cada uno.

## Fuera de alcance

- Papas pay, salsas caseras, cantidad de aderezo (poco/mucho).
