"""Hypothesis settings profiles for the test suite.

Profiles:
- ``fast``: 10 examples — minimal runs for quick smoke-testing.
- ``dev``:  50 examples — fast feedback during local development.
- ``ci``:  200 examples — thorough coverage in CI pipelines.

The active profile is selected by the ``HYPOTHESIS_PROFILE`` environment
variable (defaults to ``fast`` when not set).

Requirements: design.md — Testing Strategy / Test Configuration
"""

import os

from hypothesis import HealthCheck, settings

# Register profiles as specified in the design document.
settings.register_profile(
    "ci",
    max_examples=200,
    suppress_health_check=[HealthCheck.too_slow],
)
settings.register_profile(
    "dev",
    max_examples=50,
)
settings.register_profile(
    "fast",
    max_examples=10,
)

# Load the profile requested by the environment, defaulting to "fast".
_profile = os.environ.get("HYPOTHESIS_PROFILE", "fast")
settings.load_profile(_profile)
