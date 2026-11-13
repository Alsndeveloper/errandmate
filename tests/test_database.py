import sqlite3
import pytest
from server.database import get_db, init_db


def test_database_initialization_and_tables():
    init_db()
    with get_db() as conn:
        tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        assert "users" in tables
        assert "tasks" in tables
        assert "ratings" in tables


def test_task_status_indexing():
    with get_db() as conn:
        indexes = [row[1] for row in conn.execute("PRAGMA index_list('tasks')").fetchall()]
        assert any("status" in idx for idx in indexes)
