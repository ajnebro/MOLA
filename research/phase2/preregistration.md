# Pre-registro de la fase 2 (piloto)

Fecha: 2026-10-20. Se fija **antes de ajustar ninguna configuración y antes de ejecutar la evaluación
cruzada**. Lo único ejecutado hasta ahora es:
- el catálogo y la reserva de grupos de test (commit `5cdd45a`, `reserved_groups.json`);
- el micro-benchmark de tiempos (`data/microbench.csv`);
- la comprobación de invariancia de VAMOS (`data/invariance.csv`);
- la caracterización de la etapa A.

El código de cada etapa y del análisis de G2 se sube en el mismo commit que este documento. Cualquier
cambio posterior se registra como desviación en el informe.

## 1. Alcance

Fase 2 de `plan.md` §6: estabilidad, escalado, coste y complementariedad del portafolio, con la puerta
**G2**. Se aplican las decisiones D1–D3 y T1–T4 (`research/decisions/decisions.md`).

## 2. Elementos fijos

| Elemento | Valor |
|---|---|
| Software | MOLA 0.3.0 (rama `research/phase1`, perfil `paper49-v1`); VAMOS 1.0.0 en `0a8bbb0`, instalado desde `git archive`, motor `numpy`, sin numba; Python 3.12; hilos BLAS/OpenMP fijados a 1 |
| Problemas del piloto | Los 37 problemas de desarrollo de `catalogue.csv`, con un representante por conjunto de duplicados exactos (`common.pilot_problems()`). Todos tienen dos objetivos, son continuos y solo tienen cotas de caja. Los 17 problemas reservados (hash `7c97fa68…`) no se tocan |
| Grupos | La columna `group` de `catalogue.csv`: los duplicados exactos comparten grupo y DTLZ4 va con DTLZ2. Cada problema de LZ09/UF forma su propio grupo; la relación entre ambas familias sigue siendo una hipótesis |
| Semillas | LHS 1001–1005, evaluación 2001–2005, bloques del tuner 3001–3020, calibración 4001–4005, semilla del racing 7000 + índice del problema |
| Presupuesto por ejecución | 20 000 evaluaciones, con frentes guardados a 5 000, 10 000 y 20 000 |
| Caracterización | n = 200·D, geometría `bound`, k = D |

## 3. Espacio de configuraciones (D2)

El espacio de ajuste de NSGA-II de VAMOS (`build_nsgaii_config_space`), sin los parámetros de archivo
externo (como hace `vamos tune`) y **sin los operadores que rompen la invariancia ante cambios de
unidades por variable** (`data/invariance.csv`):
- cruces PCX y UNDX;
- mutaciones gaussiana y de Cauchy;
- reparación `round`;
- inicializador Halton.

Así se mantiene la premisa de la RQ1: con el resto de operadores y con NSGA-II, MOEA/D y SMS-EMOA por
defecto, la ejecución es idéntica bit a bit tras un escalado por potencias de dos. El espacio
resultante es `runs.invariant_nsgaii_space()`.

## 4. Ajuste de c*_P (etapa B)

- **Tuner:** `RacingTuner` de VAMOS (D3). Es racing clásico (F-Race), no iterado: con
  `use_elitist_restarts=True`, VAMOS 1.0.0 falla en `refill.py:25` con `KeyError` sobre los parámetros
  condicionales.
- **Configuraciones:** 60 iniciales, la de NSGA-II por defecto más 59 aleatorias.
- **Racing:** 20 bloques (semillas 3001–3020) y un máximo de 400 ejecuciones por problema.
  Eliminación con test estadístico (α = 0.05, fracción 0.25) tras al menos 3 bloques.
- **Puntuación:** HV del frente final normalizado. La normalización usa el ideal y el nadir de la
  unión de los frentes de 5 ejecuciones de calibración (NSGA-II por defecto), con referencia 1.1 en
  cada objetivo.
- **Uso de datos:** c*_P solo ve P.

## 5. Evaluación cruzada (etapa C)

**Configuraciones del portafolio (40):**
- las 37 c*_P ajustadas;
- NSGA-II por defecto;
- MOEA/D y SMS-EMOA por defecto, como comparadores sin ajustar.

**Ejecución:** cada configuración se ejecuta en los 37 problemas con las 5 semillas de evaluación, en
total 7 400 ejecuciones.

**HV normalizado:**
- **Normalización:** para cada problema, el ideal y el nadir de la unión de todos los frentes finales
  (todas las configuraciones y semillas) y referencia 1.1.
- **Valor:** HVn = HV / HV(unión), en [0, 1] al presupuesto final.
- **Presupuestos intermedios:** usan la misma normalización. En ellos HVn puede superar 1 si un
  frente intermedio domina zonas que el final perdió.

## 6. Regla de la puerta G2 (`scripts/analyze_g2.py`)

Para cada problema destino Q y cada una de las 10 particiones de las 5 semillas de evaluación en 3 de
selección y 2 de medida:

1. **Donantes:** las c*_P de los problemas P de otro grupo de formulación.
2. **SBS(Q):** el donante con mejor HVn medio sobre los problemas de otros grupos, en las semillas de
   selección.
3. **VBS(Q) (donante oráculo):** el donante con mejor HVn medio sobre Q, en las semillas de selección.
4. **Hueco:** gap(Q) = HVn(VBS) − HVn(SBS) sobre Q, en las semillas de medida, promediado sobre las
   10 particiones. La validación cruzada sobre las semillas evita el sesgo del ganador.

El hueco de un grupo es la media de sus problemas.

**G2 se supera si al menos el Y = 25 % de los grupos tienen un hueco ≥ X = 0.01** (un punto de HV
normalizado).

**Si G2 no se supera:** se diversifica el portafolio (`plan.md` §6). Primero se añaden espacios de
MOEA/D y SMS-EMOA, ajustados igual; si no basta, se pasa a la construcción por complementariedad
(opción 6 de `question1.md`). La decisión se toma con los datos del piloto y se documenta.

**Análisis secundarios, sin puerta:**
- el hueco de c*_Q (autoajustada) y de NSGA-II por defecto frente al SBS;
- la fracción con X ∈ {0.005, 0.02, 0.05};
- la fracción con 5 000 y 10 000 evaluaciones;
- la matriz de pérdida de transferencia L(P→Q) = HVn(c*_Q, Q) − HVn(c*_P, Q);
- los comparadores MOEA/D y SMS-EMOA por defecto.

## 7. Estabilidad de la caracterización (etapa A, descriptiva)

Con 37 problemas × 5 LHS:
- **Por feature:**
  - desviación típica dentro de un problema frente a la desviación entre problemas (de las medias);
  - frecuencia de valores indefinidos y sus causas.
- **Reconocimiento:** si el vecino más cercano de cada muestra es otra muestra del mismo problema.
  Se usan las features definidas en todas las muestras, con escalado robusto (mediana y rango
  intercuartílico).
- **Estabilidad del donante:** cuántas veces el problema más cercano de otro grupo es el mismo en las
  5 semillas.
- **Coste:** tiempos de evaluación y de caracterización frente a n y D.

Estas medidas no son una puerta. Preparan la RQ2 y la elección de la representación en la fase 3.

## 8. Recursos

Ocho procesos de un hilo en paralelo, en una máquina compartida (22 hilos lógicos). La carga y la
memoria se comprueban antes de cada etapa. Las ejecuciones pesadas guardan resultados incrementales
en `C:\tmp\mola-phase2\raw` y se pueden reanudar.
