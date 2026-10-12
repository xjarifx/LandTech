from app.services.canonical import canonicalize
from app.services.crypto import digest
from app.services.fraud import flags


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
