"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronDown } from "lucide-react";
import { DEFAULT_PERSONA, usePersona } from "@/lib/persona-context";
import { cx } from "./ui";

const LINKS = [
  { href: "/", label: "My Agent" },
  { href: "/matches", label: "Matches" },
  { href: "/date", label: "Date" },
  { href: "/insights", label: "Insights" },
];

export function Logo() {
  return (
    <Link href="/" className="flex items-center gap-2 font-semibold tracking-tight">
      <svg viewBox="0 0 32 32" className="size-7" aria-hidden>
        <circle cx="12" cy="16" r="8.5" className="fill-human" />
        <circle cx="20" cy="16" r="8.5" className="fill-agent" opacity="0.85" />
      </svg>
      <span className="text-[17px]">
        Wing<span className="text-human">mate</span>
      </span>
    </Link>
  );
}

export function Nav() {
  const pathname = usePathname();
  const { personaId, setPersonaId, personas } = usePersona();
  const options = personas.length
    ? personas
    : [{ id: personaId || DEFAULT_PERSONA, alias: personaId || DEFAULT_PERSONA, first_name: "" }];

  return (
    <header className="sticky top-0 z-30 border-b border-line bg-bg/85 backdrop-blur">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-3 gap-y-2 px-4 py-3 sm:flex-nowrap sm:px-6">
        <Logo />
        <nav className="order-3 -mx-1 flex w-full gap-1 overflow-x-auto sm:order-none sm:mx-0 sm:ml-6 sm:w-auto">
          {LINKS.map((l) => {
            const active = l.href === "/" ? pathname === "/" : pathname.startsWith(l.href);
            return (
              <Link
                key={l.href}
                href={l.href}
                className={cx(
                  "rounded-lg px-3 py-1.5 text-sm font-medium whitespace-nowrap transition",
                  active ? "bg-surface text-fg shadow-sm ring-1 ring-line" : "text-muted hover:text-fg",
                )}
              >
                {l.label}
              </Link>
            );
          })}
        </nav>
        <label className="relative ml-auto flex items-center gap-2 text-xs text-muted">
          <span className="hidden sm:inline">Viewing as</span>
          <select
            value={personaId}
            onChange={(e) => setPersonaId(e.target.value)}
            className="h-9 appearance-none rounded-lg border border-line bg-surface py-1 pr-8 pl-3 text-sm font-medium text-fg"
            aria-label="Switch persona"
          >
            {options.map((p) => (
              <option key={p.id} value={p.id}>
                {p.alias}
                {p.id === DEFAULT_PERSONA ? " (demo)" : ""}
              </option>
            ))}
          </select>
          <ChevronDown className="pointer-events-none absolute right-2.5 size-4" />
        </label>
      </div>
    </header>
  );
}
