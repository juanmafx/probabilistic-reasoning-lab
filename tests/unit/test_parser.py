# Parser grammar, precedence and input-limit tests.
import pytest

from probabilistic_arguments.errors import FormulaSyntaxError
from probabilistic_arguments.logic.formula import (
    Conjunction,
    Disjunction,
    Implication,
    Negation,
    Variable,
)
from probabilistic_arguments.logic.parser import MAX_FORMULA_LENGTH, parse_formula

A, B, C = Variable("A"), Variable("B"), Variable("C")


def test_conjunction_binds_tighter_than_disjunction():
    assert parse_formula("A | B & C") == Disjunction(A, Conjunction(B, C))


def test_implication_is_right_associative():
    assert parse_formula("A -> B -> C") == Implication(A, Implication(B, C))


def test_negation_binds_tightest():
    assert parse_formula("!A & B") == Conjunction(Negation(A), B)


def test_keyword_operators_match_symbols():
    assert parse_formula("not A and B or C") == parse_formula("!A & B | C")


@pytest.mark.parametrize(
    "source",
    ["", "   ", "A &", "(A", "A)", "A B", "-> A", "A $ B", "given", "__import__('os')", "A; B"],
)
def test_rejects_malformed_formulas(source):
    with pytest.raises(FormulaSyntaxError):
        parse_formula(source)


def test_rejects_oversized_formula():
    with pytest.raises(FormulaSyntaxError):
        parse_formula("A" * (MAX_FORMULA_LENGTH + 1))


@pytest.mark.parametrize("source", ["!" * 100 + "A", "(" * 100 + "A" + ")" * 100])
def test_rejects_excessive_nesting_without_recursion_error(source):
    with pytest.raises(FormulaSyntaxError):
        parse_formula(source)
