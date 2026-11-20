"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, Heart, MapPin, ShieldCheck } from "lucide-react";
import { api, errorMessage, type Fact, type ImportResult, type Persona } from "@/lib/api";
import { usePersona } from "@/lib/persona-context";
import { Avatar, Button, Card, ErrorBanner, Pill, Skeleton, VerifiedBadge } from "@/components/ui";
import { ImportPanel } from "@/components/agent/ImportPanel";
import { FactList } from "@/components/agent/FactList";
import { PublishPanel } from "@/components/agent/PublishPanel";

export default function MyAgentPage() {
  const { personaId } = usePersona();
  const [persona, setPersona] = useState<Persona | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [highlight, setHighlight] = useState<Set<string>>(new Set());
  const [verifying, setVerifying] = useState(false);
  const [verifyError, setVerifyError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setPersona(await api.persona(personaId));
    } catch (e) {
      setError(errorMessage(e));
      setPersona(null);
    } finally {
      setLoading(false);
    }
  }, [personaId]);

  useEffect(() => {
    setHighlight(new Set());
    load();
  }, [load]);

  async function onImported(r: ImportResult) {
    setHighlight(new Set(r.facts.map((f) => f.id)));
    // Refetch so the list reflects the server, then merge in case the import facts aren't persisted on the persona yet.
    try {
      const fresh = await api.persona(personaId);
      const known = new Set(fresh.facts.map((f) => f.id));
      setPersona({ ...fresh, facts: [...fresh.facts, ...r.facts.filter((f) => !known.has(f.id))] });
    } catch {
      setPersona((p) => {
        if (!p) return p;
        const known = new Set(p.facts.map((f) => f.id));
        return { ...p, facts: [...p.facts, ...r.facts.filter((f) => !known.has(f.id))] };
      });
    }
  }

  async function verify() {
    setVerifying(true);
    setVerifyError(null);
    try {
      const r = await api.verify(personaId);
      setPersona((p) => (p ? { ...p, verified: r.verified } : p));
    } catch (e) {
      setVerifyError(errorMessage(e));
    } finally {
      setVerifying(false);
    }
  }

  const setFacts = (facts: Fact[]) => setPersona((p) => (p ? { ...p, facts } : p));

  if (loading && !persona) return <PageSkeleton />;
  if (error || !persona)
    return (
      <div className="space-y-4">
        <h1 className="sky-title text-5xl">My Agent</h1>
        <ErrorBanner message={error ?? "Persona not found"} onRetry={load} />
      </div>
    );

  return (
    <div className="space-y-6">
      <Hero />
      <Card className="relative overflow-hidden">
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.07]"
          style={{ background: `radial-gradient(600px 200px at 0% 0%, ${persona.avatar_color}, transparent)` }}
        />
        <div className="relative flex flex-col gap-5 sm:flex-row sm:items-center">
          <Avatar name={persona.alias} color={persona.avatar_color} size={84} shape="photo" tilt={-4} />
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="font-display text-[34px] leading-none tracking-tight sm:text-[40px]">{persona.alias}</h2>
              <span className="font-display text-[28px] leading-none text-muted">{persona.age}</span>
              <VerifiedBadge verified={persona.verified} />
            </div>
            <p className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-muted">
              <span className="inline-flex items-center gap-1">
                <MapPin className="size-3.5" /> {persona.neighborhood}
              </span>
              {persona.seeking && (
                <span>
                  Seeking {persona.seeking.genders.join(" / ")} · {persona.seeking.min_age}–{persona.seeking.max_age}
                </span>
              )}
            </p>
            {persona.tagline && <p className="mt-2 max-w-2xl text-[15px]">{persona.tagline}</p>}
          </div>
          <div className="flex flex-col items-start gap-2 sm:items-end">
            {persona.verified ? (
              <Pill tone="agent" className="px-3 py-1">
                <ShieldCheck className="size-4" /> Identity verified via Persona
              </Pill>
            ) : (
              <Button variant="human" icon={<ShieldCheck className="size-4" />} loading={verifying} onClick={verify}>
                Verify identity (simulated)
              </Button>
            )}
            {verifyError && <p className="max-w-xs text-xs text-danger">{verifyError}</p>}
          </div>
        </div>
      </Card>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
        <div id="teach" className="min-w-0 scroll-mt-24 space-y-6">
          <ImportPanel personaId={personaId} onImported={onImported} />
          <FactList personaId={personaId} facts={persona.facts} highlight={highlight} onChange={setFacts} />
        </div>
        <aside className="lg:sticky lg:top-20 lg:self-start">
          <PublishPanel
            personaId={personaId}
            facts={persona.facts}
            currentSummary={persona.card_summary}
            onPublished={(r) => setPersona((p) => (p ? { ...p, card_summary: r.card_summary } : p))}
          />
        </aside>
      </div>
    </div>
  );
}

function Hero() {
  return (
    <section className="relative pt-6 pb-4 text-center sm:pt-10 sm:pb-8">
      <ChatBubblesArt />
      <h1 className="sky-title mx-auto max-w-3xl text-[54px] leading-[0.9] sm:text-[88px]">
        your agent dates
        <br />
        their agent first
      </h1>
      <p className="sky-text mx-auto mt-4 max-w-lg text-[15px] leading-relaxed sm:text-base">
        Teach it who you are. It meets other people&apos;s verified agents on a short pre-date, and only books the
        dates worth going on.
      </p>
      <div className="mt-6 flex flex-wrap justify-center gap-3">
        <Link
          href="/matches"
          className="inline-flex h-11 items-center gap-2 rounded-full bg-white/95 px-6 text-sm font-semibold text-[#c4166f] shadow-[0_10px_28px_-12px_rgba(0,0,0,0.45)] transition hover:bg-white active:scale-[0.98]"
        >
          Find my matches <ArrowRight className="size-4" />
        </Link>
        <a
          href="#teach"
          className="inline-flex h-11 items-center rounded-full border border-white/40 bg-white/10 px-6 text-sm font-semibold text-white backdrop-blur transition hover:bg-white/20"
        >
          Teach my agent
        </a>
      </div>
    </section>
  );
}

/** Two message bubbles and a heart, drifting above the headline. */
function ChatBubblesArt() {
  return (
    <div className="animate-float mx-auto mb-3 flex w-fit items-end gap-1.5" aria-hidden>
      <div className="rounded-[18px] rounded-bl-md bg-white/95 px-3 py-2 shadow-[0_10px_24px_-12px_rgba(0,0,0,0.5)]">
        <div className="flex gap-1">
          <span className="size-1.5 rounded-full bg-[#9aa3ad]" />
          <span className="size-1.5 rounded-full bg-[#9aa3ad]" />
          <span className="size-1.5 rounded-full bg-[#9aa3ad]" />
        </div>
      </div>
      <div className="mb-4 grid size-9 place-items-center rounded-full bg-[#ff2cab] text-white shadow-[0_10px_24px_-10px_#ff2cab]">
        <Heart className="size-4 fill-current" />
      </div>
      <div className="rounded-[18px] rounded-br-md bg-[#1f6fe0] px-3 py-2 text-xs font-medium text-white shadow-[0_10px_24px_-12px_rgba(0,0,0,0.5)]">
        Friday, 7pm?
      </div>
    </div>
  );
}

function PageSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-32" />
      <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
        <Skeleton className="h-96" />
        <Skeleton className="h-64" />
      </div>
    </div>
  );
}
