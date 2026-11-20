"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { CalendarPlus, Clock, HeartHandshake, ListTree, MapPin, Sparkles } from "lucide-react";
import { api, formatDateRangeLA, type Booking } from "@/lib/api";
import { lastBookingId, loadBooking, type StoredBooking } from "@/lib/storage";
import { AuditTimeline } from "@/components/AuditTimeline";
import { Button, Card, CardTitle, Pill, Skeleton } from "@/components/ui";

export default function DatePage() {
  return (
    <Suspense fallback={<Skeleton className="h-64" />}>
      <DateInner />
    </Suspense>
  );
}

function DateInner() {
  const params = useSearchParams();
  const router = useRouter();
  const bookingParam = params.get("booking");
  const runParam = params.get("run");

  const [stored, setStored] = useState<StoredBooking | null>(null);
  const [icsBooking, setIcsBooking] = useState<Booking | null>(null);
  const [hydrated, setHydrated] = useState(false);
  const [runInput, setRunInput] = useState("");

  const bookingId = bookingParam ?? (hydrated && !runParam ? lastBookingId() : null);

  useEffect(() => setHydrated(true), []);

  useEffect(() => {
    if (!bookingId) {
      setStored(null);
      return;
    }
    const s = loadBooking(bookingId);
    setStored(s);
    if (!s) {
      // Booking wasn't made in this browser: recover what we can from the .ics.
      api
        .icsText(bookingId)
        .then((t) => setIcsBooking(parseIcs(t, bookingId)))
        .catch(() => setIcsBooking(null));
    }
  }, [bookingId]);

  const booking = stored?.booking ?? icsBooking;
  const runId = runParam ?? stored?.run_id ?? null;

  return (
    <div className="space-y-8">
      {bookingId ? (
        booking ? (
          <BookingCard booking={booking} stored={stored} />
        ) : (
          <Card>
            <p className="text-sm text-muted">
              Loading booking <code className="font-mono">{bookingId}</code>…
            </p>
          </Card>
        )
      ) : (
        hydrated && (
          <Card className="py-10 text-center">
            <HeartHandshake className="mx-auto mb-3 size-8 text-human" />
            <p className="font-medium">No date booked yet</p>
            <p className="mb-4 text-sm text-muted">Run a pre-date on the Matches page and book it.</p>
            <Link href="/matches" className="text-sm font-medium text-human hover:underline">
              Go to Matches →
            </Link>
          </Card>
        )
      )}

      <Card>
        <CardTitle
          kicker="Every step, on the record"
          tone="agent"
          title={
            <span className="inline-flex flex-wrap items-center gap-2">
              <ListTree className="size-5 text-agent" /> Audit trail
              {runId && <code className="rounded bg-surface-2 px-2 py-0.5 font-mono text-xs font-normal text-muted ring-1 ring-line">{runId}</code>}
            </span>
          }
          action={
            <form
              className="flex gap-2"
              onSubmit={(e) => {
                e.preventDefault();
                const r = runInput.trim();
                if (!r) return;
                const q = new URLSearchParams();
                if (bookingParam) q.set("booking", bookingParam);
                q.set("run", r);
                router.push(`/date?${q.toString()}`);
              }}
            >
              <input
                value={runInput}
                onChange={(e) => setRunInput(e.target.value)}
                placeholder="Load run_id…"
                className="h-8 w-36 rounded-lg border border-line bg-surface-2 px-2.5 font-mono text-xs focus:border-agent focus:outline-none sm:w-44"
              />
              <Button size="sm" type="submit">
                Load
              </Button>
            </form>
          }
        />
        {runId ? (
          <AuditTimeline runId={runId} />
        ) : (
          <p className="rounded-xl border border-dashed border-line px-4 py-8 text-center text-sm text-muted">
            No run selected. Import, publish, search or pre-date to create one.
          </p>
        )}
      </Card>
    </div>
  );
}

function BookingCard({ booking, stored }: { booking: Booking; stored: StoredBooking | null }) {
  const { day, time } = formatDateRangeLA(booking.start, booking.end);
  const me = stored?.my_first_name;
  const them = stored?.partner_first_name ?? stored?.partner_alias;
  return (
    <section className="relative overflow-hidden rounded-3xl border border-human/30 bg-surface">
      <div
        className="pointer-events-none absolute inset-0 opacity-60 dark:opacity-40"
        style={{
          background:
            "radial-gradient(500px 220px at 100% 0%, color-mix(in oklab, var(--human) 18%, transparent), transparent), radial-gradient(400px 200px at 0% 100%, color-mix(in oklab, var(--agent) 14%, transparent), transparent)",
        }}
      />
      <div className="relative grid gap-6 p-6 sm:p-8 md:grid-cols-[1fr_auto]">
        <div className="min-w-0">
          <Pill tone="human" className="mb-3">
            <HeartHandshake className="size-3.5" /> First date booked
          </Pill>
          {me && them && (
            <p className="mb-1 text-sm font-medium text-human">
              {me} &amp; {them}
            </p>
          )}
          <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">{booking.venue.name}</h1>
          <p className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted">
            <span className="inline-flex items-center gap-1">
              <MapPin className="size-4" /> {booking.venue.neighborhood}
            </span>
            <span className="inline-flex items-center gap-1">
              <Clock className="size-4" /> {day} · {time}
            </span>
          </p>
          {booking.venue.tags?.length > 0 && (
            <ul className="mt-4 flex flex-wrap gap-1.5">
              {booking.venue.tags.map((t) => (
                <li key={t}>
                  <Pill tone="neutral">{t}</Pill>
                </li>
              ))}
            </ul>
          )}
          {booking.venue.why && (
            <div className="mt-5 max-w-2xl rounded-xl bg-agent-soft/70 p-4 ring-1 ring-agent/20">
              <p className="mb-1 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-[0.14em] text-agent">
                <Sparkles className="size-3.5" /> Why your agents chose it
              </p>
              <p className="text-sm leading-relaxed">{booking.venue.why}</p>
            </div>
          )}
        </div>
        <div className="flex flex-col items-start gap-3 md:items-end">
          <div className="rounded-2xl bg-surface px-5 py-4 text-center ring-1 ring-line">
            <div className="text-xs font-semibold uppercase tracking-wider text-human">
              {formatDateRangeLA(booking.start, booking.end).day.split(",")[0]}
            </div>
            <div className="text-4xl font-semibold tabular-nums">
              {new Intl.DateTimeFormat("en-US", { timeZone: "America/Los_Angeles", day: "numeric" }).format(
                new Date(booking.start),
              )}
            </div>
            <div className="text-xs text-muted">
              {new Intl.DateTimeFormat("en-US", { timeZone: "America/Los_Angeles", month: "short" }).format(
                new Date(booking.start),
              )}
            </div>
          </div>
          <a
            href={api.icsUrl(booking.id)}
            className="inline-flex h-10 items-center gap-2 rounded-lg bg-human px-4 text-sm font-medium text-white shadow-sm shadow-human/20 hover:brightness-110 dark:text-[#1a0a10]"
          >
            <CalendarPlus className="size-4" /> Add to calendar
          </a>
        </div>
      </div>
    </section>
  );
}

/** Minimal .ics reader used only when the booking wasn't made in this browser. */
function parseIcs(text: string, id: string): Booking | null {
  const unfolded = text.replace(/\r?\n[ \t]/g, "");
  const get = (key: string) => {
    const m = new RegExp(`^${key}(?:;[^:]*)?:(.*)$`, "m").exec(unfolded);
    return m?.[1]?.trim().replace(/\\n/g, "\n").replace(/\\([,;\\])/g, "$1");
  };
  const toIso = (v?: string) => {
    if (!v) return "";
    const m = /^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})(Z?)$/.exec(v);
    if (!m) return v;
    return `${m[1]}-${m[2]}-${m[3]}T${m[4]}:${m[5]}:${m[6]}${m[7] ? "Z" : ""}`;
  };
  const summary = get("SUMMARY");
  const start = toIso(get("DTSTART"));
  if (!summary || !start) return null;
  return {
    id,
    venue: {
      name: get("LOCATION")?.split(",")[0] || summary,
      neighborhood: get("LOCATION")?.split(",").slice(1).join(",").trim() || "",
      tags: [],
      why: get("DESCRIPTION") || "",
    },
    start,
    end: toIso(get("DTEND")) || start,
    ics_path: `/api/bookings/${id}.ics`,
  };
}
