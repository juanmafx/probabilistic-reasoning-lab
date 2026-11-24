# Argument bounds checked against hand-derived closed forms.
from fractions import Fraction as F

import pytest

from probabilistic_arguments.catalog.arguments import ARGUMENT_FORMS
from probabilistic_arguments.errors import InconsistentPremisesError, ModelError
from probabilistic_arguments.inference.bounds import MAX_PREMISES, analyze_argument
from probabilistic_arguments.logic.parser import parse_formula
from probabilistic_arguments.probability.statements import parse_statement


@pytest.mark.parametrize(
    ("key", "lower", "upper", "valid"),
    [
        ("modus_ponens", F(7, 10), F(4, 5), True),
        ("modus_tollens", F(7, 10), F(9, 10), True),
        ("hypothetical_syllogism", F(4, 5), F(1), True),
        ("conditional_modus_ponens", F(18, 25), F(82, 100), None),
        ("conjunction_rule", F(1, 5), F(3, 10), True),
        ("affirming_the_consequent", F(1, 10), F(9, 10), False),
        ("denying_the_antecedent", F(1, 10), F(9, 10), False),
    ],
)
def test_catalog_bounds(key, lower, upper, valid):
    form = ARGUMENT_FORMS[key]
    analysis = analyze_argument(form.premises, form.conclusion)
    assert (analysis.lower, analysis.upper) == (lower, upper)
    assert analysis.classically_valid is valid


def test_interval_premise_widens_bounds():
    premises = [parse_statement("P(A) in [1/2, 3/4]"), parse_statement("P(A -> B) = 9/10")]
    analysis = analyze_argument(premises, parse_formula("B"))
    assert (analysis.lower, analysis.upper) == (F(2, 5), F(9, 10))


def test_conditional_interval_premise():
    premises = [parse_statement("P(A) = 1/2"), parse_statement("P(B given A) in [1/2, 3/4]")]
    analysis = analyze_argument(premises, parse_formula("B"))
    assert (analysis.lower, analysis.upper) == (F(1, 4), F(7, 8))


def test_no_premises_gives_trivial_bounds():
    analysis = analyze_argument([], parse_formula("A"))
    assert (analysis.lower, analysis.upper) == (0, 1)


def test_tautology_has_probability_one():
    analysis = analyze_argument([], parse_formula("A | !A"))
    assert (analysis.lower, analysis.upper) == (1, 1)


def test_inconsistent_premises_are_rejected():
    premises = [parse_statement("P(A) = 1/4"), parse_statement("P(!A) = 1/4")]
    with pytest.raises(InconsistentPremisesError):
        analyze_argument(premises, parse_formula("A"))


def test_rejects_too_many_variables():
    names = " & ".join(f"V{index}" for index in range(11))
    with pytest.raises(ModelError):
        analyze_argument([], parse_formula(names))


def test_rejects_too_many_premises():
    premises = [parse_statement("P(A) = 1/2")] * (MAX_PREMISES + 1)
    with pytest.raises(ModelError):
        analyze_argument(premises, parse_formula("A"))


def test_accepts_premises_at_the_limit():
    premises = [parse_statement("P(A) = 1/2")] * MAX_PREMISES
    assert analyze_argument(premises, parse_formula("A")).lower == F(1, 2)
