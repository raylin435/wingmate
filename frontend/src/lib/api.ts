// Typed client for the Wingmate backend. Mirrors docs/API.md exactly.

export const API_BASE = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/+$/, "");

// ---------- Types ----------

export type FactField = "value" | "interest" | "lifestyle" | "dealbreaker" | "logistics" | "seeking";
export type ShareLevel = "public" | "agent_only" | "private";

export type Fact = {
  id: string;
  field: FactField;
  value: string;
  quote: string;
  share: ShareLevel;
  approved: boolean;
  source: "seed" | "chat" | "import";
  source_title?: string;
};

export type PersonaSummary = {
  id: string;
  alias: string;
  first_name: string;
  age: number;
  gender: string;
  neighborhood: string;
  verified: boolean;
  tagline: string;
  avatar_color: string;
};

export type Persona = PersonaSummary & {
  seeking: { genders: string[]; min_age: number; max_age: number };
  facts: Fact[];
  card_summary: string;
};

export type Candidate = {
  agent_id: string;
  alias: string;
  age: number;
  neighborhood: string;
  summary: string;
  vector_rank: number;
  vector_score: number;
  rerank_rank: number;
  rerank_score: number;
};

export type A2AMessage = { turn: number; from: string; alias: string; text: string };

export type Verdict = {
  score: number;
  recommend: boolean;
  reasons: { claim: string; my_fact_id: string; their_quote: string }[];
  concerns: string[];
};

export type AuditEvent = {
  id: number;
  run_id: string;
  ts: string;
  step: string;
  actor: string;
  model: string | null;
  latency_ms: number | null;
  detail: Record<string, unknown>;
};

export type ImportResult = {
  run_id: string;
  source: "chatgpt" | "claude" | "paste";
  conversations_seen: number;
  conversations_kept: number;
  messages_used: number;
  facts: Fact[];
  dropped_untraceable: number;
};

export type SponsorKey = "sie" | "singlestore" | "cognee" | "statsig" | "amplitude";

export type StatusResponse = {
  sponsors: Record<SponsorKey, boolean>;
  demo_persona: string;
};

export type PublishResponse = { card_summary: string; redactions: string[]; run_id: string };
export type VerifyResponse = { verified: true };
export type SearchResponse = { run_id: string; strategy: string; candidates: Candidate[] };
export type PredateResponse = {
  run_id: string;
  transcript: A2AMessage[];
  verdicts: Record<string, Verdict>;
  match: boolean;
  avg_score: number;
  threshold: number;
};
export type AcceptResponse = { both_accepted: boolean; revealed: Record<string, string> };
export type Venue = { name: string; neighborhood: string; tags: string[]; why: string };
export type Booking = { id: string; venue: Venue; start: string; end: string; ics_path: string };
export type BookResponse = { booking: Booking };
export type ConfigResponse = { policy: Record<string, unknown>; strategy: "vector_only" | "agent_predate" | string };
export type FunnelCounts = { searched: number; proposed: number; mutual_accept: number; booked: number };
export type SimulateResponse = { by_strategy: Record<string, FunnelCounts> };

// ---------- Errors ----------

export class ApiError extends Error {
  constructor(
    message: string,
    public kind: "network" | "http",
    public status?: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export function errorMessage(err: unknown): string {
  if (err instanceof Error) return err.message;
  return String(err);
}

// ---------- Core request ----------

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: {
        Accept: "application/json",
        ...(init?.body && !(init.body instanceof FormData) ? { "Content-Type": "application/json" } : {}),
        ...init?.headers,
      },
      cache: "no-store",
    });
  } catch {
    throw new ApiError(`Backend not reachable at ${API_BASE}`, "network");
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (body && typeof body === "object" && "detail" in body) {
        detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
      }
    } catch {
      // non-JSON error body
    }
    throw new ApiError(`${res.status} ${detail || "Request failed"} (${path})`, "http", res.status);
  }
  return (await res.json()) as T;
}

const json = (body: unknown): RequestInit => ({ method: "POST", body: JSON.stringify(body) });
const enc = encodeURIComponent;

// ---------- Endpoints ----------

export const api = {
  status: () => request<StatusResponse>("/api/status"),
  personas: () => request<PersonaSummary[]>("/api/personas"),
  persona: (id: string) => request<Persona>(`/api/personas/${enc(id)}`),

  importPaste: (id: string, text: string) =>
    request<ImportResult>(`/api/personas/${enc(id)}/import/paste`, json({ text })),
  importCallbackStatus: (id: string, requestId: string) =>
    request<{ result: ImportResult | null }>(`/api/personas/${enc(id)}/import/callback/${enc(requestId)}`),
  importExport: (id: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<ImportResult>(`/api/personas/${enc(id)}/import/export`, { method: "POST", body: form });
  },
  /** Downloads the demo fake export and wraps it as a File ready to re-upload. */
  sampleExport: async (id: string): Promise<File> => {
    const path = `/api/personas/${enc(id)}/import/sample`;
    let res: Response;
    try {
      res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
    } catch {
      throw new ApiError(`Backend not reachable at ${API_BASE}`, "network");
    }
    if (!res.ok) throw new ApiError(`${res.status} ${res.statusText} (${path})`, "http", res.status);
    const blob = await res.blob();
    const cd = res.headers.get("content-disposition") || "";
    const name = /filename="?([^";]+)"?/i.exec(cd)?.[1] || "conversations.json";
    return new File([blob], name, { type: blob.type || "application/json" });
  },

  patchFact: (id: string, factId: string, patch: Partial<Pick<Fact, "approved" | "share" | "value">>) =>
    request<Fact>(`/api/personas/${enc(id)}/facts/${enc(factId)}`, { method: "PATCH", body: JSON.stringify(patch) }),
  deleteFact: (id: string, factId: string) =>
    request<{ ok: true }>(`/api/personas/${enc(id)}/facts/${enc(factId)}`, { method: "DELETE" }),

  publish: (id: string) => request<PublishResponse>(`/api/personas/${enc(id)}/publish`, { method: "POST" }),
  verify: (id: string) => request<VerifyResponse>(`/api/personas/${enc(id)}/verify`, json({})),

  search: (id: string) => request<SearchResponse>(`/api/match/${enc(id)}/search`, { method: "POST" }),
  predate: (id: string, candidate_id: string, run_id?: string) =>
    request<PredateResponse>(`/api/match/${enc(id)}/predate`, json(run_id ? { candidate_id, run_id } : { candidate_id })),
  accept: (id: string, candidate_id: string, run_id: string) =>
    request<AcceptResponse>(`/api/match/${enc(id)}/accept`, json({ candidate_id, run_id })),
  book: (id: string, candidate_id: string, run_id: string) =>
    request<BookResponse>(`/api/match/${enc(id)}/book`, json({ candidate_id, run_id })),

  icsUrl: (bookingId: string) => `${API_BASE}/api/bookings/${enc(bookingId)}.ics`,
  icsText: async (bookingId: string): Promise<string> => {
    let res: Response;
    try {
      res = await fetch(`${API_BASE}/api/bookings/${enc(bookingId)}.ics`, { cache: "no-store" });
    } catch {
      throw new ApiError(`Backend not reachable at ${API_BASE}`, "network");
    }
    if (!res.ok) throw new ApiError(`${res.status} ${res.statusText}`, "http", res.status);
    return res.text();
  },

  audit: (runId: string) => request<AuditEvent[]>(`/api/audit/${enc(runId)}`),
  config: () => request<ConfigResponse>("/api/config"),
  simulate: () => request<SimulateResponse>("/api/simulate", { method: "POST" }),
  /** Reloads seed data on the backend (demo helper). */
  reset: () => request<{ ok: boolean; personas: unknown }>("/api/reset", { method: "POST" }),
};

// ---------- Formatting helpers ----------

const LA = "America/Los_Angeles";

export function formatLA(iso: string, opts: Intl.DateTimeFormatOptions): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return new Intl.DateTimeFormat("en-US", { timeZone: LA, ...opts }).format(d);
}

export function formatDateRangeLA(start: string, end: string): { day: string; time: string } {
  const day = formatLA(start, { weekday: "long", month: "long", day: "numeric" });
  const s = formatLA(start, { hour: "numeric", minute: "2-digit" });
  const e = formatLA(end, { hour: "numeric", minute: "2-digit", timeZoneName: "short" });
  return { day, time: `${s} – ${e}` };
}
