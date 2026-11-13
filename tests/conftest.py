"""Shared test setup.

Every test run gets its own throwaway SQLite database, so tests never read or
modify the real ErrandMate.db and pass on a fresh clone.
"""

import os
import tempfile

# Must run before `server.config` is imported: config reads these at import time.
_tmpdir = tempfile.mkdtemp(prefix="errandmate-test-")
os.environ["DATABASE_PATH"] = os.path.join(_tmpdir, "test.db")
os.environ.setdefault("SECRET_KEY", "test-only-secret-key")

import pytest  # noqa: E402

from server.database import init_db  # noqa: E402
from server.seed_data import seed_database  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def test_database():
    init_db()
    seed_database()  # demo personas (e.g. admin) that some tests log in as
    yield
