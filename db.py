"""
MathQuest - PostgreSQL Database Layer
Migration from SQLite to Neon PostgreSQL (2026-05-12)
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get('DATABASE_URL', '')

def get_db():
    """Return a PostgreSQL connection with dict-like row factory."""
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL environment variable not set")
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

# PostgreSQL table creation SQL (run once via init_db)
CREATE_TABLES_SQL = """
-- parents table
CREATE TABLE IF NOT EXISTS parents (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    has_access INTEGER DEFAULT 0,
    access_code TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- children table
CREATE TABLE IF NOT EXISTS children (
    id BIGSERIAL PRIMARY KEY,
    parent_id BIGINT NOT NULL REFERENCES parents(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    pin_hash TEXT NOT NULL,
    avatar TEXT DEFAULT 'lion',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- progress table
CREATE TABLE IF NOT EXISTS progress (
    id BIGSERIAL PRIMARY KEY,
    child_id BIGINT NOT NULL REFERENCES children(id) ON DELETE CASCADE,
    topic TEXT NOT NULL,
    questions_completed INTEGER DEFAULT 0,
    quiz_score INTEGER DEFAULT 0,
    quiz_taken INTEGER DEFAULT 0,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(child_id, topic)
);

-- quiz_results table
CREATE TABLE IF NOT EXISTS quiz_results (
    id BIGSERIAL PRIMARY KEY,
    child_id BIGINT NOT NULL REFERENCES children(id) ON DELETE CASCADE,
    topic TEXT NOT NULL,
    score INTEGER NOT NULL,
    total INTEGER NOT NULL,
    taken_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- achievements table
CREATE TABLE IF NOT EXISTS achievements (
    id BIGSERIAL PRIMARY KEY,
    child_id BIGINT NOT NULL REFERENCES children(id) ON DELETE CASCADE,
    badge TEXT NOT NULL,
    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- exam_results table
CREATE TABLE IF NOT EXISTS exam_results (
    id BIGSERIAL PRIMARY KEY,
    child_id BIGINT NOT NULL REFERENCES children(id) ON DELETE CASCADE,
    score INTEGER NOT NULL,
    total INTEGER NOT NULL,
    percentage INTEGER NOT NULL,
    passed INTEGER NOT NULL,
    answers_json TEXT,
    taken_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- access_codes table
CREATE TABLE IF NOT EXISTS access_codes (
    id BIGSERIAL PRIMARY KEY,
    code TEXT UNIQUE NOT NULL,
    used INTEGER DEFAULT 0,
    used_by_parent_id BIGINT REFERENCES parents(id),
    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

def init_db():
    """Create all tables in PostgreSQL."""
    conn = get_db()
    c = conn.cursor()
    c.execute(CREATE_TABLES_SQL)
    conn.commit()
    conn.close()
