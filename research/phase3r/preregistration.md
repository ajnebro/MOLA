# Pre-registro de la fase 3r — Suelo de ruido del ajuste (C10)

Fecha: 2026-11-02. Corresponde a la decisión D12 del usuario (cambio C10 de la revisión externa).
Se fija **antes de ejecutar ningún ajuste de esta fase**.

**Scripts:**
- `irace/launch.sh`;
- `scripts/evaluate_3r.py`;
- `scripts/analyze_3r.py`, probado solo con frentes sintéticos.

## 1. Pregunta

En 5 de los 37 problemas de desarrollo, la configuración ajustada en el propio problema queda más
de 0.01 por debajo del mejor donante (`phase3/report.md`, §15). ¿Cuánto de esa diferencia es suerte
de una sola ejecución de irace?

## 2. Diseño

- **Problemas y diferencia con el mejor donante:**

  | Problema | Diferencia |
  |---|---|
  | UF3 | 0.046 |
  | UF7 | 0.017 |
  | DTLZ4 | 0.074 |
  | LZ09_F3 | 0.012 |
  | ZDT4 | 0.022 |

- **Reajuste:** el mismo escenario que la fase 3. Es decir: irace 4.5, 20 000 experimentos, el
  espacio invariante y NSGA-II por defecto como candidata inicial. Solo cambia la semilla: 8400 +
  índice, frente a 8000 + índice en la fase 3 (`data/retune_tasks.json`).
- **Evaluación:** cada élite nueva, c*_Q', en los 37 problemas, con las semillas 5001–5010 y 20 000
  evaluaciones. HVn con la normalización de la matriz de la fase 3; las élites nuevas no entran en
  su unión.

## 3. Lo que se informa (descriptivo, sin puerta)

Para cada problema:
- el HVn en Q de c*_Q, de c*_Q', del mejor donante y del mejor de c*_Q y c*_Q';
- la diferencia con el mejor donante antes y después, y qué fracción cierra el reajuste;
- |HVn(c*_Q') − HVn(c*_Q)| en Q, la variación entre semillas de irace;
- como donantes, el HVn medio de c*_Q y de c*_Q' en los otros 36 problemas.

**Lo que no cambia:** ningún resultado de la fase 3. Esto es un análisis de sensibilidad del techo
"configuración propia".

## 4. Recursos

- **Coste:** 5 × 20 000 = 100 000 experimentos de irace, unas 6–10 h en NicoVM.
- **Evaluación:** 5 × 37 × 10 ejecuciones, del orden de una hora.
- **Cuándo:** se lanza encadenado detrás de la fase 4b (`irace/chain_3r.sh`).
