# End-to-end CLI and optional SQLite persistence tests.
import json
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from probabilistic_arguments.catalog.arguments import ARGUMENT_FORMS
from probabilistic_arguments.catalog.scenarios import SCENARIOS
from probabilistic_arguments.cli.main import main

SCHEMA = Path(__file__).resolve().parents[2] / "db" / "schema.sql"


def run_json(capsys, *arguments):
    assert main(list(arguments)) == 0
    return json.loads(capsys.readouterr().out)


@pytest.fixture
def database(tmp_path):
    path = tmp_path / "runs.sqlite3"
    with closing(sqlite3.connect(path)) as connection:
        connection.executescript(SCHEMA.read_text(encoding="utf-8"))
    return path


def test_list_reports_catalog(capsys):
    payload = run_json(capsys, "list")
    assert set(payload["arguments"]) == set(ARGUMENT_FORMS)
    assert set(payload["scenarios"]) == set(SCENARIOS)


def test_analyze_custom_argument(capsys):
    payload = run_json(
        capsys,
        "analyze",
        "--premise",
        "P(A) = 0.9",
        "--premise",
        "P(A -> B) = 0.8",
        "--conclusion",
        "B",
    )
    assert (payload["lower"], payload["upper"]) == ("7/10", "4/5")
    assert payload["classically_valid"] is True


@pytest.mark.parametrize("key", sorted(ARGUMENT_FORMS))
def test_every_builtin_argument_runs(capsys, key):
    assert run_json(capsys, "argument", key)["key"] == key


def test_simulate_all_is_reproducible(capsys):
    arguments = ("simulate", "all", "--samples", "2000", "--seed", "11")
    assert run_json(capsys, *arguments) == run_json(capsys, *arguments)


def test_simulation_persists_run(capsys, database):
    payload = run_json(
        capsys, "simulate", "base_rate", "--samples", "5000", "--database", str(database)
    )
    run = payload["runs"][0]
    with closing(sqlite3.connect(database)) as connection:
        row = connection.execute(
            "SELECT scenario_key, seed, hits, exact_probability FROM simulation_runs WHERE id = ?",
            (run["run_id"],),
        ).fetchone()
    assert row == ("base_rate", 2026, run["hits"], "19/118")


def test_schema_rejects_impossible_counts(database):
    statement = (
        "INSERT INTO simulation_runs (scenario_key, package_version, seed, samples, accepted, "
        "hits, estimate, interval_low, interval_high, confidence, exact_probability) "
        "VALUES ('x', '1', 1, 10, 5, 6, 0.5, 0.1, 0.9, 0.95, '1/2')"
    )
    with closing(sqlite3.connect(database)) as connection, pytest.raises(sqlite3.IntegrityError):
        connection.execute(statement)


def test_missing_database_is_not_created(capsys, tmp_path):
    missing = tmp_path / "missing.sqlite3"
    code = main(["simulate", "base_rate", "--samples", "2000", "--database", str(missing)])
    assert code == 2
    assert not missing.exists()
    assert "schema" in capsys.readouterr().err


def test_inconsistent_premises_exit_cleanly(capsys):
    code = main(
        ["analyze", "--premise", "P(A) = 1/4", "--premise", "P(!A) = 1/4", "--conclusion", "A"]
    )
    assert code == 2
    assert "no distribution" in capsys.readouterr().err


def test_malicious_formula_is_rejected_without_evaluation(capsys):
    code = main(["analyze", "--conclusion", "__import__('os').system('true')"])
    assert code == 2
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("seed", ["-1", str(2**63), "abc"])
def test_rejects_out_of_range_seed(capsys, seed):
    with pytest.raises(SystemExit) as failure:
        main(["simulate", "base_rate", f"--seed={seed}"])
    assert failure.value.code == 2
    capsys.readouterr()


def test_renders_statements_without_redundant_parentheses(capsys):
    payload = run_json(capsys, "argument", "modus_ponens")
    assert payload["premises"] == ["P(A) = 9/10", "P(A -> B) = 4/5"]
