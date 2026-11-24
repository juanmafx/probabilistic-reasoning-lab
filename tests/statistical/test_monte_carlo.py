# Seeded statistical tests of the sampler and the Wilson interval.
from fractions import Fraction
from math import comb
from random import Random
from statistics import NormalDist

import pytest
from hypothesis import given
from hypothesis import strategies as st

from probabilistic_arguments.catalog.scenarios import SCENARIOS
from probabilistic_arguments.errors import ModelError
from probabilistic_arguments.inference.network import BayesianNetwork, Node
from probabilistic_arguments.logic.parser import parse_formula
from probabilistic_arguments.simulation.monte_carlo import estimate_probability, wilson_interval

COIN = BayesianNetwork((Node("heads", (), {(): Fraction(3, 10)}),))
HEADS = parse_formula("heads")


def test_same_seed_reproduces_estimate():
    scenario = SCENARIOS["base_rate"]
    first = estimate_probability(scenario.network, scenario.query, scenario.evidence, 5_000, 7)
    second = estimate_probability(scenario.network, scenario.query, scenario.evidence, 5_000, 7)
    assert first == second


def test_different_seeds_change_the_sample_path():
    results = {estimate_probability(COIN, HEADS, None, 5_000, seed).hits for seed in range(5)}
    assert len(results) > 1


@pytest.mark.parametrize("key", sorted(SCENARIOS))
def test_estimate_agrees_with_exact_posterior(key):
    scenario = SCENARIOS[key]
    exact = scenario.network.probability(scenario.query, scenario.evidence)
    estimate = estimate_probability(
        scenario.network, scenario.query, scenario.evidence, 200_000, 2026, confidence=0.999
    )
    assert estimate.interval_low <= float(exact) <= estimate.interval_high


def exact_coverage(trials: int, probability: Fraction) -> float:
    covered = Fraction(0)
    for successes in range(trials + 1):
        low, high = wilson_interval(successes, trials, 0.95)
        if low <= probability <= high:
            covered += (
                comb(trials, successes)
                * probability**successes
                * (1 - probability) ** (trials - successes)
            )
    return float(covered)


def test_wilson_interval_exact_binomial_coverage():
    grid = [Fraction(step, 100) for step in range(5, 96)]
    coverages = [exact_coverage(100, probability) for probability in grid]
    assert 0.945 <= sum(coverages) / len(coverages) <= 0.96
    assert min(coverages) >= 0.92


@pytest.mark.parametrize("probability", [Fraction(1, 4), Fraction(3, 10), Fraction(1, 2)])
def test_wilson_interval_inverts_the_score_test(probability):
    trials = 100
    z = NormalDist().inv_cdf(0.975)
    value = float(probability)
    for successes in range(trials + 1):
        low, high = wilson_interval(successes, trials, 0.95)
        accepted = (successes / trials - value) ** 2 <= z * z * value * (1 - value) / trials
        assert (low <= value <= high) == accepted


def test_sampler_passes_chi_square_goodness_of_fit():
    network = SCENARIOS["wet_grass_rain"].network
    generator = Random(2026)
    samples = 50_000
    counts: dict[tuple[bool, ...], int] = {}
    for _ in range(samples):
        world = network.sample(generator)
        key = tuple(world[name] for name in network.names)
        counts[key] = counts.get(key, 0) + 1
    statistic = 0.0
    cells = 0
    for values, count in counts.items():
        expected = float(network.joint(dict(zip(network.names, values, strict=True)))) * samples
        statistic += (count - expected) ** 2 / expected
        cells += 1
    assert cells == 7
    assert statistic < 22.458


@given(st.integers(1, 500).flatmap(lambda n: st.tuples(st.integers(0, n), st.just(n))))
def test_wilson_interval_contains_point_estimate(pair):
    successes, trials = pair
    low, high = wilson_interval(successes, trials, 0.95)
    assert 0 <= low <= successes / trials <= high <= 1


@pytest.mark.parametrize(("successes", "trials"), [(1, 0), (-1, 5), (6, 5)])
def test_wilson_interval_rejects_invalid_counts(successes, trials):
    with pytest.raises(ModelError):
        wilson_interval(successes, trials, 0.95)


@pytest.mark.parametrize("confidence", [0, 1, -0.5, 1.5])
def test_wilson_interval_rejects_invalid_confidence(confidence):
    with pytest.raises(ModelError):
        wilson_interval(1, 2, confidence)


@pytest.mark.parametrize("samples", [0, -1, 10_000_001])
def test_estimate_rejects_invalid_sample_counts(samples):
    with pytest.raises(ModelError):
        estimate_probability(COIN, HEADS, None, samples, 1)
