"use client";

import { useEffect, useState } from "react";
import { api, errorMessage, API_BASE, type SponsorKey, type StatusResponse } from "@/lib/api";
import { RotateCcw } from "lucide-react";
import { cx } from "./ui";
import { LogoMark } from "./Nav";

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
    <footer className="mt-20 bg-[#081721] text-white/80">
      <div className="mx-auto max-w-6xl px-4 pt-10 pb-8 sm:px-6">
        <div className="mb-8 flex flex-wrap items-end justify-between gap-6">
          <div>
            <p className="relative mb-4 inline-block rounded-[18px] rounded-bl-md bg-white px-4 py-2 text-[15px] leading-snug text-[#1d2326]">
              Your agent goes on the pre-date,
              <br />
              so you only go on the good ones.
            </p>
            <div className="flex items-center gap-2 text-white">
              <LogoMark className="size-8" />
              <span className="font-display text-[40px] leading-none tracking-tight">wingmate</span>
            </div>
          </div>
        </div>
      <div className="flex flex-wrap items-center gap-x-4 gap-y-3 border-t border-white/10 pt-6">
        <p className="text-[11px] font-semibold whitespace-nowrap uppercase tracking-[0.14em] text-white/55">Powered by</p>
        <ul className="flex flex-wrap gap-2">
          {SPONSORS.map((s) => {
            const on = status?.sponsors?.[s.key] ?? false;
            return (
              <li
                key={s.key}
                title={`${s.label}: ${status ? (on ? "live" : "fallback / off") : "unknown"}`}
                className={cx(
                  "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium",
                  on ? "border-[#6aa8ff]/40 bg-[#6aa8ff]/15 text-[#a9cbff]" : "border-white/15 bg-white/5 text-white/60",
                )}
              >
                <span
                  className={cx(
                    "size-1.5 rounded-full",
                    !status ? "bg-white/30" : on ? "bg-[#6aa8ff] shadow-[0_0_0_3px_rgba(106,168,255,0.25)]" : "bg-white/35",
                  )}
                />
                {s.label}
                <span className="opacity-70">{status ? (on ? "on" : "off") : "–"}</span>
              </li>
            );
          })}
        </ul>
        <div className="ml-auto flex items-center gap-3 text-xs whitespace-nowrap text-white/60">
          {error ? (
            <span className="whitespace-normal text-[#ff9a9a]">Status unavailable: backend not reachable at {API_BASE}</span>
          ) : (
            <span>All personas are synthetic.</span>
          )}
          <ResetButton />
        </div>
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
        "inline-flex items-center gap-1 rounded-full border border-white/15 px-3 py-1 font-medium transition hover:bg-white/10 hover:text-white disabled:opacity-50",
        state === "error" && "text-[#ff9a9a]",
      )}
    >
      <RotateCcw className={cx("size-3", state === "busy" && "animate-spin")} />
      {state === "error" ? "Reset failed" : state === "busy" ? "Resetting…" : "Reset demo"}
    </button>
  );
}
