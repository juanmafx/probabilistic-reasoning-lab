# Parameterized persistence of simulation runs into a database created from db/schema.sql.
from __future__ import annotations

import sqlite3
from collections.abc import Sequence
from contextlib import closing
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

from probabilistic_arguments.errors import StorageError
from probabilistic_arguments.simulation.monte_carlo import Estimate

_INSERT_RUN = """
INSERT INTO simulation_runs (
    scenario_key, package_version, seed, samples, accepted, hits,
    estimate, interval_low, interval_high, confidence, exact_probability
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


@dataclass(frozen=True, slots=True)
class RunRecord:
    scenario_key: str
    estimate: Estimate
    exact: Fraction


def _parameters(run: RunRecord, package_version: str) -> tuple[str | int | float, ...]:
    estimate = run.estimate
    return (
        run.scenario_key,
        package_version,
        estimate.seed,
        estimate.samples,
        estimate.accepted,
        estimate.hits,
        estimate.value,
        estimate.interval_low,
        estimate.interval_high,
        estimate.confidence,
        str(run.exact),
    )


def save_runs(database: Path, package_version: str, runs: Sequence[RunRecord]) -> list[int]:
    uri = f"{database.resolve().as_uri()}?mode=rw"
    run_ids: list[int] = []
    try:
        with closing(sqlite3.connect(uri, uri=True)) as connection, connection:
            for run in runs:
                row_id = connection.execute(
                    _INSERT_RUN, _parameters(run, package_version)
                ).lastrowid
                if row_id is None:
                    raise StorageError("database did not return a run id")
                run_ids.append(row_id)
    except sqlite3.Error as error:
        raise StorageError("could not store the runs; apply db/schema.sql first") from error
    return run_ids
