"""Discovery, agent-to-agent pre-dates, mutual opt-in, booking and the strategy simulation."""

import json
import re
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Any

from . import audit, config, core, integrations, llm

RUNS: dict[str, dict[str, Any]] = {}
BOOKINGS: dict[str, dict[str, Any]] = {}
VENUES: list[dict[str, Any]] = []

ATTR_WORDS = {"smokes": ["smok", "cigarette", "vape"], "wants_kids": ["kid", "children"],
              "drinks": ["drink", "sober", "wine", "beer"], "pets": ["dog", "cat", "pet"],
              "religion_important": ["faith", "church", "relig", "god", "temple", "mosque"],
              "early_bird": ["morning", "early", "sunrise", "night owl"]}


def load_venues() -> None:
    path = config.DATA / "venues.json"
    if path.exists():
        VENUES[:] = json.loads(path.read_text())


# ---------------------------------------------------------------- search

def search(pid: str) -> dict[str, Any]:
    me = core.PERSONAS[pid]
    policy = integrations.match_policy(pid)
    strategy = integrations.strategy(pid)
    run_id = audit.new_run_id()
    RUNS[run_id] = {"owner": pid, "strategy": strategy, "policy": policy, "predates": {}, "accepted": set()}
    audit.log(run_id, "policy_loaded", "statsig", None, None, policy=policy, strategy=strategy,
              live=integrations._statsig is not None)
    query = core.seeking_text(me)
    qv, emodel, ems = llm.embed([query], is_query=True)
    with audit.timer() as t:
        rows = core.DIRECTORY.search(me, qv[0], int(policy["candidate_pool"]))
    audit.log(run_id, "vector_search", f"agent:{pid}", emodel, ems + t["ms"], backend=core.DIRECTORY.name,
              filters={"age": [me["seeking"]["min_age"], me["seeking"]["max_age"]], "genders": me["seeking"]["genders"],
                       "verified_only": True, "mutual_preferences": True},
              results=[{"agent_id": r["agent_id"], "sim": round(r["sim"], 4)} for r in rows])
    scores, rmodel, rms = llm.rerank(query, [(r["agent_id"], r["summary"]) for r in rows])
    reranked = sorted(rows, key=lambda r: -scores.get(r["agent_id"], 0))
    keep = reranked[: int(policy["rerank_keep"])]
    candidates = []
    for new_rank, r in enumerate(keep, 1):
        old_rank = next(i for i, x in enumerate(rows, 1) if x["agent_id"] == r["agent_id"])
        candidates.append({"agent_id": r["agent_id"], "alias": r["alias"], "age": r["age"],
                           "neighborhood": r["neighborhood"], "summary": r["summary"],
                           "vector_rank": old_rank, "vector_score": round(r["sim"], 4),
                           "rerank_rank": new_rank, "rerank_score": round(scores.get(r["agent_id"], 0), 4)})
    audit.log(run_id, "rerank", f"agent:{pid}", rmodel, rms,
              moves=[f"{c['agent_id']}: #{c['vector_rank']} -> #{c['rerank_rank']}" for c in candidates])
    integrations.track_llm(pid, "embed_query", emodel, ems)
    integrations.track_llm(pid, "rerank", rmodel, rms)
    integrations.track(pid, "match_search_run", strategy=strategy, pool=len(rows), kept=len(candidates),
                       directory=core.DIRECTORY.name)
    RUNS[run_id]["candidates"] = candidates
    return {"run_id": run_id, "strategy": strategy, "candidates": candidates}


# ---------------------------------------------------------------- pre-date

VERDICT_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["score", "recommend", "reasons", "concerns"],
    "properties": {
        "score": {"type": "integer"},
        "recommend": {"type": "boolean"},
        "reasons": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["claim", "my_fact_id", "their_quote"],
            "properties": {"claim": {"type": "string"}, "my_fact_id": {"type": "string"},
                           "their_quote": {"type": "string"}}}},
        "concerns": {"type": "array", "items": {"type": "string"}},
    },
}


def _facts_block(p: dict[str, Any]) -> str:
    return "\n".join(f"- [{f['id']}] ({f['field']}) {f['value']}" for f in core.shareable_facts(p))


NAME_RULE = ("You may call both people by their first names; never reveal last names." if config.REAL_NAMES
             else "Never reveal names.")


def _system(p: dict[str, Any], words: int) -> str:
    dbs = ", ".join(d["label"] for d in p.get("dealbreakers", [])) or "none stated"
    return (f"You are the personal dating agent for {p['alias']} ({p['age']}, {p['neighborhood']}). "
            f"You are chatting with another person's agent to decide whether the two humans should meet.\n"
            f"What you know about your owner (fact ids in brackets):\n{_facts_block(p)}\n"
            f"Interests: {', '.join(p.get('interests', []))}. Deal-breakers: {dbs}.\n"
            f"Rules: {NAME_RULE} Never reveal contact details, employer, health details or exact address. Answer the other agent "
            "honestly, including about smoking, kids, drinking and pets. If you don't know, say so; never invent. "
            "Ask about your owner's deal-breakers early. Be warm and specific. "
            f"Reply with one message under {words} words, no preamble.")


def _live_turn(speaker: dict, other: dict, transcript: list[dict], words: int, run_id: str) -> str | None:
    msgs = [{"role": "system", "content": _system(speaker, words)}]
    last_other = next((m["text"] for m in reversed(transcript) if m["from"] == other["id"]), None)
    if last_other:
        with audit.timer() as rt:
            snippet, src = core.recall(speaker["id"], last_other)
        audit.log(run_id, "memory_recall", f"agent:{speaker['id']}", src, rt["ms"], question=last_other[:200],
                  answer=snippet[:300])
        if snippet:
            msgs[0]["content"] += f"\nFrom your owner's memory, relevant to the latest message: {snippet}"
    for m in transcript:
        msgs.append({"role": "assistant" if m["from"] == speaker["id"] else "user", "content": m["text"]})
    if not transcript:
        msgs.append({"role": "user", "content": "(You speak first. Introduce your owner briefly and ask one question.)"})
    text, model, ms = llm.chat(msgs, max_tokens=220, temperature=0.7)
    if text is None:
        return None
    if not config.REAL_NAMES:  # names stay hidden until both people accept
        for name in (speaker["first_name"], other["first_name"]):
            text = re.sub(rf"\b{re.escape(name)}\b", "my person" if name == speaker["first_name"] else "your person", text)
    integrations.track_llm(speaker["id"], "predate_message", model, ms)
    return text, model, ms


def _shared(a: dict, b: dict) -> list[str]:
    bi = {x.lower() for x in b.get("interests", [])}
    return [x for x in a.get("interests", []) if x.lower() in bi]


def _conflicts(a: dict, b: dict) -> list[dict]:
    """Deal-breakers of a that b violates."""
    return [d for d in a.get("dealbreakers", []) if b.get("attributes", {}).get(d["attr"]) == d.get("equals")]


def _attr_quote(p: dict, attr: str) -> str | None:
    words = ATTR_WORDS.get(attr, [attr])
    for f in p["facts"]:
        if any(w in f["quote"].lower() for w in words):
            return f["quote"]
    for m in p["user_messages"]:
        for s in re.split(r"(?<=[.!?])\s+", m):
            if any(w in s.lower() for w in words):
                return s.strip().rstrip(".!?")
    return None


def _mock_transcript(a: dict, b: dict) -> list[str]:
    ai, bi = a.get("interests", ["good food"]), b.get("interests", ["good food"])
    adb = a.get("dealbreakers") or [{"attr": "wants_kids", "label": "kids"}]
    bdb = b.get("dealbreakers") or [{"attr": "wants_kids", "label": "kids"}]
    shared = _shared(a, b)

    def answer(p: dict, d: dict) -> str:
        q = _attr_quote(p, d["attr"])
        val = p.get("attributes", {}).get(d["attr"])
        if q:
            return f'In their words: "{q}".'
        return f"On {d['label']}: {('yes' if val is True else 'no' if val is False else val) or 'not something they have mentioned'}."

    lines = [
        f"Hi! I'm the agent for {a['alias']}. They're into {', '.join(ai[:3])}. What does your person's ideal weekend look like?",
        f"Hey! My person is into {', '.join(bi[:3])}, so weekends usually involve {bi[0]}. Quick one from my side: how does your person feel about {bdb[0]['label']}?",
        f"{answer(a, bdb[0])} And the same question back, since it matters to my person: what about {adb[0]['label']}?",
        f"Honest answer. {answer(b, adb[0])}",
    ]
    if _conflicts(a, b):
        lines += [f"Thanks for being upfront. {adb[0]['label'].capitalize()} is a deal-breaker for my person, so I'll pass this time.",
                  "Totally understood. Appreciate the honesty, and good luck to your person!"]
    elif shared:
        lines += [f"Love that. Sounds like they'd both enjoy {', '.join(shared[:2])}. Would your person be up for a first date around that?",
                  f"Absolutely. {shared[0].capitalize()} would be a great first date for them. I'd recommend they meet."]
    else:
        lines += ["Different interests, but that can be fun. Any shared values you think would click?",
                  "Maybe. I'm not sure there's enough overlap yet, but I'm open to it."]
    return lines


def _mock_verdict(me: dict, other: dict, their_text: str) -> dict:
    shared = _shared(me, other)
    conflicts = _conflicts(me, other)
    score = min(95, 52 + 12 * len(shared)) if not conflicts else 15
    reasons = []
    for s in shared[:3]:
        fid = next((f["id"] for f in me["facts"] if s.split()[0].lower() in (f["value"] + f["quote"]).lower()),
                   me["facts"][0]["id"] if me["facts"] else "")
        reasons.append({"claim": f"Both love {s}", "my_fact_id": fid, "their_quote": s})
    concerns = [f"Deal-breaker: {d['label']}" for d in conflicts]
    return {"score": score, "recommend": not conflicts and score >= 70, "reasons": reasons, "concerns": concerns}


def _live_verdict(me: dict, other: dict, transcript: list[dict]) -> tuple[dict | None, str, int]:
    convo = "\n".join(f"{'MY AGENT' if m['from'] == me['id'] else 'THEIR AGENT'}: {m['text']}" for m in transcript)
    out, model, ms = llm.chat(
        [{"role": "system", "content":
          f"You are {me['alias']}'s dating agent. Decide if your owner should go on a first date with the other person. "
          f"Your owner's facts:\n{_facts_block(me)}\nDeal-breakers: "
          f"{', '.join(d['label'] for d in me.get('dealbreakers', [])) or 'none'}.\n"
          "Score 0-100. For each reason cite one of your owner's fact ids and copy an exact short quote from "
          "THEIR AGENT's messages. A violated deal-breaker means recommend=false and score below 30."},
         {"role": "user", "content": convo}],
        schema=VERDICT_SCHEMA, max_tokens=700, temperature=0)
    return out, model, ms


def predate(pid: str, cid: str, run_id: str | None) -> dict[str, Any]:
    a, b = core.PERSONAS[pid], core.PERSONAS[cid]
    if not run_id or run_id not in RUNS:
        run_id = audit.new_run_id()
        RUNS[run_id] = {"owner": pid, "strategy": integrations.strategy(pid),
                        "policy": integrations.match_policy(pid), "predates": {}, "accepted": set()}
    policy = RUNS[run_id]["policy"]
    turns, words = int(policy["a2a_turns"]), int(policy["max_words_per_message"])
    audit.log(run_id, "predate_started", f"agent:{pid}", None, None, with_agent=cid, turns=turns)
    transcript: list[dict[str, Any]] = []
    live_ok = llm.live()
    mock_lines = None
    for turn in range(turns):
        speaker, other = (a, b) if turn % 2 == 0 else (b, a)
        result = _live_turn(speaker, other, transcript, words, run_id) if live_ok else None
        if result is None:
            live_ok = False
            mock_lines = mock_lines or _mock_transcript(a, b)
            text, model, ms = mock_lines[min(turn, len(mock_lines) - 1)], "local:scripted-agent", 0
        else:
            text, model, ms = result
        transcript.append({"turn": turn, "from": speaker["id"], "alias": speaker["alias"], "text": text})
        audit.log(run_id, "a2a_message", f"agent:{speaker['id']}", model, ms, turn=turn, text=text)
    verdicts: dict[str, Any] = {}
    live_verdicts: dict[str, tuple] = {}
    if live_ok:  # both agents judge at the same time
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = {me["id"]: pool.submit(_live_verdict, me, other, transcript) for me, other in ((a, b), (b, a))}
            live_verdicts = {k: f.result() for k, f in futures.items()}
    for me, other in ((a, b), (b, a)):
        their_text = " ".join(m["text"] for m in transcript if m["from"] == other["id"])
        v, model, ms = live_verdicts.get(me["id"], (None, "local:rule-verdict", 0))
        if v is None:
            v, model = _mock_verdict(me, other, their_text), "local:rule-verdict"
        valid_ids = {f["id"] for f in me["facts"]}
        before = len(v["reasons"])
        v["reasons"] = [r for r in v["reasons"] if core.traceable(r["their_quote"], [their_text]) or
                        core.norm(r["their_quote"]) in core.norm(their_text)]
        for r in v["reasons"]:
            if r["my_fact_id"] not in valid_ids:
                r["my_fact_id"] = ""
        audit.log(run_id, "verdict", f"agent:{me['id']}", model, ms, score=v["score"], recommend=v["recommend"],
                  reasons_kept=len(v["reasons"]), reasons_dropped_untraceable=before - len(v["reasons"]))
        conflicts = _conflicts(me, other)
        if conflicts:
            v["recommend"] = False
            v["score"] = min(int(v["score"]), 20)
            for d in conflicts:
                msg = f"Deal-breaker: {d['label']}"
                if not any(d["label"].lower() in c.lower() for c in v["concerns"]):
                    v["concerns"].append(msg)
            audit.log(run_id, "dealbreaker_guard", f"agent:{me['id']}", "rule", None,
                      violated=[d["label"] for d in conflicts], evidence=_attr_quote(other, conflicts[0]["attr"]))
        verdicts[me["id"]] = v
    threshold = float(policy["min_score"])
    avg = round(sum(v["score"] for v in verdicts.values()) / 2, 1)
    is_match = all(v["recommend"] for v in verdicts.values()) and avg >= threshold
    RUNS[run_id]["predates"][cid] = {"match": is_match, "verdicts": verdicts}
    audit.log(run_id, "match_decision", "system", None, None, match=is_match, avg_score=avg, threshold=threshold)
    integrations.track(pid, "pre_date_completed", strategy=RUNS[run_id]["strategy"], turns=turns, avg_score=avg,
                       match=is_match, live=live_ok)
    if is_match:
        integrations.track(pid, "match_proposed", strategy=RUNS[run_id]["strategy"])
    return {"run_id": run_id, "transcript": transcript, "verdicts": verdicts, "match": is_match,
            "avg_score": avg, "threshold": threshold}


def accept(pid: str, cid: str, run_id: str) -> dict[str, Any]:
    run = RUNS.get(run_id)
    pre = (run or {}).get("predates", {}).get(cid)
    if not pre:
        raise ValueError("Run the pre-date before accepting.")
    their_yes = pre["verdicts"][cid]["recommend"]
    audit.log(run_id, "human_opt_in", f"human:{pid}", None, None, accepted=True)
    audit.log(run_id, "human_opt_in", f"human:{cid}", None, None, accepted=their_yes,
              note="simulated: the other person accepts when their agent recommended the match")
    both = bool(pre["match"] and their_yes)
    revealed = {}
    if both:
        run["accepted"].add(cid)
        revealed = {pid: core.PERSONAS[pid]["first_name"], cid: core.PERSONAS[cid]["first_name"]}
        audit.log(run_id, "identity_revealed", "system", None, None, agents=[pid, cid])
        integrations.track(pid, "match_accepted", strategy=run["strategy"])
    return {"both_accepted": both, "revealed": revealed}


# ---------------------------------------------------------------- booking

def _slots(p: dict) -> list[datetime]:
    return sorted(datetime.fromisoformat(s) for s in p.get("free_slots", []))


def book(pid: str, cid: str, run_id: str) -> dict[str, Any]:
    run = RUNS.get(run_id)
    if not run or cid not in run["accepted"]:
        raise ValueError("Both people need to accept before booking.")
    a, b = core.PERSONAS[pid], core.PERSONAS[cid]
    interests = {x.lower() for x in a.get("interests", []) + b.get("interests", [])}
    shared = {x.lower() for x in _shared(a, b)}

    def score(v: dict) -> float:
        tags = {t.lower() for t in v.get("tags", [])}
        return 3 * len(tags & shared) + len(tags & interests) + (1 if "first date" in v.get("good_for", []) else 0)

    ranked = sorted(VENUES, key=score, reverse=True)
    venue = ranked[0] if ranked else {"name": "Ocean Beach bonfire pit", "neighborhood": "Outer Sunset", "tags": []}
    matched_tags = [t for t in venue.get("tags", []) if t.lower() in shared or t.lower() in interests]
    audit.log(run_id, "venue_selected", "agent:booking", "rule", None, venue=venue.get("name"),
              matched_tags=matched_tags, considered=[v["name"] for v in ranked[:5]])
    common = sorted(set(_slots(a)) & set(_slots(b)))
    start = common[0] if common else (_slots(a) or [datetime(2026, 11, 22, 18, 0)])[0]
    audit.log(run_id, "time_selected", "agent:booking", "rule", None, start=start.isoformat(),
              common_slots=[s.isoformat() for s in common], fallback=not common)
    bid = uuid.uuid4().hex[:10]
    why = (f"Both of you are into {', '.join(sorted(shared)) or 'trying new things'}; "
           f"{venue['name']} is known for {', '.join(venue.get('tags', [])[:3])}.")
    booking = {"id": bid, "venue": {"name": venue["name"], "neighborhood": venue.get("neighborhood", ""),
                                    "tags": venue.get("tags", []), "why": why},
               "start": start.isoformat(), "end": (start + timedelta(hours=2)).isoformat(),
               "ics_path": f"/api/bookings/{bid}.ics", "people": [a["first_name"], b["first_name"]],
               "simulated_reservation": True}
    BOOKINGS[bid] = booking
    audit.log(run_id, "date_booked", "agent:booking", None, None, booking_id=bid, venue=venue["name"],
              start=booking["start"], note="reservation simulated for the demo")
    integrations.track(pid, "date_booked", strategy=run["strategy"], venue=venue["name"])
    return {"booking": booking}


def ics(bid: str) -> str:
    b = BOOKINGS[bid]
    fmt = lambda s: datetime.fromisoformat(s).strftime("%Y%m%dT%H%M%S")  # noqa: E731
    return "\r\n".join([
        "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Wingmate//EN", "BEGIN:VEVENT",
        f"UID:{bid}@wingmate.local", f"DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}",
        f"DTSTART;TZID={config.TIMEZONE}:{fmt(b['start'])}", f"DTEND;TZID={config.TIMEZONE}:{fmt(b['end'])}",
        f"SUMMARY:First date: {' & '.join(b['people'])} at {b['venue']['name']}",
        f"LOCATION:{b['venue']['name']}, {b['venue']['neighborhood']}, San Francisco",
        f"DESCRIPTION:{b['venue']['why']} (Booked by Wingmate agents)", "END:VEVENT", "END:VCALENDAR", ""])


# ---------------------------------------------------------------- simulation

def simulate() -> dict[str, Any]:
    """Counterfactual run over all synthetic personas with the local agents (fast and free).
    vector_only proposes the top vector match directly; agent_predate proposes only after a pre-date."""
    out = {arm: {"searched": 0, "proposed": 0, "mutual_accept": 0, "booked": 0} for arm in ("vector_only", "agent_predate")}
    run_id = audit.new_run_id()
    for pid, me in core.PERSONAS.items():
        cands = core.DIRECTORY.search(me, _local_query(me), 3)
        if not cands:
            continue
        for arm in out:
            out[arm]["searched"] += 1
            pick = None
            if arm == "vector_only":
                pick = cands[0]["agent_id"]
            else:
                for c in cands:
                    o = core.PERSONAS[c["agent_id"]]
                    if not _conflicts(me, o) and not _conflicts(o, me) and len(_shared(me, o)) >= 1:
                        pick = c["agent_id"]
                        break
            if not pick:
                continue
            out[arm]["proposed"] += 1
            o = core.PERSONAS[pick]
            accepts = not _conflicts(me, o) and not _conflicts(o, me) and len(_shared(me, o)) >= 1
            if accepts:
                out[arm]["mutual_accept"] += 1
                out[arm]["booked"] += 1
            integrations.track(pid, "simulated_match", strategy=arm, accepted=accepts, synthetic=True)
    audit.log(run_id, "simulation", "system", "local:rule-agents", None, result=out)
    return {"by_strategy": out, "synthetic": True, "run_id": run_id}


def _local_query(me: dict):
    vec = core.DIRECTORY.cards[me["id"]]["embedding"] if hasattr(core.DIRECTORY, "cards") else None
    if vec is None:
        qv, _, _ = llm.embed([core.seeking_text(me)], is_query=True)
        vec = qv[0]
    return vec
