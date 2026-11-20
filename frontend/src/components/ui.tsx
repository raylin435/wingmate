"use client";

import { AlertTriangle, BadgeCheck, Loader2, RotateCw } from "lucide-react";
import type { ButtonHTMLAttributes, ReactNode } from "react";

export function cx(...parts: (string | false | null | undefined)[]) {
  return parts.filter(Boolean).join(" ");
}

type Variant = "human" | "agent" | "neutral" | "ghost";

const variants: Record<Variant, string> = {
  human: "bg-human text-white hover:brightness-110 dark:text-[#1a0a10] shadow-sm shadow-human/20",
  agent: "bg-agent text-white hover:brightness-110 dark:text-[#04201f] shadow-sm shadow-agent/20",
  neutral: "bg-surface text-fg border border-line hover:bg-surface-2",
  ghost: "text-muted hover:text-fg hover:bg-surface-2",
};

export function Button({
  variant = "neutral",
  loading,
  icon,
  className,
  children,
  disabled,
  size = "md",
  ...rest
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant;
  loading?: boolean;
  icon?: ReactNode;
  size?: "sm" | "md";
}) {
  return (
    <button
      {...rest}
      disabled={disabled || loading}
      className={cx(
        "inline-flex items-center justify-center gap-2 rounded-lg font-medium transition",
        "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-agent",
        "disabled:cursor-not-allowed disabled:opacity-50",
        size === "md" ? "h-10 px-4 text-sm" : "h-8 px-3 text-xs",
        variants[variant],
        className,
      )}
    >
      {loading ? <Loader2 className="size-4 animate-spin" /> : icon}
      {children}
    </button>
  );
}

export function Card({ className, children }: { className?: string; children: ReactNode }) {
  return (
    <section className={cx("rounded-2xl border border-line bg-surface p-5 sm:p-6", className)}>{children}</section>
  );
}

export function CardTitle({
  kicker,
  title,
  action,
  tone = "neutral",
}: {
  kicker?: string;
  title: ReactNode;
  action?: ReactNode;
  tone?: "human" | "agent" | "neutral";
}) {
  return (
    <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
      <div>
        {kicker && (
          <p
            className={cx(
              "mb-1 text-[11px] font-semibold uppercase tracking-[0.14em]",
              tone === "human" ? "text-human" : tone === "agent" ? "text-agent" : "text-muted",
            )}
          >
            {kicker}
          </p>
        )}
        <h2 className="text-lg font-semibold tracking-tight">{title}</h2>
      </div>
      {action}
    </div>
  );
}

export function Pill({
  children,
  tone = "neutral",
  className,
}: {
  children: ReactNode;
  tone?: "human" | "agent" | "neutral" | "ok" | "warn";
  className?: string;
}) {
  const tones = {
    human: "bg-human-soft text-human",
    agent: "bg-agent-soft text-agent",
    neutral: "bg-surface-2 text-muted border border-line",
    ok: "bg-ok/10 text-ok",
    warn: "bg-warn/10 text-warn",
  };
  return (
    <span
      className={cx(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium whitespace-nowrap",
        tones[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}

export function ErrorBanner({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div
      role="alert"
      className="flex flex-wrap items-center gap-3 rounded-xl border border-danger/30 bg-danger/5 px-4 py-3 text-sm text-danger"
    >
      <AlertTriangle className="size-4 shrink-0" />
      <span className="min-w-0 flex-1 break-words">{message}</span>
      {onRetry && (
        <button
          onClick={onRetry}
          className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium hover:bg-danger/10"
        >
          <RotateCw className="size-3.5" /> Retry
        </button>
      )}
    </div>
  );
}

export function Spinner({ label }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 text-sm text-muted">
      <Loader2 className="size-4 animate-spin" />
      {label}
    </div>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={cx("animate-pulse rounded-lg bg-surface-2", className)} />;
}

export function Avatar({ name, color, size = 48 }: { name: string; color?: string; size?: number }) {
  const initials = name
    .split(/[\s_-]+/)
    .filter((w) => /^[a-z0-9]/i.test(w))
    .map((w) => w[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
  return (
    <div
      className="grid shrink-0 place-items-center rounded-full font-semibold text-white ring-2 ring-surface"
      style={{
        width: size,
        height: size,
        fontSize: size * 0.36,
        background: `linear-gradient(135deg, ${color || "#C9295F"}, color-mix(in oklab, ${color || "#C9295F"} 60%, #000))`,
      }}
      aria-hidden
    >
      {initials}
    </div>
  );
}

export function VerifiedBadge({ verified }: { verified: boolean }) {
  if (!verified)
    return (
      <Pill tone="neutral" className="text-[11px]">
        Not verified
      </Pill>
    );
  return (
    <Pill tone="agent">
      <BadgeCheck className="size-3.5" /> Verified
    </Pill>
  );
}

export function Stat({ label, value, tone }: { label: string; value: ReactNode; tone?: "human" | "agent" }) {
  return (
    <div className="rounded-xl border border-line bg-surface-2 px-4 py-3">
      <div
        className={cx(
          "text-2xl font-semibold tabular-nums tracking-tight",
          tone === "human" && "text-human",
          tone === "agent" && "text-agent",
        )}
      >
        {value}
      </div>
      <div className="text-xs text-muted">{label}</div>
    </div>
  );
}
