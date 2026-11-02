# Pre-registro de la fase 4b — Nivel 2: irace arrancado en caliente y umbral t₂

Fecha: 2026-11-02. Corresponde a la decisión D13 del usuario y a la §12.3 de `plan.md`. Se fija
**antes de ejecutar ningún ajuste de esta fase**.

**Lo que ya existe:**
- el brazo en frío, que son los ajustes de la fase 3, cuyos `irace.Rdata` se conservan en NicoVM;
- los arranques en caliente, calculados solo con la matriz de entrenamiento de la fase 3.

**Scripts:**
- `scripts/make_warm_starts.py`;
- `irace/launch.sh`;
- `scripts/evaluate_4b.py`;
- `scripts/analyze_4b.py`.

El análisis solo se ha probado con élites sintéticas, copias de frentes de la matriz de la fase 3.
Con un t₂ sintético de unas 2 unidades, lo recupera (1.92).

## 1. Pregunta

Cuando el problema nuevo se parece algo, pero no tanto como para transferir directamente, ¿ahorra
experimentos de irace arrancar desde la configuración de los vecinos? ¿Hasta qué distancia, en
unidades de ruido, compensa hacerlo? Esa distancia es t₂.

## 2. Elementos fijos

| Elemento | Valor |
|---|---|
| Problemas | Los 24 de desarrollo que no están en el estrato fácil (`phase3/data/strata.csv`): 17 intermedios y 7 muy difíciles |
| Brazo en frío | El ajuste de la fase 3 de cada problema: irace 4.5, 20 000 experimentos, arranque desde NSGA-II por defecto y semilla 8000 + índice |
| Brazo en caliente | El mismo escenario, con estas dos diferencias: <ul><li>**configuraciones iniciales:** el arranque en caliente y NSGA-II por defecto (`data/initial/<problema>.txt`);</li><li>**semilla:** 8300 + índice.</li></ul> |
| Arranque en caliente | Con el entrenamiento LOGO del problema (sin su grupo de formulación). Es la configuración que más elige `knn_selector` entre las 5 muestras del problema; los empates se rompen por el mejor HVn medio en los vecinos (`make_warm_starts.py`). Solo usa la matriz de entrenamiento |
| d | La mediana, sobre las 5 muestras, de la distancia a la media de entrenamiento más cercana, en unidades de ruido (`policy.distance_and_s1` de la fase 4) |
| Curvas *anytime* | La mejor élite de cada iteración de irace y los experimentos acumulados al final de esa iteración (`state$experiment_log`). Antes de la primera iteración, la configuración inicial (en frío, NSGA-II por defecto; en caliente, el arranque en caliente) |
| Evaluación | Cada élite distinta, con las semillas 5001–5010 y 20 000 evaluaciones. HVn con la normalización de la matriz de la fase 3 |

## 3. Medidas y umbral

- **Objetivo:** el HVn de la élite final del brazo en frío menos 0.005.
- **N_frío y N_caliente:** los experimentos mínimos tras los que cada brazo alcanza el objetivo. Si
  no lo alcanza, se cuentan 20 000 y se marca como censurado.
- **Ahorro:** S = N_frío − N_caliente.
- **t₂:** la mayor d a la que una regresión isotónica decreciente de S frente a d sigue dando
  S ≥ 2 000 experimentos (el 10 % del presupuesto). Vale 0 si eso no ocurre en ninguna d, y se marca
  si ocurre en todo el rango observado.
- **Validación,** dejando fuera un grupo de formulación entre los 24 problemas:
  - t₂ se recalcula sin el grupo, y para sus problemas se predice que compensa arrancar en caliente
    si d ≤ t₂;
  - se informa del acierto frente a S ≥ 2 000;
  - y de los experimentos que gastaría la política de niveles, frente a arrancar siempre en frío y
    siempre en caliente.
- **Incertidumbre:** bootstrap sobre problemas (2 000 remuestreos, semilla 20261102), con el
  intervalo del 95 % de t₂.
- **Descriptivo:** el HVn medio de los dos brazos con 1 000, 2 000, 5 000, 10 000 y 20 000
  experimentos.

**No hay puerta.** Es una calibración pre-registrada: t₂ y su validación se informan tal como
salgan, y no se cambian el criterio de 2 000 ni la tolerancia de 0.005.

**Expectativa:**
- con d pequeña, el ahorro será positivo;
- con d grande, nulo o negativo;
- con 24 problemas, t₂ tendrá un intervalo ancho.

**Límite declarado:** la resolución de las curvas son las iteraciones de irace. La primera termina
hacia los 2 500–3 000 experimentos, así que antes solo cuenta la configuración inicial.

## 4. Lo que no cubre

- **Los 17 reservados:** t₂ no se valida con ellos, porque habría que ajustar con irace sobre ellos.
- **Los destinos de la 3c:** la comprobación externa con ellos es opcional y tendría su propia
  enmienda.

## 5. Recursos

- **Ajuste:** 24 × 20 000 = 480 000 experimentos de irace, unos 1–2 días en NicoVM.
- **Evaluación:** las élites distintas de los dos brazos, del orden de 300, con 10 semillas: una o
  dos horas.
- **Cuándo:** se lanza en NicoVM después de la cadena de la 3c y la 3g, cuando quede libre y con 31
  procesos.
