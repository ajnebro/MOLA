# Preguntas y respuestas del proyecto

Registro cronológico de las preguntas del usuario, la respuesta que se dio (resumida) y lo que se
decidió. Al final están las preguntas pendientes. Las decisiones formales están en
[`decisions.md`](decisions.md). La primera respuesta larga se guardó literal en
[`question1.md`](question1.md).

## Preguntas ya respondidas

### 1. ¿Qué recomendaciones e ideas hay para continuar MOLA? (2026-10-19)
- **Pregunta:** "Revisa https://github.com/ajnebro/MOLA. La idea es continuar con el trabajo de los
  autores previos, mejorarlo o actualizarlo. ¿Qué recomendaciones e ideas tienes?"
- **Respuesta:**
  - Fallos verificados en MOLA 0.2.0: el test de punto soportado (`supported_mask`), el grafo de
    vecinos sobre variables sin escalar, `dist_*_avg_neig` sin normalizar, el `pom.xml` apuntando a
    un snapshot ya retirado, la falta de CI y alias duplicados entre problemas.
  - Líneas de continuación: corregir, versionar y usar las features para recomendar
    configuraciones.
- **Resultado:** registro de evidencias E1–E18 en `plan.md`.

### 2. ¿Se puede aprovechar el capítulo 4 de la tesis de Aldana-Martín? (2026-10-19)
- **Respuesta:**
  - La idea de similitud entre paisajes (moorphology, la distancia de cocientes de la ec. 4.1 y
    recommoonder) es el antecedente directo.
  - Los números de la tesis salen de una implementación con fallos documentados: el ranking local
    sobrescribe el global (E13), el acumulador `=` en lugar de `+=` (E14) y otros.
  - La conclusión de estabilidad de la Tabla 4.2 se invierte al recalcularla con MOLA (un problema,
    pendiente de ablación).
- **Resultado:** E12–E16; ablación hecha en la fase 0.

### 3. Revisar las propuestas pegadas y plantear preguntas de investigación y un plan (2026-10-19)
- **Respuesta:**
  - RQ1, invariancia y geometría.
  - RQ2, incertidumbre del muestreo.
  - RQ3, transferencia: la pregunta central.
  - RQ4, cuándo recomendar.
  - Fases 0 a 5 con puertas G1–G3.
- **Resultado:** `plan.md` (commit `96c5071`).

### 4. Objetivo: dada una instancia, devolver una similar con una configuración recomendada (2026-10-19)
- **Pregunta:** "El objetivo es, dada una instancia, encontrar una similar o con características
  similares, y que se devuelva con una configuración recomendada… revisa el plan y actualiza el
  prompt. No lances ninguna fase todavía."
- **Respuesta:**
  - Es la pregunta "When does landscape similarity support reliable configuration transfer?"
  - Plan reescrito con el objetivo operativo y el contrato de salida del recomendador.
  - Prompt de la fase 0 actualizado: casos A, B y C, presupuesto y entorno.
- **Resultado:** `plan.md`, §9.

### 5. "Lanza la primera fase del plan" (2026-10-19)
- **Respuesta:** fase 0 ejecutada. Termina con `PHASE0_COMPLETE`, con un exceso de presupuesto
  declarado: 32 400 evaluaciones frente a 25 000.
- **Resultado:** `research/phase0/`, E1–E25.

### 6. ¿Qué geometría usar por defecto y de dónde sale el portafolio de configuraciones? (2026-10-19)
- **Respuesta, literal en `question1.md`:**
  - Geometría: A (`raw`), B (`bound`), C (híbrida) o D (normalización por la muestra).
  - Portafolio: opciones 1 a 6.
- **Resultado:** la pregunta 7.

### 7. "Guarda la respuesta como question1; 1B y 2.5; usamos VAMOS; guarda las decisiones; commit, push y siguiente fase" (2026-10-19)
- **Decisiones:**
  - **D1:** geometría `bound`.
  - **D2:** una configuración ajustada por problema de entrenamiento.
  - **D3:** VAMOS como ejecutor.
- **Resultado:** fase 1 ejecutada (MOLA 0.3.0, G1 superada), en `research/phase1/`.

### 8. "Comprueba lo ocupada que está esta máquina; si lo está, prueba cada 30 min hasta que sea razonable lanzar la siguiente fase" (2026-10-19)
- **Respuesta:**
  - La CPU estaba bien, pero la memoria no: 5 GB libres y el 88 % de memoria comprometida.
  - Bucle de comprobación cada 30 min con `check_load.ps1`, con estos umbrales: CPU < 35 %, ≥ 8 GB
    libres y memoria comprometida ≤ 85 %.
- **Resultado:** a las 00:16 del 2026-10-20 dio OK y se lanzó la fase 2.

### 9. "Si te quedas sin acabar, lanza continuar en 5 h" (2026-10-19)
- **Respuesta:** se programó un "continuar" para las 04:44 del 2026-10-20, y se ejecutó.

### 10. ¿Habrá diferencias si se usa irace en lugar de F-Race clásico? (2026-10-20)
- **Respuesta:**
  - Sí, sobre todo en la calidad de cada c*_P. F-Race desaprovechó presupuesto (mediana de 276 de
    400 ejecuciones), exploró solo 60 configuraciones aleatorias y eligió ganadores con 9 semillas.
  - G2 podría moverse en cualquier sentido.
  - Propuesta: comparar F-Race e irace con la normalización corregida.

### 11. "Usa irace en NicoVM" (2026-10-20)
- **Resultado:** fase 2b, en `research/phase2b/`.
  - irace supera a F-Race con el mismo presupuesto: 32 de 37 problemas, p = 6.5·10⁻⁷.
  - La normalización corregida, por sí sola, no cambia nada sistemático.
  - G2 se sigue superando: 31 % de los grupos con F-Race y 39 % con irace.

### 12. "¿Ha terminado? ¿Qué estamos haciendo?" (2026-10-20)
- **Respuesta:** la fase 2b había terminado; se resumieron sus resultados (los de la pregunta 11).

### 13. ¿Para qué necesitamos las mejores configuraciones de irace? (2026-10-20)
- **Respuesta:**
  - **En el recomendador**, son la base de conocimiento: se devuelve la c*_P del problema conocido
    más parecido.
  - **En la evaluación**, son la referencia: L(P→Q) = HVn(c*_Q, Q) − HVn(c*_P, Q), y de ellas salen
    el SBS y el VBS.
  - Si el ajuste es malo, se mide ruido del ajuste y no similitud. Ejemplo: DTLZ3 con F-Race.
  - Alternativa sin ajuste: un portafolio fijo. Sería selección de algoritmos, no transferencia.

### 14. "Usa siempre irace. Presupuesto de 20 000 o más. Comprueba siempre que NicoVM no está ocupado. Procede con tu recomendación" (2026-10-20)
- **Decisión:** D5.
- **Resultado:**
  - Fase 3 lanzada con irace, 20 000 experimentos por problema y normalización por el frente
    verdadero (T7).
  - Servidor persistente en NicoVM (T8).
  - Pre-registro de G3.

### 15. ¿Qué 37 problemas son? ¿Los de VAMOS o los de jMetal? (2026-10-20)
- **Respuesta:**
  - Son las implementaciones de VAMOS 1.0.0: ZDT1–4, DTLZ1–4 y 6 con M=2, LZ09 (8), UF1–7,
    10 ZCAT, RE21, RE24 y RWA1.
  - Se excluyeron:
    - los de codificación no continua;
    - los 17 reservados para el test final;
    - 5 duplicados exactos.

### 16. ¿Cómo encontramos y vemos si un problema se parece a otro? (2026-10-20)
- **Respuesta:**
  - Caracterizar con MOLA (49 features de una muestra LHS) y buscar el vecino más cercano con una
    distancia euclídea sobre features escaladas de forma robusta.
  - El parecido se valida midiendo si la configuración se transfiere bien (G3).
- **Hallazgo:** las features en unidades de los objetivos dominan la distancia. En DTLZ3, la
  distancia al vecino más cercano es 98 536.
- **Opciones presentadas:** escalar los objetivos por muestra, usar rangos en la distancia o dejarlo
  como está.

### 17. "Aplica la opción y actualiza el plan" (2026-10-20)
- **Decisión:** D4.
- **Resultado:**
  - MOLA 0.4.0 con `objective_scaling = "sample"`.
  - Se verificó que NSGA-II y MOEA/D de VAMOS son invariantes a las unidades de los objetivos.
  - Enmienda 1 al pre-registro de la fase 3.
  - `plan.md` actualizado.

### 18. ¿Tendría sentido hacerlo con Evolver en lugar de VAMOS? ¿Con todos los parámetros o con los del artículo? (2026-10-20)
- **Respuesta:**
  - **A favor de Evolver:** es la línea de la tesis y de Nebro, trae irace y un servidor de
    evaluación, y Java es más rápido.
  - **En contra:** revertir D3 y rehacer la base.
  - **Recomendación sobre el espacio:** el del artículo menos los operadores no invariantes.
  - **Opciones:** pasar a Evolver, hacer ambas o seguir solo con VAMOS.

### 19. "2, todo el espacio de NSGA-II" (2026-10-20)
- **Decisión:** D6. Primero la fase 3 en VAMOS y después una réplica completa en Evolver con todo
  el espacio de NSGA-II (`NSGAIIDouble.yaml`).
- **Resultado:** se midió la invariancia en jMetal 7.8.
  - **Objetivos:** todas las opciones son invariantes.
  - **Variables:** no lo son PCX, UNDC, el cruce de Laplace y la mutación uniforme.

### 20. "Quita esos 4 parámetros" (2026-10-21)
- **Resultado:**
  - Espacio de Evolver con 28 parámetros.
  - Pre-registro de la fase 3e y herramientas, en `research/phase3e/`.
  - Hallazgos de implementación:
    - **VAMOS:** UF3 tiene cotas [−1, 1].
    - **RE24:** las cotas difieren entre VAMOS y jMetal.
    - **jMetal:** RWA1 tiene un error de `10e-3`.
    - **Evolver:** la mutación no uniforme no se atenúa.

### 21. "En un fichero aparte, guarda todas las preguntas y respuestas, las hechas y las que vienen" (2026-10-21)
- **Resultado:** este fichero.

### 22. ¿Cuáles son las preguntas de investigación de MOLA? (2026-10-26)
- **Respuesta:** son las cuatro de `plan.md` §4. Son del artículo de continuación, no de la
  herramienta, y siguen el flujo del recomendador (caracterizar, recuperar, recomendar, decidir).
  - **RQ1, invariancia y geometría:** ¿cambian el vecino recuperado y la configuración recomendada
    al cambiar las unidades de las variables o de los objetivos? La invariancia ya está verificada
    en las features, en VAMOS y en jMetal. Falta el estudio completo de factores (k, solo el grafo
    o también las medidas, escalado del vector).
  - **RQ2, incertidumbre del muestreo:** ¿cuánta variabilidad del muestreo llega a la
    recomendación? En la fase 2, con 5 muestras: mediana de la proporción de varianza entre
    problemas de 0.99, reconocimiento del 63 % y donante estable en 21 de 37 problemas. Falta la
    malla de tamaños de muestra.
  - **RQ3, transferencia (la central):** ¿da el vecino más similar una configuración mejor que el
    SBS, el vecino por metadatos, un donante aleatorio, la distancia de la tesis o un selector
    directo, en formulaciones y familias no vistas? Se decide con G3 (fase 3, y su réplica 3e).
  - **RQ4, cuándo recomendar:** ¿reduce una política calibrada (recomendar o recurrir a la
    alternativa generalista) las transferencias perjudiciales con el mismo presupuesto total?
    Es la fase 4, aún sin empezar.

### 23. ¿El título y los pasos "caracterizar, buscar, recomendar, decidir" son las preguntas de investigación? (2026-10-26)
- **Respuesta:** no, son tres niveles distintos.
  - **El título** es la pregunta general del artículo: *cuándo* es fiable transferir configuraciones
    por similitud del paisaje.
  - **Los cuatro pasos** son el flujo del sistema (el objetivo operativo, `plan.md` §1). No son
    preguntas, solo ordenan las RQ.
  - **Las preguntas de investigación** son RQ1–RQ4, una por paso:
    - caracterizar → RQ1 (invariancia);
    - buscar → RQ2 (incertidumbre del muestreo);
    - recomendar → RQ3 (transferencia);
    - decidir → RQ4 (cuándo recomendar).

### 24. ¿Es correcto el orden de las RQ? ¿La RQ3 debería ser la primera, la segunda, la cuarta o seguir tercera? (2026-10-26)
- **Respuesta (recomendación):** la transferencia debería ser la primera. Orden propuesto:
  1. transferencia (la actual RQ3);
  2. invariancia (la actual RQ1);
  3. incertidumbre del muestreo (la actual RQ2);
  4. cuándo recomendar (la actual RQ4).
- **Motivos:**
  - Es la pregunta del título, la que tiene la puerta pre-registrada (G3) y el resultado principal.
  - Las otras tres se miden con la pérdida de transferencia, que se define en ella.
  - La invariancia está asegurada en gran parte por diseño (D1, D4, T5, D6). Queda como análisis de
    sensibilidad: cuánto cambiaría la recomendación con las definiciones publicadas.
  - El muestreo enlaza con la última: la estabilidad entre muestras es una señal de confianza.
  - Decidir cuándo recomendar tiene que ir al final, porque usa las señales y las pérdidas de las
    anteriores.
- **Si se adopta:**
  - Se renumera solo en `plan.md` y en el artículo, con una tabla de correspondencia.
  - Los pre-registros y los informes ya escritos conservan la numeración antigua, porque están
    congelados.
- **Decisión (2026-10-26):** "aplica el nuevo orden" (D7). Renumerado `plan.md` §4.

### 25. Dados unos problemas de test, ¿tiene sentido obtener de nuestro conjunto los problemas de entrenamiento? (2026-10-26)
- **Pregunta:** "¿tiene sentido que dados unos problemas, pongamos de test, obtengamos los problemas,
  pongamos de training, del conjunto de problemas que tenemos? Un poco al revés que la RQ1, o
  similar al menos."
- **Respuesta:** sí. Es la misma hipótesis de similitud, aplicada al conjunto de entrenamiento en
  lugar de a un solo donante.
  - **No es la dirección inversa.** Se va igualmente del destino a los problemas conocidos.
    Cambian dos cosas:
    - se parte de un conjunto de destinos, no de uno solo;
    - con los problemas recuperados se ajusta una configuración nueva, en lugar de reutilizar la
      del donante.
  - **Tres variantes, de menor a mayor coste:**
    - (a) 1 destino → 1 donante → su c*_P. Es `landscape_1nn`, la RQ1.
    - (b) 1 destino → sus k problemas más cercanos → la c*_P con mejor HVn medio sobre ellos. Es
      `knn_selector`, ya pre-registrado como análisis secundario de la fase 3. No cuesta ajuste
      adicional.
    - (c) Conjunto de test → subconjunto de entrenamiento más parecido → irace sobre ese
      subconjunto. Es la propuesta completa.
  - **Diseño propuesto para (c):** se deja fuera una familia en cada pliegue (LOFO) y se
    comparan cuatro brazos con el mismo presupuesto de irace (20 000 experimentos):
    - irace sobre todos los problemas de entrenamiento (generalista);
    - irace sobre los k más parecidos por paisaje;
    - irace sobre los k más parecidos por metadatos;
    - irace sobre k problemas al azar.
  - **Coste estimado de (c):** unas 32 ejecuciones de irace, alrededor de 1.5–2 días en NicoVM
    por framework. La campaña de la fase 3 tardó 43 h para 37 ejecuciones.
  - **Riesgos:**
    - Con pocos problemas de entrenamiento se sobreajusta.
    - Si el conjunto de test es heterogéneo, la selección acaba cogiendo casi todo y equivale al
      generalista.
    - Las features de test solo se usan para seleccionar, nunca su rendimiento.
  - **Encaje:** la fase 5, en la que los 17 problemas reservados harían de conjunto de test,
    seleccionando entre los 37 de desarrollo. También justificaría la elección del conjunto de
    entrenamiento en el artículo de Evolver, que hoy se hace a mano.
- **Recomendación:**
  - Mirar primero (b) en la matriz de la fase 3.
  - Pre-registrar (c) como RQ5 tras G3, con su propia campaña.
- **Decisión (2026-10-26):** "si, rq5" (D8). Añadida como RQ5 en `plan.md` §4 y como fase 3s en
  §6. Se pre-registra después de G3.

### 26. "Lanza la matriz" (2026-10-26)
- **Respuesta:** se lanza tras comprobar que NicoVM está libre (carga 0, 29 GB disponibles).
  - **Ajuste previo:** irace terminó el 2026-10-22 a las 05:41 UTC (43 h), y se recogieron las 37
    elites en `research/phase3/data/tuned_configs.json`.
  - **Cada irace:** entre 19 994 y 20 000 experimentos, 11–24 iteraciones y 2 582–3 932
    configuraciones.
  - **Matriz:** 40 configuraciones (las 37 ajustadas más NSGA-II, MOEA/D y SMS-EMOA por defecto),
    sobre 37 problemas y con 10 semillas (5001–5010), con 31 procesos. Arrancó el 2026-10-26 a las
    17:56 UTC.

### 27. ¿Se usan todos los núcleos disponibles menos uno? (2026-10-26)
- **Respuesta:** sí.
  - NicoVM tiene 32 núcleos y la matriz usa 31 procesos (`PHASE2_WORKERS=31`).
  - Cada proceso está limitado a un hilo (`OMP_NUM_THREADS=1` y equivalentes de BLAS), para no
    sobresuscribir.
  - Queda un núcleo libre para el sistema, ssh y el proceso coordinador.
  - Medido a las 18:01 UTC: 31 procesos por encima del 50 % de CPU y carga media de 30.8.

### 28. ¿Se guardan las metacaracterísticas en una tabla? (2026-10-26)
- **Respuesta:** sí, en CSV.
  - **Formato:** una fila por problema y muestra LHS (37 × 5 semillas, 1001–1005, son 185 filas).
    Cada fila lleva la procedencia (problema, semilla, n, D, M, geometría, k, |ND|, tiempos,
    versión de MOLA, escalado de objetivos) y las causas de cada feature indefinida (JSON), además
    de las 49 features.
  - **VAMOS:**
    - `research/phase3/data/features_sample_scaled.csv`: MOLA 0.4.0, `sample`, la representación
      principal.
    - `research/phase2/data/pilot_features.csv`: objetivos sin escalar, MOLA 0.3.0, sin columna de
      versión.
  - **Evolver/jMetal:** `research/phase3e/data/features_sample_scaled.csv` y
    `features_raw_objectives.csv`.
  - **No están en tabla:**
    - los metadatos de `metadata_1nn` (log D, media y desviación del log del rango de las cotas),
      que `analyze_transfer.py` calcula a partir de las cotas;
    - el vector medio de cada problema;
    - el escalado robusto, que depende de cada partición de entrenamiento y por eso no debe
      precalcularse.

### 29. ¿Cómo se compara si una tabla (un problema) es distinta de otra? ¿Con qué distancia? (2026-10-26)
- **Respuesta:** no se comparan tablas enteras. Se comparan vectores de 49 features:
  - una muestra del problema destino;
  - la media de las 5 muestras de cada problema de entrenamiento.
- **Distancia principal (`landscape_1nn`):** euclídea sobre las features escaladas de forma
  robusta, d(Q, P) = √Σ_f ((x_Qf − x̄_Pf) / IQR_f)².
  - El IQR se calcula solo con las muestras de entrenamiento.
  - Se descartan las features indefinidas en alguna muestra y las constantes. Quedan 46.
  - Es una euclídea ponderada por 1/IQR², porque la mediana se cancela.
- **Otras distancias** (son los comparadores de la RQ1):
  - **Metadatos:** euclídea estandarizada sobre log D y sobre la media y la desviación del log del
    rango de las cotas.
  - **Tesis (ec. 4.1):** Σ |1 − min/max| sobre 19 features.
  - **`loss_predictor`:** aprende una distancia ponderada (ridge sobre |z_A − z_B|) que predice la
    pérdida de transferencia.
  - **`knn_selector`:** usa la distancia principal para tomar los 3 vecinos.
- **Cómo se valida:** la distancia no se valida por sí misma, sino por la pérdida de transferencia
  del donante que elige (G3). El reconocimiento de la fase 2 fue del 63 %.
- **Debilidad conocida:** las features están muy correlacionadas (dimensión efectiva ~5,
  `FEATURE_ANALYSIS.md`), así que los grupos de features redundantes pesan más.
- **Ejemplos (LOGO):**
  - zdt1 → zdt3 (3.6), zdt2 y dtlz2 (7.0);
  - dtlz2 → dtlz3 (5.7);
  - re21 → rwa1 (11.2);
  - el más lejano siempre es re24 (≈ 40–45).

### 30. ¿Qué portafolio usamos en el que esté SMS-EMOA? (2026-10-26)
- **Respuesta:** ninguno. SMS-EMOA no está en el portafolio.
  - **El portafolio (D2)** son las 37 configuraciones de NSGA-II ajustadas con irace (c*_P), una por
    problema de entrenamiento. Todos los métodos recomiendan una de ellas.
  - **SMS-EMOA y MOEA/D por defecto** (población 100) solo están en la matriz, como comparadores
    sin ajustar (pre-registro de la fase 3, §2). Entran en dos sitios:
    - el denominador de HVn, que es el HV de la unión de todos los frentes de la matriz en cada
      problema;
    - las comparaciones descriptivas: ¿mejora NSGA-II ajustado a usar otro algoritmo por defecto?
  - El método `default` solo usa NSGA-II por defecto.
- **Motivos para dejarlo fuera:**
  - el espacio de ajuste es solo el de NSGA-II (D2, D3);
  - SMS-EMOA de VAMOS no es invariante a las unidades de los objetivos (desplaza su referencia 1.0
    en unidades absolutas);
  - es mucho más caro.
- **Ampliar el portafolio** con MOEA/D y SMS-EMOA ajustados sigue siendo la pregunta pendiente 1.
- **En la réplica de Evolver (3e)** solo hay NSGA-II por defecto como comparador.

## Preguntas pendientes

### Para el usuario

1. **¿Ampliar el portafolio con MOEA/D y SMS-EMOA ajustados?** Se planteó tras la fase 2 y no
   está respondida.
   - **A favor:** añadirían margen en los problemas multimodales.
   - **En contra:** multiplican por 4 a 8 el coste de cada ejecución.
   - **Además:** SMS-EMOA de VAMOS no es invariante a las unidades de los objetivos.
2. **¿Revisar con Nebro las decisiones técnicas que cambian definiciones?**
   - **T1:** punto soportado con pesos estrictamente positivos.
   - **T5 y D6:** operadores excluidos.
   - **D4:** escalado de objetivos.
3. **Fallos encontrados en VAMOS, que es tu librería: ¿cómo y cuándo comunicarlos?**
   - `racing/refill.py:25` lanza un `KeyError` con parámetros condicionales.
   - PCX, UNDX, la mutación gaussiana, la de Cauchy, la reparación `round` y el inicializador
     Halton no son invariantes.
   - El frente de referencia de UF6 está incompleto.
   - UF3 tiene cotas [−1, 1] en lugar de [0, 1].
   - Las cotas de RE24 difieren de las de jMetal.
   - SMS-EMOA usa un desplazamiento absoluto del punto de referencia.
4. **Fallos en jMetal y Evolver: ¿se comunican, y entran en la respuesta a los revisores del
   artículo de Evolver en ECJ?**
   - RWA1 usa `10e-3` en lugar de `1e-3`.
   - La mutación no uniforme nunca actualiza su iteración, así que su parámetro no tiene efecto.
   - El cruce de Laplace y la mutación uniforme usan escalas absolutas. Laplace aparece en 3 de las
     4 configuraciones del artículo.
   - La terminación se comprueba por generación, así que se pasa del presupuesto.
   - El épsilon absoluto de SBX es 1e-14.
5. **¿Qué valor por defecto debe tener MOLA para el escalado de objetivos?** Hoy es `raw`, por
   continuidad con el artículo original. El recomendador usa `sample`.
6. **¿Cuándo se integran las ramas `research/*` en `main`?** ¿Con un pull request a ajnebro/MOLA?
7. **¿Cuándo se regeneran los CSV históricos, `FEATURE_ANALYSIS.md` y los notebooks** con MOLA
   0.4.0? Por plan, cuando las definiciones queden congeladas.
8. **¿Dónde se publica?** GECCO 2027 (plazo hacia finales de enero, por confirmar) o una revista
   (ECJ, TELO).

### Para Nebro y Aldana-Martín (de `question1.md` y de la fase 0)

9. ¿Aceptan que MOLA use por defecto `bound` y conserve `raw` para reproducir lo publicado?
10. ¿Qué versión de moorphology generó los números de la tesis y del grafo de moody? (E13)
11. ¿El artículo se plantea como transferencia de configuraciones ajustadas por problema? Es la
    línea de la tesis, y es lo que se está haciendo (D2).
12. ¿Coautoría? Comunicarles lo demostrado sobre moorphology (E12 y E13).

### Que llegarán con los resultados de la fase 3

13. **Si G3 se supera en VAMOS:** ¿se mantiene `landscape_1nn` como método del recomendador, o se
    adopta el que mejor rinda en los análisis secundarios (`knn_selector`, `loss_predictor`)? Esto
    último exigiría un nuevo pre-registro antes de la evaluación final.
14. **Si G3 no se supera:** ¿se publica como resultado negativo (`plan.md` §6) o se exploran
    representaciones distintas, por ejemplo MO-ELA, con un pre-registro nuevo?
15. **Si VAMOS y Evolver discrepan en G3:** ¿cuál se toma como principal en el artículo?
16. **¿Cuándo se abren los 17 problemas reservados** (fase 5) y con qué método congelado?
17. **RQ1 y RQ2 completas:** malla de tamaños de muestra, k ∈ {1, D, 10} y transformaciones de
    unidades. ¿Antes o después de la evaluación final?
18. **Validación con tres objetivos** (`plan.md` §5): ¿qué problemas y en qué fase?
19. **RQ4:** la política de recomendar o recurrir a la alternativa generalista, y la contabilidad del
    presupuesto total.
20. **RE24:** ¿cuál de las dos cotas (VAMOS o jMetal) coincide con el código de referencia de
    Tanabe e Ishibuchi?
