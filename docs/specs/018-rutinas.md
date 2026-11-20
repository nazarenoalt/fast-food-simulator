# SPEC-018 · Rutinas de la plaza

Estado: **Implementada (etapa 5)**

## Objetivo

Que la plaza cambie con la hora: cada franja trae su gente (oficinistas al mediodía,
familias a la tarde, grupos de noche), que se viste y se comporta según quién es y qué hora es.

## Requisitos

### Agenda (TASK-0502)
- **REQ-RUT-01** `godot/data/agenda.ron` tiene franjas horarias; cada una dice cuánta gente hay
  y qué perfiles llegan, con su peso. Reemplaza la cantidad fija de REQ-AMB-04 y el sorteo
  de actividades de REQ-AMB-05. Franjas: 0–6: 3 · 6–9: 12 · 9–12: 18 · 12–14: 28 (mayoría
  oficinistas) · 14–16: 16 · 16–20: 28 (mayoría familias) · 20–24: 20 (mayoría nocturnos).
- **REQ-RUT-02** Cada persona nace con un perfil (`agenda.ron`: velocidad, paciencia, tamaño de
  grupo y actividades) y lo conserva hasta irse.
- **REQ-RUT-03** La agenda se adelanta 45 min: la gente de la franja siguiente sale antes y
  la plaza ya está llena cuando la franja empieza. Si sobra gente nadie desaparece: termina
  lo que hace, se va y no se repone.
- **REQ-RUT-04** Un cliente (REQ-CLI-01) tiene el perfil del paseante que se tentó o uno
  sorteado de la franja. Su paciencia (REQ-CLI-06) se multiplica por la del perfil:
  oficinista 0,8, jubilado 1,2, el resto 1.

### Perfiles (TASK-0503)
- **REQ-RUT-05** Oficinistas: llegan de a 1–3, caminan rápido (1,4–1,7 m/s) y se sientan en
  un banco a comer (con comida en la mano) o cruzan. A las 14:30 cortan lo que hacen y se van.
- **REQ-RUT-06** Familias: 1–2 adultos y 1–2 chicos (1,0–1,3 m) que los siguen a menos de
  2 m. Van a la fuente; los chicos corren 1–3 vueltas alrededor; a veces se sientan juntos.
- **REQ-RUT-07** Salida nocturna: grupos de 3–4 que charlan en ronda (mirando al centro, con
  gestos) cerca de la fuente o de un farol, 30–90 min de juego.
- **REQ-RUT-08** Los grupos caminan juntos por la misma ruta, de a dos, respetando REQ-AMB-13;
  si uno se adelanta más de 3 m, espera.
- **REQ-RUT-09** Los demás: corredor (trota), paseador (con perro), al trabajo (cruza sin
  parar), jubilado (lento, 0,8–1,1 m/s; se sienta 40–120 min), pareja (grupo de 2: pasea y
  se sienta junta), adolescentes (de a 2–3, pasean y charlan), trasnochado (pasea solo).

### Día y noche (TASK-0507)
- **REQ-RUT-10** Ropa según perfil y hora: de 7 a 20, manga corta y colores claros; de 20 a 7,
  campera o buzo de manga larga (el brazo va del color de la ropa hasta la muñeca) y colores
  oscuros. Oficinistas con camisa clara y pantalón oscuro; nocturnos con colores fuertes;
  corredores con ropa deportiva. REQ-AMB-16 vale dentro de cada paleta.
- **REQ-RUT-11** Actividades según hora: de 20 a 6 nadie trota; de 22 a 24 nadie pasea al
  perro; después de las 21 no hay chicos; de noche (REQ-DIA-06) solo se sientan en bancos a
  menos de 6 m de un farol.

## Criterios de aceptación

- **CA-RUT-01** A las 13:00 veo oficinistas sentados comiendo; a las 14:45 ya no hay.
- **CA-RUT-02** A las 17:00 hay familias con chicos corriendo alrededor de la fuente.
- **CA-RUT-03** A las 22:00 hay grupos en ronda, con campera, cerca de los faroles.
- **CA-RUT-04** Al empezar cada franja la plaza ya tiene su gente.

## Fuera de alcance

- Gente que entra a los edificios, rutas que esquivan multitudes, animaciones nuevas (etapa 7a).
- Habituales: SPEC-030. Feria y partido: SPEC-019.

## Notas de diseño

- Una hora de juego dura un minuto real y llegar desde el borde lleva ~45 min de juego:
  por eso el adelanto de REQ-RUT-03.
