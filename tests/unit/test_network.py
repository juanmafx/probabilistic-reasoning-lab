# Bayesian network validation and exact posterior tests.
from fractions import Fraction as F

import pytest

from probabilistic_arguments.catalog.scenarios import SCENARIOS
from probabilistic_arguments.errors import ModelError
from probabilistic_arguments.inference.network import BayesianNetwork, Node
from probabilistic_arguments.logic.parser import parse_formula


@pytest.mark.parametrize(
    ("key", "expected"),
    [
        ("base_rate", F(19, 118)),
        ("repeated_testing", F(361, 460)),
        ("wet_grass_rain", F(309, 629)),
        ("explaining_away", F(99, 419)),
    ],
)
def test_scenario_posteriors(key, expected):
    scenario = SCENARIOS[key]
    assert scenario.network.probability(scenario.query, scenario.evidence) == expected


def test_explaining_away_lowers_posterior():
    wet = SCENARIOS["wet_grass_rain"]
    explained = SCENARIOS["explaining_away"]
    assert explained.network.probability(explained.query, explained.evidence) < (
        wet.network.probability(wet.query, wet.evidence)
    )


def test_rejects_parent_declared_after_child():
    child = Node("child", ("parent",), {(True,): F(1), (False,): F(0)})
    with pytest.raises(ModelError):
        BayesianNetwork((child, Node("parent", (), {(): F(1, 2)})))


def test_rejects_incomplete_table():
    parent = Node("parent", (), {(): F(1, 2)})
    with pytest.raises(ModelError):
        BayesianNetwork((parent, Node("child", ("parent",), {(True,): F(1)})))


def test_rejects_out_of_range_probability():
    with pytest.raises(ModelError):
        BayesianNetwork((Node("node", (), {(): F(3, 2)}),))


def test_rejects_duplicate_node():
    node = Node("node", (), {(): F(1, 2)})
    with pytest.raises(ModelError):
        BayesianNetwork((node, node))


def test_rejects_zero_probability_evidence():
    network = BayesianNetwork((Node("node", (), {(): F(0)}),))
    with pytest.raises(ModelError):
        network.probability(parse_formula("node"), parse_formula("node"))


def test_rejects_unknown_variable():
    network = BayesianNetwork((Node("node", (), {(): F(1, 2)}),))
    with pytest.raises(ModelError):
        network.probability(parse_formula("missing"))
