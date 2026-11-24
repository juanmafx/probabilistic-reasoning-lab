# Immutable propositional formula tree evaluated against truth assignments.
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from itertools import product

World = Mapping[str, bool]


class Formula(ABC):
    @abstractmethod
    def evaluate(self, world: World) -> bool: ...

    @abstractmethod
    def variables(self) -> frozenset[str]: ...


@dataclass(frozen=True, slots=True)
class Variable(Formula):
    name: str

    def evaluate(self, world: World) -> bool:
        return world[self.name]

    def variables(self) -> frozenset[str]:
        return frozenset({self.name})

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True, slots=True)
class Negation(Formula):
    operand: Formula

    def evaluate(self, world: World) -> bool:
        return not self.operand.evaluate(world)

    def variables(self) -> frozenset[str]:
        return self.operand.variables()

    def __str__(self) -> str:
        return f"!{self.operand}"


@dataclass(frozen=True, slots=True)
class Conjunction(Formula):
    left: Formula
    right: Formula

    def evaluate(self, world: World) -> bool:
        return self.left.evaluate(world) and self.right.evaluate(world)

    def variables(self) -> frozenset[str]:
        return self.left.variables() | self.right.variables()

    def __str__(self) -> str:
        return f"({self.left} & {self.right})"


@dataclass(frozen=True, slots=True)
class Disjunction(Formula):
    left: Formula
    right: Formula

    def evaluate(self, world: World) -> bool:
        return self.left.evaluate(world) or self.right.evaluate(world)

    def variables(self) -> frozenset[str]:
        return self.left.variables() | self.right.variables()

    def __str__(self) -> str:
        return f"({self.left} | {self.right})"


@dataclass(frozen=True, slots=True)
class Implication(Formula):
    antecedent: Formula
    consequent: Formula

    def evaluate(self, world: World) -> bool:
        return not self.antecedent.evaluate(world) or self.consequent.evaluate(world)

    def variables(self) -> frozenset[str]:
        return self.antecedent.variables() | self.consequent.variables()

    def __str__(self) -> str:
        return f"({self.antecedent} -> {self.consequent})"


@dataclass(frozen=True, slots=True)
class Biconditional(Formula):
    left: Formula
    right: Formula

    def evaluate(self, world: World) -> bool:
        return self.left.evaluate(world) == self.right.evaluate(world)

    def variables(self) -> frozenset[str]:
        return self.left.variables() | self.right.variables()

    def __str__(self) -> str:
        return f"({self.left} <-> {self.right})"


_BINARY_FORMULAS = (Conjunction, Disjunction, Implication, Biconditional)


def render(formula: Formula) -> str:
    text = str(formula)
    return text[1:-1] if isinstance(formula, _BINARY_FORMULAS) else text


def enumerate_worlds(names: tuple[str, ...]) -> Iterator[dict[str, bool]]:
    for values in product((False, True), repeat=len(names)):
        yield dict(zip(names, values, strict=True))
