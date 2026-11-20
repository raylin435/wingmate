"""Personas, facts, agent cards and memory recall."""

import json
import re
from typing import Any

import numpy as np

from . import audit, config, integrations, llm
from .store import make_directory

PERSONAS: dict[str, dict[str, Any]] = {}
DIRECTORY = make_directory()
_msg_vecs: dict[str, tuple[list[str], np.ndarray]] = {}

FIELDS = ["value", "interest", "lifestyle", "dealbreaker", "logistics", "seeking"]
FACT_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["facts"],
    "properties": {"facts": {"type": "array", "items": {
        "type": "object", "additionalProperties": False,
        "required": ["field", "value", "quote", "share"],
        "properties": {
            "field": {"type": "string", "enum": FIELDS},
            "value": {"type": "string"},
            "quote": {"type": "string"},
            "share": {"type": "string", "enum": ["public", "agent_only", "private"]},
        }}}},
}


def norm(text: str) -> str:
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", text).strip().lower()


def traceable(quote: str, sources: list[str]) -> bool:
    q = norm(quote)
    return len(q) >= 6 and any(q in norm(s) for s in sources)


# ---------------------------------------------------------------- loading

def load_personas() -> None:
    for path in sorted((config.DATA / "personas").glob("*.json")):
        p = json.loads(path.read_text())
        p.setdefault("verified", p["id"] != config.DEMO_PERSONA)
        p["user_messages"] = [m["text"] for m in p.get("chat", []) if m["role"] == "user"]
        p["facts"] = [
            {**f, "id": f"{p['id']}-s{i}", "approved": True, "source": "seed"}
            for i, f in enumerate(p.get("facts", []))
        ]
        p["card_summary"] = ""
        PERSONAS[p["id"]] = p
    run_id = "startup"
    summaries = {pid: build_summary(p)[0] for pid, p in PERSONAS.items()}
    vecs = _cached_embeddings(summaries)
    for pid, p in PERSONAS.items():
        p["card_summary"] = summaries[pid]
        DIRECTORY.upsert(card_for(p), vecs[pid])
    audit.log(run_id, "directory_loaded", "system", backend=DIRECTORY.name, agents=len(PERSONAS))
    print(f"[core] loaded {len(PERSONAS)} personas into {DIRECTORY.name} directory")


def _cached_embeddings(summaries: dict[str, str]) -> dict[str, np.ndarray]:
    model = config.EMBED_MODEL if llm.live() else "local"
    path = config.CACHE / f"cards_{re.sub(r'[^a-z0-9]+', '_', model.lower())}.json"
    cache = json.loads(path.read_text()) if path.exists() else {}
    missing = [pid for pid, s in summaries.items() if cache.get(pid, {}).get("text") != s]
    if missing:
        vecs, used, _ = llm.embed([summaries[pid] for pid in missing])
        if used.startswith("local") and llm.live():
            path = config.CACHE / "cards_local.json"
        for pid, v in zip(missing, vecs):
            cache[pid] = {"text": summaries[pid], "vec": [float(x) for x in v]}
        path.write_text(json.dumps(cache))
    return {pid: np.asarray(cache[pid]["vec"], dtype=np.float32) for pid in summaries}


def summary_of(p: dict[str, Any]) -> dict[str, Any]:
    keys = ["id", "alias", "first_name", "age", "gender", "neighborhood", "verified", "tagline", "avatar_color"]
    return {k: p.get(k) for k in keys}


def detail_of(p: dict[str, Any]) -> dict[str, Any]:
    return summary_of(p) | {"seeking": p["seeking"], "facts": p["facts"], "card_summary": p["card_summary"]}


def card_for(p: dict[str, Any]) -> dict[str, Any]:
    return {"agent_id": p["id"], "alias": p["alias"], "age": p["age"], "gender": p["gender"],
            "neighborhood": p["neighborhood"], "seeks": p["seeking"]["genders"],
            "min_age": p["seeking"]["min_age"], "max_age": p["seeking"]["max_age"],
            "verified": bool(p["verified"]), "summary": p["card_summary"]}


def shareable_facts(p: dict[str, Any], include_agent_only: bool = True) -> list[dict[str, Any]]:
    allowed = {"public", "agent_only"} if include_agent_only else {"public"}
    return [f for f in p["facts"] if f["approved"] and f["share"] in allowed]


def build_summary(p: dict[str, Any]) -> tuple[str, list[str]]:
    facts = shareable_facts(p, include_agent_only=False)
    parts = [f"{p['alias']}, {p['age']}, {p['neighborhood']}."]
    if p.get("interests"):
        parts.append("Into " + ", ".join(p["interests"]) + ".")
    parts += [f["value"].rstrip(".") + "." for f in facts if f["field"] != "dealbreaker"]
    text = " ".join(parts)
    redacted, redactions, _, _ = llm.redact(text, [p["first_name"]])
    return redacted, redactions


def seeking_text(p: dict[str, Any]) -> str:
    facts = [f["value"] for f in shareable_facts(p) if f["field"] in ("seeking", "value", "interest", "lifestyle")]
    return (f"Someone compatible with a {p['age']}-year-old in {p['neighborhood']} who is into "
            + ", ".join(p.get("interests", [])) + ". " + " ".join(facts))


def publish(pid: str) -> dict[str, Any]:
    p = PERSONAS[pid]
    run_id = audit.new_run_id()
    with audit.timer() as t:
        summary, redactions = build_summary(p)
    audit.log(run_id, "card_redacted", f"agent:{pid}", config.PII_MODEL if llm.live() else "local:regex-redact",
              t["ms"], redactions=redactions)
    vecs, model, ms = llm.embed([summary])
    p["card_summary"] = summary
    DIRECTORY.upsert(card_for(p), vecs[0])
    audit.log(run_id, "card_published", f"agent:{pid}", model, ms, backend=DIRECTORY.name, summary=summary)
    integrations.track(pid, "agent_card_published", facts_public=len(shareable_facts(p, False)))
    _msg_vecs.pop(pid, None)
    return {"card_summary": summary, "redactions": redactions, "run_id": run_id}


def set_verified(pid: str, inquiry_id: str | None) -> dict[str, Any]:
    ok, how = integrations.persona_inquiry_passed(inquiry_id)
    run_id = audit.new_run_id()
    audit.log(run_id, "identity_check", f"human:{pid}", None, None, result=how, passed=ok)
    if ok:
        PERSONAS[pid]["verified"] = True
        DIRECTORY.set_verified(pid, True)
        integrations.track(pid, "identity_verified", method=how)
    return {"verified": ok, "method": how}


# ---------------------------------------------------------------- facts

def extract_facts(pid: str, messages: list[tuple[str, str]], source: str, run_id: str) -> tuple[list[dict], int]:
    """messages: (conversation title, user text). Returns (new facts, dropped_untraceable)."""
    p = PERSONAS[pid]
    texts = [m for _, m in messages]
    raw: list[dict[str, Any]] | None = None
    chunks, current = [], ""
    for title, text in messages:
        line = f"[{title}] {text}\n"
        if len(current) + len(line) > 9000 and current:
            chunks.append(current)
            current = ""
        current += line
    if current:
        chunks.append(current)
    model, total_ms = "local:sentence-extractor", 0
    if llm.live():
        raw = []
        for chunk in chunks[:6]:
            out, used, ms = llm.chat(
                [{"role": "system", "content":
                  "You extract dating-relevant facts about a person from their own messages. "
                  "Return 4-12 facts. 'quote' must copy the person's exact words (a short span, 5-25 words). "
                  "'value' is a short normalized statement. Mark health, money and employer details 'private'. "
                  "Mark deal-breakers and kids/smoking/drinking views 'agent_only'. Everything else 'public'."},
                 {"role": "user", "content": chunk}],
                schema=FACT_SCHEMA, max_tokens=1500, temperature=0)
            total_ms += ms
            if out is None:
                raw = None
                break
            model = used
            raw += out.get("facts", [])
    if raw is None:
        raw, model = _heuristic_facts(messages), "local:sentence-extractor"
    kept, dropped = [], 0
    seen = {norm(f["quote"]) for f in p["facts"]}
    for i, f in enumerate(raw):
        if not traceable(f["quote"], texts):
            dropped += 1
            continue
        if norm(f["quote"]) in seen:
            continue
        seen.add(norm(f["quote"]))
        title = next((t for t, m in messages if norm(f["quote"]) in norm(m)), None)
        kept.append({"id": f"{pid}-{source[0]}{len(p['facts']) + len(kept)}", "field": f["field"],
                     "value": f["value"], "quote": f["quote"], "share": "private", "suggested_share": f["share"],
                     "approved": False, "source": source, "source_title": title})
    p["facts"] += kept
    p["user_messages"] += texts
    _msg_vecs.pop(pid, None)
    audit.log(run_id, "facts_extracted", f"agent:{pid}", model, total_ms or None,
              kept=len(kept), dropped_untraceable=dropped, source=source)
    integrations.track_llm(pid, "fact_extraction", model, total_ms)
    return kept, dropped


_PATTERNS = [
    ("dealbreaker", r"\b(deal ?breaker|can't date|could never date|won't date|hard no|never date)\b"),
    ("seeking", r"\b(looking for|want someone|i want a partner|my ideal|i'd love to meet|hoping to find)\b"),
    ("value", r"\b(matters to me|i value|important to me|i believe|family is|honesty)\b"),
    ("logistics", r"\b(weeknights?|evenings?|free on|schedule|live in|moved to|commute)\b"),
    ("lifestyle", r"\b(i (don't|never|rarely) (drink|smoke)|i smoke|sober|vegetarian|vegan|early bird|night owl|my dog|my cat)\b"),
    ("interest", r"\b(i love|i'm into|i am into|obsessed with|my favorite|i've been|weekends|i like to|i enjoy)\b"),
]


def _heuristic_facts(messages: list[tuple[str, str]]) -> list[dict[str, Any]]:
    out = []
    for _, text in messages:
        for sent in re.split(r"(?<=[.!?])\s+", text):
            s = sent.strip()
            if not (12 <= len(s) <= 220):
                continue
            for field, rx in _PATTERNS:
                if re.search(rx, s, re.I):
                    share = "agent_only" if field == "dealbreaker" or re.search(r"smok|drink|kid", s, re.I) else "public"
                    value = s.rstrip(".!?")
                    value = value[:90] + ("…" if len(value) > 90 else "")
                    out.append({"field": field, "value": value, "quote": s.rstrip(".!?"), "share": share})
                    break
    return out[:14]


def update_fact(pid: str, fid: str, changes: dict[str, Any]) -> dict[str, Any] | None:
    for f in PERSONAS[pid]["facts"]:
        if f["id"] == fid:
            for k in ("approved", "share", "value"):
                if changes.get(k) is not None:
                    f[k] = changes[k]
            if changes.get("approved") and f["share"] == "private" and f.get("suggested_share"):
                f["share"] = f["suggested_share"] if changes.get("share") is None else f["share"]
            return f
    return None


def delete_fact(pid: str, fid: str) -> bool:
    p = PERSONAS[pid]
    before = len(p["facts"])
    p["facts"] = [f for f in p["facts"] if f["id"] != fid]
    return len(p["facts"]) < before


# ---------------------------------------------------------------- memory

def ingest_memory(pid: str) -> None:
    """Build the owner's Cognee memory graph from their own messages (best effort, background)."""
    integrations.cognee_ingest(pid, PERSONAS[pid]["user_messages"])


def recall(pid: str, question: str) -> tuple[str, str]:
    """Answer a question about the owner from memory. Returns (snippet, source)."""
    ans = integrations.cognee_recall(pid, question)
    if ans:
        return ans, "cognee"
    p = PERSONAS[pid]
    msgs = p["user_messages"]
    if not msgs:
        return "", "none"
    if pid not in _msg_vecs:
        vecs, _, _ = llm.embed(msgs)
        _msg_vecs[pid] = (msgs, np.stack(vecs))
    msgs, mat = _msg_vecs[pid]
    qv, _, _ = llm.embed([question], is_query=True)
    sims = mat @ qv[0]
    best = [msgs[i] for i in np.argsort(-sims)[:2]]
    return " | ".join(best)[:600], "vector-memory"
