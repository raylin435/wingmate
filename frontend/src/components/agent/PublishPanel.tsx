"use client";

import Link from "next/link";
import { useState } from "react";
import { EyeOff, ListTree, Radio } from "lucide-react";
import { api, errorMessage, type Fact, type PublishResponse } from "@/lib/api";
import { Button, Card, CardTitle, ErrorBanner, Pill } from "../ui";

export function PublishPanel({
  personaId,
  facts,
  currentSummary,
  onPublished,
}: {
  personaId: string;
  facts: Fact[];
  currentSummary: string;
  onPublished: (r: PublishResponse) => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PublishResponse | null>(null);

  const approved = facts.filter((f) => f.approved);
  const counts = {
    public: approved.filter((f) => f.share === "public").length,
    agent_only: approved.filter((f) => f.share === "agent_only").length,
    private: approved.filter((f) => f.share === "private").length,
  };

  async function publish() {
    setBusy(true);
    setError(null);
    try {
      const r = await api.publish(personaId);
      setResult(r);
      onPublished(r);
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }

  const summary = result?.card_summary ?? currentSummary;

  return (
    <Card>
      <CardTitle kicker="Go live" tone="agent" title="Agent card" />
      <div className="mb-4 grid grid-cols-3 gap-2 text-center">
        <Count label="Public" value={counts.public} />
        <Count label="Agent only" value={counts.agent_only} />
        <Count label="Private" value={counts.private} />
      </div>
      <p className="mb-4 text-xs text-muted">
        Only approved facts are used. Other agents see the public card; agent-only facts inform your agent&apos;s
        judgement but are never quoted.
      </p>
      <Button
        variant="agent"
        className="w-full"
        icon={<Radio className="size-4" />}
        loading={busy}
        onClick={publish}
      >
        Publish agent card
      </Button>
      {approved.length === 0 && (
        <p className="mt-2 text-center text-xs text-warn">No approved facts yet. Approve some before publishing.</p>
      )}

      {error && (
        <div className="mt-4">
          <ErrorBanner message={error} />
        </div>
      )}

      {summary && (
        <div className="animate-msg-in mt-5">
          <div className="mb-2 flex items-center gap-2">
            <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted">
              {result ? "Published card" : "Current card"}
            </p>
            {result && <Pill tone="agent">Live</Pill>}
          </div>
          <div className="rounded-xl border border-agent/30 bg-agent-soft/50 p-4 text-sm leading-relaxed">{summary}</div>
        </div>
      )}

      {result && (
        <div className="mt-4">
          <p className="mb-2 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-[0.14em] text-muted">
            <EyeOff className="size-3.5" /> Redacted ({result.redactions.length})
          </p>
          {result.redactions.length ? (
            <ul className="flex flex-wrap gap-1.5">
              {result.redactions.map((r, i) => (
                <li key={i} className="rounded-md bg-surface-2 px-2 py-1 text-xs text-muted line-through ring-1 ring-line">
                  {r}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-muted">Nothing needed redacting.</p>
          )}
          <Link
            href={`/date?run=${encodeURIComponent(result.run_id)}`}
            className="mt-4 inline-flex items-center gap-1 text-xs font-medium text-agent hover:underline"
          >
            <ListTree className="size-3.5" /> View audit trail
          </Link>
        </div>
      )}
    </Card>
  );
}

function Count({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg bg-surface-2 px-2 py-2 ring-1 ring-line">
      <div className="text-lg font-semibold tabular-nums">{value}</div>
      <div className="text-[11px] text-muted">{label}</div>
    </div>
  );
}
