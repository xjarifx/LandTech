"""Hash-chained append-only ledger operations."""

import hashlib
import json
import sqlite3
from datetime import datetime, timezone

from .crypto import sign


def append(db: sqlite3.Connection, deed_id: str, deed_hash: str,
           signature: str, now: str | None = None) -> dict:
    now = now or datetime.now(timezone.utc).isoformat()
    previous = db.execute("SELECT entry_hash FROM ledger ORDER BY sequence DESC LIMIT 1").fetchone()
    prev_hash = previous["entry_hash"] if previous else ""
    body = json.dumps([deed_id, deed_hash, signature, now, prev_hash],
                      separators=(",", ":"))
    entry_hash = hashlib.sha256(body.encode()).hexdigest()
    db.execute("""INSERT INTO ledger
      (deed_id,deed_hash,signature,timestamp,prev_entry_hash,entry_hash)
      VALUES (?,?,?,?,?,?)""", (deed_id, deed_hash, signature, now, prev_hash, entry_hash))
    return {"deed_id": deed_id, "entry_hash": entry_hash}


def check(db: sqlite3.Connection) -> dict:
    rows = db.execute("SELECT * FROM ledger ORDER BY sequence").fetchall()
    previous = ""
    for row in rows:
        body = json.dumps([row["deed_id"], row["deed_hash"], row["signature"],
                           row["timestamp"], row["prev_entry_hash"]], separators=(",", ":"))
        expected = hashlib.sha256(body.encode()).hexdigest()
        if row["prev_entry_hash"] != previous or row["entry_hash"] != expected:
            return {"valid": False, "broken_sequence": row["sequence"],
                    "message": "Ledger link or entry hash is broken."}
        previous = row["entry_hash"]
    return {"valid": True, "entries": len(rows)}
