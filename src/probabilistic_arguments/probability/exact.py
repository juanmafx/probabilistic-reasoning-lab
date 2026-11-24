# Strict conversion of user input into exact rational probabilities.
from __future__ import annotations

import re
from fractions import Fraction

from probabilistic_arguments.errors import InvalidProbabilityError

_DECIMAL = re.compile(r"(?:0(?:\.\d{1,12})?|1(?:\.0{1,12})?|\.\d{1,12})", re.ASCII)
_RATIO = re.compile(r"\d{1,12}/[1-9]\d{0,11}", re.ASCII)


def parse_probability(value: str | int | Fraction) -> Fraction:
    if isinstance(value, bool) or not isinstance(value, str | int | Fraction):
        raise InvalidProbabilityError("probability must be text, an integer or a Fraction")
    if isinstance(value, str):
        text = value.strip()
        if _DECIMAL.fullmatch(text) is None and _RATIO.fullmatch(text) is None:
            raise InvalidProbabilityError("probability must look like 0.25 or 1/4")
        result = Fraction(text)
    else:
        result = Fraction(value)
    if not 0 <= result <= 1:
        raise InvalidProbabilityError("probability must lie in [0, 1]")
    return result
