"use client";

import { useEffect, useState } from "react";
import { AlertCircle, Bot, Check, FastForward, Heart, RotateCcw, ThumbsDown, ThumbsUp, X } from "lucide-react";
import type { A2AMessage, PredateResponse, Verdict } from "@/lib/api";
import { Button, Pill, cx } from "../ui";

const REVEAL_MS = 700;

export function isMine(m: A2AMessage, myId: string) {
  return m.from === myId || m.from.startsWith(`${myId}-`) || m.from.startsWith(`${myId}_`);
}

/** Reveal transcript messages one at a time. Returns [visibleCount, done, skip, replay]. */
export function useReveal(total: number, key: string) {
  const [count, setCount] = useState(0);
  const [nonce, setNonce] = useState(0);
  useEffect(() => {
    setCount(0);
    if (!total) return;
    let i = 0;
    const t = setInterval(() => {
      i += 1;
      setCount(i);
      if (i >= total) clearInterval(t);
    }, REVEAL_MS);
    return () => clearInterval(t);
  }, [total, key, nonce]);
  return {
    count,
    done: count >= total,
    skip: () => setCount(total),
    replay: () => setNonce((n) => n + 1),
  };
}

function Typing({ mine }: { mine: boolean }) {
  return (
    <div
      className={cx(
        "inline-flex items-center gap-1 rounded-2xl px-4 py-3",
        mine ? "bg-agent-soft" : "bg-surface-2 ring-1 ring-line",
      )}
      aria-label="Agent is typing"
    >
      {[0, 1, 2].map((i) => (
        <span key={i} className={cx("typing-dot size-1.5 rounded-full", mine ? "bg-agent" : "bg-muted")} />
      ))}
    </div>
  );
}

export function Transcript({
  transcript,
  myId,
  myLabel,
  theirLabel,
  count,
  pending,
}: {
  transcript: A2AMessage[];
  myId: string;
  myLabel: string;
  theirLabel: string;
  count: number;
  pending: boolean;
}) {
  const visible = transcript.slice(0, count);
  const next = transcript[count];
  const showTyping = pending || next !== undefined;
  const typingMine = next ? isMine(next, myId) : true;

  return (
    <div className="rounded-2xl border border-line bg-surface">
      <div className="grid grid-cols-2 border-b border-line text-xs font-semibold">
        <div className="flex items-center gap-2 px-4 py-3 text-agent">
          <Bot className="size-4" /> {myLabel}
        </div>
        <div className="flex items-center justify-end gap-2 border-l border-line px-4 py-3 text-muted md:justify-start">
          <Bot className="size-4" /> {theirLabel}
        </div>
      </div>
      <div className="relative grid gap-3 p-4 md:grid-cols-2 md:gap-x-8">
        <div className="pointer-events-none absolute inset-y-0 left-1/2 hidden w-px bg-line md:block" />
        {visible.map((m, i) => {
          const mine = isMine(m, myId);
          return (
            <div
              key={`${m.turn}-${i}`}
              className={cx(
                "animate-msg-in flex flex-col",
                mine ? "items-start md:col-start-1" : "items-end md:col-start-2 md:items-start",
              )}
            >
              <span className={cx("mb-1 text-[11px] font-medium", mine ? "text-agent" : "text-muted")}>
                {m.alias} · turn {m.turn}
              </span>
              <div
                className={cx(
                  "max-w-[92%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed md:max-w-full",
                  mine
                    ? "rounded-tl-sm bg-agent-soft text-fg"
                    : "rounded-tr-sm bg-surface-2 ring-1 ring-line md:rounded-tl-sm md:rounded-tr-2xl",
                )}
              >
                {m.text}
              </div>
            </div>
          );
        })}
        {showTyping && (
          <div
            className={cx(
              "flex",
              typingMine ? "justify-start md:col-start-1" : "justify-end md:col-start-2 md:justify-start",
            )}
          >
            <Typing mine={typingMine} />
          </div>
        )}
      </div>
    </div>
  );
}

// Scores are 0-100 per the match policy (min_score: 70); tolerate 0-1 fractions too.
const isFraction = (v: number) => v > 0 && v < 1;

function scoreMax(v: number) {
  return isFraction(v) ? 1 : 100;
}

export function fmtScore(v: number) {
  if (isFraction(v)) return `${Math.round(v * 100)}`;
  return Number.isInteger(v) ? `${v}` : v.toFixed(1);
}

export function VerdictCard({ title, verdict, mine }: { title: string; verdict?: Verdict; mine: boolean }) {
  if (!verdict)
    return (
      <div className="rounded-2xl border border-dashed border-line p-5 text-sm text-muted">{title}: no verdict returned</div>
    );
  const max = scoreMax(verdict.score);
  const pct = Math.min(100, (verdict.score / max) * 100);
  return (
    <div className="animate-msg-in rounded-2xl border border-line bg-surface p-5">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <p className={cx("text-[11px] font-semibold uppercase tracking-[0.14em]", mine ? "text-agent" : "text-muted")}>
            Verdict
          </p>
          <h3 className="font-semibold">{title}</h3>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right">
            <div className="text-2xl font-semibold tabular-nums">
              {fmtScore(verdict.score)}
              <span className="text-sm font-normal text-muted">/{max === 1 ? 100 : max}</span>
            </div>
          </div>
          {verdict.recommend ? (
            <Pill tone="ok" className="py-1">
              <ThumbsUp className="size-3.5" /> Recommend
            </Pill>
          ) : (
            <Pill tone="warn" className="py-1">
              <ThumbsDown className="size-3.5" /> Pass
            </Pill>
          )}
        </div>
      </div>
      <div className="mb-4 h-1.5 overflow-hidden rounded-full bg-surface-2 ring-1 ring-line">
        <div
          className={cx("h-full rounded-full transition-all duration-700", verdict.recommend ? "bg-agent" : "bg-warn")}
          style={{ width: `${pct}%` }}
        />
      </div>
      {verdict.reasons.length > 0 && (
        <ul className="space-y-3">
          {verdict.reasons.map((r, i) => (
            <li key={i} className="text-sm">
              <p className="flex gap-2 font-medium">
                <Check className="mt-0.5 size-4 shrink-0 text-agent" /> {r.claim}
              </p>
              {r.their_quote && (
                <blockquote className="mt-1 ml-6 border-l-2 border-human/50 pl-3 text-[13px] italic text-muted">
                  “{r.their_quote}”
                </blockquote>
              )}
              {r.my_fact_id && (
                <p className="mt-1 ml-6 font-mono text-[10px] text-muted/80">matches fact {r.my_fact_id}</p>
              )}
            </li>
          ))}
        </ul>
      )}
      {verdict.concerns.length > 0 && (
        <div className="mt-4 rounded-xl bg-warn/5 p-3 ring-1 ring-warn/20">
          <p className="mb-1.5 flex items-center gap-1.5 text-xs font-semibold text-warn">
            <AlertCircle className="size-3.5" /> Concerns
          </p>
          <ul className="list-disc space-y-1 pl-5 text-[13px] text-muted">
            {verdict.concerns.map((c, i) => (
              <li key={i}>{c}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export function MatchBanner({ result }: { result: PredateResponse }) {
  return (
    <div
      className={cx(
        "animate-msg-in flex flex-wrap items-center gap-3 rounded-2xl px-5 py-4",
        result.match ? "bg-human text-white dark:text-[#1a0a10]" : "bg-surface-2 ring-1 ring-line",
      )}
    >
      {result.match ? <Heart className="size-6 fill-current" /> : <X className="size-6 text-muted" />}
      <div className="flex-1">
        <p className="font-semibold">
          {result.match ? "Both agents recommend a first date" : "The agents decided to pass"}
        </p>
        <p className={cx("text-sm", result.match ? "opacity-90" : "text-muted")}>
          Average score {fmtScore(result.avg_score)} vs. threshold {fmtScore(result.threshold)}
        </p>
      </div>
    </div>
  );
}

export function RevealControls({ done, onSkip, onReplay }: { done: boolean; onSkip: () => void; onReplay: () => void }) {
  return done ? (
    <Button size="sm" variant="ghost" icon={<RotateCcw className="size-3.5" />} onClick={onReplay}>
      Replay
    </Button>
  ) : (
    <Button size="sm" variant="ghost" icon={<FastForward className="size-3.5" />} onClick={onSkip}>
      Skip
    </Button>
  );
}
