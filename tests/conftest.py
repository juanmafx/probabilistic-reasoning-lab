# Deterministic Hypothesis profile so every test run is reproducible.
from hypothesis import settings

settings.register_profile("reproducible", derandomize=True, database=None, deadline=None)
settings.load_profile("reproducible")
