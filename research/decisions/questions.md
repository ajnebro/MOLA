# Preguntas al usuario

Registro de las preguntas que Claude ha hecho al usuario, con su respuesta y lo que se decidió, y de
las que siguen pendientes. Las preguntas del usuario a Claude no se registran aquí. La versión
anterior de este fichero, que también las incluía, está en el historial de git (commit `df294fc`).
Las decisiones formales están en [`decisions.md`](decisions.md), y la primera respuesta larga, literal,
en [`question1.md`](question1.md).

## Respondidas

### 1. Decisiones de la fase 0 (2026-10-19)
- **Pregunta:**
  - ¿Se acepta que MOLA use por defecto la geometría `bound`, conservando el perfil histórico para
    reproducir lo publicado?
  - ¿Los experimentos se ejecutan en VAMOS o en jMetal?
  - ¿El artículo se plantea como transferencia de configuraciones ajustadas por problema (opción
    2.5, la línea de la tesis) o como selección sobre un portafolio fijo?
- **Respuesta:** "Guarda esta respuesta como question1; una 1B y 2.5; usamos VAMOS; guarda también
  las decisiones; haz commit y push y procede con la siguiente fase".
- **Decisión:** D1 (`bound`), D2 (una c*_P ajustada por problema) y D3 (VAMOS).

### 2. ¿Lanzo la comparación de irace con F-Race, y con qué variante de irace? (2026-10-20)
- **Respuesta:** "usa irace en NicoVM".
- **Resultado:** fase 2b. irace supera a F-Race en 32 de 37 problemas.

### 3. ¿Adopto irace para la fase 3 y la preparo, o prefieres revisar antes el informe? (2026-10-20)
- **Respuesta:** "Usa siempre irace. Usa budget de 20000, o más si lo consideras necesario. Siempre
  comprueba que NicoVM no está ocupado. Procede con tu recomendación".
- **Decisión:** D5.

### 4. ¿Aplico la opción 1, escalar los objetivos por muestra, como enmienda al pre-registro? (2026-10-20)
- **Respuesta:** "aplica la opción y actualiza el plan".
- **Decisión:** D4, MOLA 0.4.0 (`objective_scaling = "sample"`) y enmienda 1 del pre-registro de la
  fase 3.

### 5. ¿Evolver en lugar de VAMOS, los dos, o solo VAMOS? ¿Con todo el espacio de NSGA-II o con el del artículo? (2026-10-20)
- **Respuesta:** "2, todo espacio del nsga-ii".
- **Decisión:** D6. La fase 3 se hace en VAMOS y después se replica en Evolver con el espacio completo
  de NSGA-II.

### 6. ¿Espacio completo o sin los cuatro operadores no invariantes? (2026-10-20)
- **Respuesta:** "quita esos 4 parámetros".
- **Decisión:** D6 resuelto. El espacio de Evolver queda en 28 parámetros (sin PCX, UNDC, Laplace ni
  la mutación uniforme).

### 7. ¿Lanzo la matriz de rendimiento de la fase 3? (2026-10-26)
- **Respuesta:** "si, rq5, y lanza la matriz".
- **Resultado:** la matriz se lanzó el 2026-10-26 a las 17:56 UTC. G3 no se superó
  (`research/phase3/report.md`).

### 8. ¿Aplico el nuevo orden de las preguntas de investigación, con la transferencia como RQ1? (2026-10-26)
- **Respuesta:** "aplica el nuevo orden".
- **Decisión:** D7.

### 9. ¿La selección del conjunto de entrenamiento como RQ5, a decidir después de G3? (2026-10-26)
- **Respuesta:** "si, rq5".
- **Decisión:** D8.

### 10. ¿Subo la rama de IBEA a VAMOS y abro un pull request? (2026-10-26)
- **Respuesta:** "si, sube IBEA a VAMOS y abre PR".
- **Resultado:** PR vamos-optimization/VAMOS#115.

### 11. Tras el diagnóstico de la fase 3, ¿qué análisis hago: (a) 5 000 y 10 000 evaluaciones, (b) configuraciones aleatorias del espacio como referencia, (c) pre-registrar la RQ4 contra la cola, o (d) contarlo así en el artículo? (2026-10-26)
- **Respuesta:** "haz b)".
- **Resultado:** 37 configuraciones muestreadas del espacio invariante (`phase3/scripts/random_configs.py`,
  protocolo en el commit `9a917db`), ejecutadas en NicoVM sobre los 37 problemas con las semillas
  5001–5010.

### 12. Plan recomendado tras la fase 3: (1) estratos y regla de consenso sobre la matriz actual; (2) diseñar y pre-registrar un estudio con COCO bbob-biobj, con el generalista ajustado sobre todo el entrenamiento; (3) ejecutarlo. ¿Empiezo? (2026-10-26)
- **Respuesta:** "revisa cada hora si tienes tokens para seguir, procede con todo, y recuerda lanzar
  en nicovm cuando esté libre y en todos los núcleos -1".
- **Decisión:** se ejecuta el plan completo.
  - Una tarea horaria en la sesión (id `a9636817`) retoma el trabajo.
  - En NicoVM se lanza solo cuando está libre, con 31 procesos.

### 13. ¿Añado al artículo de Overleaf la comparación con NSGA-II por defecto, la cita de ASlib y la métrica de hueco SBS–VBS cerrado? (2026-10-26)
- **Respuesta:** incluida en "procede con todo" (pregunta 12).
- **Resultado:** se añade al artículo junto con los análisis a posteriori de la fase 3.

### 14. ¿Ajusto un generalista "de verdad" (irace sobre todo el entrenamiento)? ¿Los problemas son demasiado fáciles; qué hago? (2026-10-26)
- **Respuesta:** "procede con todo" (pregunta 12).
- **Resultado:** la fase 3c incluye los generalistas ajustados sobre el entrenamiento y un benchmark
  menos saturado (bbob-biobj, D = 10). Está pre-registrada en el commit `0ea3209` y lanzada en
  NicoVM.

### 15. ¿Incorporo al plan la transferencia de lo sintético a lo real y el análisis de qué eligen las configuraciones ajustadas? (2026-10-27)
- **Respuesta:** "añade al plan, pero al final si".
- **Resultado:** RQ6 y RQ7 en `plan.md` §11, al final y sin tocar las RQ1–RQ5 (D10).
  - **RQ6:** primero se mide cuántos problemas RE y RWA biobjetivo no están saturados.
  - **RQ7:** análisis exploratorio de las élites, sin ejecuciones nuevas.

### 16. ¿Preparo la comparación con un generalista irace y NSGA-II por defecto como líneas base? ¿Qué método principal se pre-registra? (2026-10-31)
- **Respuesta:** "ok a tus recomendaciones". Antes, el usuario fijó las dos líneas base: "NSGA-II
  con valores por defecto es el baseline 2" e "irace para el conjunto de entrenamiento en lugar del
  SBS". También dijo que el tercer elemento es la recomendación para cada instancia, no una línea
  base.
- **Resultado (D11):**
  - Lo que se evalúa es la recomendación por similitud en cada instancia. El método principal es
    `knn_selector`, y la regla de consenso queda como secundaria.
  - Líneas base: el generalista ajustado con irace sobre el entrenamiento y NSGA-II por defecto.
  - El donante al azar es un control de ablación, y hay análisis instancia a instancia frente a la
    distancia.
  - En la fase 3, 5 generalistas LOFO más 1 sobre los 37 problemas, pre-registrados antes de
    lanzarlos cuando NicoVM quede libre.
  - Esto responde también a la antigua pendiente 2.

### 17. ¿Plazo exacto de GECCO 2027? ¿Borro los `hs_err_pid*.log` de la raíz del repositorio? (2026-11-01)
- **Respuesta:** "olvida la parte, ya no hay prisa, y borra los logs".
- **Resultado:**
  - El plazo de GECCO deja de condicionar el plan (`plan.md`, §7, "Calendario").
  - Los dos registros de fallo de Java se borraron sin subirlos.
  - Las recomendaciones de la revisión externa que se apoyaban en el plazo cambian; ver la
    pendiente 21.

### 18. Revisión externa de Fable: ¿qué cambios C1–C14 se adoptan? Y las preguntas que solo puede decidir el autor (2026-11-01 y 2026-11-02)
- **Respuestas:**
  - "Si, adopta los cambios" (el paquete que recomendó Claude, sin plazo);
  - G7 en LOGO: "Opción C", con 32 generalistas LOGO;
  - verificar los reservados: "ok", lo hace Claude;
  - la réplica en Evolver: "ok";
  - "coautores Nico, Antonio y Javi, el resto, pendiente".
- **Resultado (D12):**
  - C1–C14 adoptados, con tres ajustes por no haber plazo:
    - un único artículo de revista;
    - el nivel 2 *anytime* entra en el artículo;
    - la 3e se hace.
  - Quedan respondidas también las antiguas pendientes:
    - 1, la réplica en Evolver: sí;
    - 3, el encuadre: condicional, con el resultado negativo en el centro;
    - 4, la campaña de la 3c: seguir sin enmendar;
    - la de la revisión de Fable y las del umbral de similitud y la política de tres niveles, que
      absorben C3 y C4.

### 19. ¿Recupero el segundo umbral expresándolo en unidades de ruido, con la política de tres niveles? (2026-11-02)
- **Respuesta:** "procede con tu recomendación".
- **Resultado (D13):** t₂ en unidades de ruido, calibrado con el experimento del nivel 2 y validado
  con validación cruzada sobre los problemas de desarrollo. No se valida en los reservados (`plan.md`,
  §12.2 y §12.3).

## Pendientes

### Planteadas antes, sin respuesta

5. ¿Ampliar el portafolio con algoritmos ajustados además de NSGA-II? Se planteó como MOEA/D y
   SMS-EMOA (2026-10-20); desde D9 el comparador es IBEA en lugar de SMS-EMOA.
6. ¿Validar con Nebro las decisiones técnicas que cambian definiciones? (2026-10-20)
   - T1: punto soportado con pesos estrictamente positivos.
   - T5 y D6: operadores excluidos.
   - D4: escalado de objetivos.
7. ¿Cómo y cuándo se comunican los demás fallos de VAMOS? IBEA ya está en el PR #115.
   - el `KeyError` de `racing/refill.py`;
   - los operadores no invariantes;
   - el frente de referencia de UF6;
   - las cotas de UF3;
   - el desplazamiento absoluto del punto de referencia de SMS-EMOA.
8. ¿Se comunican los fallos de jMetal y Evolver, y entran en la respuesta a los revisores del
   artículo de Evolver en ECJ?
   - RWA1 con `10e-3`;
   - la mutación no uniforme que no se atenúa;
   - Laplace y la mutación uniforme con escala absoluta;
   - la terminación por generación;
   - el épsilon de SBX.
9. ¿Qué valor por defecto debe tener MOLA para el escalado de objetivos? Hoy es `raw`, por
   continuidad; el recomendador usa `sample`.
10. ¿Cuándo se integran las ramas `research/*` en `main`, y con un pull request a ajnebro/MOLA?
11. ¿Cuándo se regeneran los CSV históricos, `FEATURE_ANALYSIS.md` y los notebooks con la versión
    actual de MOLA?
12. ¿Dónde se publica: una revista (ECJ, TELO) u otra? Sin plazo fijo desde el 2026-11-02. Los
    coautores ya están decididos: Nico, Antonio y Javi; el resto, pendiente.

### Que se plantearán más adelante

13. Si VAMOS y Evolver discrepan, ¿cuál se toma como principal en el artículo?
14. ¿Cuándo se abren los 17 problemas reservados, y con qué método congelado?
15. ¿Las RQ2 y RQ3 completas (malla de tamaños de muestra, k ∈ {1, D, 10} y transformaciones de
    unidades) van antes o después de la evaluación final?
16. ¿Qué problemas y en qué fase para la validación con tres objetivos?
17. (Resuelta por D12: la RQ4 se evalúa con la puerta G7, pre-registrada en la fase 4.)

### Hechas el 2026-11-02, sin respuesta todavía

22. ¿Encadeno en NicoVM, para que arranque sola al terminar la campaña de la 3c y la repetición de
    f20, la matriz de la 3c? Es la recogida de élites, la evaluación de las 64 configuraciones,
    IBEA reparado y las configuraciones aleatorias, ya pre-registrada.
    - ¿Y después la fase 3g, con sus 38 generalistas y su evaluación?
    - **Recomendación de Claude:** encadenar la matriz de la 3c, que dura unas 10–20 h. La 3g solo
      si NicoVM no se necesita para el plan v2 de TEVC; son unos 2–2.5 días más.
