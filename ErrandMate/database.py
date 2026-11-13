import sqlite3

from config import DB


def db_connect():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def _column_exists(cursor, table, column):
    columns = [row[1] for row in cursor.execute(f"PRAGMA table_info({table})").fetchall()]
    return column in columns


def _add_column_if_missing(cursor, table, column, column_type):
    if not _column_exists(cursor, table, column):
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")


def setup_database():
    conn = db_connect()
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT NOT NULL,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'both',
        tasks_done INTEGER DEFAULT 0,
        joined_date TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        category TEXT,
        location TEXT NOT NULL,
        price REAL NOT NULL,
        deadline TEXT,
        status TEXT DEFAULT 'open',
        poster_id INTEGER NOT NULL,
        runner_id INTEGER,
        posted_on TEXT DEFAULT CURRENT_TIMESTAMP,
        accepted_on TEXT,
        started_on TEXT,
        submitted_on TEXT,
        finished_on TEXT,
        cancelled_on TEXT,
        cancellation_reason TEXT
    )""")

    # Safe migration for databases created by older versions of the app.
    _add_column_if_missing(c, "tasks", "started_on", "TEXT")
    _add_column_if_missing(c, "tasks", "submitted_on", "TEXT")
    _add_column_if_missing(c, "tasks", "cancelled_on", "TEXT")
    _add_column_if_missing(c, "tasks", "cancellation_reason", "TEXT")

    c.execute("""CREATE TABLE IF NOT EXISTS ratings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER NOT NULL,
        reviewer_id INTEGER NOT NULL,
        runner_id INTEGER NOT NULL,
        rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
        review TEXT,
        created_on TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(task_id, reviewer_id)
    )""")

    # Performance optimization indexes
    c.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_tasks_poster ON tasks(poster_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_tasks_runner ON tasks(runner_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_ratings_runner ON ratings(runner_id)")

    conn.commit()
    conn.close()
