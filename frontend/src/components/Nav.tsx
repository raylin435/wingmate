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

export function LogoMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" className={className} aria-hidden>
      <circle cx="12" cy="16" r="8.5" fill="#ff2cab" />
      <circle cx="20" cy="16" r="8.5" fill="#3d8bff" opacity="0.85" />
    </svg>
  );
}

export function Logo() {
  return (
    <Link href="/" className="flex items-center gap-2 text-white">
      <LogoMark className="size-7" />
      <span className="font-display text-[28px] leading-none tracking-tight">wingmate</span>
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
    <header className="sticky top-0 z-30 border-b border-white/15 bg-[#2f5664]/55 backdrop-blur-xl backdrop-saturate-150 dark:bg-[#081022]/65">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-3 gap-y-2 px-4 py-3 sm:px-6 lg:flex-nowrap">
        <Logo />
        <nav className="order-3 -mx-1 flex w-full gap-1 overflow-x-auto lg:order-none lg:mx-0 lg:ml-6 lg:w-auto">
          {LINKS.map((l) => {
            const active = l.href === "/" ? pathname === "/" : pathname.startsWith(l.href);
            return (
              <Link
                key={l.href}
                href={l.href}
                className={cx(
                  "rounded-full px-3.5 py-1.5 text-sm font-medium whitespace-nowrap transition",
                  active
                    ? "bg-white/95 font-semibold text-[#c4166f] shadow-[0_6px_18px_-10px_rgba(0,0,0,0.5)]"
                    : "text-white/85 hover:bg-white/12 hover:text-white",
                )}
              >
                {l.label}
              </Link>
            );
          })}
        </nav>
        <label className="relative ml-auto flex items-center gap-2 text-xs text-white/80">
          <span className="hidden lg:inline">Viewing as</span>
          <select
            value={personaId}
            onChange={(e) => setPersonaId(e.target.value)}
            className="h-9 max-w-[200px] appearance-none truncate rounded-full border border-white/35 bg-white/12 py-1 pr-8 pl-3.5 text-sm font-medium text-white [color-scheme:dark] hover:bg-white/18"
            aria-label="Switch persona"
          >
            {options.map((p) => (
              <option key={p.id} value={p.id}>
                {p.alias}
                {p.id === DEFAULT_PERSONA ? " (demo)" : ""}
              </option>
            ))}
          </select>
          <ChevronDown className="pointer-events-none absolute right-2.5 size-4 text-white" />
        </label>
      </div>
    </header>
  );
}
