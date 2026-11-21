# Wingmate

**Your agent dates their agent first.** Wingmate is a personal-agent dating platform built at the
Personal Agents Hackathon (AWS Builder Loft, SF, Nov 20 2026).

Each person's agent learns them from conversation, or from an imported ChatGPT or Claude memory.
It searches other people's verified agents and runs a short agent-to-agent "pre-date" to test
values and deal-breakers. When both agents recommend the match and both humans accept, it books the
first date. Every step is written to an audit trail you can inspect.

All people in this repo are fictional. No real dating or chat data is used.

## How it works

```
01 Chat or import memory ─► 02 Memory graph ─► 03 Facts with quotes ─► 04 Public agent card
        (ChatGPT/Claude)        (Cognee)          (SIE extract + redact)    (SIE embed → SingleStore)
                                                                                   │
08 Book the date ◄─ 07 Both humans opt in ◄─ 06 Agent ↔ agent pre-date ◄─ 05 Filter → vector → rerank
   (venue + .ics)      (names revealed)         (SIE chat + memory recall)    (SingleStore + SIE score)

Across every step: Statsig match policy + experiment · Amplitude events · verified-only discovery · audit trail
```

**Reliable context.** Every fact the agent holds carries the exact words it came from. Facts that
can't be traced back to the owner's own messages are dropped, and the count is shown. Verdict reasons
must quote the other agent's actual messages. Imported facts stay private until the owner approves them.

**Meaningful action.** The booking agent picks a venue from shared interests and a time both calendars
allow, then writes a calendar invite. Reservations are simulated in this demo.

**Visible steps.** The audit timeline shows each search, rerank move, agent message, memory lookup,
verdict, deal-breaker check, opt-in and booking, with the model and latency for each.

## Sponsor technology

| Sponsor | What it does in Wingmate |
|---|---|
| **Superlinked SIE Serverless** | Every model call runs on a small task-specific model: fact extraction with a JSON schema, personal-conversation classification for imports, PII redaction of the public card, embeddings, reranking, and the agent-to-agent conversation and verdicts. |
| **Cognee** | Each owner's memory graph, built from their own messages. During a pre-date, the agent recalls answers from it. |
| **SingleStore** | The agent directory. One SQL query applies hard filters (verified, ages, genders, mutual preferences) and vector similarity together. It also stores the audit trail. |
| **Statsig** | `match_policy` dynamic config (pool size, rerank cut, turns, min score, model) and the `matching_strategy` experiment (vector-only vs agent pre-date). |
| **Amplitude** | Product funnel events (`memory_imported` → `match_search_run` → `pre_date_completed` → `match_accepted` → `date_booked`) and an `[Agent] Model Call` event per model call with model and latency. |

**Verified-only discovery.** Only verified people's agents appear in search. The identity check is
simulated in this demo; a production version would plug in an identity provider.

Each integration is optional. Without its key, Wingmate uses a labeled local fallback (`local:*` in the
audit trail), so the demo always runs.

## Run it

```bash
cp .env.example .env          # add the keys you have
cd backend && uv sync && uv run uvicorn app.main:app --port 8000
cd frontend && pnpm install && pnpm dev   # http://localhost:3000
```

Tests: `cd backend && uv run pytest -q`

### Statsig setup
- Dynamic config `match_policy`, for example:
  `{"rerank_keep": 5, "candidate_pool": 20, "a2a_turns": 6, "min_score": 70, "max_words_per_message": 60}`
- Experiment `matching_strategy` with a string parameter `strategy`: `vector_only` or `agent_predate`.

## Demo storyline
Rachel imports her ChatGPT export. Hundreds of conversations get filtered to the personal ones, and
she approves the facts. Her agent searches the directory. Chris looks perfect on paper, but his agent
honestly says he smokes, which is Rachel's deal-breaker, and her agent passes. Matt is a real match: both
people accept, and the agents book a first date.

The `/insights` page runs a simulation over the 30 synthetic personas, comparing vector-only
matching with agent pre-dates. These numbers come from simulated people, not real users.

## Team
Add names and contact emails here before submitting.

### Direct assistant import (demo)

The import prompt includes an unauthenticated HTTP POST callback with a per-page request ID.
Copying the prompt starts polling for up to 15 minutes; received facts appear for review automatically.
The assistant must have an HTTP POST tool. A prompt alone does not grant that capability; manual paste remains available.
Set `NEXT_PUBLIC_API_URL` to a publicly reachable backend before building the frontend.
Alternatively set `NEXT_PUBLIC_IMPORT_CALLBACK_URL` to a public tunnel for callbacks while the browser uses a local API.
Both addresses must reach the same backend process. The backend must include the callback routes.
Callback receipts are held in memory (up to 500), so run one worker for this demo; restarting clears them.
Repeated POSTs to the same request ID return the original result without importing twice.
There is no authentication, as requested for the prototype.

`POST /api/personas/{pid}/import/callback/{request_id}` accepts `{"text":"summary"}`.
`GET` at the same path returns `{"result":null}` while waiting, then the import result.
