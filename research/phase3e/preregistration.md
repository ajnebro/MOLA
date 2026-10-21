# Pre-registro de la fase 3e — Réplica de la fase 3 en Evolver/jMetal (D6)

Fecha: 2026-10-21. Se fija **antes de cualquier ajuste y de la matriz de esta réplica**. La campaña de
la fase 3 en VAMOS sigue en marcha y no hay resultados de transferencia de ninguna de las dos.

## 1. Qué se replica

Es la fase 3 entera (`research/phase3/preregistration.md`, con su enmienda 1):
- la misma pregunta (RQ3);
- los mismos 37 problemas de desarrollo, grupos y familias;
- los mismos métodos, particiones y medidas;
- **la misma regla de G3:** en LOGO, `landscape_1nn` frente a `metadata_1nn`, Wilcoxon unilateral
  sobre los grupos, p < 0.05.

El análisis es el mismo script, `phase3/scripts/analyze_transfer.py`, con las variables de entorno
de la §4.

## 2. Qué cambia

| Elemento | Fase 3 (VAMOS) | Fase 3e (Evolver/jMetal) |
|---|---|---|
| Framework | VAMOS 1.0.0 (`0a8bbb0`), motor numpy | Evolver 2.5 (`caf212157`) sobre jMetal 7.8; Java 21 en NicoVM y Temurin 24 en local |
| Implementaciones de los problemas | VAMOS | jMetal (`scripts/catalogue_3e.py`: `SPECS`) |
| Espacio de configuraciones | NSGA-II de VAMOS sin sus operadores no invariantes; tamaño de población ajustable en [20, 200] | `NSGAIIDouble.yaml` de Evolver sin PCX, UNDC, Laplace ni la mutación uniforme (D6, 28 parámetros, `irace/parameters.txt`); población fija en 100 |
| Configuración inicial de irace | NSGA-II por defecto de VAMOS | NSGA-II por defecto de Evolver (`irace/default.txt`) |
| Semilla de irace | 8000 + índice | 8600 + índice |
| Comparadores sin ajustar | NSGA-II, MOEA/D y SMS-EMOA por defecto | Solo NSGA-II por defecto de Evolver |

Todo lo demás coincide con la fase 3:
- **irace:** 4.5, `maxExperiments = 20 000` y el resto por defecto.
- **Ejecuciones:** 20 000 evaluaciones cada una.
- **Objetivo del ajuste:** HV con normalización por el frente verdadero y referencia 1.1
  (`data/tuning_bounds.json`). Es analítico en DTLZ, LZ09 y UF6; en el resto, el frente de
  referencia de Evolver, aceptado tras comprobarlo con 5 ejecuciones por defecto.
- **Matriz:** 10 semillas de evaluación (5001–5010) y el frente no dominado del resultado.
- **Caracterización:** MOLA 0.4.0, mismas semillas LHS (1001–1005), geometría `bound`, k = D,
  objetivos escalados por muestra como representación principal
  (`data/features_sample_scaled.csv`) y objetivos sin escalar para el método secundario.

## 3. Diferencias conocidas entre las dos implementaciones

Medido en `data/catalogue_3e.json`, con 1 000 puntos comunes por problema:
- **34 de los 37 problemas coinciden con VAMOS** hasta ~1e-16. Sus 49 features coinciden también
  con las de la fase 3 en las 5 muestras.
- **UF3:** VAMOS pone x2…x30 ∈ [−1, 1]; jMetal usa [0, 1], que es la definición del CEC 2009. Las
  fórmulas coinciden.
- **RE24:** VAMOS pone x2 ∈ [4, 50] y jMetal x2 ∈ [0.5, 50]. Falta contrastarlo con el código de
  referencia de Tanabe e Ishibuchi.
- **RWA1:** jMetal 7.8 escribe `10e-3` donde debería poner `1e-3`, así que sus coeficientes son 10
  veces mayores. Diferencia relativa de los objetivos: 12.4.
- **No hay duplicados exactos** entre las 37 implementaciones de jMetal.

Cada réplica usa las implementaciones de su framework y no se corrige ninguna. En la comparación
entre frameworks, estos tres problemas se marcan.

## 4. Ejecución

En NicoVM, cuando termine la campaña de la fase 3 y la máquina esté libre:
1. **Ajuste:** `irace/launch.sh`, con 31 JVM `RunWorker` de un solo hilo detrás de
   `scripts/jrun_server.py`. Cada JVM atiende una ejecución cada vez, así que el generador global de
   jMetal no se comparte y cada ejecución se reproduce desde su semilla.
2. **Elites:** `scripts/collect_3e.py` → `data/tuned_configs.json`.
3. **Matriz:** `scripts/evaluate_3e.py`.
4. **Análisis:** `MOLA_TRANSFER_DIR=research/phase3e`,
   `MOLA_RAW_FEATURES=research/phase3e/data/features_raw_objectives.csv`,
   `MOLA_TRANSFER_DEFAULTS=default__nsgaii` y `MOLA_PHASE3_MATRIX=<matriz>`, con
   `phase3/scripts/analyze_transfer.py`.

## 5. Comparación entre frameworks (secundaria, descriptiva)

- **Veredicto de G3** en cada framework y signo de la diferencia `landscape_1nn` − `metadata_1nn`.
- **Coincidencia de donantes:** en cuántos destinos coincide el donante de `landscape_1nn`. Las
  features son las mismas en 34 problemas, así que el donante depende solo de las implementaciones.
- **Matrices de pérdida de transferencia:** correlación entre la de VAMOS y la de jMetal.
- **Problemas marcados:** todo se informa con y sin UF3, RE24 y RWA1.
