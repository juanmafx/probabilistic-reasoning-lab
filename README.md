# programacionExperimental

A Python toolkit for experimental programming on logical arguments about probabilities. It computes what uncertain premises actually imply about a conclusion, then checks probabilistic claims against seeded simulations.

> **Project history:** originally created in 2023 as a repository containing only a one-line description, modernized in 2026. All of the implementation was added in 2026.

## Purpose

The original repository described its subject as experimental programming and logical arguments about probabilities. This project implements exactly that subject.

## Why this project exists

Classical logic says whether a conclusion follows from true premises. Real premises are rarely certain, which raises sharper questions:

- If `A` is 90% likely and `A -> B` is 80% likely, how likely is `B`?
- Does a valid argument stay reliable as its premises become uncertain?
- Why does a positive result from a 95% accurate test on a rare condition still leave the condition unlikely?

This toolkit answers the first two with exact rational arithmetic and the third with exact inference, then tests the answers experimentally.

## What it does

| Capability | Method |
| --- | --- |
| Parse propositional formulas | Bounded recursive-descent parser, no `eval` |
| Tight bounds on a conclusion | Exact two-phase simplex over all truth assignments |
| Witness distributions | The distributions that attain each bound |
| Classical validity check | Truth-table enumeration |
| Uncertainty bound for valid arguments | Adams' uncertainty sum |
| Exact posterior probabilities | Bayesian network enumeration |
| Experimental verification | Seeded rejection sampling with Wilson score intervals |
| Optional run history | Parameterized SQLite storage |

The catalog contains seven argument forms, including two fallacies, and four scenarios: base-rate neglect, repeated testing, diagnostic reasoning and explaining away. The scenarios follow standard textbook patterns, and their parameters are teaching values, not real-world data.

## Architecture

```text
src/probabilistic_arguments/
  logic/          formulas and parser
  probability/    exact values and probability statements
  optimization/   exact simplex solver
  inference/      argument bounds and Bayesian networks
  simulation/     seeded Monte Carlo and confidence intervals
  catalog/        built-in arguments and scenarios
  persistence/    optional SQLite run store
  cli/            JSON command-line interface
```

This is a command-line library with no client or server. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the design, algorithms and complexity notes.

## Quick start

Requires Python 3.13 or newer. The package has no runtime dependencies.

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install .
probabilistic-arguments list
```

To run it without installing:

```bash
PYTHONPATH=src python3 -m probabilistic_arguments list
```

## Usage guide

Analyze a built-in argument:

```bash
probabilistic-arguments argument modus_ponens
```

Analyze your own argument:

```bash
probabilistic-arguments analyze \
  --premise "P(A) = 0.9" \
  --premise "P(A -> B) = 4/5" \
  --conclusion "B"
```

The result reports `lower` as `7/10` and `upper` as `4/5`, with a witness distribution for each.

Premises can be conditional or use an interval:

```bash
probabilistic-arguments analyze \
  --premise "P(A) in [1/2, 3/4]" \
  --premise "P(B given A) = 0.8" \
  --conclusion "B"
```

Run a reproducible experiment:

```bash
probabilistic-arguments simulate base_rate --samples 100000 --seed 2026
probabilistic-arguments simulate all --seed 2026
```

### Formula syntax

| Operator | Symbols |
| --- | --- |
| Not | `!`, `~`, `not` |
| And | `&`, `and` |
| Or | `\|`, `or` |
| Implies (right-associative) | `->` |
| If and only if | `<->` |

Precedence runs from `not` (tightest) through `and`, `or` and `->` to `<->`. Probabilities are written as decimals such as `0.25` or ratios such as `1/4`.

## Configuration

There are no configuration files or environment variables. Behavior is set through CLI options:

| Option | Command | Default | Range |
| --- | --- | --- | --- |
| `--samples` | `simulate` | `100000` | 1 to 10,000,000 |
| `--seed` | `simulate` | `2026` | 0 to 2^63 - 1 |
| `--confidence` | `simulate` | `0.95` | Between 0 and 1, excluding values too close to either end to compute an interval |
| `--database` | `simulate` | None | Path to an existing database |

## Optional database

**The database is optional.** The toolkit has no natural persistence requirement, so [db/schema.sql](db/schema.sql) provides a small schema for keeping simulation run results.

```bash
sqlite3 runs.sqlite3 < db/schema.sql
probabilistic-arguments simulate base_rate --database runs.sqlite3
```

The schema uses `STRICT` tables, which require SQLite 3.37 or newer. All runs from one `simulate` command are stored in a single transaction, so a failed command stores none of them.

## Testing

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install --require-hashes --only-binary :all: -r requirements-dev.txt
python -m pytest
python tools/generate_test_report.py
```

The suite contains unit, property-based, statistical and integration tests. Hypothesis runs in a derandomized profile and the statistical tests use fixed seeds, so results are reproducible. The most recent committed report is in [reports/tests/summary.md](reports/tests/summary.md).

## Security notes

- Formulas are parsed by a grammar and are never evaluated as code.
- Formula length, nesting, variable count, premise count, network size and sample count are bounded.
- SQL statements are parameterized, and the CLI never creates a database or runs schema files.
- The project makes no network requests and stores no credentials.

See [SECURITY.md](SECURITY.md) and [docs/SECURITY_AUDIT.md](docs/SECURITY_AUDIT.md).

## Limitations

- Exact analysis is limited to 10 variables and 12 premises because the model has one column per truth assignment and one or two rows per premise. An analysis near those limits can take many seconds.
- `P(F given G) = p` is encoded linearly as `P(F and G) = p * P(G)`, so it holds vacuously when `P(G) = 0`.
- Conclusions are unconditional formulas.
- Seeded results are reproducible for a given Python version; the standard library does not guarantee identical random streams across all future versions.

## License

No license has been selected yet, so default copyright applies.
