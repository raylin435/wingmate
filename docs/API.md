# Wingmate API contract

Backend: FastAPI at `http://localhost:8000`, all routes under `/api`, CORS open for `http://localhost:3000`.
Every response is JSON unless noted. IDs are lowercase slugs (`maya`, `jordan`).

## Types

```ts
type Fact = {
  id: string;                 // "maya-f3"
  field: "value" | "interest" | "lifestyle" | "dealbreaker" | "logistics" | "seeking";
  value: string;              // short normalized statement, e.g. "Loves bouldering"
  quote: string;              // exact words from the owner's own messages
  share: "public" | "agent_only" | "private";
  approved: boolean;          // imported facts start false
  source: "seed" | "chat" | "import";
  source_title?: string;      // conversation title for imported facts
};

type PersonaSummary = { id: string; alias: string; first_name: string; age: number; gender: string;
  neighborhood: string; verified: boolean; tagline: string; avatar_color: string };

type Persona = PersonaSummary & { seeking: { genders: string[]; min_age: number; max_age: number };
  facts: Fact[]; card_summary: string };

type Candidate = { agent_id: string; alias: string; age: number; neighborhood: string; summary: string;
  vector_rank: number; vector_score: number; rerank_rank: number; rerank_score: number };

type A2AMessage = { turn: number; from: string; alias: string; text: string };

type Verdict = { score: number; recommend: boolean;
  reasons: { claim: string; my_fact_id: string; their_quote: string }[]; concerns: string[] };

type AuditEvent = { id: number; run_id: string; ts: string; step: string; actor: string;
  model: string | null; latency_ms: number | null; detail: Record<string, unknown> };
```

## Routes

| Method | Path | Body | Returns |
|---|---|---|---|
| GET | `/api/status` | | `{ sponsors: {sie, singlestore, cognee, statsig, amplitude, persona: boolean}, demo_persona: "maya" }` |
| GET | `/api/personas` | | `PersonaSummary[]` |
| GET | `/api/personas/{id}` | | `Persona` |
| POST | `/api/personas/{id}/import/paste` | `{ text: string }` | `ImportResult` |
| POST | `/api/personas/{id}/import/export` | multipart `file` (conversations.json or .zip) | `ImportResult` |
| GET | `/api/personas/{id}/import/sample` | | the demo fake export file (JSON download) |
| PATCH | `/api/personas/{id}/facts/{fact_id}` | `{ approved?, share?, value? }` | `Fact` |
| DELETE | `/api/personas/{id}/facts/{fact_id}` | | `{ ok: true }` |
| POST | `/api/personas/{id}/publish` | | `{ card_summary: string, redactions: string[], run_id }` |
| POST | `/api/personas/{id}/verify` | `{ inquiry_id?: string }` | `{ verified: true }` |
| POST | `/api/match/{id}/search` | | `{ run_id, strategy, candidates: Candidate[] }` |
| POST | `/api/match/{id}/predate` | `{ candidate_id, run_id? }` | `{ run_id, transcript: A2AMessage[], verdicts: Record<agentId, Verdict>, match: boolean, avg_score, threshold }` |
| POST | `/api/match/{id}/accept` | `{ candidate_id, run_id }` | `{ both_accepted: boolean, revealed: { [agentId]: first_name } }` |
| POST | `/api/match/{id}/book` | `{ candidate_id, run_id }` | `{ booking: { id, venue: {name, neighborhood, tags, why}, start, end, ics_path } }` |
| GET | `/api/bookings/{booking_id}.ics` | | `text/calendar` |
| GET | `/api/audit/{run_id}` | | `AuditEvent[]` (oldest first) |
| GET | `/api/config` | | `{ policy: {...match_policy}, strategy: "vector_only" \| "agent_predate" }` |
| POST | `/api/reset` | | `{ ok, personas }` reload seed data for a clean demo run |
| POST | `/api/simulate` | | `{ by_strategy: { [arm]: {searched, proposed, mutual_accept, booked} } }` |

```ts
type ImportResult = { run_id: string; source: "chatgpt" | "claude" | "paste";
  conversations_seen: number; conversations_kept: number; messages_used: number;
  facts: Fact[]; dropped_untraceable: number };
```
