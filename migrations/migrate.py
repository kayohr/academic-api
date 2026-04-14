#!/usr/bin/env python3
"""
Migration runner — aplica ou reverte arquivos SQL numerados em ordem.

Uso:
  python migrations/migrate.py up       # aplica todas as pendentes
  python migrations/migrate.py down     # reverte a última
  python migrations/migrate.py status   # mostra quais foram aplicadas
"""

import os
import sys
import glob
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
MIGRATIONS_DIR = Path(__file__).parent


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def ensure_migrations_table(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(255) PRIMARY KEY,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
    conn.commit()


def get_applied(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT version FROM schema_migrations ORDER BY version")
        return {row[0] for row in cur.fetchall()}


def get_migration_files():
    files = sorted(glob.glob(str(MIGRATIONS_DIR / "*.up.sql")))
    return [(Path(f).name.replace(".up.sql", ""), f) for f in files]


def apply(conn, version, filepath):
    print(f"  → Applying {version}...")
    with open(filepath) as f:
        sql = f.read()
    with conn.cursor() as cur:
        cur.execute(sql)
        cur.execute(
            "INSERT INTO schema_migrations (version) VALUES (%s)", (version,)
        )
    conn.commit()
    print(f"  ✓ {version} applied")


def revert(conn, version, filepath):
    down_path = filepath.replace(".up.sql", ".down.sql")
    if not os.path.exists(down_path):
        print(f"  ✗ No down migration found for {version}")
        sys.exit(1)
    print(f"  → Reverting {version}...")
    with open(down_path) as f:
        sql = f.read()
    with conn.cursor() as cur:
        cur.execute(sql)
        cur.execute("DELETE FROM schema_migrations WHERE version = %s", (version,))
    conn.commit()
    print(f"  ✓ {version} reverted")


def cmd_up():
    conn = get_connection()
    ensure_migrations_table(conn)
    applied = get_applied(conn)
    migrations = get_migration_files()
    pending = [(v, f) for v, f in migrations if v not in applied]

    if not pending:
        print("Nothing to migrate — all migrations already applied.")
        return

    print(f"Applying {len(pending)} migration(s)...")
    for version, filepath in pending:
        apply(conn, version, filepath)
    print("Done.")
    conn.close()


def cmd_down():
    conn = get_connection()
    ensure_migrations_table(conn)
    applied = get_applied(conn)
    migrations = get_migration_files()
    applied_migrations = [(v, f) for v, f in migrations if v in applied]

    if not applied_migrations:
        print("Nothing to revert.")
        return

    version, filepath = applied_migrations[-1]
    revert(conn, version, filepath)
    conn.close()


def cmd_status():
    conn = get_connection()
    ensure_migrations_table(conn)
    applied = get_applied(conn)
    migrations = get_migration_files()

    print(f"{'VERSION':<40} {'STATUS'}")
    print("-" * 50)
    for version, _ in migrations:
        status = "applied" if version in applied else "pending"
        print(f"{version:<40} {status}")
    conn.close()


if __name__ == "__main__":
    if not DATABASE_URL:
        print("Error: DATABASE_URL environment variable is not set")
        sys.exit(1)

    command = sys.argv[1] if len(sys.argv) > 1 else "up"

    if command == "up":
        cmd_up()
    elif command == "down":
        cmd_down()
    elif command == "status":
        cmd_status()
    else:
        print(f"Unknown command: {command}. Use: up | down | status")
        sys.exit(1)
