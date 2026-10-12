import sqlite3

from app.services.canonical import canonicalize
from app.services.crypto import digest, generate_key, sign, verify
from app.services.fraud import flags
from app.services.ledger import append, check


def test_canonicalization_is_order_and_unicode_stable():
    assert canonicalize({"b": "আ", "a": 1}) == canonicalize({"a": 1, "b": "\u0986"})
    assert digest(canonicalize({"x": 1})) == digest(canonicalize({"x": 1}))


def test_fraud_rules():
    plot = {"plot_id": "P-1", "area": 10}
    old = [{"plot_id": "P-1", "seller": "S", "area": 8, "registered_at": "2026-01-01"}]
    candidate = {"plot_id": "P-1", "seller": "S", "area": 8,
                 "registered_at": "2026-01-02", "mutation_status": "PENDING"}
    codes = {flag["code"] for flag in flags(plot, old, candidate)}
    assert {"SAME_SELLER_RESOLD", "OVER_SOLD_AREA", "RAPID_TRANSFER", "NO_MUTATION"} <= codes


def test_signature_and_ledger_tamper_detection():
    private, public = generate_key()
    deed_hash = digest(canonicalize({"deed_id": "D-1", "plot_id": "P-1"}))
    signature = sign(private, deed_hash)
    assert verify(public, deed_hash, signature)
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.execute("""CREATE TABLE ledger (
      sequence INTEGER PRIMARY KEY AUTOINCREMENT, deed_id TEXT, deed_hash TEXT,
      signature TEXT, timestamp TEXT, prev_entry_hash TEXT, entry_hash TEXT)""")
    append(db, "D-1", deed_hash, signature, "2026-01-01")
    db.commit()
    assert check(db)["valid"]
    db.execute("UPDATE ledger SET deed_hash='tampered' WHERE sequence=1")
    assert check(db)["valid"] is False
