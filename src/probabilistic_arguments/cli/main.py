# JSON command-line interface for argument analysis and seeded experiments.
from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from fractions import Fraction
from pathlib import Path
from typing import Any

from probabilistic_arguments import __version__
from probabilistic_arguments.catalog.arguments import ARGUMENT_FORMS
from probabilistic_arguments.catalog.scenarios import SCENARIOS, Scenario
from probabilistic_arguments.errors import ProbabilisticArgumentsError
from probabilistic_arguments.inference.bounds import (
    ArgumentAnalysis,
    WeightedWorld,
    analyze_argument,
)
from probabilistic_arguments.logic.formula import Formula, render
from probabilistic_arguments.logic.parser import parse_formula
from probabilistic_arguments.persistence.run_store import save_run
from probabilistic_arguments.probability.statements import ProbabilityStatement, parse_statement
from probabilistic_arguments.simulation.monte_carlo import MAX_SAMPLES, estimate_probability

DEFAULT_SEED = 2026
DEFAULT_SAMPLES = 100_000
MAX_SEED = 2**63 - 1


def _witness_payload(witness: tuple[WeightedWorld, ...]) -> list[dict[str, Any]]:
    return [{"world": world, "probability": str(weight)} for world, weight in witness]


def _analysis_payload(
    premises: Sequence[ProbabilityStatement], conclusion: Formula, analysis: ArgumentAnalysis
) -> dict[str, Any]:
    adams = analysis.adams_lower_bound
    return {
        "premises": [str(premise) for premise in premises],
        "conclusion": render(conclusion),
        "lower": str(analysis.lower),
        "upper": str(analysis.upper),
        "classically_valid": analysis.classically_valid,
        "adams_lower_bound": None if adams is None else str(adams),
        "lower_witness": _witness_payload(analysis.lower_witness),
        "upper_witness": _witness_payload(analysis.upper_witness),
    }


def _run_list(_: argparse.Namespace) -> dict[str, Any]:
    return {
        "arguments": {key: form.title for key, form in ARGUMENT_FORMS.items()},
        "scenarios": {key: scenario.title for key, scenario in SCENARIOS.items()},
    }


def _run_analyze(options: argparse.Namespace) -> dict[str, Any]:
    premises = [parse_statement(source) for source in options.premise]
    conclusion = parse_formula(options.conclusion)
    return _analysis_payload(premises, conclusion, analyze_argument(premises, conclusion))


def _run_argument(options: argparse.Namespace) -> dict[str, Any]:
    form = ARGUMENT_FORMS[options.key]
    analysis = analyze_argument(form.premises, form.conclusion)
    return {"key": form.key, "title": form.title} | _analysis_payload(
        form.premises, form.conclusion, analysis
    )


def _simulate_scenario(scenario: Scenario, options: argparse.Namespace) -> dict[str, Any]:
    exact: Fraction = scenario.network.probability(scenario.query, scenario.evidence)
    estimate = estimate_probability(
        scenario.network,
        scenario.query,
        scenario.evidence,
        options.samples,
        options.seed,
        options.confidence,
    )
    payload: dict[str, Any] = {
        "key": scenario.key,
        "title": scenario.title,
        "claim": scenario.claim,
        "exact": str(exact),
        "exact_decimal": float(exact),
        "estimate": estimate.value,
        "interval": [estimate.interval_low, estimate.interval_high],
        "confidence": estimate.confidence,
        "seed": estimate.seed,
        "samples": estimate.samples,
        "accepted": estimate.accepted,
        "hits": estimate.hits,
        "exact_within_interval": estimate.interval_low <= exact <= estimate.interval_high,
    }
    if options.database is not None:
        payload["run_id"] = save_run(options.database, scenario.key, __version__, estimate, exact)
    return payload


def _run_simulate(options: argparse.Namespace) -> dict[str, Any]:
    keys = list(SCENARIOS) if options.key == "all" else [options.key]
    return {"runs": [_simulate_scenario(SCENARIOS[key], options) for key in keys]}


def _sample_count(text: str) -> int:
    value = int(text)
    if not 0 < value <= MAX_SAMPLES:
        raise argparse.ArgumentTypeError(f"must lie in [1, {MAX_SAMPLES}]")
    return value


def _seed(text: str) -> int:
    value = int(text)
    if not 0 <= value <= MAX_SEED:
        raise argparse.ArgumentTypeError(f"must lie in [0, {MAX_SEED}]")
    return value


def _confidence(text: str) -> float:
    value = float(text)
    if not 0 < value < 1:
        raise argparse.ArgumentTypeError("must lie in (0, 1)")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="probabilistic-arguments",
        description="Evaluate logical arguments about probabilities, exactly and experimentally.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)

    list_command = commands.add_parser("list", help="list built-in arguments and scenarios")
    list_command.set_defaults(handler=_run_list)

    analyze = commands.add_parser("analyze", help="compute tight bounds for a custom argument")
    analyze.add_argument("--premise", action="append", default=[], metavar="STATEMENT")
    analyze.add_argument("--conclusion", required=True, metavar="FORMULA")
    analyze.set_defaults(handler=_run_analyze)

    argument = commands.add_parser("argument", help="analyze a built-in argument form")
    argument.add_argument("key", choices=sorted(ARGUMENT_FORMS))
    argument.set_defaults(handler=_run_argument)

    simulate = commands.add_parser("simulate", help="run a seeded Monte Carlo experiment")
    simulate.add_argument("key", choices=[*sorted(SCENARIOS), "all"])
    simulate.add_argument("--samples", type=_sample_count, default=DEFAULT_SAMPLES)
    simulate.add_argument("--seed", type=_seed, default=DEFAULT_SEED)
    simulate.add_argument("--confidence", type=_confidence, default=0.95)
    simulate.add_argument("--database", type=Path, default=None)
    simulate.set_defaults(handler=_run_simulate)
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    options = build_parser().parse_args(arguments)
    try:
        result = options.handler(options)
    except ProbabilisticArgumentsError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0
