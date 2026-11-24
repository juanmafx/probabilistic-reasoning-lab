# Parameterized persistence of simulation runs into a database created from db/schema.sql.
from __future__ import annotations

import sqlite3
from contextlib import closing
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


def save_run(
    database: Path, scenario_key: str, package_version: str, estimate: Estimate, exact: Fraction
) -> int:
    uri = f"{database.resolve().as_uri()}?mode=rw"
    parameters = (
        scenario_key,
        package_version,
        estimate.seed,
        estimate.samples,
        estimate.accepted,
        estimate.hits,
        estimate.value,
        estimate.interval_low,
        estimate.interval_high,
        estimate.confidence,
        str(exact),
    )
    try:
        with closing(sqlite3.connect(uri, uri=True)) as connection, connection:
            connection.execute("PRAGMA foreign_keys = ON")
            cursor = connection.execute(_INSERT_RUN, parameters)
            row_id = cursor.lastrowid
    except sqlite3.Error as error:
        raise StorageError("could not store the run; apply db/schema.sql first") from error
    if row_id is None:
        raise StorageError("database did not return a run id")
    return row_id
