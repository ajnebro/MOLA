# Plan propuesto tras la revisión externa (Fable, 2026-11-01)

Versión propuesta del plan. **No sustituye a `plan.md`**, que no se ha modificado; es una propuesta
para que el autor decida. Cada cambio respecto al plan vigente lleva su número (**C1–C14**), la
sección de `plan.md` a la que afecta y su motivo. Lo que no aparece como cambio se mantiene tal
cual.

**Lo que este documento no toca, por ser restricción o decisión del autor:**
- las puertas pre-registradas G3–G6, que no se reinterpretan ni se repiten cambiando el método;
- los 17 problemas reservados (`research/phase2/reserved_groups.json`), que no se usan hasta la
  evaluación final con el método congelado;
- el ajuste siempre con irace y ≥ 20 000 experimentos (D5);
- NicoVM compartida: se lanza solo cuando está libre y nunca se detienen procesos ajenos;
- VAMOS y Evolver de solo lectura;
- las decisiones D1–D11 y T1–T8. Donde creo que una decisión merece revisarse lo digo y lo razono,
  pero no la doy por cambiada.

**Fuentes comprobadas para esta propuesta:** `research/review/briefing_2026-10-31.md`; `plan.md`
§1–7 y §10–11; `research/decisions/decisions.md` y `questions.md`;
`research/references/state_of_the_art.md`; `research/phase3/report.md` §1–13 y sus datos
(`g3_result.json`, `g3_secondary.json`, `g3_groups.csv`, `strata.csv`, `consensus_strata.json`,
`diagnosis.json`, `distance_table.json`, `algorithm_selection_control.json`,
`rq7_tuned_configs.json`, `transfer_long.csv`); los pre-registros de las fases 3, 3c y 3g;
`research/phase2/catalogue.csv` y `report.md`. Además reproduje el análisis de distancia frente
a pérdida sobre los 1 332 pares ordenados con la matriz local (`C:\tmp\mola-phase3\matrix\fronts`)
y el entorno de la fase 2; el script de trabajo está en `C:\tmp\fable_review\pairs_analysis.py`
(fuera del repositorio).

---

## 1. Resumen de los cambios

| # | Cambio | Afecta a | Motivo (resumen) | Coste NicoVM | Para GECCO |
|---|---|---|---|---|---|
| C1 | El encuadre se decide ya: **condicional, con el resultado negativo en el centro** | `plan.md` §10.1, pregunta pendiente 3 | Los tres desenlaces posibles de G4/G5 son condicionales; esperar solo retrasa la escritura | 0 | Imprescindible |
| C2 | Reparto fijo GECCO 2027 / revista | §6, pregunta 12 | El plazo (finales de enero) y el límite de páginas no admiten todo | 0 | Imprescindible |
| C3 | **RQ4 redefinida como política de dos niveles** (transferir o generalista irace) con un único índice s₁ corregido y una **puerta nueva G7**, pre-registrada sobre las matrices de las fases 3+3g y 3c | §4 RQ4, §6 fase 4, pregunta 20 | El nivel intermedio no se puede medir dentro de D5 (ver C4); s₁ tal como se propuso se calibra con un estadístico distinto del que se aplica | 0 | Imprescindible |
| C4 | El **nivel 2 (irace en caliente)** sale del primer artículo y se rediseña compatible con D5: 20 000 experimentos por ejecución y análisis *anytime* desde `irace.Rdata` | pregunta 20 | El experimento de 5 000 experimentos viola D5; a 20 000 ambos arranques convergen y no discriminan; el brazo frío ya existe (las c*_Q) | 1–2 días (opcional) | Opcional |
| C5 | **s₂ se descarta como criterio de decisión**; queda como descriptivo | pregunta 20 | Es un percentil relativo al entrenamiento: no es comparable entre la fase 3, la 3c y los reservados; sin nivel 2 no decide nada | 0 | — |
| C6 | El análisis de los **1 332 pares se incorpora al repositorio** (script y datos) antes de usarlo en ningún pre-registro | §10.4 L13, pregunta 18 | No está en el repo: solo en el briefing y en la pregunta 20. Lo reproduje y los números coinciden, pero debe ser trazable | 0 (horas de trabajo) | Imprescindible |
| C7 | **Orden de cálculo fijado**: reanudar 3c → 3g → evaluación final → (opcional) nivel 2 → (opcional) RQ5. **3e se aplaza a revista** | §6, pregunta 1 | Camino crítico y NicoVM compartida | ≈ 7.5 días en total los imprescindibles | — |
| C8 | **Fase 5 detallada**: qué se congela, qué se prepara (cotas y frentes de referencia de los reservados) y qué no se hace (no se ajusta c*_Q en los reservados) | §6 fase 5, pregunta 14 | Es irreversible: se abre una sola vez | 1–2 h | Imprescindible |
| C9 | Análisis descriptivo que **separe "familia no vista" de "estrato difícil"** en LOFO | §4 RQ1, informe fase 3 | 6 de los 7 problemas muy difíciles son LZ09/UF, que es el 40 % del conjunto: en LOFO ambos efectos son colineales | 0 | Imprescindible |
| C10 | **Suelo de ruido del ajuste**: documentar los 5 problemas en los que c*_Q queda > 0.01 por debajo del mejor donante; opcional, dos reajustes con otra semilla | §4 RQ1 medidas | La "pérdida de transferencia" mezcla desajuste donante–destino con la varianza de una sola ejecución de irace | 0 (1–2 días la parte opcional) | Imprescindible la parte gratuita |
| C11 | RQ7: repetir el Mantel **sin el estrato fácil** y con permutaciones dentro de familia | §11 RQ7 | Los ZCAT son a la vez cercanos en features y fáciles para todos: pueden crear por sí solos la correlación | 0 | Opcional |
| C12 | **Contactar ya** con Nebro y Aldana-Martín | §7 "Comunicación" | Coautoría, propiedad del repositorio MOLA y sensibilidad de E12/E13; cuesta semanas de ida y vuelta | 0 | Imprescindible |
| C13 | Hacer explícito en el artículo que **G3 era una prueba de baja potencia** y por qué (metadatos casi degenerados; media dominada por 2 grupos) | §6 fase 3 | Evita que un revisor lea "p = 0.078" como un casi-éxito o como un fracaso del paisaje | 0 | Imprescindible |
| C14 | Reproducibilidad menor: nota de parada de la 3c en el repo, `hs_err_pid*.log` fuera del árbol, estado de los `irace.Rdata` de la fase 3 | — | Hoy la nota de parada solo está en `~/mola-phase3c/STOPPED-20261028.txt` | 0 | Opcional |

---

## 2. Objetivo y mensaje del artículo (C1, C2)

**Objetivo científico.** Sin cambios: *cuándo* la similitud de paisaje permite transferir
configuraciones de forma fiable.

**Mensaje, decidido ahora y no a la vista de la 3c** (C1). Tres frases que valen para cualquier
desenlace de G4/G5:
1. Con el problema destino fuera del entrenamiento, ningún método basado en similitud supera a un
   generalista (ni al SBS ni, previsiblemente, al generalista irace), en 37 problemas biobjetivo y
   en el benchmark que se añada (fase 3). Esto coincide con Cenikj et al. 2025 en un objetivo.
2. La señal existe (correlación distancia–calidad −0.40; pérdida mediana del vecino 0.002; Mantel
   con la pérdida mutua 0.38) pero **no es fiable**: un 18 % de las elecciones del vecino pierde
   más de 0.10, y el éxito publicado de las meta-características depende de tener el problema o sus
   hermanos en el entrenamiento (control positivo).
3. La similitud sirve [solo para parientes cercanos | ni siquiera para parientes cercanos | también
   entre funciones, pero no entre grupos] — la alternativa la decide la 3c — y, como regla de
   abstención calibrada, evita las transferencias catastróficas sin perder frente al generalista
   (RQ4, G7), o no lo consigue, en cuyo caso también se publica.

**Motivo de decidirlo ya:** el borrador de Overleaf puede escribirse completo con huecos
numéricos; la frase 3 tiene tres variantes cerradas. Esperar a la 3c para "saber cómo contarlo" no
cambia la estructura y resta tres semanas de escritura.

**Reparto GECCO / revista** (C2):

| Va a GECCO 2027 | Va a la versión de revista (ECJ o TELO) |
|---|---|
| RQ1: G3, el generalista dominante, la cola del vecino único, `knn_selector` y el consenso (exploratorios, etiquetados) | 3e: réplica en Evolver/jMetal (D6) |
| Control positivo con el protocolo de MO-ELA frente a particiones por problema (fase 3) y sus cuatro protocolos en la 3c | RQ5 (3s): selección del conjunto de entrenamiento |
| 3c: gradiente de similitud S1 → S3 → S2, G4 y G5 | Nivel 2: irace en caliente, análisis *anytime* (C4) |
| 3g: G6, generalista irace frente a `knn_selector` | RQ2 y RQ3 completas (rejillas de tamaño de muestra y k) |
| RQ4: política de abstención, G7 (C3) | RQ6 (sintético → real) y la validación con tres objetivos |
| Evaluación final en los 17 reservados con el método congelado | Reajuste de los reservados como techo (`self`) |
| RQ7 en su versión corta (Mantel y "los parámetros no se predicen") | RQ7 completa con las 61 élites de la 3c |

La auditoría de la fase 0 (E1–E25) va al material suplementario y a la documentación de MOLA, no
al cuerpo del artículo.

---

## 3. Preguntas de investigación: estado y destino

La numeración de D7 no cambia. Lo nuevo está en RQ4.

| RQ | Pregunta | Estado | Destino |
|---|---|---|---|
| RQ1 | Transferencia frente a las líneas base | G3 no superada; G6 pendiente (3g); G4/G5 pendientes (3c) | GECCO |
| RQ2 | Invariancia y geometría | Asegurada por diseño (D1, D4, T5); análisis de sensibilidad | GECCO, un párrafo; rejilla a revista |
| RQ3 | Incertidumbre del muestreo | Parcial (donante estable en el 49 %); alimenta s₁ | GECCO, dentro de RQ4 |
| **RQ4** | **Cuándo recomendar: política de dos niveles con umbral s₁ calibrado sin fuga** (C3) | Por pre-registrar, coste 0 | GECCO |
| RQ4b | Nivel intermedio: irace arrancado desde el vecino (C4) | Diseño nuevo compatible con D5 | Revista (GECCO solo si sobra tiempo) |
| RQ5 | Selección del conjunto de entrenamiento | Primera evidencia (`knn_selector`); 3s sin pre-registrar | Revista |
| RQ6 | De lo sintético a lo real | Sin empezar; los 3 reales de desarrollo están saturados | Revista |
| RQ7 | Qué eligen las configuraciones ajustadas | Hecho sobre las 37 élites (exploratorio) | GECCO corto; completo a revista |

**RQ4 redefinida** (C3). Pregunta: *¿Reduce una regla de abstención, calibrada solo con el
entrenamiento, las transferencias perjudiciales sin perder frente al generalista irace?*
- **Política π_α:** caracterizar Q; si s₁(Q) ≥ α, devolver `knn_selector(Q)`; si no, el
  generalista de la línea base 1 (D11).
- **Un solo índice, s₁, con una corrección** respecto a la propuesta de la pregunta 20. La
  propuesta calibra s₁ con la distancia **entre dos muestras** de un mismo problema, pero el
  recomendador mide la distancia de **una muestra del destino a la media de las 5 muestras** del
  problema de entrenamiento. Son estadísticos distintos: con los datos de la fase 3, el percentil
  95 de la distancia entre pares de muestras es 1.60 unidades y el de la distancia de una muestra a
  la media de las otras cuatro (*leave-one-sample-out*, LOSO) es 1.25. Calibrar con el primero y
  aplicar con el segundo infla el nivel 1 en un 28 %. **Definición corregida:** s₁(Q) es la fracción
  de las distancias LOSO del entrenamiento que superan d(Q), donde d(Q) es la distancia de la
  muestra de Q a la media del problema de entrenamiento más cercano, en el mismo escalado robusto.
- **α = 0.05 fijado a priori**, como propuso el autor. No hay ningún parámetro aprendido del
  rendimiento: lo único que sale del entrenamiento es la escala y la distribución LOSO, así que no
  hay fuga que vigilar. La variante calibrada por pérdida (el mayor umbral con el que al menos el
  1 − β de los pares de entrenamiento pierde ≤ ε frente al generalista) se informa como análisis de
  sensibilidad, calibrada dentro de cada pliegue sobre la submatriz entrenamiento × entrenamiento.
- **Por qué no s₂** (C5): un percentil de las distancias entre problemas del entrenamiento depende
  de la composición del entrenamiento; con 37 problemas, con 165 de bbob o con los reservados da
  escalas distintas, así que un p* calibrado en una fase no vale en la siguiente. Y sin el nivel 2 en
  el primer artículo no hay decisión que tomar con él. Se conserva como columna descriptiva.
- **Lo que ya se sabe y hay que decir en el pre-registro:** en la fase 3, por debajo de 1.5
  unidades el 70 % de los pares pierde ≤ 0.01 frente al oráculo y el 6 % pierde más de 0.10; pero el
  97 % de esos pares son de la misma familia y la mitad tiene un destino fácil; sin los fáciles,
  43 % y 11 %. Y el par más cercano que no es ZCAT, **UF5 ↔ UF7 a 0.35 unidades**, pierde 0.30 y
  0.18 según la dirección: la similitud máxima no garantiza la transferencia. Por eso G7 exige las
  dos cosas, no perder y reducir la cola, y no solo "no perder".

---

## 4. Fases, puertas, coste y orden (C7, C8)

| Orden | Fase | Trabajo | Puerta o criterio | NicoVM | Estado y fecha objetivo |
|---|---|---|---|---|---|
| 1 | 3c (reanudar) | 53 ajustes restantes, matriz 64 × 165 × 10, IBEA aparte, configuraciones aleatorias (enmienda 1), control positivo (enmienda 2) | **G4, G5** (sin cambios) | ≈ 6 días + ≈ 6 h | Reanudar en cuanto NicoVM quede libre (≈ 2–3 nov); análisis ≈ 12 nov |
| 2 | RQ4, pre-registro (C3) | Escribir y subir el pre-registro de G7 y la enmienda 3 de la 3c **antes** de que exista la matriz de la 3c y antes de ver los generalistas de la 3g | — | 0 | Semana del 3 nov |
| 3 | 3g | 6 generalistas irace; evaluación 6 × 37 × 10 | **G6** (sin cambios) | 10–15 h + minutos | Tras la matriz de la 3c; ≈ 13–14 nov |
| 4 | RQ4, análisis | G7 sobre fase 3 + 3g (LOGO; LOFO y aleatoria descriptivas) y sobre la 3c (S1, S3, S2) | **G7** (nueva) | 0 | ≈ 15–17 nov |
| 5 | C9, C10, C11, C13 | Análisis descriptivos sobre las matrices existentes | — | 0 | En paralelo, semanas del 3 y 10 nov |
| 6 | Fase 5: evaluación final | Congelar el método; preparar y verificar cotas y frentes de referencia de los 17 reservados; caracterizarlos; matriz 40 × 17 × 10; análisis | Resultado confirmatorio pre-registrado (no es una puerta de desarrollo) | 1–2 h | Método congelado ≈ 20 nov; apertura ≈ 24–28 nov |
| 7 | Artículo | Borrador completo con huecos desde ya; cierre con los números de 1–6 | — | 0 | Borrador completo 5 dic; versión para coautores 19 dic; envío en el plazo de GECCO |
| 8 (opc.) | RQ4b, nivel 2 (C4) | 24 ajustes irace en caliente, 20 000 experimentos cada uno, análisis *anytime* | — | 1–2 días | Solo si 1–6 están cerradas antes del 10 dic; si no, revista |
| 9 (opc.) | RQ5 (3s) | 4 brazos × 5 pliegues LOFO = 20 ajustes | — | 1.5–2 días | Revista |
| 10 (opc.) | 3e Evolver | Réplica completa | G3 en Evolver | ≈ 2 días + preparación | Revista (pregunta pendiente 1) |
| 11 (opc.) | C10, parte opcional | Reajustar DTLZ4 y UF3 con otra semilla de irace | — | ≈ 1 día | Revista |

**Total imprescindible en NicoVM:** unos 7.5 días de reloj, casi todo la 3c. Con la máquina libre
desde el 3 de noviembre y sin más interrupciones, el cálculo imprescindible termina hacia el 15 de
noviembre y la evaluación final antes de diciembre. La holgura hasta finales de enero es de unas
siete semanas, que absorben una interrupción de NicoVM como la del 28 de octubre.

**Qué cambia respecto a `plan.md` §6:** la fase 4 ("confianza y presupuesto") se concreta en G7 y
se adelanta a antes de la evaluación final, porque la política tiene que estar congelada para
poder evaluarla en los reservados; 3e y 3s pasan explícitamente a después del envío; la fase 5 gana
una lista de preparación (sección 7).

---

## 5. Pre-registro borrador de la RQ4 (puerta G7) — coste 0

Para subir a `research/phase4/preregistration.md` **antes** de ejecutar la matriz de la 3c y antes
de ejecutar `analyze_3g.py` sobre datos reales. Nada de lo que sigue necesita ejecuciones nuevas.

**Datos.** La matriz de la fase 3 (37 c*_P, NSGA-II/MOEA/D/IBEA por defecto), los 6 generalistas
de la 3g, las 185 muestras de `features_sample_scaled.csv`; y, para la réplica, la matriz y las
features de la 3c.

**Definiciones.**
- Escalado robusto, distancia euclídea y `knn_selector` como en `analyze_transfer.py`.
- d(Q, muestra): distancia de la muestra de Q a la media más cercana entre los problemas de
  entrenamiento T.
- Distribución de ruido LOSO de T: para cada problema P ∈ T y cada una de sus 5 muestras, la
  distancia de esa muestra a la media de las otras 4, en el escalado del pliegue. Son 5·|T| valores.
- s₁(Q, muestra) = fracción de esa distribución que supera d(Q, muestra).
- π_α: `knn_selector` si s₁ ≥ α, con α = 0.05; si no, el generalista de la línea base 1 (D11): en
  la fase 3, `gen_lofo` de la familia del destino; en la 3c, `gen_all` en S1 y S3 y `gen_g` en S2.

**Puerta G7 (principal), en LOGO de la fase 3, sobre los 32 grupos:**
1. **No inferioridad frente al generalista** con margen 0.005: prueba de Wilcoxon de rangos con
   signo unilateral de (π − generalista + 0.005) > 0, p < 0.05.
2. **Reducción de la cola:** la fracción de pares destino–muestra con pérdida > 0.10 frente al
   oráculo es, con π, **como mucho la mitad** de la de `knn_selector`.

G7 se supera si se cumplen las dos. Si no, se informa como resultado negativo. No se cambian α, la
distancia ni la regla para repetir la prueba.

**Por qué LOGO y no LOFO para G7:** con la familia fuera, s₁ ≥ 0.05 casi nunca se cumple (solo 4
de los 1 332 pares ordenados por debajo de 1.5 unidades son de familias distintas), así que en LOFO
π ≈ generalista y la rama de transferencia no se pone a prueba. LOFO y la partición aleatoria se
informan como secundarias. **Asimetría que hay que declarar:** en LOGO el generalista `gen_lofo`
no ha visto la familia del destino, mientras que los donantes sí; favorece a π. Como secundario se
informa π con el SBS de T como alternativa, que no tiene esa asimetría. Si el autor prefiere
eliminarla del todo, hacen falta 32 generalistas LOGO (≈ 1.5 días de NicoVM); no lo recomiendo para
GECCO.

**Réplica en la 3c (enmienda 3 de su pre-registro, antes de su matriz):** las mismas definiciones
y las mismas dos condiciones, por partición: S1 (cobertura alta esperada), S3 y S2 (cobertura baja
esperada). Es la respuesta cuantitativa al "cuándo": la cobertura de π y su ganancia en cada
peldaño del gradiente de similitud.

**Secundarios, descriptivos:**
- cobertura de π (fracción de pares destino–muestra en los que transfiere) por partición y por
  estrato;
- en la rama de transferencia, la diferencia frente al generalista y frente al oráculo;
- curvas cobertura–riesgo para α ∈ {0.01, 0.05, 0.10, 0.25};
- la variante calibrada por pérdida (ε = 0.01 y 0.02; β = 0.10), con el umbral calibrado en cada
  pliegue sobre la submatriz T × T, y la dispersión de ese umbral entre pliegues;
- el caso UF5 ↔ UF7 y, en general, los pares con s₁ alto y pérdida > 0.10;
- s₂ como columna descriptiva (C5);
- la tabla de 1 332 pares (C6) por tramos de distancia, con y sin destinos fáciles, con y sin la
  misma familia.

**Expectativa declarada:** probable que la condición 2 se cumpla y la 1 también, pero con una
cobertura baja (en la fase 3, 22 de 37 destinos tienen algún donante por debajo de 1.5 unidades,
14 de los 24 no saturados) y una ganancia media nula frente al generalista. Eso sería el resultado:
"la abstención calibrada hace la transferencia segura, no mejor".

---

## 6. Nivel 2, irace en caliente: diseño compatible con D5 (C4)

**Problema con la propuesta de la pregunta 20.** Propone un experimento "en caliente frente a en
frío con 5 000 experimentos". D5 fija ≥ 20 000 por tarea de ajuste y es una restricción que no se
cambia. Además, a 20 000 experimentos irace converge con cualquier arranque: en la fase 3, c*_Q
queda a menos de 0.01 del mejor donante en 32 de 37 problemas, así que la calidad final no
distinguirá los dos brazos y p* quedaría indefinido.

**Diseño alternativo, dentro de D5.**
- **Brazo frío:** ya existe. Cada c*_Q de la fase 3 salió de irace con 20 000 experimentos y
  NSGA-II por defecto como candidata inicial. Hace falta que sus `irace.Rdata` sigan en NicoVM
  (`~/mola-phase3/irace/<problema>/`); hay que comprobarlo.
- **Brazo caliente:** el mismo escenario, 20 000 experimentos, con `configurationsFile` = {la
  configuración que elegiría `knn_selector` para Q desde los otros 36, NSGA-II por defecto}, otra
  semilla. Solo en los 24 problemas no saturados (estratos intermedio y muy difícil de
  `strata.csv`); en los 13 fáciles no hay nada que medir.
- **Lo que se mide:** no la calidad final, sino la curva *anytime*. irace guarda en `irace.Rdata` las
  élites de cada iteración y el registro de experimentos, así que se reconstruye "mejor élite tras
  n experimentos" para n ∈ {1 000, 2 000, 5 000, 10 000, 20 000}; esas élites se evalúan con las
  semillas 5001–5010 (minutos). Medidas: experimentos necesarios para alcanzar la calidad final del
  brazo frío menos 0.005, y la diferencia de calidad a cada n.
- **Relación con la distancia:** la ventaja del arranque en caliente frente a d(Q) en unidades de
  ruido. Si existe un tramo donde el caliente ahorra presupuesto y más allá no, ese tramo es el
  nivel 2; se describe, no se convierte en umbral para el primer artículo.
- **Coste:** 24 ajustes ≈ 1–2 días de NicoVM (los arranques desde configuraciones estacionarias son
  lentos), más minutos de evaluación.
- **Cuándo:** después de las fases 1–6 de la sección 4 y solo si quedan antes del 10 de diciembre;
  si no, revista. Es lo que convierte la política en "de tres niveles" y merece su propio espacio.

**Nota sobre D5:** si el autor considera que el experimento de eficiencia de presupuesto no es "una
tarea de ajuste" en el sentido de D5 y quiere ejecuciones de 5 000, es una reinterpretación que
solo él puede hacer; este plan no la supone.

---

## 7. Fase 5: evaluación final en los 17 reservados (C8)

**Se congela antes de abrirlos, por escrito en el pre-registro de la fase 5:**
- el método principal `knn_selector` y el secundario (consenso k = 3, δ = 0.05), según D11;
- la política π_0.05 de la RQ4, con su procedimiento, no un número;
- las líneas base: `gen_all` de la 3g (línea base 1) y NSGA-II por defecto (línea base 2); el SBS
  sobre los 37 y el donante al azar como referencias; el oráculo como techo;
- el portafolio: las 37 c*_P de la fase 3 más `gen_all`; la unión que normaliza HVn incluye, como en
  la fase 3, NSGA-II, MOEA/D e IBEA por defecto;
- la caracterización: MOLA 0.4.0, `bound`, k = D, `sample`, semillas LHS 1001–1005;
- la comparación confirmatoria: `knn_selector` frente a `gen_all`, Wilcoxon unilateral sobre los
  15 grupos reservados (ZCAT18 y ZCAT20 comparten grupo con ZCAT14 y ZCAT16), y lo mismo para
  π_0.05, con Holm sobre las dos; todo lo demás, descriptivo.

**Preparación previa, sin mirar ningún rendimiento de los métodos:**
- las cotas de ajuste (ideal y nadir del frente verdadero, T7) para WFG1–9, ZDT6, DTLZ7 y los seis
  ZCAT, con el mismo procedimiento de la fase 3 y la misma comprobación que destapó el frente
  incompleto de UF6 y la duda de RE24;
- las cotas de WFG en VAMOS ([0, 2i], heterogéneas): es el primer conjunto de la campaña donde la
  geometría `bound` (D1) y la `raw` difieren de verdad; se registra la dimensión (k y l de WFG) y se
  comprueba que coincide con la de la caracterización;
- comprobar que los duplicados ZCAT reservados (E23) siguen siendo duplicados exactos en VAMOS;
- un ensayo general del pipeline completo con un problema de desarrollo, para no depurar con los
  reservados.

**Qué no se hace para GECCO:** no se ajusta c*_Q en los reservados (17 ajustes ≈ 20 h). El techo es el
oráculo entre donantes; el techo `self` queda para la revista.

**Lectura por subconjuntos, fijada de antemano:** WFG (9) es una familia no vista; ZDT6, DTLZ7 y los
ZCAT (8) son formulaciones no vistas de familias vistas. Es la misma escalera LOFO/LOGO del
desarrollo, con problemas nunca tocados.

**Coste:** caracterización en minutos; matriz 40 × 17 × 10 = 6 800 ejecuciones, 1–2 h en NicoVM (WFG
con D ≈ 22–30 y configuraciones estacionarias es lo más lento).

---

## 8. Calendario hasta GECCO 2027

El plazo exacto de GECCO 2027 hay que confirmarlo (históricamente, resumen a finales de enero y
texto completo a primeros de febrero). Se planifica para **el 29 de enero de 2027**.

| Semana | Cálculo (NicoVM) | Análisis y escritura |
|---|---|---|
| 2–8 nov | Reanudar la 3c cuando quede libre | C6 (pares al repo); pre-registro de la RQ4 y enmienda 3 de la 3c (sección 5); C9, C10, C13 sobre la fase 3; esqueleto completo del artículo con huecos; C12 (contacto con coautores) |
| 9–15 nov | 3c termina; matriz, IBEA, aleatorias; lanzar 3g | Análisis de la 3c: G4, G5, control positivo con 4 protocolos; RQ7 sobre las 61 élites (versión corta) |
| 16–22 nov | 3g termina; evaluación | G6; G7 en fase 3 + 3g y en la 3c; informe de la fase 4; congelar el método; pre-registro de la fase 5 |
| 23–29 nov | Preparación y apertura de los reservados; matriz final | Informe de la fase 5; primera versión completa de resultados |
| 30 nov – 13 dic | (opcional) nivel 2 *anytime* si todo lo anterior está cerrado | Borrador completo a coautores; figuras: gradiente S1→S3→S2, cobertura–riesgo, distancia–pérdida |
| 14 dic – 10 ene | Libre | Revisión de coautores; material suplementario (auditoría, pre-registros, datos) |
| 11–29 ene | Libre | Versión final y envío |

Si NicoVM vuelve a quedar ocupada más de una semana en noviembre, lo primero que cae es el nivel 2
y después la réplica del control positivo en la 3c; G4, G5, G6, G7 y la evaluación final no se
recortan.

---

## 9. Qué no hacer

- **No repetir G3 con otra distancia o representación** como si fuera una corrección. Ya hay seis
  distancias exploradas; con Bonferroni ninguna supera 0.05 (`distance_table.json`), y
  pre-registrar ahora la mejor de ellas sería una prueba elegida a posteriori.
- **No afinar k ni δ del consenso sobre la matriz de la fase 3** y presentarlo como confirmatorio.
  En la 3c ya están fijados (k = 3, δ = 0.05) y así se quedan.
- **No abrir los 17 reservados** antes de que estén cerrados G6 y G7 y escrito el pre-registro de la
  fase 5.
- **No ampliar el portafolio** con MOEA/D o IBEA ajustados antes del envío: obligaría a rehacer la
  matriz y el generalista, y cambiaría la pregunta. Revista o segundo artículo (L6, Hydra).
- **No cambiar el límite de población de 200** ni el espacio de ajuste: rompe la comparabilidad con
  las fases 3, 3c y 3g. Se declara como limitación (RQ7).
- **No usar S1 de la 3c para afirmar que el éxito de la literatura "es solo reconocimiento".** S1 es
  un caso legítimo de hermanos; lo que el control positivo demuestra es que el protocolo por filas
  de MO-ELA mide reconocimiento, y que con el problema fuera ningún selector supera al SBS. Con
  Liefooghe 2021 (hermanos del mismo generador) la comparación justa es S1, pendiente.
- **No presentar el hueco cerrado sin el hueco absoluto** (L3): con SBS–VBS = 0.014, un −3.6 es
  −0.05 de HVn.
- **No analizar la 3c parcialmente** si la campaña se retrasa: la puerta se evalúa con las 55
  funciones o no se evalúa.

---

## 10. Riesgos

| Riesgo | Probabilidad | Efecto | Mitigación |
|---|---|---|---|
| La 3c tarda 9 días en lugar de 6 (configuraciones estacionarias) | Alta | Desplaza todo una semana | Reanudar el primer día libre; la holgura de enero lo absorbe |
| NicoVM vuelve a ocuparse por otro proyecto | Media | Interrupción de días | Orden de prioridad de la sección 8; nunca se detienen procesos ajenos |
| G5 empata por construcción (el consenso con δ = 0.05 rara vez se aparta del generalista; en la fase 3, el 16 %) | Alta | G5 "no superada" sin información | Informar siempre la tasa de desviación junto a G5; la cobertura de G7 cuenta lo mismo con más detalle |
| `gen_lofo`/`gen_all` salen más débiles que el SBS (irace reparte 20 000 experimentos entre 32–37 instancias heterogéneas) | Media | G6 podría superarse por debilidad del generalista | D11 ya exige informar del SBS al lado; si el generalista < SBS, decirlo y discutir ambos |
| Cotas o frentes de referencia erróneos en los reservados (como UF6 o RE24) | Media | Evaluación final viciada e irrepetible | Lista de preparación de la sección 7, hecha sin rendimiento de métodos |
| Desacuerdo tardío con los coautores sobre E12/E13 o sobre el encuadre | Media | Semanas perdidas en enero | C12: contactar en la semana del 3 de noviembre |
| Límite de páginas | Alta | Hay que cortar | Reparto de la sección 2; suplementario |

---

## 11. Reproducibilidad pendiente (C6, C14)

1. **Los 1 332 pares.** Añadir `research/phase3/scripts/pair_distance_loss.py` y sus salidas. Mi
   reproducción (`C:\tmp\fable_review\pairs_analysis.py`, con `analyze_transfer.hvn_matrix` y la
   matriz local) coincide con el briefing: 144 pares por debajo de 1.5 unidades, 70.1 % con pérdida
   ≤ 0.01, 5.6 % con pérdida > 0.10, 97.2 % de la misma familia, 51.4 % con destino fácil; sin los
   fáciles, 42.9 % y 11.4 %. Unidad de ruido: 1.798 en el espacio robusto.
2. **La nota de parada de la 3c** (`STOPPED-20261028.txt`) y el registro de reanudación, al informe
   de la fase cuando exista.
3. **Los `hs_err_pid*.log`** de la raíz del repositorio son volcados de la JVM y no deben entrar en
   git.
4. **Las `irace.Rdata` de la fase 3** en NicoVM: confirmar que se conservan (sección 6) y, si caben,
   archivarlas comprimidas.
5. **La comparación `knn_selector` frente al donante al azar** (+0.112, p = 4·10⁻⁹ en el briefing) no
   está en `g3_secondary.json` ni en `consensus_strata.json`; la diferencia de medias por destino
   (0.877 − 0.771) es coherente, pero el valor p debe salir de un script del repositorio.

---

## 12. Preguntas al autor, por importancia

1. ¿Acepta que el primer artículo lleve una política de **dos** niveles (transferir o generalista) y
   que el nivel intermedio pase a RQ4b, dado que el experimento de 5 000 experimentos de la
   pregunta 20 no cabe en D5 y que a 20 000 los dos arranques convergen?
2. ¿Dónde y con qué script se calculó el análisis de los 1 332 pares que cita el briefing? ¿Se
   añade al repositorio antes de la enmienda 3 de la 3c?
3. Para G7 en LOGO, ¿qué alternativa quiere cuando no se transfiere: el generalista LOFO de la
   familia (D11, que no ha visto la familia y por tanto favorece a la política), el mejor de
   {generalista, SBS} elegido en entrenamiento, o 32 generalistas LOGO (≈ 1.5 días de NicoVM)?
4. ¿Se conservan las `irace.Rdata` de los 37 ajustes de la fase 3 en NicoVM? Sin ellas, el brazo
   frío del nivel 2 hay que repetirlo (≈ 2 días más).
5. ¿Cuál es el plazo exacto y el formato de GECCO 2027, y quiénes son los coautores? El calendario
   de la sección 8 supone el 29 de enero.
6. ¿Se contacta ya con Nebro y Aldana-Martín, y con qué mensaje sobre E12/E13 y sobre MOLA 0.3.0+?
7. ¿Quién verifica las cotas y los frentes de referencia de WFG, ZDT6, DTLZ7 y los ZCAT reservados
   en VAMOS antes de abrirlos, y con qué fuente (Huband et al. para WFG)?
8. ¿Se aplaza formalmente la réplica 3e a la revista (pregunta pendiente 1)?
9. Pregunta pendiente 4 (duración de la 3c): ¿se mantiene tal como está pre-registrada? Mi
   recomendación es que sí; enmendarla ahora, ya con 8 ajustes hechos, sería peor que el retraso.
10. ¿Entra en el artículo el análisis que separa "familia no vista" de "estrato difícil" (C9) como
    descriptivo del informe de la fase 3?
