# Boolean Bayesian network with exact enumeration and exact ancestral sampling.
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from fractions import Fraction
from itertools import product
from random import Random

from probabilistic_arguments.errors import ModelError
from probabilistic_arguments.logic.formula import Formula, enumerate_worlds

MAX_NODES = 16


@dataclass(frozen=True, slots=True)
class Node:
    name: str
    parents: tuple[str, ...]
    table: Mapping[tuple[bool, ...], Fraction]

    def probability_true(self, world: Mapping[str, bool]) -> Fraction:
        return self.table[tuple(world[parent] for parent in self.parents)]


@dataclass(frozen=True, slots=True)
class BayesianNetwork:
    nodes: tuple[Node, ...]

    def __post_init__(self) -> None:
        if len(self.nodes) > MAX_NODES:
            raise ModelError(f"network exceeds {MAX_NODES} nodes")
        seen: set[str] = set()
        for node in self.nodes:
            if node.name in seen:
                raise ModelError(f"duplicate node: {node.name}")
            if not seen.issuperset(node.parents):
                raise ModelError(f"node {node.name} must follow its parents")
            expected = set(product((False, True), repeat=len(node.parents)))
            if set(node.table) != expected:
                raise ModelError(f"incomplete probability table for {node.name}")
            if any(not 0 <= value <= 1 for value in node.table.values()):
                raise ModelError(f"probability out of range in {node.name}")
            seen.add(node.name)

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(node.name for node in self.nodes)

    def joint(self, world: Mapping[str, bool]) -> Fraction:
        result = Fraction(1)
        for node in self.nodes:
            probability = node.probability_true(world)
            result *= probability if world[node.name] else 1 - probability
        return result

    def probability(self, query: Formula, evidence: Formula | None = None) -> Fraction:
        self._require_known(query, evidence)
        evidence_mass = Fraction(0)
        joint_mass = Fraction(0)
        for world in enumerate_worlds(self.names):
            if evidence is not None and not evidence.evaluate(world):
                continue
            weight = self.joint(world)
            evidence_mass += weight
            if query.evaluate(world):
                joint_mass += weight
        if evidence_mass == 0:
            raise ModelError("evidence has probability zero")
        return joint_mass / evidence_mass

    def sample(self, generator: Random) -> dict[str, bool]:
        world: dict[str, bool] = {}
        for node in self.nodes:
            probability = node.probability_true(world)
            world[node.name] = generator.randrange(probability.denominator) < probability.numerator
        return world

    def _require_known(self, query: Formula, evidence: Formula | None) -> None:
        used = query.variables() | (evidence.variables() if evidence else frozenset())
        unknown = used - set(self.names)
        if unknown:
            raise ModelError(f"unknown variables: {', '.join(sorted(unknown))}")
