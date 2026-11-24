# Two-phase primal simplex over exact rationals, using Bland's anti-cycling rule.
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from fractions import Fraction

ZERO = Fraction(0)
ONE = Fraction(1)


class InfeasibleProgramError(ValueError):
    pass


class UnboundedProgramError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class Solution:
    value: Fraction
    point: tuple[Fraction, ...]


def _pivot(tableau: list[list[Fraction]], basis: list[int], row: int, column: int) -> None:
    pivot_value = tableau[row][column]
    pivot_row = [entry / pivot_value for entry in tableau[row]]
    tableau[row] = pivot_row
    for index, current in enumerate(tableau):
        factor = current[column]
        if index != row and factor != ZERO:
            tableau[index] = [
                entry - factor * pivot_entry
                for entry, pivot_entry in zip(current, pivot_row, strict=True)
            ]
    basis[row] = column


def _entering_column(
    tableau: list[list[Fraction]], basis: list[int], costs: Sequence[Fraction], limit: int
) -> int | None:
    priced = [(row, costs[base]) for row, base in zip(tableau, basis, strict=True) if costs[base]]
    for column in range(limit):
        reduced = costs[column] - sum((cost * row[column] for row, cost in priced), ZERO)
        if reduced < ZERO:
            return column
    return None


def _leaving_row(tableau: list[list[Fraction]], basis: list[int], column: int) -> int | None:
    best: tuple[Fraction, int, int] | None = None
    for index, row in enumerate(tableau):
        if row[column] > ZERO:
            candidate = (row[-1] / row[column], basis[index], index)
            if best is None or candidate < best:
                best = candidate
    return None if best is None else best[2]


def _optimize(
    tableau: list[list[Fraction]], basis: list[int], costs: Sequence[Fraction], limit: int
) -> None:
    while (column := _entering_column(tableau, basis, costs, limit)) is not None:
        row = _leaving_row(tableau, basis, column)
        if row is None:
            raise UnboundedProgramError("objective is unbounded")
        _pivot(tableau, basis, row, column)


def minimize(
    costs: Sequence[Fraction], rows: Sequence[Sequence[Fraction]], rhs: Sequence[Fraction]
) -> Solution:
    width = len(costs)
    height = len(rows)
    tableau: list[list[Fraction]] = []
    for index, (row, target) in enumerate(zip(rows, rhs, strict=True)):
        sign = -1 if target < ZERO else 1
        identity = [ONE if index == offset else ZERO for offset in range(height)]
        tableau.append([sign * entry for entry in row] + identity + [sign * target])
    basis = [width + offset for offset in range(height)]
    _optimize(tableau, basis, [ZERO] * width + [ONE] * height, width)
    residual = sum(
        (row[-1] for row, base in zip(tableau, basis, strict=True) if base >= width), ZERO
    )
    if residual != ZERO:
        raise InfeasibleProgramError("constraints are infeasible")
    redundant: set[int] = set()
    for index in range(height):
        if basis[index] < width:
            continue
        column = next((j for j in range(width) if tableau[index][j] != ZERO), None)
        if column is None:
            redundant.add(index)
        else:
            _pivot(tableau, basis, index, column)
    reduced = [
        [*tableau[index][:width], tableau[index][-1]]
        for index in range(height)
        if index not in redundant
    ]
    reduced_basis = [basis[index] for index in range(height) if index not in redundant]
    _optimize(reduced, reduced_basis, costs, width)
    point = [ZERO] * width
    for row, base in zip(reduced, reduced_basis, strict=True):
        point[base] = row[-1]
    value = sum((cost * entry for cost, entry in zip(costs, point, strict=True)), ZERO)
    return Solution(value, tuple(point))
