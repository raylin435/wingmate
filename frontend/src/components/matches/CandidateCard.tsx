"use client";

import { ArrowDown, ArrowUp, MapPin, Minus, Send } from "lucide-react";
import type { Candidate } from "@/lib/api";
import { Avatar, Button, cx } from "../ui";

const PALETTE = ["#C9295F", "#17807F", "#7C3AED", "#D97706", "#2563EB", "#DB2777", "#059669", "#9333EA"];

export function colorFor(id: string) {
  let h = 0;
  for (const c of id) h = (h * 31 + c.charCodeAt(0)) >>> 0;
  return PALETTE[h % PALETTE.length];
}

export function RankMove({ from, to }: { from: number; to: number }) {
  const delta = from - to;
  const Icon = delta > 0 ? ArrowUp : delta < 0 ? ArrowDown : Minus;
  return (
    <span
      className={cx(
        "inline-flex items-center gap-1 rounded-md px-2 py-0.5 font-mono text-xs font-semibold tabular-nums",
        delta > 0 && "bg-agent-soft text-agent",
        delta < 0 && "bg-human-soft text-human",
        delta === 0 && "bg-surface-2 text-muted ring-1 ring-line",
      )}
      title={`Vector rank #${from}, after agent rerank #${to}`}
    >
      #{from} <span className="opacity-60">→</span> #{to}
      <Icon className="size-3.5" />
    </span>
  );
}

function ScoreBar({ label, value, tone }: { label: string; value: number; tone: "agent" | "muted" }) {
  const pct = Math.max(0, Math.min(1, value <= 1 ? value : value / 100)) * 100;
  return (
    <div className="flex items-center gap-2 text-[11px]">
      <span className="w-12 shrink-0 text-muted">{label}</span>
      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-surface-2 ring-1 ring-line">
        <div
          className={cx("h-full rounded-full", tone === "agent" ? "bg-agent" : "bg-muted/50")}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="w-10 text-right font-mono tabular-nums">{value.toFixed(3)}</span>
    </div>
  );
}

export function CandidateCard({
  c,
  active,
  disabled,
  onPredate,
}: {
  c: Candidate;
  active: boolean;
  disabled: boolean;
  onPredate: () => void;
}) {
  return (
    <article
      className={cx(
        "flex flex-col rounded-2xl border bg-surface p-4 transition",
        active ? "border-agent ring-2 ring-agent/20" : "border-line hover:border-agent/40",
      )}
    >
      <div className="flex items-start gap-3">
        <Avatar name={c.alias} color={colorFor(c.agent_id)} size={44} />
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-baseline gap-x-2">
            <h3 className="truncate font-semibold">{c.alias}</h3>
            <span className="text-sm text-muted">{c.age}</span>
          </div>
          <p className="flex items-center gap-1 text-xs text-muted">
            <MapPin className="size-3" /> {c.neighborhood}
          </p>
        </div>
        <RankMove from={c.vector_rank} to={c.rerank_rank} />
      </div>
      <p className="mt-3 line-clamp-3 flex-1 text-sm leading-relaxed">{c.summary}</p>
      <div className="mt-3 space-y-1">
        <ScoreBar label="Vector" value={c.vector_score} tone="muted" />
        <ScoreBar label="Rerank" value={c.rerank_score} tone="agent" />
      </div>
      <Button
        variant={active ? "agent" : "neutral"}
        size="sm"
        className="mt-4 w-full"
        icon={<Send className="size-3.5" />}
        disabled={disabled}
        onClick={onPredate}
      >
        Send my agent on a pre-date
      </Button>
    </article>
  );
}
