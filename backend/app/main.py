"""Wingmate API. Run: uv run uvicorn app.main:app --reload --port 8000"""

import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel

from . import audit, config, core, importer, integrations, llm, match


@asynccontextmanager
async def lifespan(_: FastAPI):
    core.load_personas()
    match.load_venues()
    if integrations.cognee_enabled():
        def warm():
            # Build memory graphs for the demo persona and her likely candidates first; the rest
            # fall back to vector memory recall so startup stays cheap.
            for pid in config.WARM_MEMORY:
                if pid in core.PERSONAS:
                    core.ingest_memory(pid)
        threading.Thread(target=warm, daemon=True).start()
    yield
    integrations.shutdown()


app = FastAPI(title="Wingmate", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def _persona(pid: str) -> dict:
    p = core.PERSONAS.get(pid)
    if not p:
        raise HTTPException(404, f"No persona '{pid}'.")
    return p


class PasteBody(BaseModel):
    text: str


class FactPatch(BaseModel):
    approved: bool | None = None
    share: str | None = None
    value: str | None = None


class CandidateBody(BaseModel):
    candidate_id: str
    run_id: str | None = None


@app.get("/api/status")
def status():
    return {"sponsors": {"sie": llm.live(), "singlestore": core.DIRECTORY.name == "singlestore",
                         "cognee": integrations.cognee_enabled(), "statsig": integrations._statsig is not None,
                         "amplitude": integrations._amp is not None},
            "demo_persona": config.DEMO_PERSONA}


@app.get("/api/personas")
def personas():
    return [core.summary_of(p) for p in core.PERSONAS.values()]


@app.get("/api/personas/{pid}")
def persona(pid: str):
    return core.detail_of(_persona(pid))


@app.post("/api/personas/{pid}/import/paste")
def import_paste(pid: str, body: PasteBody):
    _persona(pid)
    try:
        return importer.import_paste(pid, body.text)
    except ValueError as exc:
        raise HTTPException(400, str(exc))


@app.post("/api/personas/{pid}/import/export")
async def import_export(pid: str, file: UploadFile = File(...)):
    _persona(pid)
    raw = await file.read()
    try:
        return importer.import_export(pid, raw, file.filename or "conversations.json")
    except (ValueError, KeyError) as exc:
        raise HTTPException(400, f"Couldn't read that export: {exc}")


@app.get("/api/personas/{pid}/import/sample")
def import_sample(pid: str):
    path = config.DATA / "exports" / f"{pid}_chatgpt_conversations.json"
    if not path.exists():
        path = config.DATA / "exports" / f"{config.DEMO_PERSONA}_chatgpt_conversations.json"
    if not path.exists():
        raise HTTPException(404, "Sample export not generated yet.")
    return FileResponse(path, media_type="application/json", filename="conversations.json")


@app.patch("/api/personas/{pid}/facts/{fid}")
def patch_fact(pid: str, fid: str, body: FactPatch):
    _persona(pid)
    f = core.update_fact(pid, fid, body.model_dump())
    if not f:
        raise HTTPException(404, "Fact not found.")
    return f


@app.delete("/api/personas/{pid}/facts/{fid}")
def delete_fact(pid: str, fid: str):
    _persona(pid)
    if not core.delete_fact(pid, fid):
        raise HTTPException(404, "Fact not found.")
    return {"ok": True}


@app.post("/api/personas/{pid}/publish")
def publish(pid: str):
    _persona(pid)
    out = core.publish(pid)
    if integrations.cognee_enabled():
        threading.Thread(target=core.ingest_memory, args=(pid,), daemon=True).start()
    return out


@app.post("/api/personas/{pid}/verify")
def verify(pid: str):
    _persona(pid)
    return core.set_verified(pid)


@app.post("/api/match/{pid}/search")
def search(pid: str):
    _persona(pid)
    return match.search(pid)


@app.post("/api/match/{pid}/predate")
def predate(pid: str, body: CandidateBody):
    _persona(pid)
    _persona(body.candidate_id)
    return match.predate(pid, body.candidate_id, body.run_id)


@app.post("/api/match/{pid}/accept")
def accept(pid: str, body: CandidateBody):
    try:
        return match.accept(pid, body.candidate_id, body.run_id or "")
    except ValueError as exc:
        raise HTTPException(400, str(exc))


@app.post("/api/match/{pid}/book")
def book(pid: str, body: CandidateBody):
    try:
        return match.book(pid, body.candidate_id, body.run_id or "")
    except ValueError as exc:
        raise HTTPException(400, str(exc))


@app.get("/api/bookings/{bid}.ics")
def booking_ics(bid: str):
    if bid not in match.BOOKINGS:
        raise HTTPException(404, "Booking not found.")
    return PlainTextResponse(match.ics(bid), media_type="text/calendar",
                             headers={"Content-Disposition": f'attachment; filename="wingmate-{bid}.ics"'})


@app.get("/api/bookings/{bid}")
def booking(bid: str):
    if bid not in match.BOOKINGS:
        raise HTTPException(404, "Booking not found.")
    return match.BOOKINGS[bid]


@app.get("/api/audit/{run_id}")
def audit_events(run_id: str):
    return audit.events(run_id)


@app.get("/api/config")
def get_config(persona_id: str = config.DEMO_PERSONA):
    return {"policy": integrations.match_policy(persona_id), "strategy": integrations.strategy(persona_id),
            "statsig_live": integrations._statsig is not None}


@app.post("/api/reset")
def reset():
    """Reload the seed personas so the demo can be rehearsed from a clean state."""
    core.PERSONAS.clear()
    match.RUNS.clear()
    core.load_personas()
    return {"ok": True, "personas": len(core.PERSONAS)}


@app.post("/api/simulate")
def simulate():
    return match.simulate()
