import inspect, warnings; warnings.filterwarnings("ignore")
from jmetal.core.problem import FloatProblem
from jmetal.problem.multiobjective import re as re_mod, rwa as rwa_mod
for mod in (re_mod, rwa_mod):
    rows = []
    for _, cls in inspect.getmembers(mod, inspect.isclass):
        if cls.__module__ == mod.__name__ and issubclass(cls, FloatProblem):
            try:
                p = cls(); rows.append((p.name(), p.number_of_constraints()))
            except Exception as e:
                rows.append((cls.__name__, f"err {e}"))
    con = [r for r in rows if r[1] not in (0,)]
    print(mod.__name__, f"{len(rows)} problems; with constraints: {con}")
