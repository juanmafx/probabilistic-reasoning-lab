# Illustrative probability scenarios; every parameter is a teaching value, not real data.
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from probabilistic_arguments.inference.network import BayesianNetwork, Node
from probabilistic_arguments.logic.formula import Formula
from probabilistic_arguments.logic.parser import parse_formula


@dataclass(frozen=True, slots=True)
class Scenario:
    key: str
    title: str
    claim: str
    network: BayesianNetwork
    query: Formula
    evidence: Formula | None


def _root(name: str, probability: Fraction) -> Node:
    return Node(name, (), {(): probability})


def _screening_test(name: str) -> Node:
    return Node(name, ("condition",), {(True,): Fraction(95, 100), (False,): Fraction(5, 100)})


_SCREENING = BayesianNetwork((_root("condition", Fraction(1, 100)), _screening_test("test")))
_REPEATED_SCREENING = BayesianNetwork(
    (
        _root("condition", Fraction(1, 100)),
        _screening_test("first_test"),
        _screening_test("second_test"),
    )
)
_WET_GRASS = BayesianNetwork(
    (
        _root("rain", Fraction(1, 5)),
        _root("sprinkler", Fraction(3, 10)),
        Node(
            "wet_grass",
            ("rain", "sprinkler"),
            {
                (True, True): Fraction(99, 100),
                (True, False): Fraction(9, 10),
                (False, True): Fraction(4, 5),
                (False, False): Fraction(0),
            },
        ),
    )
)

SCENARIOS: dict[str, Scenario] = {
    scenario.key: scenario
    for scenario in (
        Scenario(
            "base_rate",
            "Base-rate neglect",
            "A 95% accurate test on a 1% prevalence condition yields a low posterior.",
            _SCREENING,
            parse_formula("condition"),
            parse_formula("test"),
        ),
        Scenario(
            "repeated_testing",
            "Two conditionally independent positive tests",
            "A second independent positive result raises the posterior sharply.",
            _REPEATED_SCREENING,
            parse_formula("condition"),
            parse_formula("first_test & second_test"),
        ),
        Scenario(
            "wet_grass_rain",
            "Diagnostic reasoning",
            "Observing wet grass raises the probability of rain above its prior.",
            _WET_GRASS,
            parse_formula("rain"),
            parse_formula("wet_grass"),
        ),
        Scenario(
            "explaining_away",
            "Explaining away",
            "Learning the sprinkler ran lowers the probability of rain given wet grass.",
            _WET_GRASS,
            parse_formula("rain"),
            parse_formula("wet_grass & sprinkler"),
        ),
    )
}
