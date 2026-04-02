"""Lightweight SQL migration runner for ClassGen.

Usage:
    python -m migrations.runner          # apply pending migrations
    python -m migrations.runner status   # show applied/pending

Connects directly to Postgres (not PostgREST) via DATABASE_URL.
"""

import os
import pathlib
import sys

import psycopg

MIGRATIONS_DIR = pathlib.Path(__file__).parent


def get_dsn() -> str:
    if dsn := os.environ.get("DATABASE_URL"):
        return dsn
    pw = os.environ.get("POSTGRES_PASSWORD", "postgres")
    host = os.environ.get("POSTGRES_HOST", "db")
    return f"postgresql://postgres:{pw}@{host}:5432/classgen"


def run():
    mode = sys.argv[1] if len(sys.argv) > 1 else "apply"
    dsn = get_dsn()

    conn = psycopg.connect(dsn, autocommit=False)

    # Ensure tracking table exists
    conn.execute("""
        CREATE TABLE IF NOT EXISTS _migrations (
            id serial PRIMARY KEY,
            name text UNIQUE NOT NULL,
            applied_at timestamptz DEFAULT now()
        )
    """)
    conn.commit()

    applied = {row[0] for row in conn.execute("SELECT name FROM _migrations").fetchall()}
    files = sorted(MIGRATIONS_DIR.glob("[0-9]*.sql"))

    if mode == "status":
        for f in files:
            tag = "applied" if f.stem in applied else "pending"
            print(f"  {f.name:40s} [{tag}]")
        conn.close()
        return

    pending = [f for f in files if f.stem not in applied]
    if not pending:
        print("All migrations applied.")
        conn.close()
        return

    for f in pending:
        print(f"Applying {f.name} ...")
        sql = f.read_text()
        try:
            conn.execute(sql)
            conn.execute("INSERT INTO _migrations (name) VALUES (%s)", [f.stem])
            conn.commit()
            print(f"  OK")
        except Exception as e:
            conn.rollback()
            print(f"  FAILED: {e}", file=sys.stderr)
            conn.close()
            sys.exit(1)

    print(f"Applied {len(pending)} migration(s).")
    conn.close()


if __name__ == "__main__":
    run()
