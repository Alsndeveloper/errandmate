import sqlite3
from contextlib import contextmanager
from typing import Generator
from server.config import DATABASE_URL


def get_db_connection() -> sqlite3.Connection:
    """Creates a configured sqlite3 connection with dict-like row access."""
    conn = sqlite3.connect(DATABASE_URL, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Context manager for safe database connections and automatic commits."""
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Initializes tables, columns, and indexes if they do not exist yet."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'both',
            id_type TEXT,
            id_number TEXT,
            residential_address TEXT,
            postcode TEXT,
            is_id_verified INTEGER DEFAULT 0,
            tasks_done INTEGER DEFAULT 0,
            joined_date TEXT DEFAULT CURRENT_TIMESTAMP
        )""")

        # Migration: Ensure new identification columns exist in users table if table was created previously
        user_cols = [row[1] for row in c.execute("PRAGMA table_info(users)").fetchall()]
        if "username" not in user_cols:
            c.execute("ALTER TABLE users ADD COLUMN username TEXT")
        if "id_type" not in user_cols:
            c.execute("ALTER TABLE users ADD COLUMN id_type TEXT DEFAULT 'Passport'")
        if "id_number" not in user_cols:
            c.execute("ALTER TABLE users ADD COLUMN id_number TEXT")
        if "residential_address" not in user_cols:
            c.execute("ALTER TABLE users ADD COLUMN residential_address TEXT")
        if "postcode" not in user_cols:
            c.execute("ALTER TABLE users ADD COLUMN postcode TEXT")
        if "is_id_verified" not in user_cols:
            c.execute("ALTER TABLE users ADD COLUMN is_id_verified INTEGER DEFAULT 0")

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
            cancellation_reason TEXT,
            FOREIGN KEY (poster_id) REFERENCES users(id),
            FOREIGN KEY (runner_id) REFERENCES users(id)
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            reviewer_id INTEGER NOT NULL,
            runner_id INTEGER NOT NULL,
            rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
            review TEXT,
            created_on TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(task_id, reviewer_id),
            FOREIGN KEY (task_id) REFERENCES tasks(id),
            FOREIGN KEY (reviewer_id) REFERENCES users(id),
            FOREIGN KEY (runner_id) REFERENCES users(id)
        )""")

        # Performance indexes
        c.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_tasks_poster ON tasks(poster_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_tasks_runner ON tasks(runner_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_ratings_runner ON ratings(runner_id)")
