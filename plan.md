# Plan — Recomendación de configuraciones por similitud de paisajes (continuación de MOLA)

Borrador del 2026-10-19, actualizado el 2026-10-20 y el 2026-10-26 (orden de las RQ, D7).

**Estado:**
- **Fase 0:** ejecutada el 2026-10-19. Resultados en `research/phase0/report.md`; el registro
  E1–E25 está en `research/phase0/claims.csv` y sustituye al de §3.
- **Fase 1:** ejecutada el 2026-10-19 (MOLA 0.3.0). G1 superada; `research/phase1/report.md`.
- **Fase 2:** ejecutada el 2026-10-20 (piloto). G2 superada por poco, con el margen concentrado en
  problemas multimodales; `research/phase2/report.md`.
- **Fase 2b:** irace frente a F-Race, el 2026-10-20. Con el mismo presupuesto, irace da mejores
  configuraciones en 32 de 37 problemas; `research/phase2b/report.md`.
- **Fase 3 (transferencia, RQ1; RQ3 en su pre-registro):** ejecutada el 2026-10-26.
  - **G3 no se supera:** en LOGO, +0.049 de media, mediana ≈ 0, p = 0.078.
  - Ningún método supera al generalista c*_ZDT3. Detalle en `research/phase3/report.md`.
  - El pre-registro tiene dos enmiendas, ambas anteriores a la matriz o a su análisis:
    - la 1, escalado de objetivos (D4);
    - la 2, IBEA en lugar de SMS-EMOA (D9).
  - El artículo (borrador en Overleaf) recoge el resultado negativo.
- **Fase 3c (bbob-biobj):** pre-registrada el 2026-10-26 (`research/phase3c/preregistration.md`),
  después de los análisis a posteriori de la fase 3: estratos, consenso, distancias y
  configuraciones aleatorias.
  - **Problemas:** 165 de bbob-biobj con D = 10, con la similitud controlada (misma función, función
    fuera y grupo fuera).
  - **Referencias:** generalistas ajustados con irace sobre el entrenamiento.
  - **Puertas:** G4 y G5.
  - **Estado:** la campaña de irace corre en NicoVM desde las 21:12 UTC del 2026-10-26 (61
    ajustes, unas 70 h).
- **Fase 3 en Evolver (D6):** después de la de VAMOS, la fase 3 se repite entera en Evolver/jMetal,
  con el espacio completo de NSGA-II (`NSGAIIDouble.yaml`) e irace.
- Las decisiones están en `research/decisions/decisions.md` (D1–D9, T1–T8).

---

## 1. Objetivo

**Objetivo operativo (el sistema).** Dada una instancia nueva, caracterizarla con MOLA, recuperar
la instancia o instancias conocidas más similares y devolver una configuración recomendada. La
respuesta debe incluir también la evidencia que la sostiene, una medida de confianza y una
alternativa generalista cuando la confianza sea baja.

**Objetivo científico (el artículo).** Determinar *cuándo* esa recomendación es fiable:

> **When Does Landscape Similarity Support Reliable Configuration Transfer in Multi-Objective Optimisation?**
> (¿Cuándo permite la similitud del paisaje transferir configuraciones de forma fiable en optimización multiobjetivo?)

**Relación entre ambos.** El sistema es la hipótesis del capítulo 7 de la tesis de Aldana-Martín
(recommoonder), reconstruida sobre MOLA. El artículo evalúa esa hipótesis. El sistema se mide por
la calidad de la configuración que devuelve. Acertar el vecino es solo un medio, aunque también
aporta explicación: "tu problema se parece a RE37".

**Contrato de salida del recomendador** (se define en la fase 0 y se implementa más adelante):

| Campo | Contenido |
|---|---|
| `neighbours` | Las k instancias conocidas más cercanas, con su distancia y su grupo de formulación |
| `recommended_configuration` | La configuración del portafolio que se recomienda, con su procedencia (de qué vecino o vecinos sale) |
| `expected_quality` | La calidad estimada para el presupuesto indicado, con incertidumbre |
| `confidence` y `decision` | `recommend` o `fallback_generalist`, junto con las señales que llevaron a esa decisión |
| `characterization` | El perfil y la versión del cálculo, el tamaño de muestra, la semilla, el estado de cada feature y las evaluaciones consumidas |

## 2. Posicionamiento frente al trabajo previo

| Trabajo | Qué hace | Consecuencia para nosotros |
|---|---|---|
| Aldana-Martín, tesis 2024, cap. 4 y 7 | moorphology (21 descriptores), una distancia de cocientes (ec. 4.1) y recommoonder; evaluación con pocos casos | Es el antecedente que se reproduce y amplía. Sus valores proceden de una implementación con fallos documentados (E12, E13) |
| MO-ELA, Preuß, Rook, Bossek y Trautmann, [arXiv 2602.00098](https://arxiv.org/html/2602.00098v1) | Escala X a [0,1] por cotas y F con min-max sobre la muestra. Usa 4 tamaños de muestra (100–1000) con 20 semillas, grafos kNN con k=1 y descuenta el coste de muestreo. Selecciona entre NSGA-II, SMS-EMOA y MOEA/D por defecto. Evalúa con una partición aleatoria 80/20 y **elige el modelo final en test** | Normalizar y descontar el coste **no son novedad**, son controles. Su protocolo de evaluación deja espacio para las particiones agrupadas |
| van der Blom y Vermetten, [arXiv 2605.04954](https://arxiv.org/abs/2605.04954) | Estudia el presupuesto dedicado a features en selección por instancia: compensa en la mayoría de escenarios, incluso con el 25 % del presupuesto | La contabilidad del coste forma parte del protocolo desde el principio |
| Liefooghe et al., EMO 2023 | 945 configuraciones *del generador de problemas* (28 350 instancias); NSGA-II, IBEA, MOEA/D y búsqueda aleatoria | Antecedente para la relación entre propiedades, algoritmo y presupuesto |

**Novedad posible:**
1. Una recomendación basada en recuperar instancias, que puede abstenerse, evaluada por la calidad
   de la configuración que devuelve.
2. Particiones agrupadas por formulación, comparadas con particiones aleatorias.
3. La invariancia frente a cambios de unidades, de las variables (D1) y de los objetivos (D4),
   como requisito que se puede comprobar. Se verifica ejecutando, tanto en las features como en el
   optimizador.

## 3. Registro de evidencias (estado a 2026-10-19)

Estados posibles: REPRODUCIDO, CONFIRMADO_EN_CODIGO, DOCUMENTADO_EN_HISTORIAL,
COMUNICADO_NO_REPRODUCIDO, HIPOTESIS y NO_DISPONIBLE.

| ID | Afirmación | Estado | Evidencia y alcance |
|---|---|---|---|
| E1 | `supported_mask` marca todo como soportado si hay ≤ M puntos, lo que es falso para M ≥ 3 | REPRODUCIDO | Caso A (§9). En RE33 (M=3) el 33.5 % de los conjuntos no dominados locales pasan por el atajo; en RE61 (M=6), el 100 % |
| E2 | Se pierden los puntos interiores de una cara soportada | REPRODUCIDO | Caso B. **Depende de la definición**: son soportados pero no extremos. Con datos continuos casi nunca aparecen |
| E3 | La prueba de facetas pierde vértices soportados: la combinación de normales de sus facetas incidentes apunta al ortante negativo, pero ninguna normal individual es ≤ 0 | REPRODUCIDO | Caso C (§9): se pierde el punto que minimiza f₃. En DTLZ2 se pierden 215 vértices y `lsupp_avg_neig` sale 0.379 frente a 0.408 exacto; en RE33, 0.771 frente a 0.788. **Es el error que más pesa** |
| E4 | El k-NN se construye sobre las variables sin escalar | REPRODUCIDO | En RE25, RE33, RE35 y RE42 solo se comparte un 7–20 % de vecinos con el grafo normalizado por cotas. **Corrección:** el cambio de `fdc` en RE25 (−0.04 → 0.51) viene de cambiar las coordenadas de las distancias globales, no del grafo, porque `fdc` no usa vecinos |
| E5 | `dist_x_avg_neig` y `dist_f_avg_neig` devuelven valores en bruto, pero CLAUDE.md los da por normalizados | CONFIRMADO_EN_CODIGO | `features/evolvability.py` |
| E6 | Bajo un escalado uniforme de X cambian por un factor constante los `*_max` en bruto, `dist_x_avg_neig`, `slo/plo_dist_max` y los cocientes `dist_f_dist_x_*` y `diff_f_dist_x_*`; no cambian las correlaciones, proporciones y rangos | CONFIRMADO_EN_CODIGO, por lectura; falta un test | **Corrige** la afirmación previa de que "solo cambian los máximos" |
| E7 | El `pom.xml` depende de un snapshot en un repositorio cerrado (OSSRH terminó en junio de 2025). Con jMetal 7.8 compila y pasan los 32 tests | REPRODUCIDO con la caché `~/.m2` | Falta comprobarlo con un repositorio Maven vacío |
| E8 | No hay CI | CONFIRMADO_EN_CODIGO | No existe `.github/workflows/` |
| E9 | `Sample` no rechaza NaN ni inf | CONFIRMADO_EN_CODIGO | `sample.py`. Hay que distinguir una entrada inválida de una feature matemáticamente indefinida |
| E10 | `moocore.pareto_rank` da los mismos rangos que el ranking de jMetalPy, y es mucho más rápido | REPRODUCIDO en 15 problemas RE | Falta probar duplicados, empates y M > 3. El ranking supone unos 7 s de los 15 s totales a D=30 |
| E11 | Duplicados en jMetalPy: RE34 ≡ Liao2008 y RE37 ≡ Goel2007 (51/51 columnas idénticas); Vaidyanathan2004 es la variante de 4 objetivos de RE37 | REPRODUCIDO | La tesis empareja Vaidyanathan2004 con RE37; en jMetalPy el idéntico es Goel2007. Los 72 problemas de MOLA son en realidad 70 distintos |
| E12 | Fallos de moorphology recogidos en la auditoría: sup/inf/inc por rango global, acumulador `=`, filtro de pares, D−1 vecinos y normalizador de F | DOCUMENTADO_EN_HISTORIAL | Commits `0eda131` y `64c88d5`. Las sumas (d−1)/d del Listado 4.1 y la Tabla 4.2 son coherentes con el fallo de los vecinos |
| E13 | En moorphology, el ranking local sobrescribe el rango global | CONFIRMADO_EN_CODIGO | moorphology `master` (última actividad 2024-01-19), líneas 129–131, 243–248 y 324–328. En jMetal 6.1, `attributeId = getClass().getName()`. Es coherente con los `rank_max` publicados (1 con D=2; 2 con D=4). **Pendiente:** ejecutarlo y confirmar que esa versión generó los resultados de la tesis |
| E14 | Réplica de la Tabla 4.2 con MOLA (un problema de COCO, 100 muestreos): las distancias vecinales tienen CV 1.8–3.2 % y las del subconjunto no dominado 43–60 %; `|ND|` ≈ 4 | REPRODUCIDO para ese problema | **No es generalizable.** Comparar una media normalizada con una en bruto no es equivalente; para atribuir el cambio al fallo `=` hay que ablacionar sobre las mismas X y F |
| E15 | La métrica de la tesis, con features de MOLA, reconoce el mismo problema tras remuestrear (ZDT y DTLZ, 3 semillas: 100 % en 1-NN; ruido medio entre distancia media a otros = 0.10) | REPRODUCIDO | **No es comparable** con el 2.175/5.573 de la tesis, que usa el vecino distinto más cercano. Reconocer no es transferir |
| E16 | La métrica de la tesis no está definida con valores con signo ni con 0/0 | CONFIRMADO matemáticamente | Las dos correlaciones vecinales del conjunto de 21 **ya tienen signo**, así que el problema está en el diseño original |
| E17 | La región de bbob-biobj es [−100,100]^d | REPRODUCIDO | `cocoex` 2.8.2: `lower_bounds`/`upper_bounds`. Las instancias de una misma función pueden diferir mucho, así que no sirven como verdad de referencia de similitud |
| E18 | Protocolo de MO-ELA (ver §2) | DOCUMENTAL | arXiv v1 |

**Matriz de afectación**, en lugar de "los números de la tesis no sirven":
- **Fiables según la auditoría:** `nd_n`, `dist_x_avg`, `dist_x_max`, `dist_f_max` y los máximos
  vecinales.
- **Afectados:** `rank_*` (E13), `sup/inf/inc`, `lnd`, `lsupp`, `dist_f_avg`, `dist_x_nd_*` y las
  medias vecinales.
- Hay que comprobarla feature a feature en la fase 0.

**Scripts de evidencia (temporales).** Están en
`C:\Users\nicor\AppData\Local\Temp\claude\c--Users-nicor-Desktop-MOLA\b46447c5-9140-40db-99a7-3a5aa63cce61\scratchpad\`:
`scale_check.py`, `scale_impact.py`, `table42_replica.py`, `similarity_runs.py`,
`similarity_analysis.py`, `thesis_metric.py`, `metric_breakage.py`, `lsupp_impact.py`,
`zdt_dtlz_seeds.csv` y `moorph_src/ProblemCharacterization.java`. **Ese directorio se borra al
terminar la sesión**; si se quieren conservar, hay que copiarlos a `research/evidence/`.

## 4. Preguntas de investigación

Orden fijado el 2026-10-26 (D7):
1. primero la pregunta central, la del título;
2. después las dos que acotan cuándo se sostiene: las unidades y el muestreo;
3. al final la que decide cuándo recomendar, que usa las señales y las pérdidas de las anteriores.

La RQ2, la RQ3 y la RQ4 se miden con la pérdida de transferencia que define la RQ1. La RQ5, añadida
el mismo día (D8), lleva la hipótesis de la RQ1 de un solo destino a un conjunto de test.

**Correspondencia con la numeración anterior.** Hasta el 2026-10-26 las RQ seguían el flujo del
recomendador: caracterizar, recuperar, recomendar y decidir. Los documentos anteriores a esa fecha
conservan la numeración antigua, porque están congelados: los pre-registros, los informes de las
fases 0 a 3e, D1–D6 y T1–T8 en `decisions.md` y el prompt de la §9. La puerta G3 contesta la RQ1
actual; su regla no cambia.

| Actual | Anterior | Pregunta | Paso del sistema |
|---|---|---|---|
| RQ1 | RQ3 | Transferencia | Recomendar |
| RQ2 | RQ1 | Invariancia y geometría | Caracterizar |
| RQ3 | RQ2 | Incertidumbre del muestreo | Recuperar |
| RQ4 | RQ4 | Cuándo recomendar | Decidir |
| RQ5 | (nueva) | Selección del conjunto de entrenamiento | Recuperar un conjunto y ajustar sobre él |

**RQ1. Transferencia (pregunta central).** ¿Devuelve el vecino más similar una configuración mejor
que las alternativas siguientes, en formulaciones y familias no vistas?
- **Comparadores:**
  1. Configuración generalista (el SBS de entrenamiento).
  2. Vecino por metadatos (D, M y cotas).
  3. Donante aleatorio.
  4. Distancia de la tesis, documentando sus casos indefinidos.
  5. Distancia adaptada a cada tipo de feature.
  6. Pesos aprendidos o un predictor sencillo de la pérdida de transferencia.
  7. **Un selector directo de configuraciones con las mismas features**, para ver si recuperar
     donantes aporta algo más que explicación.
- **Medidas:**
  - La pérdida de transferencia L(P→Q; b) = H_Q(c*_Q, b) − H_Q(c*_P, b), que puede ser asimétrica y
    depender del presupuesto.
  - El regret frente al VBS y la mejora frente al SBS.
  - Acertar el ganador queda como medida secundaria, porque hay casi empates.
- **Control de fuga:** el mismo pipeline con 80/20 aleatorio y con particiones agrupadas. Todas
  las semillas, cambios de unidades, alias (E11) y variantes van al mismo grupo.
- **Lo que debilitaría la hipótesis:** que la ventaja desaparezca al agrupar o que los metadatos
  den lo mismo. Sería un resultado negativo publicable.

**RQ2. Invariancia y geometría.** ¿Cambian el vecino recuperado y la configuración recomendada
cuando se cambian las unidades de las variables o de los objetivos sin cambiar el problema?
- **Estado (2026-10-20):**
  - **Variables:** las 49 features con geometría `bound` (fase 1) y el portafolio de NSGA-II de
    VAMOS sin PCX, UNDX, mutación gaussiana, mutación de Cauchy, reparación `round` ni inicializador
    Halton (fase 2) son invariantes bit a bit.
  - **Objetivos:** las 49 features con `objective_scaling = "sample"`, todo el espacio de NSGA-II y
    MOEA/D son invariantes; SMS-EMOA no lo es (fase 3, D4).
- **Idea clave.** Si los operadores del optimizador trabajan relativos a las cotas (SBX y mutación
  polinómica), su comportamiento no cambia ante transformaciones afines positivas por variable,
  aplicadas a la vez a puntos, cotas y función. En ese caso la recomendación correcta tampoco debe
  cambiar, y cualquier cambio es un artefacto de la caracterización. Hay que verificar primero esa
  invariancia en VAMOS.
- **Factores:**
  - Geometría en bruto frente a normalizada por cotas.
  - k ∈ {1, D, valores acotados}.
  - Cambiar solo el grafo frente a cambiar también las coordenadas de medida.
  - Escalado del vector de features al comparar problemas.
- **Medidas:** solapamiento de vecinos, cambio de features, cambio del donante y pérdida de calidad
  de la configuración elegida.
- **Resultado que también sería informativo:** que el grafo cambie mucho y la recomendación apenas.

**RQ3. Incertidumbre del muestreo.** ¿Cuánta variabilidad del muestreo llega a la recomendación?
- **Tamaños de muestra:** 100, 200, 500, 1000 (alineados con MO-ELA) y 200·D, con LHS
  independientes para cada tamaño y nunca prefijos de un LHS mayor.
- **Hay que separar:** la variabilidad de la caracterización, la del algoritmo y las diferencias
  entre problemas.
- **Medidas:**
  - Varianza dentro de un problema frente a la separación entre problemas.
  - Frecuencia de features indefinidas y número de puntos no dominados.
  - Estabilidad de los vecinos y de la configuración elegida.
  - Relación entre la confianza estimada y la pérdida observada.
- **Hipótesis:** estas señales predicen la fiabilidad mejor que la normalidad de cada descriptor.
  Una recomendación puede ser estable y aun así estar equivocada.

**RQ4. Cuándo recomendar.** ¿Reduce una política de recomendación calibrada las transferencias
perjudiciales con el mismo presupuesto total?
- **Política del primer artículo:** caracterizar con un presupuesto fijo, recomendar si la
  evidencia supera un umbral calibrado y usar la configuración generalista en los demás casos.
- **Cómo se calibra:** el umbral se ajusta solo en entrenamiento y validación. No se presenta como
  garantía fuera de distribución.
- **Medidas:** calidad final, coste de caracterización, curvas de cobertura frente a riesgo y
  frecuencia y tamaño de las pérdidas frente al SBS.
- **Ampliación para un segundo artículo:** poder comprar otro bloque de muestras, es decir, una
  política secuencial. Se aborda solo si el piloto muestra margen.

**RQ5. Selección del conjunto de entrenamiento.** Dado un conjunto de problemas de test, ¿da mejor
resultado en el test una configuración ajustada sobre los problemas de entrenamiento más parecidos
por paisaje que otra ajustada sobre estos conjuntos?
- todos los problemas de entrenamiento;
- los más parecidos por metadatos;
- una selección aleatoria del mismo tamaño.

Detalles:
- **Relación con la RQ1:** misma hipótesis de similitud y misma dirección (de los destinos a los
  problemas conocidos). Cambian dos cosas:
  - se recupera un conjunto de problemas;
  - sobre él se ajusta una configuración nueva, en lugar de reutilizar la de un donante.
- **Primera evidencia, sin coste adicional:** `knn_selector` de la fase 3, que elige la
  configuración del portafolio con mejor HVn medio sobre los 3 problemas más cercanos.
- **Diseño:** se pre-registra después de G3.
  - **Pliegues:** se deja fuera una familia en cada uno (LOFO).
  - **Cuatro brazos de irace con el mismo presupuesto** (20 000 experimentos, D5): todos los
    problemas de entrenamiento, los k más parecidos por paisaje, los k más parecidos por metadatos
    y k al azar.
  - **Evaluación:** HVn en los problemas de test con las semillas 5001–5010.
  - **Se fijan en el pre-registro:** cómo se agrega la similitud sobre varios destinos, el valor de
    k y el framework.
- **Medidas:** HVn en test frente al generalista, distancia al VBS y sensibilidad a k.
- **Coste:** unas 32 ejecuciones de irace por framework, alrededor de 1.5–2 días en NicoVM.
- **Riesgos:**
  - Con un k pequeño, irace sobreajusta.
  - Si el test es heterogéneo, la selección tiende al conjunto completo y equivale al generalista.
  - De los problemas de test solo se usan sus features, nunca su rendimiento.
- **Aplicación final:** en la fase 5, elegir entre los 37 problemas de desarrollo el conjunto de
  entrenamiento para los 17 reservados. También da un criterio para elegir los conjuntos de
  entrenamiento en estudios de meta-optimización como el de Evolver, donde hoy se eligen a mano.

## 5. Diseño experimental

| Elemento | Decisión |
|---|---|
| Problemas | Continuos y deterministas, con restricciones solo de caja. Dos objetivos en el estudio principal y tres como validación |
| Suites | COCO bbob-biobj, que aporta repetibilidad e instancias identificables; DTLZ, WFG y ZDT; UF y LZ09 mediante el adaptador Java; ZCAT; RE y RWA sin duplicados |
| Particiones | 1. Mismo problema con otro muestreo (reconocimiento). 2. Misma formulación con otra instancia (transferencia próxima). 3. Formulación excluida (generalización). 4. Familia o suite excluida. Los grupos finales se reservan **antes** de ajustar el método; los casos RE/RWA ya inspeccionados son de desarrollo |
| Portafolio | **Decidido (D2, D3, D5):** una configuración c*_P ajustada **con irace** (≥ 20 000 experimentos) para cada problema de entrenamiento P; el portafolio es la unión de esas c*_P. Todo se ejecuta en VAMOS 1.0.0 (`0a8bbb0`, motor numpy), sobre el espacio de NSGA-II invariante. La configuración por defecto y la generalista (SBS) son comparadores. **La complementariedad entre la mejor c*_P única y el VBS es una puerta** (§6). Ver `research/decisions/decisions.md` |
| Caracterización | MOLA (0.4.0) con geometría `bound`, k = D y escalado de objetivos `sample` (D1, D4), con las 49 features y con el perfil histórico comparable (19 de los 21 descriptores, distancia de la tesis). Como trabajo futuro, un método viable basado en MO-ELA o ELA bajo el mismo protocolo |
| Presupuesto | B_total = B_caracterización + B_optimización + B_configuración_en_objetivo; el último término es 0 si no se configura sobre el problema nuevo. Las soluciones evaluadas al caracterizar se **conservan** en el archivo final |
| Controles | La configuración generalista con todo el presupuesto, y **el mismo muestreo inicial con la configuración generalista** y el presupuesto restante. Si la muestra inicializa la población, esa decisión se fija y se controla |
| Medidas | HV con referencia y normalización fijas por problema (solo para evaluar, nunca como entrada) e IGD+ donde haya un frente defendible. Se guardan trayectorias para cubrir varios presupuestos con una ejecución |
| Estadística | Agregación por problema o grupo y comparaciones emparejadas. Las semillas y los pares donante–destino no cuentan como problemas independientes. Semillas independientes para muestreo, optimización y particiones. Nada de bootstrap ingenuo de filas de un LHS |
| Figuras | Sensibilidad a unidades; incertidumbre e indefinidos frente al tamaño de muestra; distancia frente a pérdida de transferencia; calidad frente al coste de caracterización; cobertura frente a pérdida cuando se recomienda |

## 6. Fases y puertas

| Fase | Trabajo | Criterio de cierre o puerta |
|---|---|---|
| 0. Evidencias y contrato | Recuperar scripts, fijar versiones, verificar E1–E18 con ejemplos mínimos, escribir el contrato de features y del recomendador, y definir el protocolo del piloto (prompt en §9) | `PHASE0_COMPLETE` o `PHASE0_PARTIAL`, con los hallazgos trazables |
| 1. Núcleo verificable | Corregir los defectos confirmados (prueba de soporte exacta, perfil de geometría versionado, contrato de normalización, estados de indefinido, validación de no finitos, `k` explícito, CI y `pom`), sin regenerar todavía los CSV históricos | **G1:** tests verdes y concordancia con referencias exactas |
| 2. Piloto | Estabilidad, escalado, coste y complementariedad del portafolio con unos 40 problemas y 5 semillas | **G2:** hueco SBS–VBS suficiente, con umbral fijado antes. Si no lo hay, se diversifica el portafolio |
| 3. Transferencia | Matriz de rendimiento con VAMOS y comparación de métodos con particiones agrupadas frente a aleatorias | **G3** (RQ1): ¿supera el paisaje a los metadatos? Si no, el resultado negativo se publica |
| 3s. Selección del conjunto de entrenamiento | Pre-registro tras G3; LOFO con cuatro brazos de irace (paisaje, metadatos, todos, al azar) | RQ5 respondida en desarrollo; se aplica a los 17 reservados en la fase 5 |
| 4. Confianza y presupuesto | Calibrar la política de recomendación o alternativa generalista | RQ4 respondida con presupuesto total |
| 5. Evaluación final y artículo | Congelar el método, ejecutar los grupos reservados y preparar datos, código y manuscrito | Resultados reproducibles, incluidos los negativos |

## 7. Decisiones abiertas y riesgos

- **Decidido el 2026-10-19** (`research/decisions/decisions.md`): geometría `bound` por defecto
  (D1), portafolio de configuraciones ajustadas por problema (D2) y ejecución en VAMOS (D3).
- **Decidido el 2026-10-20:**
  - escalado de objetivos `sample` para el recomendador (D4);
  - ajuste siempre con irace, con ≥ 20 000 experimentos (D5);
  - el cálculo pesado se hace en NicoVM, comprobando antes que está libre.

  Con los tiempos medidos se estimaron unas 20 h para el ajuste de los 37 problemas de desarrollo
  en NicoVM, y unos 30 min para la matriz cruzada. El ajuste tardó en realidad 43 h, del
  2026-10-20 a las 10:27 UTC al 2026-10-22 a las 05:41 UTC.
- **Decidido el 2026-10-20 y el 2026-10-21:** réplica de la fase 3 en Evolver/jMetal con el espacio
  de NSGA-II sin los cuatro operadores no invariantes (D6).
- **Decidido el 2026-10-26:**
  - nuevo orden de las preguntas de investigación, con la transferencia como RQ1 (D7, §4);
  - nueva RQ5, la selección del conjunto de entrenamiento, que se pre-registra tras G3 (D8, §4).
- **Fallos de VAMOS 1.0.0 encontrados, a comunicar al proyecto:**
  - `racing/refill.py:25` falla con parámetros condicionales en el racing iterado;
  - PCX, UNDX, la mutación gaussiana, la de Cauchy, la reparación `round` y el inicializador Halton
    no son invariantes ante cambios de unidades;
  - el frente de referencia de UF6 está incompleto.
- **Comunicación con Aldana-Martín y Nebro:** al terminar la fase 0, describiendo exactamente lo
  demostrado (E12 y E13) y proponiendo coautoría. Preguntas para ellos (antes en
  `research/decisions/questions.md`):
  - ¿Aceptan que MOLA use por defecto la geometría `bound` y conserve `raw` para reproducir lo
    publicado?
  - ¿Qué versión de moorphology generó los números de la tesis y del grafo de moody? (E13)
  - ¿El artículo se plantea como transferencia de configuraciones ajustadas por problema? Es la
    línea de la tesis y la que sigue el estudio (D2).
- **Comprobación pendiente: cotas de RE24.** VAMOS pone x2 ∈ [4, 50] y jMetal x2 ∈ [0.5, 50]; hay
  que contrastarlo con el código de referencia de Tanabe e Ishibuchi.
- **Invariancia de los operadores de VAMOS:** es la condición de la RQ2 y hay que verificarla
  antes de usarla.
- **Calendario:** GECCO 2027, cuyo plazo suele caer a finales de enero (confirmarlo). Si no llega,
  una revista (ECJ o TELO).
- **No regenerar ahora los CSV de `examples/benchmarks/`.** Cada resultado nuevo identifica la
  versión del cálculo y la geometría que lo produjeron.

---

## 8. Cambios respecto al prompt de fase 0 recibido

1. Incluye el **objetivo operativo** y pide como entregable el contrato de salida del
   recomendador, sin implementarlo.
2. Añade el **caso C** (E3, el error que más pesa) y aclara que el resultado esperado del caso B
   depende de la definición de soportado.
3. **Corrige el presupuesto.** La versión anterior, con 5 semillas, sumaba unas 19 000 evaluaciones
   frente a un límite de 10 000. Ahora el límite es de 25 000 y se fija el número de semillas por
   problema. El control de cotas homogéneas pasa a ser RE36, porque RE34 y RE37 tienen duplicados.
4. Añade los **detalles del entorno**: Python 3.12 para el venv, Maven incluido en IntelliJ (no
   está en el PATH), Java 21/24, instalación de `coco-experiment` y lectura del repo de VAMOS sin
   tocar la configuración global de git.
5. Incluye el **registro previo E1–E18** como punto de partida para volver a verificar.
6. Añade la **ablación `=`/`+=` sobre las mismas X y F** y la comprobación, solo leyendo código, de
   la invariancia de los operadores de VAMOS.
7. Fija la **ubicación de los resultados**: rama `research/phase0`, directorio `research/phase0/`.

## 9. Prompt de fase 0 (actualizado)

```markdown
# Fase 0 — Referencia reproducible para un recomendador de configuraciones basado en similitud de paisajes

Trabaja sobre el repositorio local `C:\Users\nicor\Desktop\MOLA` (remoto https://github.com/ajnebro/MOLA).
Lee primero `plan.md` (objetivo, registro E1–E18, RQs) y `CLAUDE.md`.

**Objetivo del proyecto.** Dada una instancia nueva, caracterizarla con MOLA, recuperar las instancias
conocidas más similares y devolver una configuración recomendada con su confianza, o la configuración
generalista si la confianza es baja. El artículo asociado estudia cuándo esa transferencia es fiable.
VAMOS (`C:\Users\nicor\Desktop\VAMOS`) ejecutará más adelante el portafolio.

**Ejecuta únicamente la fase 0:** recuperar evidencias, verificar el comportamiento actual con ejemplos
pequeños y fijar el contrato y el protocolo del piloto. No des por buenas las conclusiones previas:
distingue lo reproducido, lo confirmado por lectura, lo documentado en el historial, lo comunicado sin
reproducir y las hipótesis.

## 1. Alcance

- Crea la rama `research/phase0` y guarda todo en `research/phase0/`. Conserva cualquier trabajo previo
  del usuario.
- No cambies el comportamiento por defecto del núcleo ni sobrescribas `examples/benchmarks/`.
- No implementes selectores, muestreo adaptativo, RDF ni la integración con VAMOS o Evolver.
- No hagas push, no abras PR y no envíes mensajes a nadie.
- No lances campañas de optimización ni las 55 × 100 caracterizaciones.
- Límite del piloto: **25 000 evaluaciones nuevas** y **60 minutos de reloj**. Registra lo que gastes de
  verdad. Si una comprobación no puede completarse, documenta la causa y sigue con el resto.
- Al terminar, entrega el informe y la propuesta de fase 1. No empieces la fase 1.

## 2. Entorno (Windows 11; Git Bash y PowerShell disponibles)

- Python: crea un venv temporal con `C:\Users\nicor\AppData\Local\Programs\Python\Python312\python.exe`
  (el 3.14 por defecto puede no tener ruedas para todas las dependencias) e instala `pip install -e ".[dev]"`
  y `coco-experiment`.
- Java: hay JDK 21 y 24. Maven no está en el PATH; usa
  `C:\Program Files\JetBrains\IntelliJ IDEA 261.17801.55\plugins\maven\lib\maven3\bin\mvn.cmd`.
- VAMOS: léelo sin modificar la configuración global de git (por ejemplo
  `git -c safe.directory=C:/Users/nicor/Desktop/VAMOS log -1`).
- Registra las versiones de Python, Java, Maven, numpy, scipy, jmetalpy, moocore, cocoex y VAMOS, y
  los comandos para reproducir el entorno.

## 3. Inventario y evidencias

- Registra ruta, remoto, rama, SHA y estado de MOLA. La referencia revisada es
  `58bc0ca69f17c1bee2c078360ec7cfa4995e621b`; comprueba si sigue siéndolo.
- Busca los scripts de evidencia de `plan.md` §3, primero en `research/evidence/` y después en la ruta
  temporal indicada allí. Si faltan, márcalos como NO_DISPONIBLE; puedes reproducirlos de forma
  independiente, pero sin atribuirles las cifras originales. Guarda hashes y procedencia de todo lo que
  uses.
- Recupera la auditoría de moorphology de los commits `0eda131` y `64c88d5`.
- Descarga moorphology (`https://gitlab.com/jfaldanam-phd/moorphology`, rama `master`), registra su SHA y
  no presupongas que esa versión generó los resultados de la tesis.

## 4. Registro de afirmaciones (`claims.csv`)

Columnas: id, descripción, fuente, comprobación ejecutada, resultado, estado, features afectadas y acción
recomendada. Estados: REPRODUCIDO, CONFIRMADO_EN_CODIGO, DOCUMENTADO_EN_HISTORIAL,
COMUNICADO_NO_REPRODUCIDO, HIPOTESIS y NO_DISPONIBLE.

Parte de E1–E18 de `plan.md` y **vuelve a verificar cada una**. Una diferencia entre implementaciones no
prueba por sí sola que una de ellas esté mal.

## 5. Contratos

**`feature_contract.csv`.** Recoge la correspondencia entre las 21 features del capítulo 4 de la tesis y
las 49 de MOLA. Para cada una:
- definición y datos que usa;
- normalización y denominador;
- rango esperado y si admite signo;
- condiciones para estar definida;
- diferencias entre el documento, moorphology y MOLA;
- procedencia de la definición.

Separa los 19 nombres compartidos de `dist_x_max_neig` y `dist_f_max_neig`, y no añadas estas dos a
MOLA. Separa también:
1. las coordenadas con que se construye el grafo;
2. las coordenadas y la escala con que se mide cada feature;
3. el escalado del vector de features para comparar problemas o aprender.

Revisa con especial atención `dist_x_avg_neig`, `dist_f_avg_neig`, `dist_x_nd_*`, `fdc`, `rank_*`,
`supp_n` y `lsupp_avg_neig`. Distingue una entrada X/F no finita, que es inválida, de una feature
matemáticamente indefinida, que necesita un estado y una causa y nunca debe convertirse en 0.

**`recommender_contract.md`.** Define los campos de salida de `plan.md` §1, la representación de una
abstención y qué información de procedencia se devuelve. No lo implementes.

**`affectation_matrix.csv`.** Indica, por feature y fuente (tesis, grafo moody de Zenodo y CSV de MOLA),
si está afectada, por qué fallo y con qué nivel de evidencia.

## 6. Comprobaciones mínimas

### 6.1 Puntos soportados

Define "soportado": minimizador de alguna suma ponderada con w ≥ 0 y Σw = 1. Distingue "soportado" de
"soportado extremo". Construye un verificador independiente mediante factibilidad lineal y compara con
`supported_mask`:

- **A** `[(0,1,1), (1,0,0), (0.6,0.6,0.6)]` → referencia `[True, True, False]`.
- **B** `[(0,2), (0.5,1.5), (2,0), (1.5,1)]` → `[True, True, True, False]` con "soportado";
  `[True, False, True, False]` con "soportado extremo". Documenta cuál adopta MOLA.
- **C** `[(0.4,0.5,0.3), (0.9,0.2,0.8), (0.5,0.3,0.7), (0.8,0.9,0.1)]` → referencia
  `[True, True, True, True]`. El cuarto punto minimiza f₃ y por tanto es soportado; MOLA lo marca como
  no soportado (E3).
- Mide el impacto sobre `supp_n` y `lsupp_avg_neig` en DTLZ2 (M=3) y RE33 con el verificador exacto.

### 6.2 Rankings y efectos laterales

- Verifica en jMetal 6.1 cómo se almacena el rango (`attributeId`).
- Si puedes ejecutarlo, crea soluciones con frentes conocidos, calcula el ranking global, calcula
  rankings locales sobre las mismas instancias y comprueba si cambian los valores que después se leen
  como globales. Repite con objetos aislados.
- En moorphology, comprueba el orden de las llamadas y la identidad de los objetos.
- Separa la demostración del mecanismo de su impacto en los datos publicados.
- Comprueba también que MOLA no sufre el efecto (crea objetos nuevos en cada ranking).

### 6.3 Vecindades y dominancia

Comprueba:
- que el propio punto se excluye por índice;
- el comportamiento con vectores duplicados;
- el número efectivo de vecinos y los denominadores cuando hay menos vecinos de los pedidos;
- que sup + inf + inc suman 1;
- la diferencia entre dominancia por pares y comparación de rangos globales.

### 6.4 Escalado

- Aplica transformaciones afines positivas por variable a la vez a puntos, cotas y función, sobre los
  mismos puntos canónicos.
- Separa el cambio del grafo del cambio de las coordenadas de medida, y comprueba que cambiar solo el
  grafo no modifica `fdc`.
- Verifica E6: qué features cambian por un factor constante y cuáles son invariantes.
- No exijas invariancia a las features que, por definición, son distancias en bruto.
- **Solo leyendo código:** comprueba si los operadores de VAMOS (SBX, mutación polinómica, reparación
  de cotas) son relativos a las cotas y, por tanto, invariantes ante esas transformaciones. Es la
  condición de la RQ1.

### 6.5 Casos degenerados y similitud

- Entradas no finitas, cotas degeneradas y muestras con 0–1 puntos no dominados.
- Para la distancia de la tesis, prueba valores positivos, negativos, 0/0 y features no disponibles.
  Recuerda que las correlaciones vecinales del conjunto de 21 ya tienen signo.
- No uses épsilons ni imputaciones silenciosas.

### 6.6 Entorno de ejecución

- Ejecuta `pytest` y `ruff` y registra los resultados reales.
- Compila el adaptador Java con un repositorio Maven **vacío** (`-Dmaven.repo.local=<dir temporal>`):
  primero tal cual, y después en una copia con `-Djmetal.version=7.8`, sin tocar el `pom.xml` de
  referencia.
- Comprueba `moocore.pareto_rank` frente al ranking de jMetalPy con duplicados, empates y M ∈ {2, 3, 5}.
- Los fallos conocidos que se reproduzcan son resultados válidos: no adaptes las pruebas para que pasen.

## 7. Piloto limitado (≤ 25 000 evaluaciones)

- **COCO** `bbob-biobj_f02_i02_d02` (`bbob_f001_i03_d02__bbob_f002_i05_d02`): n=400 y 5 semillas
  (2 000 evaluaciones). Registra identificador, instancias, dimensión, versión, región (`lower_bounds`
  y `upper_bounds`) y valores en puntos de referencia.
- **RE con cotas heterogéneas:** RE25, RE33 y RE42 con n=200·D y 3 semillas (unas 7 800 evaluaciones).
- **Control de cotas homogéneas:** RE36 con n=200·D y 3 semillas (unas 2 400 evaluaciones).
- Conserva las mismas X y F para comparar variantes, incluida una **ablación `=` frente a `+=`** del
  acumulador vecinal de moorphology reimplementado sobre esas mismas matrices.
- **Registra:**
  - features;
  - estado y causa de los indefinidos;
  - `|ND|` y vecinos efectivos;
  - solapamiento del grafo (bruto frente a normalizado por cotas);
  - tiempos de evaluación y de caracterización por etapa;
  - diferencias entre variantes.
- Si comparas similitud entre remuestreos, informa **por separado** de (a) la distancia al mismo problema
  dividida por la distancia media a otros y (b) la misma distancia dividida por la del vecino distinto
  más cercano.
- No presentes el reconocimiento como prueba de transferencia, ni este piloto como prueba general de que
  se invierte una conclusión de la tesis.

## 8. Protocolo y propuesta de fase 1

Prepara `protocol.md` para RQ1–RQ4 de `plan.md`. Incluye:
- el catálogo de equivalencias y variantes RE/RWA (E11) y las particiones agrupadas por formulación;
- la separación de semillas;
- el portafolio candidato y los comparadores (generalista, metadatos, donante aleatorio, distancia
  histórica, distancia revisada y selector directo);
- la contabilidad del presupuesto y la conservación de las soluciones del muestreo;
- el control con el mismo muestreo y la configuración generalista;
- las métricas;
- una estimación del piloto siguiente basada en tiempos medidos.

No uses prefijos de un LHS como muestras de menor tamaño ni interpretes un bootstrap de filas como
incertidumbre calibrada. Indica qué defectos deben corregirse antes de generar la matriz de
rendimiento y priorízalos frente a funcionalidades nuevas.

## 9. Entregables y cierre

En `research/phase0/`: `report.md`, `claims.csv`, `feature_contract.csv`, `affectation_matrix.csv`,
`recommender_contract.md`, `manifest.json` (versiones, hashes y procedencia), `costs.csv`, los scripts
y muestras del piloto, y `protocol.md` con la propuesta de fase 1.

El informe distingue: lo reproducido, lo confirmado por lectura, lo pendiente, las diferencias de
definición, los cambios recomendados y los límites de las conclusiones. Termina con `PHASE0_COMPLETE` o
`PHASE0_PARTIAL`, explicando el criterio.

Devuelve un resumen con los hallazgos prioritarios, las versiones, el coste real, los comandos de
reproducción y el alcance de la fase 1. No declares correcto MOLA porque pasen sus tests, ni inválida
la tesis porque se reproduzca un defecto.
```
