"""Explicit v2 schema creation. Never opens, migrates or assigns legacy records."""
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from app.review.settings import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_version(version INTEGER PRIMARY KEY CHECK(version=1));
INSERT OR IGNORE INTO schema_version VALUES(1);
CREATE TABLE IF NOT EXISTS documents(
 id TEXT PRIMARY KEY, workspace TEXT NOT NULL, owner TEXT NOT NULL,
 filename TEXT NOT NULL, kind TEXT NOT NULL, hash TEXT NOT NULL,
 context TEXT NOT NULL, mode TEXT NOT NULL, status TEXT NOT NULL,
 created TEXT NOT NULL, retention_until TEXT NOT NULL, tombstone TEXT,
 epoch INTEGER NOT NULL DEFAULT 0, source TEXT, result TEXT,
 error_code TEXT, revision INTEGER NOT NULL DEFAULT 0,
 review_complete INTEGER NOT NULL DEFAULT 0, idempotency TEXT NOT NULL,
 ai_calls INTEGER NOT NULL DEFAULT 0,
 UNIQUE(workspace, owner, idempotency)
);
CREATE INDEX IF NOT EXISTS documents_scope ON documents(workspace,owner,created);
CREATE TABLE IF NOT EXISTS jobs(
 id TEXT PRIMARY KEY, document_id TEXT UNIQUE NOT NULL REFERENCES documents(id),
 state TEXT NOT NULL, stage TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
 epoch INTEGER NOT NULL DEFAULT 0, lease_token TEXT, lease_until REAL,
 updated TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS decisions(
 document_id TEXT NOT NULL REFERENCES documents(id), finding_id TEXT NOT NULL,
 actor TEXT NOT NULL, status TEXT NOT NULL, note TEXT NOT NULL,
 revision_text TEXT NOT NULL, version INTEGER NOT NULL, updated TEXT NOT NULL,
 PRIMARY KEY(document_id,finding_id)
);
CREATE TABLE IF NOT EXISTS decision_events(
 id TEXT PRIMARY KEY, document_id TEXT NOT NULL REFERENCES documents(id),
 finding_id TEXT NOT NULL, actor TEXT NOT NULL, payload TEXT NOT NULL, created TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS deletions(
 document_id TEXT PRIMARY KEY, workspace TEXT NOT NULL, owner TEXT NOT NULL,
 requested TEXT NOT NULL, completed TEXT, state TEXT NOT NULL, error_code TEXT,
 backup_policy TEXT NOT NULL, provider_policy TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS rate_limits(
 principal TEXT NOT NULL, minute INTEGER NOT NULL, count INTEGER NOT NULL,
 PRIMARY KEY(principal,minute)
);
"""


def now():
    return datetime.now(timezone.utc).isoformat()


def database_path():
    return settings().data_dir.resolve() / "reviews.sqlite3"


def initialize():
    root = settings().data_dir.resolve()
    root.mkdir(parents=True, exist_ok=True)
    (root / "uploads").mkdir(exist_ok=True)
    with sqlite3.connect(database_path()) as conn:
        conn.executescript(SCHEMA)
        conn.execute("PRAGMA journal_mode=WAL")


@contextmanager
def transaction():
    # mode=rw: requests cannot silently create an uninitialized datastore.
    path = database_path()
    conn = sqlite3.connect(path.as_uri() + "?mode=rw", uri=True, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA secure_delete=ON")
    try:
        conn.execute("BEGIN IMMEDIATE")
        yield conn
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    initialize()
    print("Initialized separate review-v2 schema. Legacy data was not opened.")
