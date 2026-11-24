# Property-based soundness, tightness and closed-form checks for argument bounds.
from fractions import Fraction

from hypothesis import given, settings
from hypothesis import strategies as st

from probabilistic_arguments.errors import InconsistentPremisesError
from probabilistic_arguments.inference.bounds import analyze_argument
from probabilistic_arguments.logic.formula import (
    Biconditional,
    Conjunction,
    Disjunction,
    Formula,
    Implication,
    Negation,
    Variable,
    enumerate_worlds,
)
from probabilistic_arguments.logic.parser import parse_formula
from probabilistic_arguments.probability.statements import ProbabilityStatement

NAMES = ("A", "B", "C")
WORLDS = list(enumerate_worlds(NAMES))

probabilities = st.fractions(min_value=0, max_value=1, max_denominator=20)
formulas = st.recursive(
    st.sampled_from([Variable(name) for name in NAMES]),
    lambda children: st.one_of(
        children.map(Negation),
        st.builds(Conjunction, children, children),
        st.builds(Disjunction, children, children),
        st.builds(Implication, children, children),
        st.builds(Biconditional, children, children),
    ),
    max_leaves=6,
)
distributions = (
    st.lists(st.integers(min_value=0, max_value=20), min_size=len(WORLDS), max_size=len(WORLDS))
    .filter(any)
    .map(lambda weights: [Fraction(weight, sum(weights)) for weight in weights])
)


def measure(formula: Formula, distribution: list[Fraction]) -> Fraction:
    return sum(
        (
            weight
            for world, weight in zip(WORLDS, distribution, strict=True)
            if formula.evaluate(world)
        ),
        Fraction(0),
    )


def witness_measure(formula: Formula, witness) -> Fraction:
    return sum(
        (weight for world, weight in witness if formula.evaluate(world)),
        Fraction(0),
    )


@settings(max_examples=60)
@given(probabilities, probabilities)
def test_modus_ponens_matches_closed_form(antecedent, implication):
    if antecedent + implication < 1:
        return
    premises = [
        ProbabilityStatement(Variable("A"), antecedent, antecedent),
        ProbabilityStatement(parse_formula("A -> B"), implication, implication),
    ]
    analysis = analyze_argument(premises, Variable("B"))
    assert analysis.lower == antecedent + implication - 1
    assert analysis.upper == implication


@settings(max_examples=60)
@given(probabilities, probabilities)
def test_conditional_modus_ponens_matches_closed_form(antecedent, conditional):
    premises = [
        ProbabilityStatement(Variable("A"), antecedent, antecedent),
        ProbabilityStatement(Variable("B"), conditional, conditional, Variable("A")),
    ]
    analysis = analyze_argument(premises, Variable("B"))
    assert analysis.lower == antecedent * conditional
    assert analysis.upper == antecedent * conditional + 1 - antecedent


@settings(max_examples=80)
@given(distributions, st.lists(formulas, min_size=1, max_size=3), formulas)
def test_true_probability_lies_within_bounds(distribution, premise_formulas, conclusion):
    premises = [
        ProbabilityStatement(formula, value, value)
        for formula in premise_formulas
        for value in [measure(formula, distribution)]
    ]
    analysis = analyze_argument(premises, conclusion)
    assert analysis.lower <= measure(conclusion, distribution) <= analysis.upper


@settings(max_examples=60)
@given(distributions, st.lists(formulas, min_size=1, max_size=3), formulas)
def test_witnesses_satisfy_premises_and_attain_bounds(distribution, premise_formulas, conclusion):
    premises = [
        ProbabilityStatement(formula, value, value)
        for formula in premise_formulas
        for value in [measure(formula, distribution)]
    ]
    analysis = analyze_argument(premises, conclusion)
    for witness, bound in (
        (analysis.lower_witness, analysis.lower),
        (analysis.upper_witness, analysis.upper),
    ):
        assert sum((weight for _, weight in witness), Fraction(0)) == 1
        assert all(weight > 0 for _, weight in witness)
        assert witness_measure(conclusion, witness) == bound
        for premise in premises:
            assert witness_measure(premise.formula, witness) == premise.lower


@settings(max_examples=60)
@given(st.lists(st.tuples(formulas, probabilities), min_size=1, max_size=3), formulas)
def test_adams_bound_never_exceeds_tight_lower_bound(raw_premises, conclusion):
    premises = [ProbabilityStatement(formula, value, value) for formula, value in raw_premises]
    try:
        analysis = analyze_argument(premises, conclusion)
    except InconsistentPremisesError:
        return
    if analysis.classically_valid:
        assert analysis.adams_lower_bound is not None
        assert analysis.adams_lower_bound <= analysis.lower


@settings(max_examples=60)
@given(formulas, formulas)
def test_probability_bounds_stay_in_unit_interval(premise_formula, conclusion):
    premises = [ProbabilityStatement(premise_formula, Fraction(1, 2), Fraction(1, 2))]
    try:
        analysis = analyze_argument(premises, conclusion)
    except InconsistentPremisesError:
        return
    assert 0 <= analysis.lower <= analysis.upper <= 1


@settings(max_examples=100)
@given(formulas)
def test_rendered_formula_round_trips_semantically(formula):
    reparsed = parse_formula(str(formula))
    assert all(reparsed.evaluate(world) == formula.evaluate(world) for world in WORLDS)


@settings(max_examples=60)
@given(distributions, formulas, formulas, formulas, probabilities)
def test_conditional_interval_premises_are_sound(distribution, formula, condition, target, slack):
    condition_mass = measure(condition, distribution)
    if condition_mass == 0:
        return
    value = measure(Conjunction(formula, condition), distribution) / condition_mass
    lower = max(Fraction(0), value - slack)
    upper = min(Fraction(1), value + slack)
    analysis = analyze_argument([ProbabilityStatement(formula, lower, upper, condition)], target)
    assert analysis.lower <= measure(target, distribution) <= analysis.upper
