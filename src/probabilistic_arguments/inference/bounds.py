# Tight conclusion bounds for probabilistic arguments via exact linear programming.
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from fractions import Fraction

from probabilistic_arguments.errors import InconsistentPremisesError, ModelError
from probabilistic_arguments.logic.formula import Formula, enumerate_worlds
from probabilistic_arguments.optimization.simplex import (
    ONE,
    ZERO,
    InfeasibleProgramError,
    minimize,
)
from probabilistic_arguments.probability.statements import ProbabilityStatement

MAX_VARIABLES = 10

WeightedWorld = tuple[dict[str, bool], Fraction]


@dataclass(frozen=True, slots=True)
class ArgumentAnalysis:
    lower: Fraction
    upper: Fraction
    classically_valid: bool | None
    adams_lower_bound: Fraction | None
    lower_witness: tuple[WeightedWorld, ...]
    upper_witness: tuple[WeightedWorld, ...]


def _indicator(formula: Formula, world: dict[str, bool]) -> Fraction:
    return ONE if formula.evaluate(world) else ZERO


def _statement_coefficients(
    statement: ProbabilityStatement, worlds: list[dict[str, bool]], bound: Fraction
) -> list[Fraction]:
    if statement.condition is None:
        return [_indicator(statement.formula, world) for world in worlds]
    condition = statement.condition
    return [
        _indicator(statement.formula, world) * _indicator(condition, world)
        - bound * _indicator(condition, world)
        for world in worlds
    ]


def _build_constraints(
    premises: Sequence[ProbabilityStatement], worlds: list[dict[str, bool]]
) -> tuple[list[list[Fraction]], list[Fraction], int]:
    interval_count = sum(2 for premise in premises if premise.lower != premise.upper)
    slack_total = interval_count
    rows: list[list[Fraction]] = [[ONE] * len(worlds) + [ZERO] * slack_total]
    rhs: list[Fraction] = [ONE]
    slack_index = 0

    def append_row(coefficients: list[Fraction], target: Fraction, slack_sign: int) -> None:
        nonlocal slack_index
        slacks = [ZERO] * slack_total
        if slack_sign:
            slacks[slack_index] = Fraction(slack_sign)
            slack_index += 1
        rows.append(coefficients + slacks)
        rhs.append(target)

    for premise in premises:
        lower_target = ZERO if premise.condition is not None else premise.lower
        upper_target = ZERO if premise.condition is not None else premise.upper
        lower_row = _statement_coefficients(premise, worlds, premise.lower)
        if premise.lower == premise.upper:
            append_row(lower_row, lower_target, 0)
            continue
        append_row(lower_row, lower_target, -1)
        append_row(_statement_coefficients(premise, worlds, premise.upper), upper_target, 1)
    return rows, rhs, slack_total


def _witness(
    point: tuple[Fraction, ...], worlds: list[dict[str, bool]]
) -> tuple[WeightedWorld, ...]:
    return tuple(
        (world, weight) for world, weight in zip(worlds, point, strict=False) if weight != ZERO
    )


def _is_classically_valid(
    premises: Sequence[ProbabilityStatement], conclusion: Formula, worlds: list[dict[str, bool]]
) -> bool | None:
    if any(premise.condition is not None for premise in premises):
        return None
    return all(
        conclusion.evaluate(world)
        for world in worlds
        if all(premise.formula.evaluate(world) for premise in premises)
    )


def analyze_argument(
    premises: Sequence[ProbabilityStatement], conclusion: Formula
) -> ArgumentAnalysis:
    names = sorted(conclusion.variables().union(*(p.variables() for p in premises)))
    if len(names) > MAX_VARIABLES:
        raise ModelError(f"argument uses more than {MAX_VARIABLES} variables")
    worlds = list(enumerate_worlds(tuple(names)))
    rows, rhs, slack_total = _build_constraints(premises, worlds)
    objective = [_indicator(conclusion, world) for world in worlds]
    try:
        low = minimize(objective + [ZERO] * slack_total, rows, rhs)
        high = minimize([-entry for entry in objective] + [ZERO] * slack_total, rows, rhs)
    except InfeasibleProgramError as error:
        raise InconsistentPremisesError("no distribution satisfies the premises") from error
    classically_valid = _is_classically_valid(premises, conclusion, worlds)
    adams = None
    if classically_valid:
        total_uncertainty = sum((ONE - premise.lower for premise in premises), ZERO)
        adams = max(ZERO, ONE - total_uncertainty)
    return ArgumentAnalysis(
        lower=low.value,
        upper=-high.value,
        classically_valid=classically_valid,
        adams_lower_bound=adams,
        lower_witness=_witness(low.point, worlds),
        upper_witness=_witness(high.point, worlds),
    )
