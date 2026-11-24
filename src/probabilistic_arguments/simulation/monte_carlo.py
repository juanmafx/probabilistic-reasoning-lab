# Reproducible rejection sampling with Wilson score confidence intervals.
from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from random import Random
from statistics import NormalDist

from probabilistic_arguments.errors import ModelError
from probabilistic_arguments.inference.network import BayesianNetwork
from probabilistic_arguments.logic.formula import Formula

MAX_SAMPLES = 10_000_000


@dataclass(frozen=True, slots=True)
class Estimate:
    seed: int
    samples: int
    accepted: int
    hits: int
    value: float
    interval_low: float
    interval_high: float
    confidence: float


def _critical_value(confidence: float) -> float:
    if not 0 < confidence < 1:
        raise ModelError("confidence must lie in (0, 1)")
    quantile = (1 + confidence) / 2
    if not 0.5 < quantile < 1:
        raise ModelError("confidence is too close to 0 or 1 to compute an interval")
    return NormalDist().inv_cdf(quantile)


def wilson_interval(successes: int, trials: int, confidence: float) -> tuple[float, float]:
    if trials <= 0 or not 0 <= successes <= trials:
        raise ModelError("interval requires 0 <= successes <= trials and trials > 0")
    z = _critical_value(confidence)
    z_squared = z * z
    proportion = successes / trials
    denominator = 1 + z_squared / trials
    center = (proportion + z_squared / (2 * trials)) / denominator
    spread = z * sqrt(proportion * (1 - proportion) / trials + z_squared / (4 * trials**2))
    margin = spread / denominator
    low = 0.0 if successes == 0 else max(0.0, center - margin)
    high = 1.0 if successes == trials else min(1.0, center + margin)
    return low, high


def estimate_probability(
    network: BayesianNetwork,
    query: Formula,
    evidence: Formula | None,
    samples: int,
    seed: int,
    confidence: float = 0.95,
) -> Estimate:
    if not 0 < samples <= MAX_SAMPLES:
        raise ModelError(f"samples must lie in [1, {MAX_SAMPLES}]")
    _critical_value(confidence)
    network.probability(query, evidence)
    generator = Random(seed)
    accepted = 0
    hits = 0
    for _ in range(samples):
        world = network.sample(generator)
        if evidence is not None and not evidence.evaluate(world):
            continue
        accepted += 1
        hits += query.evaluate(world)
    if accepted == 0:
        raise ModelError("no sample satisfied the evidence; increase samples")
    low, high = wilson_interval(hits, accepted, confidence)
    return Estimate(seed, samples, accepted, hits, hits / accepted, low, high, confidence)
