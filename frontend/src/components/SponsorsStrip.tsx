"use client";

import { useEffect, useState } from "react";
import { api, errorMessage, API_BASE, type SponsorKey, type StatusResponse } from "@/lib/api";
import { RotateCcw } from "lucide-react";
import { cx } from "./ui";

const SPONSORS: { key: SponsorKey; label: string }[] = [
  { key: "sie", label: "SIE" },
  { key: "singlestore", label: "SingleStore" },
  { key: "cognee", label: "Cognee" },
  { key: "statsig", label: "Statsig" },
  { key: "amplitude", label: "Amplitude" },
];

export function SponsorsStrip() {
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    const load = () =>
      api
        .status()
        .then((s) => {
          if (!alive) return;
          setStatus(s);
          setError(null);
        })
        .catch((e) => alive && setError(errorMessage(e)));
    load();
    const t = setInterval(load, 20000);
    return () => {
      alive = false;
      clearInterval(t);
    };
  }, []);

  return (
    <footer className="mt-16 border-t border-line">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-4 gap-y-3 px-4 py-6 sm:px-6">
        <p className="text-[11px] font-semibold whitespace-nowrap uppercase tracking-[0.14em] text-muted">Powered by</p>
        <ul className="flex flex-wrap gap-2">
          {SPONSORS.map((s) => {
            const on = status?.sponsors?.[s.key] ?? false;
            return (
              <li
                key={s.key}
                title={`${s.label}: ${status ? (on ? "live" : "fallback / off") : "unknown"}`}
                className={cx(
                  "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium",
                  on ? "border-agent/40 bg-agent-soft text-agent" : "border-line bg-surface text-muted",
                )}
              >
                <span
                  className={cx(
                    "size-1.5 rounded-full",
                    !status ? "bg-muted/40" : on ? "bg-agent shadow-[0_0_0_3px] shadow-agent/20" : "bg-muted/50",
                  )}
                />
                {s.label}
                <span className="opacity-70">{status ? (on ? "on" : "off") : "–"}</span>
              </li>
            );
          })}
        </ul>
        <div className="ml-auto flex items-center gap-3 text-xs whitespace-nowrap text-muted">
          {error ? (
            <span className="whitespace-normal text-danger">Status unavailable: backend not reachable at {API_BASE}</span>
          ) : (
            <span>Personas are fictional, except Cici, a real teammate who shared her own data.</span>
          )}
          <ResetButton />
        </div>
      </div>
    </footer>
  );
}

function ResetButton() {
  const [state, setState] = useState<"idle" | "busy" | "error">("idle");
  async function reset() {
    setState("busy");
    try {
      await api.reset();
      try {
        // Drop client-side flow state (bookings) so the demo starts clean.
        Object.keys(localStorage)
          .filter((k) => k.startsWith("wingmate.booking.") || k === "wingmate.lastBooking")
          .forEach((k) => localStorage.removeItem(k));
      } catch {
        // storage unavailable
      }
      window.location.reload();
    } catch {
      setState("error");
      setTimeout(() => setState("idle"), 2500);
    }
  }
  return (
    <button
      onClick={reset}
      disabled={state === "busy"}
      title="Reload seed data on the backend"
      className={cx(
        "inline-flex items-center gap-1 rounded-md px-2 py-1 font-medium transition hover:bg-surface-2 hover:text-fg disabled:opacity-50",
        state === "error" && "text-danger",
      )}
    >
      <RotateCcw className={cx("size-3", state === "busy" && "animate-spin")} />
      {state === "error" ? "Reset failed" : state === "busy" ? "Resetting…" : "Reset demo"}
    </button>
  );
}
