import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))


def load_chapter_module(rel_path: str):
    """Import a chapter script by path (chapter folders are not packages)."""
    path = ROOT / rel_path
    sys.path.insert(0, str(path.parent))
    name = "chapter_" + rel_path.replace("/", "_").replace("-", "_").removesuffix(".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def load():
    return load_chapter_module


@pytest.fixture
def sample_copy(tmp_path):
    """A throwaway copy of sample-repo so tests can write files."""
    import shutil

    dest = tmp_path / "sample-repo"
    shutil.copytree(ROOT / "sample-repo", dest)
    return dest
