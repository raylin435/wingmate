"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Bot, ChevronRight, Cpu, RefreshCw, Server, Timer, User } from "lucide-react";
import { api, errorMessage, formatLA, type AuditEvent } from "@/lib/api";
import { Button, ErrorBanner, Skeleton, cx } from "./ui";

type ActorKind = "human" | "agent" | "system";

function actorKind(actor: string): ActorKind {
  // Backend actors look like "agent:maya", "human:theo", "system", "statsig".
  const a = actor.toLowerCase();
  if (a.startsWith("agent")) return "agent";
  if (a.startsWith("human") || a.startsWith("user")) return "human";
  return "system";
}

const KIND_STYLE: Record<ActorKind, { dot: string; chip: string; icon: typeof Bot }> = {
  human: { dot: "bg-human ring-human/25", chip: "bg-human-soft text-human", icon: User },
  agent: { dot: "bg-agent ring-agent/25", chip: "bg-agent-soft text-agent", icon: Bot },
  system: { dot: "bg-muted ring-muted/20", chip: "bg-surface-2 text-muted ring-1 ring-line", icon: Server },
};

const STEP_LABEL: Record<string, string> = {
  a2a_message: "Agent-to-agent message",
  human_opt_in: "Human opt-in",
  predate_started: "Pre-date started",
};

function prettyStep(step: string) {
  if (STEP_LABEL[step]) return STEP_LABEL[step];
  const s = step.replace(/[._:/-]+/g, " ").trim();
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function previewEntries(detail: Record<string, unknown>) {
  return Object.entries(detail ?? {})
    .map(([k, v]) => {
      if (typeof v === "string") return [k, v.length > 40 ? `${v.slice(0, 40)}…` : v] as const;
      if (typeof v === "number" || typeof v === "boolean") return [k, String(v)] as const;
      if (Array.isArray(v)) return [k, `${v.length} items`] as const;
      return null;
    })
    .filter((x): x is readonly [string, string] => x !== null)
    .slice(0, 4);
}

function JsonView({ value }: { value: unknown }) {
  const text = JSON.stringify(value, null, 2) ?? "null";
  // Light syntax colouring: keys teal, strings rose, numbers/bools default.
  const html = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(
      /("(?:\\.|[^"\\])*")(\s*:)?/g,
      (_m, str: string, colon?: string) =>
        colon ? `<span class="text-agent">${str}</span>${colon}` : `<span class="text-human">${str}</span>`,
    );
  return (
    <pre
      className="max-h-96 overflow-auto rounded-xl bg-surface-2 p-3 font-mono text-[12px] leading-relaxed ring-1 ring-line"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}

export function AuditTimeline({ runId }: { runId: string }) {
  const [events, setEvents] = useState<AuditEvent[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState<Set<number>>(new Set());

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setEvents(await api.audit(runId));
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setLoading(false);
    }
  }, [runId]);

  useEffect(() => {
    setEvents(null);
    setOpen(new Set());
    load();
  }, [load]);

  const stats = useMemo(() => {
    if (!events?.length) return null;
    const t0 = new Date(events[0].ts).getTime();
    const t1 = new Date(events[events.length - 1].ts).getTime();
    const modelCalls = events.filter((e) => e.model).length;
    const latency = events.reduce((s, e) => s + (e.latency_ms ?? 0), 0);
    const maxLatency = Math.max(1, ...events.map((e) => e.latency_ms ?? 0));
    return { t0, span: Math.max(0, t1 - t0), modelCalls, latency, maxLatency };
  }, [events]);

  const toggle = (id: number) =>
    setOpen((s) => {
      const n = new Set(s);
      if (n.has(id)) n.delete(id);
      else n.add(id);
      return n;
    });
  const allOpen = !!events?.length && open.size === events.length;

  return (
    <div>
      <div className="mb-5 flex flex-wrap items-center gap-x-5 gap-y-3">
        {stats && (
          <dl className="flex flex-wrap gap-x-5 gap-y-1 text-sm">
            <div>
              <dt className="text-[11px] text-muted">Events</dt>
              <dd className="font-semibold tabular-nums">{events?.length}</dd>
            </div>
            <div>
              <dt className="text-[11px] text-muted">Model calls</dt>
              <dd className="font-semibold tabular-nums">{stats.modelCalls}</dd>
            </div>
            <div>
              <dt className="text-[11px] text-muted">Model latency</dt>
              <dd className="font-semibold tabular-nums">{fmtMs(stats.latency)}</dd>
            </div>
            <div>
              <dt className="text-[11px] text-muted">Wall clock</dt>
              <dd className="font-semibold tabular-nums">{fmtMs(stats.span)}</dd>
            </div>
          </dl>
        )}
        <div className="ml-auto flex gap-1">
          {!!events?.length && (
            <Button
              size="sm"
              variant="ghost"
              onClick={() => setOpen(allOpen ? new Set() : new Set(events.map((e) => e.id)))}
            >
              {allOpen ? "Collapse all" : "Expand all"}
            </Button>
          )}
          <Button size="sm" variant="neutral" icon={<RefreshCw className="size-3.5" />} loading={loading} onClick={load}>
            Refresh
          </Button>
        </div>
      </div>

      {error && <ErrorBanner message={error} onRetry={load} />}
      {!events && !error && (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-16" />
          ))}
        </div>
      )}
      {events && events.length === 0 && (
        <p className="rounded-xl border border-dashed border-line px-4 py-8 text-center text-sm text-muted">
          No audit events recorded for this run yet.
        </p>
      )}

      {events && events.length > 0 && stats && (
        <ol className="relative">
          <span className="absolute top-2 bottom-2 left-[11px] w-px bg-line" aria-hidden />
          {events.map((e, i) => {
            const kind = actorKind(e.actor);
            const style = KIND_STYLE[kind];
            const Icon = style.icon;
            const isOpen = open.has(e.id);
            const offset = new Date(e.ts).getTime() - stats.t0;
            const preview = previewEntries(e.detail);
            return (
              <li key={e.id} className="animate-msg-in relative pb-3 pl-9 last:pb-0" style={{ animationDelay: `${i * 40}ms` }}>
                <span
                  className={cx("absolute top-4 left-[6px] size-[11px] rounded-full ring-4", style.dot)}
                  aria-hidden
                />
                <div
                  className={cx(
                    "rounded-xl border bg-surface transition",
                    isOpen ? "border-agent/40 shadow-sm" : "border-line hover:border-agent/30",
                  )}
                >
                  <button
                    onClick={() => toggle(e.id)}
                    aria-expanded={isOpen}
                    className="flex w-full items-start gap-3 px-4 py-3 text-left"
                  >
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
                        <span className="font-semibold">{prettyStep(e.step)}</span>
                        <code className="font-mono text-[11px] text-muted">{e.step}</code>
                      </div>
                      <div className="mt-1.5 flex flex-wrap items-center gap-1.5 text-xs">
                        <span className={cx("inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 font-medium", style.chip)}>
                          <Icon className="size-3" /> {e.actor}
                        </span>
                        {e.model && (
                          <span className="inline-flex items-center gap-1 rounded-md bg-surface-2 px-1.5 py-0.5 font-mono text-[11px] ring-1 ring-line">
                            <Cpu className="size-3 text-agent" /> {e.model}
                          </span>
                        )}
                        {e.latency_ms != null && (
                          <span className="inline-flex items-center gap-1.5 rounded-md px-1.5 py-0.5 font-mono text-[11px] text-muted">
                            <Timer className="size-3" />
                            {fmtMs(e.latency_ms)}
                            <span className="hidden h-1 w-12 overflow-hidden rounded-full bg-surface-2 ring-1 ring-line sm:inline-block">
                              <span
                                className="block h-full bg-agent"
                                style={{ width: `${(e.latency_ms / stats.maxLatency) * 100}%` }}
                              />
                            </span>
                          </span>
                        )}
                      </div>
                      {!isOpen && preview.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-1.5">
                          {preview.map(([k, v]) => (
                            <span key={k} className="max-w-full truncate rounded bg-surface-2 px-1.5 py-0.5 font-mono text-[11px] text-muted">
                              <span className="text-agent">{k}</span>={v}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                    <div className="flex shrink-0 flex-col items-end gap-1 text-right">
                      <time dateTime={e.ts} className="font-mono text-[11px] tabular-nums text-muted">
                        {formatLA(e.ts, { hour: "numeric", minute: "2-digit", second: "2-digit", fractionalSecondDigits: 3 })}
                      </time>
                      <span className="font-mono text-[11px] tabular-nums text-muted/70">+{fmtMs(offset)}</span>
                      <ChevronRight className={cx("size-4 text-muted transition", isOpen && "rotate-90")} />
                    </div>
                  </button>
                  {isOpen && (
                    <div className="border-t border-line px-4 py-3">
                      <div className="mb-2 flex flex-wrap gap-x-4 gap-y-1 font-mono text-[11px] text-muted">
                        <span>id {e.id}</span>
                        <span>{e.ts}</span>
                      </div>
                      <JsonView value={e.detail} />
                    </div>
                  )}
                </div>
              </li>
            );
          })}
        </ol>
      )}
    </div>
  );
}

function fmtMs(ms: number) {
  if (ms < 1000) return `${Math.round(ms)} ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(2)} s`;
  return `${Math.floor(ms / 60000)}m ${Math.round((ms % 60000) / 1000)}s`;
}
