"use client";

import { useMemo, useState } from "react";
import { CheckCheck, Globe, Lock, MessageSquareQuote, Bot, Trash2 } from "lucide-react";
import { api, errorMessage, type Fact, type FactField, type ShareLevel } from "@/lib/api";
import { Button, Card, CardTitle, ErrorBanner, cx } from "../ui";

const FIELD_STYLE: Record<FactField, string> = {
  value: "bg-human-soft text-human",
  seeking: "bg-human-soft text-human",
  interest: "bg-agent-soft text-agent",
  lifestyle: "bg-agent-soft text-agent",
  dealbreaker: "bg-danger/10 text-danger",
  logistics: "bg-surface-2 text-muted ring-1 ring-line",
};

const SHARE_META: Record<ShareLevel, { label: string; icon: typeof Globe; hint: string }> = {
  public: { label: "Public", icon: Globe, hint: "On your agent card" },
  agent_only: { label: "Agent only", icon: Bot, hint: "Your agent can use it, never shown" },
  private: { label: "Private", icon: Lock, hint: "Never leaves your agent" },
};

type Filter = "all" | "review" | "approved";

export function FactList({
  personaId,
  facts,
  highlight,
  onChange,
}: {
  personaId: string;
  facts: Fact[];
  highlight: Set<string>;
  onChange: (facts: Fact[]) => void;
}) {
  const [filter, setFilter] = useState<Filter>("all");
  const [error, setError] = useState<string | null>(null);
  const [bulkBusy, setBulkBusy] = useState(false);

  const pending = facts.filter((f) => !f.approved);
  const sorted = useMemo(() => {
    const list = facts.filter((f) => (filter === "all" ? true : filter === "review" ? !f.approved : f.approved));
    // Freshly imported facts float to the top so the reviewer sees them first.
    return [...list].sort((a, b) => Number(highlight.has(b.id)) - Number(highlight.has(a.id)));
  }, [facts, filter, highlight]);

  async function patch(fact: Fact, change: Partial<Pick<Fact, "approved" | "share">>) {
    const prev = facts;
    onChange(facts.map((f) => (f.id === fact.id ? { ...f, ...change } : f)));
    setError(null);
    try {
      const updated = await api.patchFact(personaId, fact.id, change);
      onChange(prev.map((f) => (f.id === fact.id ? { ...f, ...change, ...updated } : f)));
    } catch (e) {
      onChange(prev);
      setError(`Couldn't update fact: ${errorMessage(e)}`);
    }
  }

  async function remove(fact: Fact) {
    const prev = facts;
    onChange(facts.filter((f) => f.id !== fact.id));
    setError(null);
    try {
      await api.deleteFact(personaId, fact.id);
    } catch (e) {
      onChange(prev);
      setError(`Couldn't delete fact: ${errorMessage(e)}`);
    }
  }

  async function approveAll() {
    setBulkBusy(true);
    setError(null);
    const ids = new Set(pending.map((f) => f.id));
    const results = await Promise.allSettled(pending.map((f) => api.patchFact(personaId, f.id, { approved: true })));
    const failed = results.filter((r) => r.status === "rejected").length;
    const ok = new Set(pending.filter((_, i) => results[i].status === "fulfilled").map((f) => f.id));
    onChange(facts.map((f) => (ids.has(f.id) && ok.has(f.id) ? { ...f, approved: true } : f)));
    if (failed) setError(`${failed} fact(s) couldn't be approved.`);
    setBulkBusy(false);
  }

  return (
    <Card>
      <CardTitle
        kicker="Review"
        tone="human"
        title={
          <>
            What your agent knows{" "}
            <span className="ml-1 text-sm font-normal text-muted tabular-nums">{facts.length} facts</span>
          </>
        }
        action={
          pending.length > 0 ? (
            <Button
              size="sm"
              variant="human"
              icon={<CheckCheck className="size-3.5" />}
              loading={bulkBusy}
              onClick={approveAll}
            >
              Approve all {pending.length}
            </Button>
          ) : null
        }
      />

      <div className="mb-4 flex gap-1 text-sm">
        {(
          [
            ["all", `All (${facts.length})`],
            ["review", `Needs review (${pending.length})`],
            ["approved", `Approved (${facts.length - pending.length})`],
          ] as const
        ).map(([key, label]) => (
          <button
            key={key}
            onClick={() => setFilter(key)}
            className={cx(
              "rounded-full px-3 py-1 text-xs font-medium transition",
              filter === key ? "bg-fg text-bg" : "text-muted hover:bg-surface-2 hover:text-fg",
            )}
          >
            {label}
          </button>
        ))}
      </div>

      {error && (
        <div className="mb-4">
          <ErrorBanner message={error} />
        </div>
      )}

      {sorted.length === 0 ? (
        <p className="rounded-xl border border-dashed border-line px-4 py-8 text-center text-sm text-muted">
          {facts.length === 0 ? "No facts yet. Import from ChatGPT or Claude above." : "Nothing in this view."}
        </p>
      ) : (
        <ul className="divide-y divide-line">
          {sorted.map((f) => (
            <FactRow
              key={f.id}
              fact={f}
              isNew={highlight.has(f.id)}
              onPatch={(c) => patch(f, c)}
              onDelete={() => remove(f)}
            />
          ))}
        </ul>
      )}
    </Card>
  );
}

function FactRow({
  fact,
  isNew,
  onPatch,
  onDelete,
}: {
  fact: Fact;
  isNew: boolean;
  onPatch: (c: Partial<Pick<Fact, "approved" | "share">>) => void;
  onDelete: () => void;
}) {
  const [confirm, setConfirm] = useState(false);
  const ShareIcon = SHARE_META[fact.share]?.icon ?? Globe;
  const sourceLabel =
    fact.source === "import" ? "Imported" : fact.source === "chat" ? "From chat" : "Profile";

  return (
    <li className={cx("py-4 first:pt-0 last:pb-0", !fact.approved && "relative")}>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start">
        <div className="min-w-0 flex-1">
          <div className="mb-1.5 flex flex-wrap items-center gap-2">
            <span
              className={cx(
                "rounded-md px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wider",
                FIELD_STYLE[fact.field] ?? FIELD_STYLE.logistics,
              )}
            >
              {fact.field}
            </span>
            {isNew && (
              <span className="rounded-md bg-agent px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-white dark:text-[#04201f]">
                New
              </span>
            )}
            <span className="text-xs text-muted">
              {sourceLabel}
              {fact.source_title ? ` · “${fact.source_title}”` : ""}
            </span>
          </div>
          <p className="font-medium leading-snug">{fact.value}</p>
          {fact.quote && (
            <blockquote className="mt-2 flex gap-2 border-l-2 border-human/50 pl-3 text-sm italic text-muted">
              <MessageSquareQuote className="mt-0.5 size-3.5 shrink-0 not-italic text-human/70" />
              <span>“{fact.quote}”</span>
            </blockquote>
          )}
        </div>

        <div className="flex shrink-0 items-center gap-2 sm:flex-col sm:items-end">
          <label className="relative flex items-center" title={SHARE_META[fact.share]?.hint}>
            <ShareIcon className="pointer-events-none absolute left-2.5 size-3.5 text-muted" />
            <select
              value={fact.share}
              onChange={(e) => onPatch({ share: e.target.value as ShareLevel })}
              className="h-8 appearance-none rounded-lg border border-line bg-surface-2 pr-3 pl-8 text-xs font-medium"
              aria-label="Share level"
            >
              <option value="public">Public</option>
              <option value="agent_only">Agent only</option>
              <option value="private">Private</option>
            </select>
          </label>
          <div className="flex items-center gap-1">
            <button
              role="switch"
              aria-checked={fact.approved}
              onClick={() => onPatch({ approved: !fact.approved })}
              className={cx(
                "inline-flex h-8 items-center gap-2 rounded-lg px-2.5 text-xs font-medium transition",
                fact.approved ? "bg-human-soft text-human" : "text-muted ring-1 ring-line hover:text-fg",
              )}
            >
              <span
                className={cx(
                  "relative h-4 w-7 rounded-full transition",
                  fact.approved ? "bg-human" : "bg-muted/30",
                )}
              >
                <span
                  className={cx(
                    "absolute top-0.5 size-3 rounded-full bg-white shadow transition-all",
                    fact.approved ? "left-3.5" : "left-0.5",
                  )}
                />
              </span>
              {fact.approved ? "Approved" : "Approve"}
            </button>
            {confirm ? (
              <button
                onClick={onDelete}
                onBlur={() => setConfirm(false)}
                autoFocus
                className="h-8 rounded-lg bg-danger/10 px-2.5 text-xs font-medium text-danger"
              >
                Delete?
              </button>
            ) : (
              <button
                onClick={() => setConfirm(true)}
                className="grid size-8 place-items-center rounded-lg text-muted hover:bg-danger/10 hover:text-danger"
                aria-label="Delete fact"
              >
                <Trash2 className="size-4" />
              </button>
            )}
          </div>
        </div>
      </div>
    </li>
  );
}
