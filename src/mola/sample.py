"""The interchange record: a structured sample of one multi-objective problem.

This is the only input MOLA's core accepts. Adapters (jMetal, jMetalPy, ...) own the sampling and
the evaluation; the core never sees a problem object and never calls ``evaluate()``. The boundary
is this schema, not a particular transport: a :class:`Sample` may be read from disk or handed over
in memory, and the core cannot tell the difference.

Objective values are required to be in **minimization** form; adapters negate natively-maximized
objectives before emitting a sample.
"""

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

SCHEMA_VERSION = 1
"""Version of the interchange schema this module reads and writes."""


@dataclass(slots=True, frozen=True)
class Sample:
    """An evaluated sample of a multi-objective problem's search space.

    Attributes:
        problem: Name of the sampled problem.
        variables: Decision vectors, shape ``(n, D)``.
        objectives: Objective vectors in minimization form, shape ``(n, M)``.
        lower_bounds: Per-variable lower bounds, shape ``(D,)``. Carried for traceability only;
            no feature computation reads them, since every normalizer is empirical over the
            sample itself.
        upper_bounds: Per-variable upper bounds, shape ``(D,)``.
        sampler: Identifier of the sampling design that produced the sample, e.g. ``"lhs"``.
        seed: Seed that produced the sample, or ``None`` if the adapter did not record one.
        schema_version: Version of the interchange schema this record follows.
    """

    problem: str
    variables: np.ndarray
    objectives: np.ndarray
    lower_bounds: np.ndarray
    upper_bounds: np.ndarray
    sampler: str
    seed: int | None = None
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        """Validate the record's internal consistency.

        Raises:
            ValueError: If the arrays are not two-dimensional, disagree on the number of
                solutions, are empty, or if the bounds do not match the number of variables.
        """
        if self.variables.ndim != 2:
            raise ValueError(f"variables must be 2-dimensional, got {self.variables.ndim}")
        if self.objectives.ndim != 2:
            raise ValueError(f"objectives must be 2-dimensional, got {self.objectives.ndim}")
        if self.variables.shape[0] != self.objectives.shape[0]:
            raise ValueError(
                f"variables and objectives disagree on the number of solutions: "
                f"{self.variables.shape[0]} vs {self.objectives.shape[0]}"
            )
        if self.variables.shape[0] == 0:
            raise ValueError("a sample must contain at least one solution")
        if self.lower_bounds.shape != (self.number_of_variables,):
            raise ValueError(
                f"lower_bounds must have shape ({self.number_of_variables},), "
                f"got {self.lower_bounds.shape}"
            )
        if self.upper_bounds.shape != (self.number_of_variables,):
            raise ValueError(
                f"upper_bounds must have shape ({self.number_of_variables},), "
                f"got {self.upper_bounds.shape}"
            )

    @property
    def size(self) -> int:
        """Number of sampled solutions (``n``)."""
        return self.variables.shape[0]

    @property
    def number_of_variables(self) -> int:
        """Number of decision variables (``D``)."""
        return self.variables.shape[1]

    @property
    def number_of_objectives(self) -> int:
        """Number of objectives (``M``)."""
        return self.objectives.shape[1]


def metadata_path_for(csv_path: str | Path) -> Path:
    """Return the sidecar metadata path matching a sample CSV path.

    Args:
        csv_path: Path of the sample CSV file.

    Returns:
        The sidecar JSON path, i.e. the same path with a ``.json`` suffix.
    """
    return Path(csv_path).with_suffix(".json")


def write_sample(sample: Sample, csv_path: str | Path) -> None:
    """Write a sample as a CSV file plus its sidecar metadata JSON.

    The CSV holds columns ``problem, sample_id, x_1..x_D, f_1..f_M``; the metadata JSON, written
    alongside it with a ``.json`` suffix, holds the problem description and provenance.

    Args:
        sample: The sample to write.
        csv_path: Destination path for the CSV file.
    """
    csv_path = Path(csv_path)
    frame = pd.DataFrame(
        {
            "problem": sample.problem,
            "sample_id": np.arange(sample.size),
        }
    )
    for index in range(sample.number_of_variables):
        frame[f"x_{index + 1}"] = sample.variables[:, index]
    for index in range(sample.number_of_objectives):
        frame[f"f_{index + 1}"] = sample.objectives[:, index]
    frame.to_csv(csv_path, index=False)

    metadata = {
        "schema_version": sample.schema_version,
        "problem": sample.problem,
        "number_of_variables": sample.number_of_variables,
        "number_of_objectives": sample.number_of_objectives,
        "lower_bounds": sample.lower_bounds.tolist(),
        "upper_bounds": sample.upper_bounds.tolist(),
        "sample_size": sample.size,
        "sampler": sample.sampler,
        "seed": sample.seed,
    }
    metadata_path_for(csv_path).write_text(json.dumps(metadata, indent=2) + "\n")


def read_sample(csv_path: str | Path) -> Sample:
    """Read a sample written by :func:`write_sample`.

    Args:
        csv_path: Path of the sample CSV file. The sidecar metadata JSON is read from the same
            path with a ``.json`` suffix.

    Returns:
        The reconstructed sample.

    Raises:
        FileNotFoundError: If the sidecar metadata JSON is missing.
        ValueError: If the schema version is unsupported, or if the CSV's columns do not match
            the dimensions declared in the metadata.
    """
    csv_path = Path(csv_path)
    metadata_path = metadata_path_for(csv_path)
    if not metadata_path.is_file():
        raise FileNotFoundError(f"missing sidecar metadata file: {metadata_path}")

    metadata = json.loads(metadata_path.read_text())
    schema_version = metadata["schema_version"]
    if schema_version != SCHEMA_VERSION:
        raise ValueError(
            f"unsupported schema version {schema_version}, this build reads {SCHEMA_VERSION}"
        )

    frame = pd.read_csv(csv_path)
    variable_columns = [f"x_{i + 1}" for i in range(metadata["number_of_variables"])]
    objective_columns = [f"f_{i + 1}" for i in range(metadata["number_of_objectives"])]
    missing = [column for column in variable_columns + objective_columns if column not in frame]
    if missing:
        raise ValueError(f"sample file {csv_path} is missing columns: {missing}")

    return Sample(
        problem=metadata["problem"],
        variables=frame[variable_columns].to_numpy(dtype=float),
        objectives=frame[objective_columns].to_numpy(dtype=float),
        lower_bounds=np.asarray(metadata["lower_bounds"], dtype=float),
        upper_bounds=np.asarray(metadata["upper_bounds"], dtype=float),
        sampler=metadata["sampler"],
        seed=metadata["seed"],
        schema_version=schema_version,
    )
