"""SQLite persistence. All records in this prototype are synthetic."""

import json
import sqlite3
from pathlib import Path
from typing import Any

DB_PATH = Path("data/deedguard.sqlite3")


def connect(path: Path = DB_PATH) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    return db


def init_db(db: sqlite3.Connection) -> None:
    db.executescript("""
    CREATE TABLE IF NOT EXISTS plots (
      plot_id TEXT PRIMARY KEY, area REAL NOT NULL, survey_type TEXT NOT NULL,
      mouza TEXT NOT NULL, upazila TEXT NOT NULL, district TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'CLEAR', pending_case INTEGER NOT NULL DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS deeds (
      deed_id TEXT PRIMARY KEY, plot_id TEXT NOT NULL, deed_json TEXT NOT NULL,
      deed_hash TEXT NOT NULL, signature TEXT NOT NULL, registered_at TEXT NOT NULL,
      seller TEXT NOT NULL, buyer TEXT NOT NULL, area REAL NOT NULL,
      mutation_status TEXT NOT NULL DEFAULT 'PENDING'
    );
    CREATE TABLE IF NOT EXISTS ledger (
      sequence INTEGER PRIMARY KEY AUTOINCREMENT, deed_id TEXT NOT NULL,
      deed_hash TEXT NOT NULL, signature TEXT NOT NULL, timestamp TEXT NOT NULL,
      prev_entry_hash TEXT NOT NULL, entry_hash TEXT NOT NULL
    );
    """)
    db.commit()


def row_json(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)


def insert_plot(db: sqlite3.Connection, plot: dict[str, Any]) -> None:
    fields = "plot_id,area,survey_type,mouza,upazila,district,status,pending_case"
    db.execute(f"INSERT OR REPLACE INTO plots ({fields}) VALUES (?,?,?,?,?,?,?,?)",
               tuple(plot.get(field, 0 if field == "pending_case" else "CLEAR")
                     for field in fields.split(",")))


def insert_deed(db: sqlite3.Connection, deed: dict[str, Any]) -> None:
    db.execute("""INSERT OR REPLACE INTO deeds
      (deed_id,plot_id,deed_json,deed_hash,signature,registered_at,seller,buyer,area,mutation_status)
      VALUES (?,?,?,?,?,?,?,?,?,?)""",
      (deed["deed_id"], deed["plot_id"], json.dumps(deed, ensure_ascii=False),
       deed["deed_hash"], deed["signature"], deed["registered_at"], deed["seller"],
       deed["buyer"], deed["area"], deed.get("mutation_status", "PENDING")))
