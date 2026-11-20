"use client";

import { useCallback, useEffect, useState } from "react";
import { MapPin, ShieldCheck } from "lucide-react";
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
        <h1 className="text-2xl font-semibold tracking-tight">My Agent</h1>
        <ErrorBanner message={error ?? "Persona not found"} onRetry={load} />
      </div>
    );

  return (
    <div className="space-y-6">
      <Card className="relative overflow-hidden">
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.07]"
          style={{ background: `radial-gradient(600px 200px at 0% 0%, ${persona.avatar_color}, transparent)` }}
        />
        <div className="relative flex flex-col gap-5 sm:flex-row sm:items-center">
          <Avatar name={persona.alias} color={persona.avatar_color} size={72} />
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">{persona.alias}</h1>
              <span className="text-xl font-light text-muted">{persona.age}</span>
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
                Verify identity (Persona sandbox)
              </Button>
            )}
            {verifyError && <p className="max-w-xs text-xs text-danger">{verifyError}</p>}
          </div>
        </div>
      </Card>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
        <div className="min-w-0 space-y-6">
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
