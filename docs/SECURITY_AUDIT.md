# Security Audit

**Date:** 2026-11-24
**Scope:** the full tree on branch `modernize/2026` and the repository history before it.

This is a tool-assisted review of the code, not an independent third-party audit or a penetration test.

## Baseline

Before modernization, the repository had one commit containing a two-line `README.md`. It had no code, dependencies, binaries, build artifacts or configuration, so there were no inherited vulnerabilities to fix.

## Attack surface

The project is a local command-line tool. It has no server, web interface, accounts, sessions, stored credentials or network calls, so XSS, CSRF, authentication and two-factor authentication do not apply. It uses no cryptography; `random.Random` drives reproducible simulations only and is never used for security.

## Checks performed

| Check | Tool or method | Result |
| --- | --- | --- |
| Secrets in history and tree | gitleaks 8.30.1 with `--redact` | No leaks found |
| Tracked binaries and dependencies | `git ls-files` review | None |
| Known dependency vulnerabilities | pip-audit 2.10.1 on `requirements-dev.txt` and the pinned build backend, 2026-11-24 | None reported |
| Static security lint | Ruff `S` rules | Passing; suppressions below |
| Type safety | mypy strict | Passing |
| CI action pins | Compared each SHA with the upstream release tags | All three match a release |
| Solver correctness | 1,500 random programs compared with the HiGHS solver | No mismatches |

## Controls in the code

| Risk | Control |
| --- | --- |
| Code injection | Formulas use a dedicated grammar; `eval` and `exec` are not used |
| SQL injection | All values are bound parameters |
| Resource exhaustion | Limits on formula length, nesting, variables, premises, network nodes and samples |
| Malformed numbers | ASCII-only patterns reject exponents, `nan`, `inf` and non-ASCII digits before conversion |
| Accidental file creation | The run store opens databases in read-write mode without creating them |
| Partial writes | All runs from one command are stored in a single transaction |
| Misleading reports | The report generator deletes earlier results before each run |
| Supply chain | No runtime dependencies; development tools pinned with hashes; build backend pinned by version |
| CI privilege | Read-only token, credentials not persisted, actions pinned to commit SHAs |

## Defects fixed during this review

- A confidence value such as `0.9999999999999999` crashed the CLI with a traceback, and a value such as `1e-320` silently produced a zero-width interval. Both are now rejected.
- Probability parsing accepted non-ASCII digits.
- The number of premises was unbounded, so a long command could run for an arbitrary time.
- A failed `simulate all` could leave some of its runs in the database.
- When pytest failed before writing results, the report generator republished the previous results with a new timestamp.

## Reviewed suppressions

| Rule | Location | Reason |
| --- | --- | --- |
| `S311` | Sampling modules and tests | Seeded, reproducible randomness is required; it is not used for security |
| `S105` | `logic/parser.py` | False positive on a parser variable named `token` |
| `S314` | `tools/generate_test_report.py` | Parses only the report that pytest just wrote locally |
| `S603` | `tools/generate_test_report.py` | Fixed argument list with no shell and no external input |
| `S101`, `S608` | Tests | Assertions and fixed SQL strings in tests |

## Open items

No code-level security findings are open.

Residual notes:

- `--database` writes to whichever existing SQLite file the local user names, with that user's permissions.
- Analysis near the documented limits can take many seconds; there is no time limit.
- The GitHub Actions workflow has not run on GitHub yet.
- GitHub private vulnerability reporting is not enabled for this repository.
