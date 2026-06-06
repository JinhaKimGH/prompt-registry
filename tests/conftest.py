from pathlib import Path

import pytest

from prompt_registry.db import init_db


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    path = tmp_path / "registry.db"
    init_db(path)
    return path
