"""FastAPI entry point for the DUMMY-only demo."""

import json
from pathlib import Path
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, StreamingResponse
import io
import qrcode
from fastapi.templating import Jinja2Templates

from .db import connect, init_db, row_json
from .services.canonical import canonicalize
from .services.crypto import digest, load_or_generate_key, verify
from .services.fraud import flags
from .services.ledger import check

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


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    db = connect()
    deeds = [row_json(row) for row in db.execute("SELECT * FROM deeds ORDER BY deed_id LIMIT 20")]
    return templates.TemplateResponse(request=request, name="home.html",
                                      context={"deeds": deeds, "dummy": True})


@app.get("/verify/{deed_id}", response_class=HTMLResponse)
def verify_page(request: Request, deed_id: str, altered: int = 0):
    db = connect()
    deed = get_deed(db, deed_id)
    result = "NOT FOUND"
    if deed:
        source = json.loads(deed["deed_json"])
        if altered:
            source["dag_no"] = str(source["dag_no"]) + "9"
        result = "AUTHENTIC" if digest(canonicalize({k: v for k, v in source.items()
            if k not in ("deed_hash", "signature")})) == deed["deed_hash"] and verify(
                PUBLIC, deed["deed_hash"], deed["signature"]) else "ALTERED"
    return templates.TemplateResponse(request=request, name="verify.html",
                                      context={"deed": deed, "result": result,
                                               "altered": altered, "dummy": True})


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
    all_deeds = [row_json(r) for r in db.execute("SELECT * FROM deeds")]
    report_flags = flags(plot_data, all_deeds[:-1], deeds[-1]) if plot_data and deeds else []
    return templates.TemplateResponse(request=request, name="report.html",
        context={"plot": plot_data, "deeds": deeds, "flags": report_flags, "dummy": True})


@app.get("/health")
def health():
    db = connect()
    return {"status": "ok", "dummy": True, "ledger": check(db)}
