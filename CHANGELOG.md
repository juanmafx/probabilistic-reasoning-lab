# Changelog

This project follows [Semantic Versioning](https://semver.org/).

## [1.0.1] - 2026-11-24

Documentation corrections only. No change to code behaviour.

### Changed

- Release notes and changelog now reflect that 1.0.0 is published and that the public Git history was rewritten on 2026-11-24 to keep only the 2026 modernization.

## [1.0.0] - 2026-11-24

The first implementation, added in 2026. The repository previously contained only a description.

### Added

- Propositional formula model and bounded parser, with limits on premises per argument.
- Probability statements with point, interval and conditional forms.
- Exact two-phase simplex solver with Bland's rule.
- Tight conclusion bounds with witness distributions.
- Classical validity check and Adams' uncertainty bound.
- Boolean Bayesian networks with exact inference and exact-rational sampling.
- Seeded Monte Carlo experiments with Wilson score intervals.
- Catalog of argument forms and probability scenarios.
- JSON command-line interface.
- Optional SQLite schema and transactional run storage.
- Unit, property-based, statistical and integration tests with a committed report.
- CI workflow, architecture documentation, security policy and security audit.

### Changed

- Rewrote the README in English.
