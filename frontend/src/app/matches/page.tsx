"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { CalendarHeart, HeartHandshake, ListTree, Search, Sparkles } from "lucide-react";
import {
  api,
  errorMessage,
  type AcceptResponse,
  type Candidate,
  type PredateResponse,
  type SearchResponse,
} from "@/lib/api";
import { usePersona } from "@/lib/persona-context";
import { saveBooking } from "@/lib/storage";
import { Button, Card, CardTitle, ErrorBanner, Pill, Skeleton, Spinner } from "@/components/ui";
import { CandidateCard } from "@/components/matches/CandidateCard";
import { MatchBanner, RevealControls, Transcript, VerdictCard, useReveal } from "@/components/matches/PredateView";

const TALKING_LINES = [
  "Agents are exchanging intros…",
  "Comparing weekend plans…",
  "Checking deal-breakers politely…",
  "Citing each other's own words…",
];

export default function MatchesPage() {
  const router = useRouter();
  const { personaId, personas } = usePersona();
  const me = personas.find((p) => p.id === personaId);
  const myAlias = me?.alias ?? personaId;

  const [search, setSearch] = useState<SearchResponse | null>(null);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  const [candidate, setCandidate] = useState<Candidate | null>(null);
  const [predate, setPredate] = useState<PredateResponse | null>(null);
  const [predating, setPredating] = useState(false);
  const [predateError, setPredateError] = useState<string | null>(null);
  const [talkLine, setTalkLine] = useState(0);

  const [accept, setAccept] = useState<AcceptResponse | null>(null);
  const [accepting, setAccepting] = useState(false);
  const [booking, setBooking] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const predateRef = useRef<HTMLDivElement>(null);
  const reveal = useReveal(predate?.transcript.length ?? 0, predate?.run_id ?? "");

  // Reset the whole flow when switching persona.
  useEffect(() => {
    setSearch(null);
    setCandidate(null);
    setPredate(null);
    setAccept(null);
    setSearchError(null);
    setPredateError(null);
    setActionError(null);
  }, [personaId]);

  useEffect(() => {
    if (!predating) return;
    const t = setInterval(() => setTalkLine((i) => (i + 1) % TALKING_LINES.length), 1800);
    return () => clearInterval(t);
  }, [predating]);

  async function runSearch() {
    setSearching(true);
    setSearchError(null);
    setCandidate(null);
    setPredate(null);
    setAccept(null);
    try {
      setSearch(await api.search(personaId));
    } catch (e) {
      setSearchError(errorMessage(e));
    } finally {
      setSearching(false);
    }
  }

  async function runPredate(c: Candidate) {
    setCandidate(c);
    setPredate(null);
    setAccept(null);
    setPredateError(null);
    setActionError(null);
    setPredating(true);
    setTimeout(() => predateRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 50);
    try {
      setPredate(await api.predate(personaId, c.agent_id, search?.run_id));
    } catch (e) {
      setPredateError(errorMessage(e));
    } finally {
      setPredating(false);
    }
  }

  async function runAccept() {
    if (!candidate || !predate) return;
    setAccepting(true);
    setActionError(null);
    try {
      setAccept(await api.accept(personaId, candidate.agent_id, predate.run_id));
    } catch (e) {
      setActionError(errorMessage(e));
    } finally {
      setAccepting(false);
    }
  }

  async function runBook() {
    if (!candidate || !predate) return;
    setBooking(true);
    setActionError(null);
    try {
      const { booking: b } = await api.book(personaId, candidate.agent_id, predate.run_id);
      saveBooking({
        booking: b,
        run_id: predate.run_id,
        persona_id: personaId,
        candidate_id: candidate.agent_id,
        partner_alias: candidate.alias,
        partner_first_name: accept?.revealed?.[candidate.agent_id],
        my_first_name: accept?.revealed?.[personaId] ?? me?.first_name,
      });
      router.push(`/date?booking=${encodeURIComponent(b.id)}&run=${encodeURIComponent(predate.run_id)}`);
    } catch (e) {
      setActionError(errorMessage(e));
      setBooking(false);
    }
  }

  const candidates = search ? [...search.candidates].sort((a, b) => a.rerank_rank - b.rerank_rank) : [];
  const myVerdictKey = predate
    ? Object.keys(predate.verdicts).find((k) => k === personaId || k.startsWith(personaId)) ??
      Object.keys(predate.verdicts).find((k) => k !== candidate?.agent_id)
    : undefined;
  const theirVerdictKey = predate
    ? candidate && predate.verdicts[candidate.agent_id]
      ? candidate.agent_id
      : Object.keys(predate.verdicts).find((k) => k !== myVerdictKey)
    : undefined;

  const myName = accept?.revealed?.[personaId] ?? me?.first_name;
  const theirName = candidate ? accept?.revealed?.[candidate.agent_id] : undefined;

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="mb-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-agent">Agent search</p>
          <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Matches for {myAlias}</h1>
          <p className="mt-1 max-w-xl text-sm text-muted">
            Your agent searches other agents by vector similarity, then reranks by reading their cards. Rank moves show
            where the second look changed its mind.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {search && (
            <Pill tone="neutral" className="font-mono">
              strategy: {search.strategy}
            </Pill>
          )}
          <Button variant="agent" icon={<Search className="size-4" />} loading={searching} onClick={runSearch}>
            {search ? "Search again" : "Find matches"}
          </Button>
        </div>
      </div>

      {searchError && <ErrorBanner message={searchError} onRetry={runSearch} />}

      {searching && !search && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-56" />
          ))}
        </div>
      )}

      {!search && !searching && !searchError && (
        <Card className="py-12 text-center">
          <Sparkles className="mx-auto mb-3 size-8 text-agent" />
          <p className="font-medium">Ready when you are.</p>
          <p className="text-sm text-muted">Hit “Find matches” to let your agent scan the other 29 agents.</p>
        </Card>
      )}

      {search && (
        <>
          {candidates.length === 0 ? (
            <Card className="text-center text-sm text-muted">No candidates passed the match policy.</Card>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {candidates.map((c) => (
                <CandidateCard
                  key={c.agent_id}
                  c={c}
                  active={candidate?.agent_id === c.agent_id}
                  disabled={predating}
                  onPredate={() => runPredate(c)}
                />
              ))}
            </div>
          )}
          <Link
            href={`/date?run=${encodeURIComponent(search.run_id)}`}
            className="inline-flex items-center gap-1 text-xs font-medium text-agent hover:underline"
          >
            <ListTree className="size-3.5" /> Search audit trail
          </Link>
        </>
      )}

      {candidate && (
        <div ref={predateRef} className="scroll-mt-24 space-y-5">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <p className="mb-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-agent">
                Agent-to-agent pre-date
              </p>
              <h2 className="text-xl font-semibold tracking-tight">
                {myAlias}&apos;s agent <span className="text-muted">×</span> {candidate.alias}&apos;s agent
              </h2>
            </div>
            {predate && <RevealControls done={reveal.done} onSkip={reveal.skip} onReplay={reveal.replay} />}
          </div>

          {predateError && <ErrorBanner message={predateError} onRetry={() => runPredate(candidate)} />}

          {(predating || predate) && (
            <Transcript
              transcript={predate?.transcript ?? []}
              myId={personaId}
              myLabel={`${myAlias}'s agent`}
              theirLabel={`${candidate.alias}'s agent`}
              count={reveal.count}
              pending={predating}
            />
          )}
          {predating && <Spinner label={TALKING_LINES[talkLine]} />}

          {predate && reveal.done && (
            <div className="space-y-5">
              <div className="grid gap-4 md:grid-cols-2">
                <VerdictCard
                  title={`${myAlias}'s agent`}
                  verdict={myVerdictKey ? predate.verdicts[myVerdictKey] : undefined}
                  mine
                />
                <VerdictCard
                  title={`${candidate.alias}'s agent`}
                  verdict={theirVerdictKey ? predate.verdicts[theirVerdictKey] : undefined}
                  mine={false}
                />
              </div>
              <MatchBanner result={predate} />

              {predate.match && (
                <Card className="border-human/30">
                  <CardTitle
                    kicker="Your call"
                    tone="human"
                    title={accept?.both_accepted ? "You both said yes" : "The agents did their part. Now it's up to you."}
                  />
                  {!accept && (
                    <>
                      <p className="mb-4 text-sm text-muted">
                        Accepting reveals first names to each other. Nothing is booked until both humans accept.
                      </p>
                      <Button
                        variant="human"
                        icon={<HeartHandshake className="size-4" />}
                        loading={accepting}
                        onClick={runAccept}
                      >
                        Accept match
                      </Button>
                    </>
                  )}
                  {accept && !accept.both_accepted && (
                    <p className="text-sm text-muted">
                      Your yes is recorded. Waiting for {candidate.alias} to accept. First names stay hidden until then.
                    </p>
                  )}
                  {accept?.both_accepted && (
                    <div className="animate-msg-in space-y-5">
                      <div className="flex flex-wrap items-center gap-3 text-2xl font-semibold tracking-tight sm:text-3xl">
                        <span className="text-human">{myName ?? myAlias}</span>
                        <HeartHandshake className="size-7 text-human" />
                        <span className="text-human">{theirName ?? candidate.alias}</span>
                      </div>
                      <p className="text-sm text-muted">
                        Names revealed. Your agents will pick a venue that suits you both.
                      </p>
                      <Button
                        variant="human"
                        icon={<CalendarHeart className="size-4" />}
                        loading={booking}
                        onClick={runBook}
                      >
                        Book the date
                      </Button>
                    </div>
                  )}
                </Card>
              )}
              {actionError && <ErrorBanner message={actionError} />}
              <Link
                href={`/date?run=${encodeURIComponent(predate.run_id)}`}
                className="inline-flex items-center gap-1 text-xs font-medium text-agent hover:underline"
              >
                <ListTree className="size-3.5" /> Pre-date audit trail
              </Link>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
