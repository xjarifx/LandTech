"""FastAPI entry point for the DUMMY-only demo."""

import json
from datetime import date
from pathlib import Path
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, StreamingResponse
import io
import qrcode
from fastapi.templating import Jinja2Templates

from .db import connect, init_db, insert_deed, row_json
from .services.canonical import canonicalize
from .services.crypto import digest, load_or_generate_key, sign, verify
from .services.fraud import flags
from .services.ledger import append, check

app = FastAPI(title="Daffodil DeedGuard - DUMMY")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
PRIVATE, PUBLIC = load_or_generate_key()


@app.on_event("startup")
def startup() -> None:
    db = connect()
    init_db(db)
    db.close()


def get_deed(db, deed_id: str):
    row = db.execute("SELECT * FROM deeds WHERE deed_id=?", (deed_id,)).fetchone()
    return row_json(row) if row else None


def verify_deed(db, deed: dict, supplied: dict | None = None) -> tuple[str, list[str]]:
    """Recompute a deed and require its ledger entry and office signature."""
    stored = json.loads(deed["deed_json"])
    stored.pop("deed_hash", None)
    stored.pop("signature", None)
    candidate = supplied or stored
    expected = digest(canonicalize(candidate))
    ledger = db.execute("SELECT * FROM ledger WHERE deed_id=?", (deed["deed_id"],)).fetchone()
    valid = (expected == deed["deed_hash"] and ledger is not None
             and ledger["deed_hash"] == deed["deed_hash"]
             and verify(PUBLIC, deed["deed_hash"], deed["signature"]))
    differences = sorted(key for key in set(stored) | set(candidate)
                        if stored.get(key) != candidate.get(key))
    return ("AUTHENTIC" if valid and not differences else "ALTERED"), differences


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    db = connect()
    deeds = [row_json(row) for row in db.execute("SELECT * FROM deeds ORDER BY deed_id LIMIT 20")]
    return templates.TemplateResponse(request=request, name="home.html",
                                      context={"deeds": deeds, "dummy": True})


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(request=request, name="register.html",
                                      context={"dummy": True})


@app.post("/register", response_class=HTMLResponse)
def register(request: Request, plot_id: str = Form(...), seller: str = Form(...),
             buyer: str = Form(...), area: float = Form(...), dag_no: str = Form(...)):
    db = connect()
    plot = db.execute("SELECT * FROM plots WHERE plot_id=?", (plot_id,)).fetchone()
    if not plot:
        return templates.TemplateResponse(request=request, name="register.html",
            context={"error": "Plot not found in the DUMMY registry.", "dummy": True},
            status_code=404)
    next_id = db.execute("SELECT COUNT(*) + 1 AS n FROM deeds").fetchone()["n"]
    deed = {"deed_id": f"NEW-{next_id:04}", "plot_id": plot_id, "seller": seller,
            "buyer": buyer, "area": area, "dag_no": dag_no,
            "father_name": "ডেমো পিতা", "khatian_no": "K-DUMMY",
            "deed_no": f"REG-2026-{next_id:04}", "registration_date": date.today().isoformat(),
            "registered_at": date.today().isoformat(), "mouza": plot["mouza"],
            "upazila": plot["upazila"], "district": plot["district"],
            "survey_type": plot["survey_type"], "sub_registry": "ডেমো সাব-রেজিস্ট্রি অফিস",
            "mutation_status": "PENDING"}
    deed["deed_hash"] = digest(canonicalize(deed))
    deed["signature"] = sign(PRIVATE, deed["deed_hash"])
    insert_deed(db, deed)
    append(db, deed["deed_id"], deed["deed_hash"], deed["signature"], deed["registered_at"])
    db.commit()
    prior = [row_json(row) for row in db.execute(
        "SELECT * FROM deeds WHERE plot_id=? AND deed_id<>?", (plot_id, deed["deed_id"]))]
    warnings = flags(row_json(plot), prior, deed)
    return templates.TemplateResponse(request=request, name="deed.html",
        context={"deed": deed, "warnings": warnings, "dummy": True})


@app.get("/verify/{deed_id}", response_class=HTMLResponse)
def verify_page(request: Request, deed_id: str, altered: int = 0):
    db = connect()
    deed = get_deed(db, deed_id)
    result = "NOT FOUND"
    differences = []
    if deed:
        source = json.loads(deed["deed_json"])
        if altered:
            source["dag_no"] = str(source["dag_no"]) + "9"
        source.pop("deed_hash", None)
        source.pop("signature", None)
        result, differences = verify_deed(db, deed, source)
    return templates.TemplateResponse(request=request, name="verify.html",
                                      context={"deed": deed, "result": result,
                                               "altered": altered, "differences": differences,
                                               "dummy": True})


@app.post("/api/verify/{deed_id}")
async def verify_fields(deed_id: str, request: Request):
    """Verify caller-supplied deed fields without exposing private keys."""
    db = connect()
    deed = get_deed(db, deed_id)
    if not deed:
        return {"result": "NOT FOUND", "differences": []}
    supplied = await request.json()
    supplied.pop("deed_hash", None)
    supplied.pop("signature", None)
    result, differences = verify_deed(db, deed, supplied)
    return {"result": result, "differences": differences, "dummy": True}


@app.get("/deed/{deed_id}/print", response_class=HTMLResponse)
def printable_deed(request: Request, deed_id: str):
    db = connect()
    deed = get_deed(db, deed_id)
    if not deed:
        return HTMLResponse("NOT FOUND", status_code=404)
    return templates.TemplateResponse(request=request, name="deed.html",
        context={"deed": deed, "warnings": [], "dummy": True, "printable": True})


@app.get("/qr/{deed_id}")
def qr_code(deed_id: str, request: Request):
    """Return a QR image containing the public verification URL."""
    db = connect()
    if not get_deed(db, deed_id):
        return HTMLResponse("NOT FOUND", status_code=404)
    image = qrcode.make(str(request.base_url).rstrip("/") + f"/verify/{deed_id}")
    output = io.BytesIO()
    image.save(output, format="PNG")
    return StreamingResponse(io.BytesIO(output.getvalue()), media_type="image/png")


@app.get("/officer", response_class=HTMLResponse)
def officer(request: Request):
    db = connect()
    plots = {r["plot_id"]: row_json(r) for r in db.execute("SELECT * FROM plots")}
    deeds = [row_json(r) for r in db.execute("SELECT * FROM deeds ORDER BY deed_id")]
    flagged = [(d, flags(plots[d["plot_id"]], deeds[:i], d)) for i, d in enumerate(deeds)]
    return templates.TemplateResponse(request=request, name="officer.html",
                                      context={"flagged": flagged, "dummy": True})


@app.get("/report/{plot_id}", response_class=HTMLResponse)
def report(request: Request, plot_id: str):
    db = connect()
    plot = db.execute("SELECT * FROM plots WHERE plot_id=?", (plot_id,)).fetchone()
    deeds = [row_json(r) for r in db.execute("SELECT * FROM deeds WHERE plot_id=? ORDER BY registered_at", (plot_id,))]
    plot_data = row_json(plot) if plot else None
    report_flags = flags(plot_data, deeds[:-1], deeds[-1]) if plot_data and deeds else []
    return templates.TemplateResponse(request=request, name="report.html",
        context={"plot": plot_data, "deeds": deeds, "flags": report_flags, "dummy": True})


@app.get("/health")
def health():
    db = connect()
    return {"status": "ok", "dummy": True, "ledger": check(db)}
