-- Optional SQLite schema for storing seeded simulation runs.
-- The library and CLI work without it. Apply with: sqlite3 runs.sqlite3 < db/schema.sql
CREATE TABLE IF NOT EXISTS simulation_runs (
    id                INTEGER PRIMARY KEY,
    scenario_key      TEXT    NOT NULL CHECK (length(scenario_key) BETWEEN 1 AND 64),
    package_version   TEXT    NOT NULL CHECK (length(package_version) BETWEEN 1 AND 32),
    seed              INTEGER NOT NULL,
    samples           INTEGER NOT NULL CHECK (samples > 0),
    accepted          INTEGER NOT NULL CHECK (accepted BETWEEN 1 AND samples),
    hits              INTEGER NOT NULL CHECK (hits BETWEEN 0 AND accepted),
    estimate          REAL    NOT NULL CHECK (estimate BETWEEN 0.0 AND 1.0),
    interval_low      REAL    NOT NULL CHECK (interval_low BETWEEN 0.0 AND 1.0),
    interval_high     REAL    NOT NULL CHECK (interval_high BETWEEN 0.0 AND 1.0),
    confidence        REAL    NOT NULL CHECK (confidence > 0.0 AND confidence < 1.0),
    exact_probability TEXT    NOT NULL CHECK (length(exact_probability) BETWEEN 1 AND 128),
    created_at        TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    CHECK (interval_low <= estimate AND estimate <= interval_high)
) STRICT;

CREATE INDEX IF NOT EXISTS idx_simulation_runs_scenario_created
    ON simulation_runs (scenario_key, created_at);
