import sqlite3
from pathlib import Path

# Default DB location: ~/.prompt-registry/registry.db
DEFAULT_DB_PATH = Path.home() / ".prompt-registry" / "registry.db"


def get_connection(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Open a connection to the SQLite database, creating it if needed."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db(db_path: Path = DEFAULT_DB_PATH) -> None:
    """Create tables if they don't exist yet."""
    with get_connection(db_path) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS prompt_versions (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt_name  TEXT    NOT NULL,
                version      INTEGER NOT NULL,
                template     TEXT    NOT NULL,
                variables    TEXT    NOT NULL,  -- JSON array, e.g. '["topic", "tone"]'
                message      TEXT    NOT NULL,
                created_at   TEXT    NOT NULL,
                UNIQUE (prompt_name, version)
            );

            CREATE TABLE IF NOT EXISTS prompts (
                name         TEXT PRIMARY KEY,
                description  TEXT NOT NULL,
                created_at   TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS deployments (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt_name  TEXT    NOT NULL,
                environment  TEXT    NOT NULL,
                version      INTEGER NOT NULL,
                deployed_at  TEXT    NOT NULL,
                UNIQUE (prompt_name, environment)  -- one active deployment per env
            );
        """)