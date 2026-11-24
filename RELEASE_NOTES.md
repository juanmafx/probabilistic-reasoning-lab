# Release Notes: 1.0.0

**Status:** prepared, not yet tagged or published.

## Summary

Version 1.0.0 is the first implementation of this project, which began in 2023 as a one-line description and was modernized in 2026. It evaluates logical arguments about probabilities exactly, then checks probabilistic claims with reproducible simulations.

## Highlights

- Tight, exact bounds on a conclusion given uncertain premises, with witness distributions.
- Classical validity and Adams' uncertainty bound for each argument.
- Exact Bayesian network inference.
- Seeded Monte Carlo verification with Wilson score intervals.
- No runtime dependencies.

## Requirements

Python 3.13 or newer.

## Upgrade notes

There is no earlier release, so no migration is needed.

## Known limitations

- Exact argument analysis supports up to 10 variables.
- Conclusions must be unconditional formulas.
- A conditional premise holds vacuously when its condition has probability zero.
- No license has been selected yet.

## Verification

Test results for this version are in `reports/tests/summary.md`.
