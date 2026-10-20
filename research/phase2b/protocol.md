# Fase 2b — irace frente a F-Race (anexo a la fase 2)

Fecha: 2026-10-20. Lo pidió el usuario después de la fase 2: "usa irace en NicoVM". Se fija antes de
ejecutar. Es **exploratorio**: no cambia la regla de G2 de la fase 2. Su objetivo es decidir qué tuner y
qué normalización se usan en la fase 3.

## Pregunta

¿Cambian las configuraciones c*_P, y con ellas el margen de transferencia (G2), si el ajuste se hace
con irace en lugar de F-Race clásico? ¿Qué parte del cambio se debe a la normalización del objetivo
de ajuste?

## Brazos

Todos usan el mismo espacio de NSGA-II invariante (`runs.invariant_nsgaii_space()`), 20 000
evaluaciones por ejecución, como máximo 400 ejecuciones de ajuste por problema y la configuración de
NSGA-II por defecto como candidata inicial.

| Brazo | Tuner | Normalización del objetivo de ajuste |
|---|---|---|
| C (fase 2) | F-Race de VAMOS: 60 configuraciones iniciales, 20 bloques de semillas | Calibración con NSGA-II por defecto (`phase2/data/calibration.json`) |
| A | El mismo F-Race | Ideal y nadir de los frentes de referencia de la fase 2 (`phase2/data/reference_fronts.npz`) |
| B | irace 4.5 (`~/R/irace-4.5-lib`): `maxExperiments = 400` y `nbIterations = 5` (con 26 parámetros, el valor por defecto, 6, exige al menos 504 experimentos), semilla 7000 + índice del problema, una instancia (el problema) con semillas nuevas en cada bloque, resto de opciones por defecto | Igual que A |

Los frentes de referencia salen de ejecuciones sobre el propio P, así que c*_P sigue viendo solo P.

## Ejecución

Todo en NicoVM (32 núcleos; estaba libre al empezar): Python 3.10, numpy de la serie 2.2 y VAMOS 1.0.0
(`0a8bbb0`), en `~/mola-phase2b`.

**Evaluación cruzada:** con las semillas 2001–2005, igual que en la fase 2, para las c*_P de A y de B.
Si las ejecuciones de NicoVM no reproducen bit a bit los frentes locales de la fase 2 (se comprueba
antes), también se vuelven a evaluar C y los tres algoritmos por defecto en NicoVM.

## Medidas

1. **Calidad de cada c*_P en su propio problema** con una normalización común: la unión de los frentes
   finales de todos los brazos para ese problema. Se comparan B frente a A (efecto del tuner) y A
   frente a C (efecto de la normalización), emparejando por problema con una prueba de Wilcoxon de
   rangos con signo.
2. **G2 en cada brazo**, aplicando la regla pre-registrada de la fase 2 al portafolio de ese brazo, con
   su propia normalización.
3. **HVn del SBS y diversidad de las configuraciones** (combinaciones de operadores distintas).
4. **Coste:** ejecuciones y tiempo de ajuste.

## Recursos

La regla de máquina libre se comprueba antes de cada etapa y nunca se detienen procesos ajenos. Se
deja margen en el disco, que tiene 5.5 GB libres. Los frentes en bruto se quedan en NicoVM y en
`C:\tmp\mola-phase2b`, con sus hashes.
