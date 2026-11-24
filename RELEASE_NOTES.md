# Release Notes: 1.0.1

Documentation-only patch release. Code behaviour is unchanged from 1.0.0.

## Changes

- The changelog and these notes now reflect that 1.0.0 is published as a tagged GitHub release.
- The public Git history was rewritten on 2026-11-24 and now contains only the 2026 modernization commits.

## Requirements

Python 3.13 or newer.

## Upgrade notes

No action is needed when upgrading from 1.0.0.

## Known limitations

- Exact argument analysis supports up to 10 variables and 12 premises, and can take many seconds near those limits.
- Conclusions must be unconditional formulas.
- A conditional premise holds vacuously when its condition has probability zero.
- No license has been selected yet.

## Verification

Test results for this version are in `reports/tests/summary.md`.
