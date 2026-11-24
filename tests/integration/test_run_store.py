# Transactional behavior of the optional SQLite run store.
import sqlite3
from contextlib import closing
from fractions import Fraction
from pathlib import Path

import pytest

from probabilistic_arguments.errors import StorageError
from probabilistic_arguments.persistence.run_store import RunRecord, save_runs
from probabilistic_arguments.simulation.monte_carlo import Estimate

SCHEMA = Path(__file__).resolve().parents[2] / "db" / "schema.sql"
VALID = Estimate(1, 10, 5, 2, 0.4, 0.1, 0.8, 0.95)
IMPOSSIBLE = Estimate(1, 10, 5, 6, 0.4, 0.1, 0.8, 0.95)


@pytest.fixture
def database(tmp_path):
    path = tmp_path / "runs.sqlite3"
    with closing(sqlite3.connect(path)) as connection:
        connection.executescript(SCHEMA.read_text(encoding="utf-8"))
    return path


def stored_count(database):
    with closing(sqlite3.connect(database)) as connection:
        return connection.execute("SELECT COUNT(*) FROM simulation_runs").fetchone()[0]


def test_saves_all_runs_in_order(database):
    records = [RunRecord("first", VALID, Fraction(1, 2)), RunRecord("second", VALID, Fraction(1))]
    run_ids = save_runs(database, "1.0.0", records)
    assert len(run_ids) == 2
    with closing(sqlite3.connect(database)) as connection:
        rows = connection.execute(
            "SELECT id, scenario_key FROM simulation_runs ORDER BY id"
        ).fetchall()
    assert rows == [(run_ids[0], "first"), (run_ids[1], "second")]


def test_rejected_run_rolls_back_the_whole_batch(database):
    records = [
        RunRecord("valid", VALID, Fraction(1, 2)),
        RunRecord("impossible", IMPOSSIBLE, Fraction(1, 2)),
    ]
    with pytest.raises(StorageError):
        save_runs(database, "1.0.0", records)
    assert stored_count(database) == 0


def test_hostile_scenario_key_is_stored_as_data(database):
    key = "x'); DROP TABLE simulation_runs; --"
    save_runs(database, "1.0.0", [RunRecord(key, VALID, Fraction(1, 2))])
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("SELECT scenario_key FROM simulation_runs").fetchone() == (key,)


def test_path_with_uri_characters_is_not_reinterpreted(tmp_path):
    path = tmp_path / "runs?mode=memory#x.sqlite3"
    with closing(sqlite3.connect(path)) as connection:
        connection.executescript(SCHEMA.read_text(encoding="utf-8"))
    save_runs(path, "1.0.0", [RunRecord("key", VALID, Fraction(1, 2))])
    assert stored_count(path) == 1
