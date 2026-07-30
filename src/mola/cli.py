"""MOLA's command-line interface.

Three commands, all documented in depth via their own ``--help`` (this is the authoritative
reference; see also README.md's "CLI usage" section and ``examples/``):

- ``mola sample``: Latin-Hypercube-sample and evaluate a jMetalPy problem, writing an interchange
  file (see ``mola.sample``).
- ``mola characterize``: compute the 49 landscape features for an existing interchange file,
  regardless of which adapter produced it.
- ``mola run``: sample, evaluate, and characterize a jMetalPy problem in one step, no file needed
  -- the most convenient entry point for a script or an AI agent.

Errors expected at this I/O boundary (an unknown problem name, a malformed sample file, an
unrecognized ``--output`` extension) are caught here and reported as a clean one-line message plus
a non-zero exit code, per PYTHON_CODING_GUIDELINES.md §4 -- not a new ``Ok[T] | Err`` type, which
would be overkill for three commands, but Typer's own idiomatic mechanism for the same purpose.
"""

import json
from pathlib import Path

import jmetal.problem as jmetalpy_problems
import pandas as pd
import typer
from jmetal.core.problem import FloatProblem

from mola.adapters.jmetalpy import sample_problem
from mola.characterize import characterize as compute_features
from mola.multimodality import DEFAULT_WALK_COUNT
from mola.sample import read_sample, write_sample

app = typer.Typer(
    name="mola",
    help=(
        "MOLA -- Multi-Objective Landscape Analyzer. Characterizes the landscape features of "
        "continuous multi-objective optimization problems (49 features across four classes: "
        "global, multimodality, evolvability, ruggedness), independent of the framework the "
        "problem is implemented in."
    ),
    no_args_is_help=True,
)

_PROBLEM_HELP = "Name of a jMetalPy FloatProblem, e.g. ZDT1, DTLZ2 (see jmetal.problem)."
_VARIABLES_HELP = "Number of decision variables, for problems whose constructor accepts it."
_SAMPLE_SIZE_HELP = "Number of solutions to Latin-Hypercube-sample. Defaults to 200 * D."
_SEED_HELP = "Seed for the Latin Hypercube sampler."
_WALK_SAMPLES_HELP = "Number of independent adaptive walks averaged for length_aws/eval_aws."
_OUTPUT_HELP = "Also save the result here, as .json or .csv (format inferred from the suffix)."


def _resolve_jmetalpy_problem(name: str, variables: int | None) -> FloatProblem:
    """Look up and instantiate a jMetalPy FloatProblem by name.

    Args:
        name: The problem's class name in ``jmetal.problem``, e.g. ``"ZDT1"``.
        variables: Passed as ``number_of_variables`` if given; problems that don't accept that
            constructor argument (e.g. ZDT4, most RE/RWA problems) must be called without it.

    Returns:
        The instantiated problem.

    Raises:
        typer.Exit: If ``name`` isn't a jMetalPy ``FloatProblem``, or if it doesn't accept
            ``variables``. Prints a one-line error to stderr first.
    """
    problem_class = getattr(jmetalpy_problems, name, None)
    if not (isinstance(problem_class, type) and issubclass(problem_class, FloatProblem)):
        typer.echo(
            f"Error: '{name}' is not a jMetalPy FloatProblem (see jmetal.problem for valid "
            "names, e.g. ZDT1, DTLZ2). MOLA only characterizes continuous problems.",
            err=True,
        )
        raise typer.Exit(code=1)
    try:
        return (
            problem_class(number_of_variables=variables)
            if variables is not None
            else problem_class()
        )
    except TypeError as error:
        typer.echo(f"Error: could not instantiate '{name}': {error}", err=True)
        raise typer.Exit(code=1) from error


def _report_result(result: dict[str, float], output: Path | None) -> None:
    """Print a feature-computation result and optionally save it to a file.

    Prints every key in ``result``'s own order -- metadata first, then the 49 features grouped by
    class, since that's exactly how ``mola.characterize.characterize`` builds the dict.

    Args:
        result: The dict returned by ``characterize()``.
        output: Optional destination path; ``.json`` writes the dict as-is, ``.csv`` writes it as
            a single-row table. Any other suffix is a clean CLI error, not a silent guess.

    Raises:
        typer.Exit: If ``output`` has an unrecognized suffix. Prints a one-line error first.
    """
    for key, value in result.items():
        typer.echo(f"{key}: {value:.6g}")
    if output is None:
        return
    if output.suffix == ".json":
        output.write_text(json.dumps(result, indent=2) + "\n")
    elif output.suffix == ".csv":
        pd.DataFrame([result]).to_csv(output, index=False)
    else:
        typer.echo(
            f"Error: unrecognized --output suffix '{output.suffix}' (use .json or .csv).",
            err=True,
        )
        raise typer.Exit(code=1)
    typer.echo(f"Wrote result to {output}")


@app.command()
def sample(
    problem: str = typer.Argument(..., help=_PROBLEM_HELP),
    output: Path = typer.Argument(
        ..., help="Destination CSV path (a sidecar .json is written too)."
    ),
    variables: int | None = typer.Option(None, "--variables", "-D", help=_VARIABLES_HELP),
    sample_size: int | None = typer.Option(None, "--sample-size", "-n", help=_SAMPLE_SIZE_HELP),
    seed: int | None = typer.Option(None, "--seed", help=_SEED_HELP),
) -> None:
    """Sample and evaluate a jMetalPy problem, writing an interchange sample file.

    Latin-Hypercube-samples PROBLEM, evaluates every solution in-process, and writes the result as
    an interchange CSV + sidecar metadata JSON at OUTPUT -- the same file format `mola
    characterize` reads, regardless of which adapter produced it (this repo's Python one, or a
    future Java one following the same schema).

    Example:
        mola sample ZDT1 sample.csv --variables 5 --sample-size 1000 --seed 42
    """
    resolved_problem = _resolve_jmetalpy_problem(problem, variables)
    result_sample = sample_problem(resolved_problem, sample_size=sample_size, seed=seed)
    write_sample(result_sample, output)
    typer.echo(
        f"Wrote {result_sample.size} solutions to {output} and {output.with_suffix('.json')}"
    )


@app.command()
def characterize(
    sample_path: Path = typer.Argument(
        ..., help="Path to an interchange sample CSV (its sidecar .json is read alongside it)."
    ),
    output: Path | None = typer.Option(None, "--output", "-o", help=_OUTPUT_HELP),
    walk_samples: int = typer.Option(DEFAULT_WALK_COUNT, "--walk-samples", help=_WALK_SAMPLES_HELP),
) -> None:
    """Compute the 49 landscape features for an existing interchange sample file.

    Reads SAMPLE_PATH -- an interchange CSV written by `mola sample`, or by any other adapter
    following the same schema (CSV + sidecar metadata JSON; see CLAUDE.md's "Interchange schema")
    -- and prints every feature plus sample_size/num_obj/num_var.

    Example:
        mola characterize sample.csv --output result.json
    """
    try:
        loaded_sample = read_sample(sample_path)
    except (FileNotFoundError, ValueError) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=1) from error
    result = compute_features(loaded_sample, walk_samples=walk_samples)
    _report_result(result, output)


@app.command()
def run(
    problem: str = typer.Argument(..., help=_PROBLEM_HELP),
    variables: int | None = typer.Option(None, "--variables", "-D", help=_VARIABLES_HELP),
    sample_size: int | None = typer.Option(None, "--sample-size", "-n", help=_SAMPLE_SIZE_HELP),
    seed: int | None = typer.Option(None, "--seed", help=_SEED_HELP),
    walk_samples: int = typer.Option(DEFAULT_WALK_COUNT, "--walk-samples", help=_WALK_SAMPLES_HELP),
    output: Path | None = typer.Option(None, "--output", "-o", help=_OUTPUT_HELP),
) -> None:
    """Sample, evaluate, and characterize a jMetalPy problem in one step -- no file needed.

    The most convenient entry point: straight from a jMetalPy problem name to its 49 landscape
    features plus sample_size/num_obj/num_var, with no intermediate interchange file. Well suited
    to scripted or AI-agent use, where a single command producing a structured result matters more
    than inspecting the intermediate sample.

    Example:
        mola run ZDT1 --variables 5 --sample-size 1000 --seed 42
    """
    resolved_problem = _resolve_jmetalpy_problem(problem, variables)
    result_sample = sample_problem(resolved_problem, sample_size=sample_size, seed=seed)
    result = compute_features(result_sample, walk_samples=walk_samples)
    _report_result(result, output)


if __name__ == "__main__":
    app()
