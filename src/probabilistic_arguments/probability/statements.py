# Probability statements such as P(B given A) = 3/4 or P(A -> B) in [0.8, 0.9].
from __future__ import annotations

import re
from dataclasses import dataclass
from fractions import Fraction

from probabilistic_arguments.errors import FormulaSyntaxError, InvalidProbabilityError
from probabilistic_arguments.logic.formula import Formula, render
from probabilistic_arguments.logic.parser import MAX_FORMULA_LENGTH, parse_formula
from probabilistic_arguments.probability.exact import parse_probability

MAX_STATEMENT_LENGTH = MAX_FORMULA_LENGTH + 64

_STATEMENT = re.compile(
    r"\s*P\((?P<body>.+)\)\s*"
    r"(?:=\s*(?P<point>[^\[\]\s]+)|in\s*\[\s*(?P<low>[^,\s]+)\s*,\s*(?P<high>[^\]\s]+)\s*\])\s*"
)
_GIVEN = re.compile(r"\bgiven\b")


@dataclass(frozen=True, slots=True)
class ProbabilityStatement:
    formula: Formula
    lower: Fraction
    upper: Fraction
    condition: Formula | None = None

    def __post_init__(self) -> None:
        if not 0 <= self.lower <= self.upper <= 1:
            raise InvalidProbabilityError("statement requires 0 <= lower <= upper <= 1")

    def variables(self) -> frozenset[str]:
        condition_names = self.condition.variables() if self.condition else frozenset()
        return self.formula.variables() | condition_names

    def __str__(self) -> str:
        body = render(self.formula)
        if self.condition:
            body = f"{body} given {render(self.condition)}"
        if self.lower == self.upper:
            return f"P({body}) = {self.lower}"
        return f"P({body}) in [{self.lower}, {self.upper}]"


def parse_statement(source: str) -> ProbabilityStatement:
    if len(source) > MAX_STATEMENT_LENGTH:
        raise FormulaSyntaxError(f"statement exceeds {MAX_STATEMENT_LENGTH} characters")
    match = _STATEMENT.fullmatch(source)
    if match is None:
        raise FormulaSyntaxError("statement must look like P(F) = p or P(F given G) in [l, u]")
    parts = _GIVEN.split(match.group("body"))
    if len(parts) > 2:
        raise FormulaSyntaxError("statement may contain only one 'given'")
    formula = parse_formula(parts[0])
    condition = parse_formula(parts[1]) if len(parts) == 2 else None
    if match.group("point") is not None:
        point = parse_probability(match.group("point"))
        return ProbabilityStatement(formula, point, point, condition)
    lower = parse_probability(match.group("low"))
    upper = parse_probability(match.group("high"))
    return ProbabilityStatement(formula, lower, upper, condition)
