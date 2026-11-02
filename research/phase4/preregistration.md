# Pre-registro de la fase 4 — RQ4: recomendar o recurrir al generalista (puerta G7)

Fecha: 2026-11-02. Corresponde a las decisiones D12 y D13 del usuario
(`research/decisions/decisions.md`) y a la §12.2 de `plan.md`.

**Se fija antes de:**
- la matriz de la fase 3c;
- cualquier ajuste o evaluación de los generalistas de la fase 3g;
- cualquier análisis con rendimiento de esta fase.

**Lo único que existe con rendimiento es la matriz de la fase 3,** que ya se analizó (G3). Lo que
no se conoce es el rendimiento de los generalistas irace, que deciden el resultado.

**Scripts:**
- `scripts/policy.py`: la política;
- `scripts/analyze_g7_phase3.py`: G7 sobre la fase 3 + 3g;
- `scripts/analyze_g7_3c.py`: la réplica en la 3c, enmienda 3 de su pre-registro.

Se han probado solo con generalistas sintéticos: copias renombradas de frentes de la matriz de la
fase 3 y una matriz de HVn inventada para la 3c.

## 1. Pregunta

¿Hace una política que transfiere solo cuando el problema nuevo es indistinguible de uno conocido,
y si no recurre al generalista, la transferencia segura sin perder frente al generalista?

## 2. Elementos fijos

| Elemento | Valor |
|---|---|
| Datos | La matriz de la fase 3: 37 c*_P, NSGA-II, MOEA/D e IBEA por defecto, semillas 5001–5010 y 20 000 evaluaciones. Las features de MOLA 0.4.0 (`sample`, 5 muestras LHS por problema). Los generalistas de la fase 3g |
| Particiones | Las de la fase 3: LOGO (32 grupos), LOFO (5 familias) y aleatoria 80/20 por problema (100) |
| Método de transferencia | `knn_selector` de `analyze_transfer.recommend`, sin cambios: la configuración con mejor HVn medio en los 3 problemas de entrenamiento más cercanos |
| Generalista (línea base 1, D11 y D12) | **LOGO:** `gen__logo_NN`, ajustado con irace sobre los problemas fuera del grupo del destino (32 ajustes, enmienda 1 de la 3g). **LOFO:** `gen__lofo_<familia>`. **Aleatoria:** `gen__lofo_<familia>`, un subconjunto del entrenamiento, solo descriptivo |
| HVn | El de la matriz de la fase 3. Los generalistas no entran en la unión que lo normaliza |

## 3. La política (`policy.py`)

Para cada muestra del destino y el conjunto de entrenamiento T del pliegue:
1. **Escalado:** las muestras de T, las medias de sus problemas y la muestra del destino se
   escalan de forma robusta (mediana e IQR) solo con las muestras de T, como en
   `analyze_transfer._robust_z`.
2. **d:** la distancia euclídea de la muestra a la media de entrenamiento más cercana.
3. **Distribución de ruido del pliegue:** para cada problema de T y cada una de sus 5 muestras, la
   distancia de esa muestra a la media de las otras 4. Son 5·|T| valores.
4. **s₁:** la fracción de esa distribución que es mayor que d.
5. **π_α:** `knn_selector` si s₁ ≥ α; si no, el generalista. Principal: **α = 0.05**, fijado a
   priori.
6. **Unidad de ruido,** para informar de las distancias: la distancia mediana entre dos muestras
   del mismo problema de T.

## 4. Puerta G7 (análisis principal)

En LOGO, sobre los 32 grupos de formulación. El valor de cada grupo es la media sobre sus destinos
y muestras. G7 se supera si se cumplen las dos condiciones:
1. **No inferioridad frente al generalista,** con un margen de 0.005: prueba de Wilcoxon de rangos
   con signo unilateral de (π₀.₀₅ − generalista + 0.005) > 0, con p < 0.05.
2. **Reducción de la cola:** la fracción de muestras destino con una pérdida mayor que 0.10 frente
   al oráculo es, con π₀.₀₅, como mucho la mitad que con `knn_selector`.

Si no se supera, se informa como resultado negativo. No se cambian α, la distancia, el método ni
el margen para repetir la prueba.

**Por qué en LOGO:** con la familia fuera, el destino casi nunca es indistinguible de un problema
de entrenamiento. Solo 4 de los 1 332 pares por debajo de 1.5 unidades son de familias distintas
(`phase3/report.md`, §14), así que en LOFO π casi siempre equivale al generalista.

**Expectativa, declarada antes de conocer el resultado:**
- Lo probable es que se cumpla la condición 2.
- La condición 1 depende de cómo rinda el generalista LOGO, que aún no se conoce.
- La cobertura, que solo depende de las features (sin rendimiento), es la fracción de muestras
  destino con s₁ ≥ 0.05:
  - LOGO: 44 % (61 % en el estrato fácil, 32 % en el intermedio y 40 % en el muy difícil);
  - LOFO: 2 %;
  - aleatoria por problema: 53 %.

## 5. Análisis secundarios, descriptivos

**Por partición (LOGO, LOFO y aleatoria):**
- el HVn medio del generalista, `knn_selector`, el SBS, NSGA-II por defecto, el oráculo, π_α y la
  variante calibrada por pérdida;
- la tabla de cobertura y riesgo para α ∈ {0.01, 0.05, 0.10, 0.25}: la fracción que transfiere, la
  fracción de pérdidas > 0.10, y la diferencia entre `knn_selector` y el generalista en la rama que
  transfiere;
- la cobertura por estrato (fácil, intermedio y muy difícil, según `phase3/data/strata.csv`);
- los casos con s₁ ≥ 0.05 y pérdida > 0.10, como UF5 y UF7.

**Variante calibrada por pérdida** (en LOGO y LOFO):
- **El umbral:** en cada pliegue, t_ε es la mayor distancia, en unidades de ruido, a la que al
  menos el 90 % de los pseudo-destinos con distancia ≤ t_ε pierden ≤ ε.
- **Los pseudo-destinos:** cada muestra de cada problema de entrenamiento, frente al resto del
  entrenamiento, con su donante más cercano.
- **Los valores:** ε ∈ {0.01, 0.02}.
- **Lo que se informa:** la dispersión de t_ε entre pliegues.

## 6. Réplica en la 3c

Va en la enmienda 3 de su pre-registro: las mismas dos condiciones, por partición (S1, S3 y S2),
sobre las 55 funciones.

## 7. Lo que no cubre

- **La política de tres niveles (D13) y el umbral t₂:** necesitan el experimento del nivel 2, que
  tendrá su propio pre-registro (`plan.md`, §12.3).
- **Los 17 reservados:** en la fase 5, π₀.₀₅ se evalúa congelado y con `gen_all` como generalista.
