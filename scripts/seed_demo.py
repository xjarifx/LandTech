"""Reset and load deterministic DUMMY scenarios."""

import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))

from app.db import connect, init_db, insert_deed, insert_plot
from app.generator import generate
from app.services.canonical import canonicalize
from app.services.crypto import load_or_generate_key, digest, sign
from app.services.ledger import append

db = connect()
db.executescript("DROP TABLE IF EXISTS ledger; DROP TABLE IF EXISTS deeds; DROP TABLE IF EXISTS plots;")
init_db(db)
private, _ = load_or_generate_key()
plots, deeds = generate()
for plot in plots:
    insert_plot(db, plot)
for deed in deeds:
    deed["deed_hash"] = digest(canonicalize(deed))
    deed["signature"] = sign(private, deed["deed_hash"])
    insert_deed(db, deed)
    append(db, deed["deed_id"], deed["deed_hash"], deed["signature"], deed["registered_at"])
db.commit()
print(f"Loaded {len(plots)} DUMMY plots and {len(deeds)} DUMMY deeds.")
