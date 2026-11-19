"""Well-known paths in the course repository."""

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# The small project our "repo assistant" agent works on in every chapter.
# Point COURSE_REPO at any other folder to try the agents on your own code.
SAMPLE_REPO = Path(os.environ.get("COURSE_REPO", REPO_ROOT / "sample-repo")).resolve()
