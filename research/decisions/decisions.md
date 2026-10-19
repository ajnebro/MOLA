# Registro de decisiones

Cada decisión indica quién la tomó, cuándo, qué alternativas se descartaron y qué implica. Las
alternativas completas para D1–D3 están en [`question1.md`](question1.md).

## D1 — Geometría por defecto: `bound` (opción 1B)

- **Fecha y autor:** 2026-10-19, decisión del usuario.
- **Decisión:** MOLA caracteriza por defecto con X llevado a [0,1]^D mediante las cotas declaradas,
  tanto para construir el grafo de vecinos como para medir distancias. La geometría en bruto se
  conserva como opción explícita (`raw`).
- **Motivo:** es la única geometría verificada como invariante ante cambios afines por variable (E6:
  ninguna de las 49 features cambia). Coincide con la referencia en la que trabajan los operadores de
  VAMOS (E19) y con MO-ELA (E18).
- **Implicaciones:**
  - Los valores dejan de coincidir con los CSV de `examples/benchmarks/` y con FEATURE_ANALYSIS.md,
    que siguen correspondiendo a MOLA 0.2.0 (`58bc0ca`). Para reproducirlos exactamente hay que usar
    ese commit. La geometría `raw` de la nueva versión reproduce la elección geométrica, pero con las
    definiciones ya corregidas.
  - Las variables fijas (cota inferior igual a la superior) necesitan un tratamiento explícito.
  - Cada salida registra la geometría y `k`.
- **`k`:** se mantiene `k = D` por defecto, por comparabilidad con el artículo; k ∈ {1, D, 10} queda
  como factor de la RQ1.

## D2 — Portafolio: una configuración ajustada por problema de entrenamiento (opción 2.5)

- **Fecha y autor:** 2026-10-19, decisión del usuario.
- **Decisión:** el artículo se plantea como **transferencia de configuraciones**, que es la línea de
  la tesis (recommoonder). Para cada problema de entrenamiento P se ajusta una configuración c*_P. Para
  un problema nuevo Q se recomienda la configuración de su donante más similar. El portafolio es la
  unión de las c*_P de entrenamiento.
- **Descartadas, salvo como comparadores o controles:** algoritmos por defecto (opción 1), variantes a
  mano (2), Evolver (3), un portafolio genérico ajustado (4) y la construcción por complementariedad
  (6). La configuración por defecto y la generalista (SBS) siguen siendo comparadores obligatorios de
  la RQ3.
- **Implicaciones:**
  - **Coste cuadrático:** cada c*_P se evalúa en todos los problemas de evaluación, con
    |entrenamiento| × |evaluación| × semillas ejecuciones, además de una ejecución de ajuste por
    problema de entrenamiento. El tamaño del estudio (número de problemas, presupuesto de ajuste,
    semillas) se fija con el micro-benchmark de tiempos de VAMOS, que es la primera tarea de la fase 2.
  - **Fuga:** c*_P solo puede ajustarse con P. Si un problema pasa de entrenamiento a evaluación en otra
    partición, su configuración no se usa como donante de su propio grupo de formulación. Los alias y
    variantes (E11, E23) comparten grupo.
  - **La puerta G2 sigue vigente:** hay que medir el hueco entre la mejor c*_P única y el VBS sobre las
    c*_P. Si las configuraciones ajustadas apenas se distinguen entre sí, no queda margen para la
    transferencia.
  - **Para los métodos 6 y 7 de la RQ3** se necesita la matriz cruzada completa del rendimiento de c*_P
    sobre Q.

## D3 — Ejecutor: VAMOS

- **Fecha y autor:** 2026-10-19, decisión del usuario.
- **Decisión:** todas las ejecuciones de optimización y el ajuste por problema de D2 se hacen en
  VAMOS (1.0.0, fork local en `0a8bbb0`), con la versión y el backend fijados. Por la regla de generar
  y evaluar en el mismo framework, el ajuste de D2 usa el tuner de VAMOS (racing por defecto; el
  backend concreto se decide en la fase 2).
- **Implicaciones:**
  - Evolver y jMetal quedan fuera de la campaña. El adaptador Java de MOLA se mantiene solo como
    productor del formato de intercambio.
  - La invariancia de los operadores de VAMOS ante cambios de unidades (E19, por lectura estática) se
    confirma ejecutando antes de la RQ1.
  - VAMOS se usa como dependencia externa de los experimentos y no se modifica desde este proyecto.

## Decisiones técnicas de la fase 1 (tomadas al implementar; reversibles)

- **T1 — Definición de punto soportado:** un punto no dominado es soportado si minimiza alguna suma
  ponderada con pesos no negativos que sumen 1, admitiendo empates. Es la intención documentada en
  CLAUDE.md ("findable by minimizing some linear scalarization" y "lies on a facet"), que incluye los
  puntos soportados no extremos (caso B). La versión 0.2.0 implementaba en la práctica la variante
  extrema y, además, con los fallos E1 y E3.
- **T2 — Contrato de normalización (E5):** `dist_x_avg_neig` y `dist_f_avg_neig` se normalizan con
  el rango global de distancias de su espacio, como establece la decisión "Normalization reference" de
  CLAUDE.md y como hacían la tesis y moorphology. Se corrige el código, no la documentación.
