# Security Audit

**Date:** 2026-11-23
**Scope:** the full tree on branch `modernize/2026` and the repository history before it.

This is a self-review with the tools listed below, not an independent third-party audit.

## Baseline

Before modernization, the repository had one commit containing a two-line `README.md`. It had no code, dependencies, binaries, build artifacts or configuration, so there were no inherited vulnerabilities to fix.

## Checks performed

| Check | Tool or method | Result |
| --- | --- | --- |
| Credentials in history | Pattern search across all commits | No matches |
| Tracked private keys | Same search | None |
| Tracked binaries and dependencies | `git ls-files` review | None |
| Known dependency vulnerabilities | `pip-audit` on `requirements-dev.txt`, 2026-11-23 | None reported |
| Static security lint | Ruff `S` rules | Passing; suppressions below |
| Type safety | mypy strict | Passing |

## Controls in the new code

| Risk | Control |
| --- | --- |
| Code injection | Formulas use a dedicated grammar; `eval` and `exec` are not used |
| SQL injection | All values are bound parameters |
| Resource exhaustion | Limits on formula length, nesting, variables, network nodes and samples |
| Malformed numbers | Strict patterns reject exponents, `nan` and `inf` before conversion |
| Accidental file creation | The run store opens databases in read-write mode without creating them |
| Supply chain | No runtime dependencies; development tools pinned with hashes; build backend pinned by version |
| CI privilege | Read-only token, credentials not persisted, actions pinned to commit SHAs |

## Reviewed suppressions

| Rule | Location | Reason |
| --- | --- | --- |
| `S311` | Sampling modules and tests | Seeded, reproducible randomness is required; it is not used for security |
| `S105` | `logic/parser.py` | False positive on a parser variable named `token` |
| `S314` | `tools/generate_test_report.py` | Parses only the report that pytest just wrote locally |
| `S603` | `tools/generate_test_report.py` | Fixed argument list with no shell and no external input |
| `S101`, `S608` | Tests | Assertions and fixed SQL strings in tests |

## Open items

No security findings are open.

Residual notes:

- `--database` writes to whichever existing SQLite file the local user names, with that user's permissions.
- The GitHub Actions workflow was validated locally as YAML but has not run on GitHub yet.
