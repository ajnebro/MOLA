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

## Pendientes

### Hechas tras la fase 3, sin respuesta todavía (2026-10-26)

1. ¿Ejecuto la réplica 3e en Evolver tal como está pre-registrada?
   - Replicar el resultado negativo dice si depende del framework.
   - Son unas 40 h de irace en NicoVM.
2. ¿Pre-registro `knn_selector`, o directamente la RQ5, como método principal para la evaluación
   final con los 17 problemas reservados?
3. ¿Planteo el artículo abiertamente como resultado negativo, con la lección del generalista
   dominante?
4. ¿Añado al artículo de Overleaf la comparación con NSGA-II por defecto, la cita de ASlib y la
   métrica de hueco SBS–VBS cerrado?

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
12. ¿Dónde se publica: GECCO 2027 o una revista (ECJ, TELO)? ¿Quiénes son los coautores?

### Que se plantearán más adelante

13. Si VAMOS y Evolver discrepan, ¿cuál se toma como principal en el artículo?
14. ¿Cuándo se abren los 17 problemas reservados, y con qué método congelado?
15. ¿Las RQ2 y RQ3 completas (malla de tamaños de muestra, k ∈ {1, D, 10} y transformaciones de
    unidades) van antes o después de la evaluación final?
16. ¿Qué problemas y en qué fase para la validación con tres objetivos?
17. RQ4: con un generalista que domina, ¿se evalúa igualmente la política de recomendar o recurrir al
    generalista, con un pre-registro nuevo sobre la misma matriz?
