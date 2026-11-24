# Probability value and statement parsing tests.
from fractions import Fraction

import pytest

from probabilistic_arguments.errors import (
    FormulaSyntaxError,
    InvalidProbabilityError,
    ProbabilisticArgumentsError,
)
from probabilistic_arguments.logic.formula import Variable
from probabilistic_arguments.probability.exact import parse_probability
from probabilistic_arguments.probability.statements import parse_statement


@pytest.mark.parametrize(
    ("text", "expected"),
    [("0", 0), ("1", 1), ("0.25", Fraction(1, 4)), (".5", Fraction(1, 2)), ("3/4", Fraction(3, 4))],
)
def test_parses_exact_values(text, expected):
    assert parse_probability(text) == expected


@pytest.mark.parametrize(
    "value",
    [
        "1.5",
        "-0.1",
        "nan",
        "inf",
        "1e999999",
        "2/1",
        "1/0",
        "abc",
        "",
        True,
        0.5,
        2,
        "0.\u0665",
        "\u0663/\u0664",
        "\u0663/4",
    ],
)
def test_rejects_invalid_values(value):
    with pytest.raises(InvalidProbabilityError):
        parse_probability(value)


def test_parses_point_statement():
    statement = parse_statement("P(A -> B) = 4/5")
    assert (statement.lower, statement.upper) == (Fraction(4, 5), Fraction(4, 5))
    assert statement.condition is None


def test_parses_conditional_interval_statement():
    statement = parse_statement("P(B given A) in [0.5, 3/4]")
    assert statement.formula == Variable("B")
    assert statement.condition == Variable("A")
    assert (statement.lower, statement.upper) == (Fraction(1, 2), Fraction(3, 4))


def test_disjunction_inside_statement_is_not_a_condition():
    assert parse_statement("P(A | B) = 1/2").condition is None


@pytest.mark.parametrize(
    "source",
    [
        "A = 1",
        "P(A)",
        "P(A) = 2",
        "P(A) in [0.9, 0.1]",
        "P(A given B given C) = 1/2",
        "P() = 1",
        "P(A) = 1; DROP TABLE x",
        "P(" + "A" * 400 + ") = 1",
    ],
)
def test_rejects_invalid_statements(source):
    with pytest.raises((FormulaSyntaxError, ProbabilisticArgumentsError)):
        parse_statement(source)
