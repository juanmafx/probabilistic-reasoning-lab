# Exact simplex solver tests, including degenerate and redundant programs.
from fractions import Fraction as F

import pytest

from probabilistic_arguments.optimization.simplex import (
    InfeasibleProgramError,
    UnboundedProgramError,
    minimize,
)


def test_solves_simple_program():
    solution = minimize([F(1), F(2)], [[F(1), F(1)]], [F(1)])
    assert solution.value == 1
    assert solution.point == (1, 0)


def test_handles_negative_right_hand_side():
    solution = minimize([F(1), F(1)], [[F(-1), F(-1)]], [F(-3)])
    assert solution.value == 3


def test_handles_redundant_rows():
    rows = [[F(1), F(1)], [F(2), F(2)]]
    assert minimize([F(0), F(1)], rows, [F(1), F(2)]).value == 0


def test_detects_infeasible_program():
    with pytest.raises(InfeasibleProgramError):
        minimize([F(1), F(1)], [[F(1), F(1)], [F(1), F(1)]], [F(1), F(2)])


def test_detects_unbounded_program():
    with pytest.raises(UnboundedProgramError):
        minimize([F(-1), F(0)], [[F(1), F(-1)]], [F(0)])


def test_terminates_on_beale_cycling_example():
    costs = [F(-3, 4), F(20), F(-1, 2), F(6), F(0), F(0), F(0)]
    rows = [
        [F(1, 4), F(-8), F(-1), F(9), F(1), F(0), F(0)],
        [F(1, 2), F(-12), F(-1, 2), F(3), F(0), F(1), F(0)],
        [F(0), F(0), F(1), F(0), F(0), F(0), F(1)],
    ]
    assert minimize(costs, rows, [F(0), F(0), F(1)]).value == F(-5, 4)
