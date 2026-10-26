# Informe de la fase 3 — Transferencia de configuraciones (RQ1, puerta G3)

Fecha: 2026-10-26 · Rama `research/phase3` · MOLA 0.4.0 · VAMOS 1.0.0 (`0a8bbb0`, motor numpy), más
IBEA reparado (VAMOS `c4569f25`, PR #115) · Pre-registro: `preregistration.md`, con sus enmiendas 1
(escalado de objetivos) y 2 (IBEA en lugar de SMS-EMOA), todas anteriores a la matriz o a su
análisis.

La pregunta se llamaba RQ3 en el pre-registro; desde D7 es la RQ1.

## 1. Resultado

**G3 no se supera.** Es un resultado negativo pre-registrado: en LOGO, el vecino más cercano por
paisaje no supera de forma significativa al vecino más cercano por metadatos.

| Medida (LOGO, 32 grupos) | Valor |
|---|---|
| Media por grupo de HVn(`landscape_1nn`) − HVn(`metadata_1nn`) | +0.049 |
| Mediana | +0.00007 |
| Victorias / derrotas / empates | 17 / 12 / 3 |
| Wilcoxon de rangos con signo unilateral | p = 0.078 (umbral 0.05) |

**Lo que más pesa en la práctica:** ningún método de transferencia supera al generalista (SBS).

| LOGO (media por grupo) | HVn | Diferencia con el SBS (media por destino) | Regret frente al oráculo (media por destino) |
|---|---|---|---|
| Propia c*_Q (referencia) | 0.928 | +0.023 | −0.009 |
| Donante oráculo (referencia) | 0.918 | +0.014 | 0 |
| **SBS** | **0.903** | — | **0.014** |
| `knn_selector` | 0.885 | −0.018 | 0.032 |
| `landscape_1nn` (principal) | 0.856 | −0.051 | 0.065 |
| NSGA-II por defecto | 0.853 | −0.049 | 0.063 |
| `thesis_1nn` | 0.843 | −0.065 | 0.079 |
| `loss_predictor` | 0.814 | −0.084 | 0.099 |
| `landscape_1nn_raw_objectives` | 0.810 | −0.085 | 0.099 |
| `metadata_1nn` | 0.807 | −0.088 | 0.102 |
| Donante aleatorio | 0.773 | −0.124 | 0.138 |

Las columnas segunda y tercera son medias por destino, como `transfer_summary.csv`; la primera es
la media por grupo de G3.

## 2. Qué se hizo

| Etapa | Resultado | Commit o fichero |
|---|---|---|
| Ajuste | 37 ejecuciones de irace 4.5, cada una con 19 994–20 000 experimentos, 11–24 iteraciones y 2 582–3 932 configuraciones. 43 h en NicoVM (2026-10-20 10:27 → 2026-10-22 05:41 UTC) | `data/tuned_configs.json` (`f8fe9a3`) |
| Matriz | 37 c*_P + NSGA-II + MOEA/D por defecto: 1 443 pares × 10 semillas, unos 60 min con 31 procesos. IBEA por defecto (VAMOS `c4569f25`): 37 pares, 23 s | `data/matrix_fronts_SHA256SUMS`, `data/evaluation_runs*.csv` |
| Enmienda 2 | IBEA en lugar de SMS-EMOA, antes de cualquier análisis | `3fa6476` |
| G3 | `analyze_transfer.py`, sin cambios salvo la lista de algoritmos por defecto de la enmienda 2 | `data/g3_result.json`, `data/transfer_summary.csv`, `data/transfer_long.csv` |
| Análisis secundarios | `secondary_transfer.py`, escrito después de G3 | `data/g3_secondary.json`, `data/g3_groups.csv` |

## 3. Hallazgos

### 3.1 Un generalista dominante

- **La configuración ajustada para ZDT3 es el SBS en 31 de los 32 grupos** (en el otro, la de
  ZCAT11). Su HVn medio sobre los 37 problemas es 0.895. Le siguen NSGA-II por defecto (0.846) y
  las configuraciones ajustadas para ZCAT11, DTLZ1, UF7 y ZDT1 (0.844–0.845).
- **Cómo es:** NSGA-II casi estacionario.
  - población 200 y `offspring_ratio = 0`;
  - torneo de tamaño 9;
  - SBX (0.85, η = 15.3);
  - mutación polinómica enlazada con un factor de probabilidad 2.1 y η = 6.2;
  - inicialización LHS y reparación por recorte.
- **Comparadores sin ajustar:** IBEA por defecto (reparado) obtiene 0.822 y MOEA/D 0.690.

Con 20 000 experimentos por problema, irace especializa mucho: no hay ningún problema en el que
todas las c*_P alcancen HVn ≥ 0.99. Por eso, elegir cualquier donante que no sea el generalista
cuesta de media unos 0.05.

### 3.2 Paisaje frente a metadatos: pocas diferencias grandes

La media positiva viene de unos pocos grupos en los que los metadatos eligen un donante
catastrófico, mientras que el paisaje acierta o queda cerca.

| Grupo | `landscape_1nn` | `metadata_1nn` | SBS | Oráculo | Donante del paisaje (veces en 5 muestras) |
|---|---|---|---|---|---|
| DTLZ1 | 0.979 | 0.000 | 0.972 | 0.979 | DTLZ3 (5) |
| DTLZ6 | 0.995 | 0.412 | 0.996 | 0.996 | UF4 (5) |
| UF6 | 0.485 | 0.262 | 0.568 | 0.568 | UF5 (4), UF7 (1) |
| UF5 | 0.234 | 0.165 | 0.478 | 0.483 | UF7 (4), UF6 (1) |
| UF3 | 0.460 | 0.396 | 0.535 | 0.766 | LZ09_F7 (5) |

Y unos pocos en los que el paisaje elige un donante peor que los metadatos:

| Grupo | `landscape_1nn` | `metadata_1nn` | SBS | Oráculo | Donante del paisaje |
|---|---|---|---|---|---|
| DTLZ2 (+DTLZ4) | 0.729 | 0.978 | 0.994 | 0.996 | DTLZ3 (5), ZCAT10 (5) |
| UF7 | 0.626 | 0.726 | 0.776 | 0.806 | UF5 (4), UF6 (1) |
| ZDT2 | 0.932 | 0.996 | 0.996 | 0.996 | UF6 (3), ZCAT6 (2) |
| ZDT4 | 0.981 | 0.995 | 0.966 | 0.996 | DTLZ3 (5) |
| UF4 | 0.874 | 0.876 | 0.950 | 0.950 | DTLZ6 (5) |

En los demás grupos, la diferencia es casi nula: la mediana es 7·10⁻⁵.

Incluso donde el paisaje gana a los metadatos, rara vez llega al SBS. El donante del paisaje es el
donante oráculo solo en el 10 % de los pares destino–muestra, y es al menos tan bueno como el SBS en
el 50 %.

### 3.3 Análisis secundarios pre-registrados (§7)

**Estrato discriminativo.** Son los 6 grupos en los que el oráculo supera al SBS en al menos 0.01:
UF2+LZ09_F5, UF3, UF7, LZ09_F3, LZ09_F7+LZ09_F8 y ZDT4. HVn medio en ellos:

| Método | HVn |
|---|---|
| SBS | 0.796 |
| `knn_selector` | 0.783 |
| `thesis_1nn` | 0.771 |
| `metadata_1nn` | 0.751 |
| `landscape_1nn` | 0.747 |
| Oráculo | 0.856 |

Justo donde transferir podría compensar, ningún método se acerca al oráculo.

**Fuga.** La ganancia de `landscape_1nn` sobre el SBS es:

| Partición | Ganancia |
|---|---|
| Aleatoria 80/20 | −0.028 |
| LOGO | −0.051 |
| LOFO | −0.101 |

La partición aleatoria que usa MO-ELA embellece el resultado en 0.023 frente a LOGO y en 0.073
frente a LOFO, en el sentido que se esperaba.

**Estabilidad del donante (RQ3 parcial).** El donante de `landscape_1nn` es el mismo en las 5
muestras para el 49 % de los destinos.

**Comparaciones exploratorias.** Son en LOGO, sobre los grupos, con Wilcoxon unilateral y sin
corregir por multiplicidad:

| Método | Frente a `metadata_1nn`: media, V/D/E, p | Frente al SBS: media, V/D/E, p |
|---|---|---|
| `knn_selector` | +0.078, 25/7/0, **p = 0.004** | −0.018, 17/11/4, p = 0.44 |
| `thesis_1nn` | +0.036, 13/16/3, p = 0.46 | −0.060, 15/16/1, p = 0.92 |
| `loss_predictor` | +0.007, 9/23/0, p = 0.96 | −0.090, 3/29/0, p ≈ 1 |
| `landscape_1nn_raw_objectives` | +0.003, 19/11/2, p = 0.030 | −0.094, 17/14/1, p = 0.79 |

- **`knn_selector`** es el único método que supera a los metadatos de forma clara, pero no al SBS.
  Elige la configuración con mejor HVn medio sobre los 3 problemas más cercanos. Es la versión
  barata de la RQ5.
- **Escalado de objetivos (enmienda 1).** Con las features sin escalar, `landscape_1nn` queda peor
  en LOGO (0.810 frente a 0.856) y mucho peor en LOFO (0.651 frente a 0.778).

## 4. Interpretación (a posteriori, no pre-registrada)

1. **El portafolio contiene un generalista muy fuerte.** Con c*_ZDT3 disponible, la transferencia
   solo puede compensar donde el generalista falla, es decir, en el estrato discriminativo (6 de 32
   grupos). Ahí el vecino por paisaje no identifica al donante oráculo.
2. **Un solo vecino es una apuesta de alta varianza.** El ajuste con un presupuesto grande produce
   configuraciones especializadas que fallan fuera de su problema. Equivocarse de donante cuesta
   mucho: en DTLZ2, elegir el de DTLZ3 o ZCAT10 cuesta 0.27. Promediar sobre varios vecinos, como
   hace `knn_selector`, reduce esa varianza, y por eso es el mejor método no oráculo.
3. **La cercanía en features no coincide con lo que necesita la configuración.** DTLZ2 se parece a
   DTLZ3 en el paisaje muestreado, pero la configuración ajustada para la convergencia multimodal de
   DTLZ3 no le sirve.
4. **Los metadatos fallan de otra manera.** Aciertan casi siempre lo mismo que el paisaje, pero
   cuando fallan lo hacen de forma catastrófica (DTLZ1, DTLZ6). La media favorece al paisaje y la
   mediana no.

## 5. Desviaciones

1. **SMS-EMOA sustituido por IBEA (enmienda 2, D9).** La matriz se paró y se relanzó a las
   18:16 UTC del 2026-10-26, antes de ejecutar ningún algoritmo por defecto. Los 259 pares ya
   guardados se comprobaron íntegros. Al parar se perdieron las filas de tiempos de 8 pares; sus
   frentes están completos.
2. **IBEA se ejecutó aparte, con VAMOS `c4569f25`.** Los 37 problemas son idénticos en ese VAMOS y en
   `0a8bbb0` (solo cambian CF1, welded beam y RE9x, que no están en el piloto).
3. **`secondary_transfer.py` se escribió después de ver G3.** Cubre los análisis del §7, más la tabla
   por grupo y la fracción de aciertos del oráculo, que son adicionales y descriptivos.
4. **Coste.** El ajuste tardó 43 h, frente a las 20 h estimadas. La matriz tardó unos 60 min, frente a
   los 30 estimados; MOEA/D por defecto tarda 28 s por ejecución.

## 6. Qué no se debe afirmar

- **Que la similitud de paisaje no sirve para recomendar.** Lo que no se sostiene es la transferencia
  desde un solo donante con este portafolio: NSGA-II ajustado por problema con irace, 37 problemas
  biobjetivo y distancia euclídea sobre las 49 features escaladas.
- **Que `knn_selector` es mejor que los metadatos.** Es una comparación exploratoria sin corregir;
  habría que pre-registrarla y comprobarla en los problemas reservados.
- **Que c*_ZDT3 es un buen generalista en general.** Lo es en estos 37 problemas.
- **Que el resultado vale en jMetal/Evolver.** La réplica 3e está pre-registrada pero no se ha
  ejecutado.

## 7. Decisiones pendientes para el usuario

1. **¿Se ejecuta la réplica 3e en Evolver tal como está pre-registrada?** Replicar un resultado
   negativo sigue siendo informativo: dice si depende del framework. Cuesta otra campaña de irace de
   unas 40 h.
2. **RQ4.** Con un SBS tan fuerte, la política de recomendar o recurrir al generalista se reduce casi
   a usar siempre el generalista. ¿Se evalúa igualmente, con un pre-registro nuevo y la misma
   matriz?
3. **RQ5 y `knn_selector`.** Agregar sobre varios problemas ayuda. ¿Se pre-registra la RQ5, o
   `knn_selector` como método principal, para la evaluación final con los 17 reservados?
4. **El artículo.** Se escribe como resultado negativo (`plan.md` §6), con el análisis de por qué y
   la lección del generalista.

## 8. Diagnóstico a posteriori (2026-10-26, no pre-registrado)

Se hizo a raíz de la pregunta del usuario de por qué el paisaje sale tan débil y el donante al azar
tan bueno. Script: `scripts/diagnose_transfer.py`. Salidas: `data/diagnosis.json` y
`data/donor_spread.csv`.

1. **"Al azar" no elige una configuración aleatoria del espacio.** Elige una de las 36 c*_P ya
   ajustadas con irace, y casi todas funcionan bien en casi todos los problemas.
   - En 13 de los 37 problemas, el donante mediano queda a menos de 0.01 del mejor.
   - El HVn medio del azar es alto porque muchos problemas son fáciles para casi cualquier
     configuración ajustada (ZCAT, ZDT1–3, RE/RWA, DTLZ2).
   - En pérdida frente al oráculo, el azar es malo: pierde de media 0.138 (el SBS, 0.014), y en el
     41 % de los casos pierde más de 0.10.
2. **La distancia en features sí contiene señal.** Por destino, la correlación de Spearman entre la
   distancia a cada problema y el HVn de su c*_P en el destino es −0.40 con el paisaje y −0.26 con
   los metadatos, en media sobre destinos.
3. **El paisaje es muy bueno en el caso típico y malo en la cola.** Pérdida frente al oráculo, sobre
   las 185 combinaciones de destino y muestra:

   | LOGO | Mediana | Media | Pérdida > 0.10 | Media del peor 10 % |
   |---|---|---|---|---|
   | Al azar | 0.079 | 0.138 | 41 % | 0.51 |
   | `metadata_1nn` | 0.017 | 0.102 | 22 % | 0.65 |
   | `landscape_1nn` | **0.002** | 0.065 | 18 % | 0.43 |
   | `knn_selector` | **0.0002** | 0.032 | 9 % | 0.26 |
   | SBS | 0.005 | **0.014** | **3 %** | **0.10** |
   | NSGA-II por defecto | 0.012 | 0.063 | 19 % | 0.40 |

   - En mediana, el paisaje supera al SBS. Unos pocos fallos catastróficos (DTLZ2, UF7, ZDT2)
     hunden su media.
   - En LOFO, con una familia nueva, el paisaje empeora también en mediana (0.023) y en la cola
     (0.76).
4. **Lectura.** El problema no es que la distancia no sirva, sino su fiabilidad. Un solo vecino
   acierta casi siempre, pero cuando falla lo hace por mucho, y el SBS casi nunca falla. Es justo la
   distinción del título ("reliable").
   - **Lo que cabe esperar:** promediar sobre vecinos (`knn_selector`) reduce la cola a la mitad, y
     una política que detecte cuándo recurrir al SBS (RQ4) podría combinar las dos virtudes.
   - **Lo que falta mostrar:** que exista una señal que anticipe esos fallos.
5. **Saturación.** Con 20 000 evaluaciones en problemas biobjetivo de D ≤ 30, muchas configuraciones
   convergen. Cerca del frente, el HV distingue poco, así que las diferencias se concentran en una
   decena de problemas difíciles. Los puntos de control de 5 000 y 10 000 evaluaciones ya están en
   la matriz y permitirían ver si con menos presupuesto la transferencia importa más.

## 9. Una columna por distancia (2026-10-26, exploratorio)

Se hizo a petición del usuario. Script: `scripts/distance_table.py`. Salidas:
`data/distance_table.csv`, `data/distance_table.json` y `data/distance_table_long.csv`.
- Cada columna elige un donante por destino y muestra, como `landscape_1nn`, y lee su HVn de la
  matriz existente.
- Las tres distancias nuevas usan las mismas 49 features escaladas por muestra:
  - **L1:** Manhattan sobre las features con escalado robusto.
  - **PCA blanqueada:** PCA sobre las muestras de entrenamiento, conservando el 95 % de la varianza,
    con cada componente dividido por su desviación.
  - **Rangos:** percentil de cada feature entre las muestras de entrenamiento, y luego euclídea.

HVn medio por destino:

| Método | LOGO | LOFO | Aleatoria 80/20 |
|---|---|---|---|
| Al azar | 0.771 | 0.760 | 0.769 |
| NSGA-II por defecto | 0.846 | 0.846 | 0.841 |
| Metadatos | 0.807 | 0.842 | 0.791 |
| Paisaje, euclídea (pre-registrada) | 0.844 | 0.778 | 0.848 |
| Paisaje, tesis | 0.830 | 0.778 | 0.823 |
| Paisaje, aprendida (`loss_predictor`) | 0.810 | 0.786 | 0.830 |
| Paisaje, L1 | 0.849 | 0.771 | 0.851 |
| Paisaje, PCA blanqueada | 0.848 | 0.784 | 0.848 |
| Paisaje, rangos | 0.847 | **0.820** | 0.849 |
| SBS | **0.895** | **0.880** | **0.876** |
| Oráculo | 0.909 | 0.902 | 0.904 |

- **La distancia apenas importa.** En LOGO, las cuatro variantes geométricas quedan entre 0.844 y
  0.849. Su correlación con la calidad del donante es parecida en todas: entre −0.37 (rangos) y −0.42
  (PCA).
- **Frente a los metadatos** (LOGO, Wilcoxon unilateral sobre grupos, sin corregir):
  - euclídea, p = 0.078; L1, p = 0.072;
  - PCA, p = 0.049 (19/10/3); rangos, p = 0.046 (17/11/4).

  Con 6 distancias probadas, una corrección de Bonferroni deja todas por encima de 0.05. Es una
  exploración, no un resultado.
- **La cola mejora un poco con PCA.** Fallan por más de 0.10 en el 14 % de los casos con PCA, el
  16 % con L1 y el 18 % con la euclídea; el SBS, en el 2.7 %.
- **Con familias nuevas (LOFO), los rangos son la única variante que se acerca a los metadatos y al
  valor por defecto:** 0.820, frente a 0.778 de la euclídea.
- **Ninguna distancia se acerca al SBS.** La conclusión de G3 no depende de la distancia elegida.

## 10. Configuraciones aleatorias del espacio (2026-10-26, a posteriori)

Se hizo a petición del usuario. El protocolo quedó fijado antes de ejecutar (commit `9a917db`).
Script: `scripts/random_configs.py`. Salidas: `data/random_configs_*.csv` y
`data/random_configs_summary.json`.
- 37 configuraciones muestreadas del espacio invariante que exploró irace, con la semilla 20261026.
- Se ejecutaron en los 37 problemas con las semillas 5001–5010, en NicoVM: 13 690 ejecuciones en
  26 min.
- Se puntúan con la normalización de la matriz y no entran en su unión.

| Referencia | HVn medio | Pérdida media frente al oráculo |
|---|---|---|
| Configuración aleatoria del espacio (media de las 37) | 0.669 | 0.240 |
| Donante ajustado al azar (`random`) | 0.771 | 0.138 |
| NSGA-II por defecto | 0.846 | 0.063 |
| `landscape_1nn` | 0.844 | 0.065 |
| SBS | 0.895 | 0.014 |
| Oráculo | 0.909 | 0 |

- **El "azar" de la tabla no es azar sobre el espacio, sino sobre configuraciones ya ajustadas.**
  Una configuración aleatoria del espacio rinde 0.10 menos. En ningún problema su media supera a la
  del donante ajustado al azar.
- **La mitad de las configuraciones aleatorias** pierde más de 0.10 frente al oráculo.
- **NSGA-II por defecto** es mejor que todas menos una: la mejor de las 37 obtiene 0.852 de media.
- **Implicación:** ajustar con irace ya captura casi todo lo que se puede ganar. Pasar de una
  configuración aleatoria a una ajustada cualquiera aporta +0.10, y elegir bien entre las ajustadas
  aporta, como mucho, +0.14 hasta el oráculo. Casi todo eso lo consigue ya el SBS (0.895).

En la tabla del §9 corresponde a una columna más, "configuración aleatoria del espacio": 0.669 en
LOGO, 0.669 en LOFO y 0.667 en la aleatoria.

## 11. Estratos y regla de consenso (2026-10-26, exploratorio; paso 1 del plan aprobado)

Script: `scripts/consensus_strata.py`. Salidas: `data/consensus_strata.json`,
`data/consensus_long.csv` y `data/strata.csv`. La rejilla de la regla se fijó antes de ejecutarla.

**Estratos.** Se definen con 20 000 evaluaciones y con la propia matriz, así que son descriptivos:
- **fáciles (13):** el donante mediano queda a menos de 0.01 del mejor;
- **muy difíciles (7):** ni el mejor donante llega a 0.8;
- **intermedios (17):** el resto.

HVn medio en LOGO:

| Estrato | Al azar | Default | Metadatos | Paisaje | `knn_selector` | Consenso k = 3, δ = 0.05 | SBS | Oráculo |
|---|---|---|---|---|---|---|---|---|
| Fáciles (13) | 0.954 | 0.990 | 0.993 | 0.995 | 0.990 | 0.993 | 0.994 | 0.997 |
| Intermedios (17) | 0.788 | 0.881 | 0.840 | 0.898 | 0.931 | 0.944 | 0.943 | 0.951 |
| Muy difíciles (7) | 0.390 | 0.492 | 0.379 | 0.432 | 0.534 | 0.596 | 0.593 | 0.642 |

Incluso donde la elección importa (los intermedios), el SBS queda a solo 0.008 del oráculo. En los
muy difíciles, a 0.05.

**Regla de consenso.**
- **Por defecto,** el SBS.
- **Cuándo cambia:** si, en los k problemas de entrenamiento más cercanos (distancia euclídea
  pre-registrada), la mejor configuración supera de media al SBS en al menos δ, se usa esa.
- **Rejilla:** k ∈ {3, 5} y δ ∈ {0, 0.01, 0.02, 0.05}. Con k = 3 y δ = 0 es `knn_selector`.

| LOGO | HVn medio | Frente al SBS (grupos: media, V/D/E, p) | Pérdida > 0.10 | Peor 10 % | Se desvía del SBS |
|---|---|---|---|---|---|
| `landscape_1nn` | 0.844 | −0.047, 16/15/1, p = 0.72 | 18 % | 0.43 | — |
| k = 3, δ = 0 (`knn_selector`) | 0.877 | −0.018, 17/11/4, p = 0.44 | 9 % | 0.26 | 75 % |
| k = 3, δ = 0.02 | 0.891 | −0.004, 4/7/21, p = 0.84 | 3.8 % | 0.13 | 24 % |
| k = 3, δ = 0.05 | **0.895** | +0.0007, 4/1/27, p = 0.11 | **2.7 %** | **0.09** | 16 % |
| k = 5, δ = 0.05 | 0.895 | — | — | — | — |
| SBS | 0.895 | — | 2.7 % | 0.10 | 0 % |

- **La regla elimina la cola del vecino único** y, con un δ exigente, iguala al SBS.
  - Con una familia nueva (LOFO) queda algo por debajo: 0.872 frente a 0.880.
  - Con la partición aleatoria queda algo por encima: 0.879 frente a 0.876.
- **No hay margen para superar al SBS.** En este benchmark, con este portafolio y 20 000
  evaluaciones, la distancia entre el SBS y el oráculo es 0.014 de media. La similitud de paisaje
  puede, como mucho, igualar al generalista.
- **Esto refuerza el paso 2 del plan:** un benchmark con más margen (COCO bbob-biobj), una similitud
  conocida de antemano y el generalista ajustado sobre todo el entrenamiento como referencia.
