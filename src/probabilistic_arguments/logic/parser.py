# Bounded recursive-descent parser for propositional formulas; never uses eval.
from __future__ import annotations

import re

from probabilistic_arguments.errors import FormulaSyntaxError
from probabilistic_arguments.logic.formula import (
    Biconditional,
    Conjunction,
    Disjunction,
    Formula,
    Implication,
    Negation,
    Variable,
)

MAX_FORMULA_LENGTH = 256
MAX_NESTING_DEPTH = 32

_TOKEN = re.compile(r"\s*(<->|->|[()!~&|]|[A-Za-z_][A-Za-z0-9_]*)")
_KEYWORD_OPERATORS = {"not": "!", "and": "&", "or": "|"}
_RESERVED_WORDS = frozenset({"given", "in"})


def _tokenize(source: str) -> list[str]:
    tokens: list[str] = []
    position = 0
    stripped_end = len(source.rstrip())
    while position < stripped_end:
        match = _TOKEN.match(source, position)
        if match is None:
            raise FormulaSyntaxError(f"unexpected character at offset {position}")
        token = match.group(1)
        if token in _RESERVED_WORDS:
            raise FormulaSyntaxError(f"reserved word used as a variable: {token}")
        tokens.append(_KEYWORD_OPERATORS.get(token, token))
        position = match.end()
    return tokens


class _Parser:
    def __init__(self, tokens: list[str]) -> None:
        self._tokens = tokens
        self._index = 0
        self._depth = 0

    def parse(self) -> Formula:
        formula = self._biconditional()
        if self._peek() is not None:
            raise FormulaSyntaxError(f"unexpected token: {self._peek()}")
        return formula

    def _peek(self) -> str | None:
        return self._tokens[self._index] if self._index < len(self._tokens) else None

    def _advance(self) -> str:
        token = self._peek()
        if token is None:
            raise FormulaSyntaxError("unexpected end of formula")
        self._index += 1
        return token

    def _accept(self, token: str) -> bool:
        if self._peek() == token:
            self._index += 1
            return True
        return False

    def _enter(self) -> None:
        self._depth += 1
        if self._depth > MAX_NESTING_DEPTH:
            raise FormulaSyntaxError(f"nesting exceeds {MAX_NESTING_DEPTH} levels")

    def _leave(self) -> None:
        self._depth -= 1

    def _biconditional(self) -> Formula:
        formula = self._implication()
        while self._accept("<->"):
            formula = Biconditional(formula, self._implication())
        return formula

    def _implication(self) -> Formula:
        antecedent = self._disjunction()
        if not self._accept("->"):
            return antecedent
        self._enter()
        consequent = self._implication()
        self._leave()
        return Implication(antecedent, consequent)

    def _disjunction(self) -> Formula:
        formula = self._conjunction()
        while self._accept("|"):
            formula = Disjunction(formula, self._conjunction())
        return formula

    def _conjunction(self) -> Formula:
        formula = self._unary()
        while self._accept("&"):
            formula = Conjunction(formula, self._unary())
        return formula

    def _unary(self) -> Formula:
        if self._accept("!") or self._accept("~"):
            self._enter()
            operand = self._unary()
            self._leave()
            return Negation(operand)
        return self._atom()

    def _atom(self) -> Formula:
        token = self._advance()
        if token == "(":
            self._enter()
            formula = self._biconditional()
            self._leave()
            if not self._accept(")"):
                raise FormulaSyntaxError("missing closing parenthesis")
            return formula
        if not (token[0].isalpha() or token[0] == "_"):
            raise FormulaSyntaxError(f"unexpected token: {token}")
        return Variable(token)


def parse_formula(source: str) -> Formula:
    if len(source) > MAX_FORMULA_LENGTH:
        raise FormulaSyntaxError(f"formula exceeds {MAX_FORMULA_LENGTH} characters")
    tokens = _tokenize(source)
    if not tokens:
        raise FormulaSyntaxError("formula is empty")
    return _Parser(tokens).parse()
