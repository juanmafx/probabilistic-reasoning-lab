# Classic valid forms and fallacies expressed with uncertain premises.
from __future__ import annotations

from dataclasses import dataclass

from probabilistic_arguments.logic.formula import Formula
from probabilistic_arguments.logic.parser import parse_formula
from probabilistic_arguments.probability.statements import ProbabilityStatement, parse_statement


@dataclass(frozen=True, slots=True)
class ArgumentForm:
    key: str
    title: str
    premises: tuple[ProbabilityStatement, ...]
    conclusion: Formula


def _form(key: str, title: str, premises: tuple[str, ...], conclusion: str) -> ArgumentForm:
    return ArgumentForm(
        key,
        title,
        tuple(parse_statement(premise) for premise in premises),
        parse_formula(conclusion),
    )


ARGUMENT_FORMS: dict[str, ArgumentForm] = {
    form.key: form
    for form in (
        _form("modus_ponens", "Modus ponens", ("P(A) = 9/10", "P(A -> B) = 4/5"), "B"),
        _form("modus_tollens", "Modus tollens", ("P(A -> B) = 9/10", "P(!B) = 4/5"), "!A"),
        _form(
            "hypothetical_syllogism",
            "Hypothetical syllogism",
            ("P(A -> B) = 9/10", "P(B -> C) = 9/10"),
            "A -> C",
        ),
        _form(
            "conditional_modus_ponens",
            "Modus ponens with a conditional probability",
            ("P(A) = 9/10", "P(B given A) = 4/5"),
            "B",
        ),
        _form("conjunction_rule", "Conjunction rule", ("P(A) = 3/10", "P(B) = 9/10"), "A & B"),
        _form(
            "affirming_the_consequent",
            "Affirming the consequent (fallacy)",
            ("P(A -> B) = 9/10", "P(B) = 4/5"),
            "A",
        ),
        _form(
            "denying_the_antecedent",
            "Denying the antecedent (fallacy)",
            ("P(A -> B) = 9/10", "P(!A) = 4/5"),
            "!B",
        ),
    )
}
