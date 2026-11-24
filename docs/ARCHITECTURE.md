# Architecture

## Overview

The project is a dependency-free Python library with a command-line front door. There is no client or server, so it has no `frontend/` and `backend/` split. Dependencies point in one direction, from the interface toward pure domain logic.

```text
cli
 |-- catalog ------------+
 |-- persistence         |
 |-- simulation          |
 |     |                 v
 |     +----------> inference
 |                   |     |
 |                   |     +--> optimization
 |                   v
 +--------------> probability --> logic
```

## Module structure

| Module | Responsibility | Key types and functions |
| --- | --- | --- |
| `logic/formula.py` | Immutable formula tree | `Formula`, `enumerate_worlds` |
| `logic/parser.py` | Bounded grammar | `parse_formula` |
| `probability/exact.py` | Strict rational input | `parse_probability` |
| `probability/statements.py` | Premise syntax | `ProbabilityStatement`, `parse_statement` |
| `optimization/simplex.py` | Exact linear programming | `minimize` |
| `inference/bounds.py` | Argument analysis | `analyze_argument` |
| `inference/network.py` | Exact inference and sampling | `BayesianNetwork`, `Node` |
| `simulation/monte_carlo.py` | Experiments | `estimate_probability`, `wilson_interval` |
| `catalog/` | Built-in content | `ARGUMENT_FORMS`, `SCENARIOS` |
| `persistence/run_store.py` | Optional storage | `save_run` |
| `cli/main.py` | JSON interface | `main` |

## Algorithms

### Tight bounds

This is the probabilistic satisfiability formulation of Boole, Hailperin and Nilsson. For `n` variables, each of the `N = 2^n` truth assignments receives an unknown probability `x_w >= 0`:

```text
minimize or maximize   sum of x_w over worlds where the conclusion holds
subject to             sum of all x_w = 1
                       l_i <= sum of x_w over worlds where premise i holds <= u_i
```

A conditional premise `P(F given G)` in `[l, u]` stays linear after multiplying through by `P(G)`:

```text
P(F and G) - l * P(G) >= 0
P(F and G) - u * P(G) <= 0
```

Interval premises add one slack column per side. Because the feasible region is a closed polytope, both bounds are attained, and the solver returns a distribution that attains each one.

### Exact simplex

The solver is a two-phase primal simplex over `fractions.Fraction`. Phase one finds a feasible basis or proves that the premises are inconsistent. Redundant rows are removed before phase two. Bland's rule guarantees termination on degenerate programs, which are common here because many right-hand sides are zero. Rational arithmetic removes floating-point tolerances, so results such as `7/10` are exact.

### Adams' uncertainty sum

Define the uncertainty of a statement as `U(X) = 1 - P(X)`. For a classically valid argument, `U(conclusion) <= sum of U(premise)`. The tool reports this as `adams_lower_bound`. The linear program can be tighter, and never looser, which the property tests verify.

### Bayesian inference

`P(Q given E)` is computed by enumerating all assignments and multiplying conditional probability table entries, which gives an exact rational result.

### Monte Carlo verification

Ancestral sampling draws each node after its parents. Bernoulli draws compare `randrange(denominator)` with the numerator, so they are exact for rational probabilities rather than rounded to a float. Rejection sampling handles evidence. Each generator is an isolated `random.Random(seed)`.

Results use the Wilson score interval, which behaves better than the normal approximation near 0 and 1 and for small accepted-sample counts.

## Complexity

| Operation | Time | Space |
| --- | --- | --- |
| Parse a formula of length `L` | `O(L)` | `O(L)` |
| Evaluate a formula of size `F` | `O(F)` | `O(depth)` |
| Classical validity | `O(2^n * F)` | `O(2^n * n)` |
| One simplex pivot with `m` rows | `O(m * (2^n + s))` rational operations | `O(m * (2^n + s))` |
| Simplex overall | Exponential worst case, usually few pivots | As above |
| Network enumeration | `O(n * 2^n)` | `O(n)` |
| Monte Carlo with `S` samples | `O(S * n)` | `O(n)` |
| Wilson interval | `O(1)` | `O(1)` |

Here `s` is the number of slack columns. Rational operation cost also grows with the bit length of the values involved. These costs are the reason for the limits of 10 argument variables and 16 network nodes.

## Reproducibility

- Every experiment takes an explicit seed and reports it.
- Hypothesis runs derandomized with no example database.
- Exact results do not depend on the seed or the platform.
- Development tools are pinned with hashes in `requirements-dev.txt`.

## Recommended evolution

These are possible extensions and are not implemented:

1. Column generation, to scale probabilistic satisfiability beyond 10 variables.
2. Variable elimination, to replace enumeration on sparse networks.
3. Fractional-linear programming, to support conditional conclusions.

## References

- G. Boole, *An Investigation of the Laws of Thought*, 1854.
- T. Hailperin, "Best possible inequalities for the probability of a logical function of events", *The American Mathematical Monthly*, 1965.
- N. Nilsson, "Probabilistic logic", *Artificial Intelligence*, 1986.
- E. Adams, *A Primer of Probability Logic*, CSLI Publications, 1998.
- R. Bland, "New finite pivoting rules for the simplex method", *Mathematics of Operations Research*, 1977.
- E. Wilson, "Probable inference, the law of succession, and statistical inference", *Journal of the American Statistical Association*, 1927.
