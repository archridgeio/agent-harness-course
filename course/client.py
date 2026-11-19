"""Model client used by every chapter.

Set ANTHROPIC_API_KEY before running anything. Override the model with
COURSE_MODEL, for example: export COURSE_MODEL=claude-haiku-5-5
"""

import os

from anthropic import Anthropic

MODEL = os.environ.get("COURSE_MODEL", "claude-sonnet-5-5")


def get_client() -> Anthropic:
    """Return an Anthropic client. Reads ANTHROPIC_API_KEY from the environment."""
    return Anthropic()
