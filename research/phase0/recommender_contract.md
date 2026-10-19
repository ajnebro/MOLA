# Contrato del recomendador (fase 0, sin implementar)

Qué debe devolver el sistema descrito en `plan.md` §1: dada una instancia nueva, sus vecinos conocidos
más similares y una configuración recomendada, o la configuración generalista cuando la evidencia no
basta. Es un contrato de interfaz para guiar las fases 1–4. **No existe código que lo implemente.**

## Entrada

| Campo | Tipo | Notas |
|---|---|---|
| `sample` | registro de intercambio de MOLA (CSV + JSON, `schema_version` 1) o una muestra en memoria | Solo X, F y metadatos. El núcleo nunca recibe el objeto problema |
| `budget_total` | entero | El presupuesto total de evaluaciones que tiene el usuario |
| `budget_characterisation` | entero | Las evaluaciones ya gastadas en la muestra; se descuentan del total |
| `options.k_neighbours` | entero, por defecto 5 | Número de instancias conocidas que se devuelven |
| `options.profile` | texto | Versión del perfil de cálculo de features y de la geometría (`raw` o `bound`, ver E4 y E6) |

## Salida (JSON)

```json
{
  "request": {"instance_id": "user-problem-001", "D": 4, "M": 3, "bounds_sha256": "…",
              "budget_total": 20000, "budget_characterisation": 800},
  "characterisation": {
    "mola_version": "0.3.0", "feature_profile": "paper49-v1", "geometry": "bound", "k_graph": 4,
    "sample_size": 800, "sampler": "lhs", "seed": 1, "evaluations_used": 800,
    "features": {
      "nd_n": {"value": 0.04, "status": "defined"},
      "fdc":  {"value": null, "status": "undefined", "cause": "|ND| = 2 (one pair)"},
      "lsupp_avg_neig": {"value": 0.77, "status": "defined", "method": "lp-exact"}
    }
  },
  "neighbours": [
    {"instance_id": "RE37", "formulation_group": "rocket-injector-3obj", "distance": 2.18,
     "distance_metric": "typed-v1", "top_contributing_features": ["dist_f_cor_neig", "nd_n"]}
  ],
  "recommendation": {
    "configuration_id": "nsgaii-c07", "algorithm": "NSGA-II", "parameters": {"...": "..."},
    "source": {"donors": ["RE37"], "rule": "best-of-portfolio on nearest donor"},
    "expected_quality": {"metric": "normalised_hv", "budget": 19200, "estimate": 0.91, "interval": [0.88, 0.93]}
  },
  "decision": {
    "action": "recommend",
    "confidence": 0.82,
    "signals": {"nearest_distance": 2.18, "margin_to_second": 6.5, "donor_agreement": 1.0,
                "resampling_stability": 0.95, "undefined_feature_fraction": 0.02},
    "threshold": 0.6, "threshold_calibration": "train/validation folds of protocol v1"
  },
  "fallback": {"configuration_id": "generalist-sbs", "used": false},
  "provenance": {"knowledge_base_version": "kb-…", "portfolio_version": "pf-…", "created_utc": "…"}
}
```

## Reglas

1. **Abstención.** Cuando la evidencia no supera el umbral, `decision.action` vale
   `"fallback_generalist"`, `fallback.used` vale `true` y `recommendation` contiene la configuración
   generalista. Los vecinos y las señales se devuelven igualmente, para que se vea el motivo.
2. **Features indefinidas.** Llevan `value: null`, `status: "undefined"` y una `cause`; nunca se
   sustituyen por 0. Una entrada no finita (NaN o inf en X o F) se rechaza antes de caracterizar (E9).
3. **Presupuesto.** Se cumple `budget_total = budget_characterisation + budget_optimisation +
   budget_configuration_on_target`, y el último término es 0 cuando se reutiliza una configuración. Las
   soluciones evaluadas durante la caracterización se devuelven para incorporarlas al archivo final.
4. **Sin información de evaluación del objetivo.** Las features y la decisión usan solo la muestra. La
   calidad de referencia del problema nuevo (HV con su frente de referencia) no entra nunca en la
   recomendación.
5. **Procedencia.** Cada respuesta identifica la versión de MOLA, el perfil de features, la geometría,
   la base de conocimiento y el portafolio, porque los valores dependen de todo ello (E4, E6, E25).
6. **Grupos de formulación.** Cada vecino lleva su `formulation_group`, para que la evaluación pueda
   excluir alias y variantes (E11, E23).

## Decisiones abiertas

- Cómo se define `confidence` y qué señales entran: lo responde la RQ4.
- Qué métrica de distancia y qué representación de features se usan: lo responde la RQ3.
- Si el valor por defecto es `k_neighbours = 1`, recomendando desde el vecino más cercano, o una
  agregación de varios vecinos.
- Si `geometry` es `bound` por defecto. En la fase 0, la geometría `bound` resulta exactamente
  invariante ante cambios de unidades por variable (E6), pero eso cambia los valores de la línea base
  actual de MOLA.
