"use client";

import { AlertTriangle, BadgeCheck, Check, ClipboardCopy, Loader2, RotateCw } from "lucide-react";
import { useState, type ButtonHTMLAttributes, type ReactNode } from "react";

export function cx(...parts: (string | false | null | undefined)[]) {
  return parts.filter(Boolean).join(" ");
}

type Variant = "human" | "agent" | "neutral" | "ghost" | "cta";

const variants: Record<Variant, string> = {
  human: "bg-human text-white hover:brightness-110 dark:text-[#2a0718] shadow-[0_10px_24px_-12px_var(--human)]",
  agent: "bg-agent text-white hover:brightness-110 dark:text-[#04152e] shadow-[0_10px_24px_-12px_var(--agent)]",
  neutral: "bg-white/70 text-fg border border-line hover:bg-white dark:bg-white/8 dark:hover:bg-white/14",
  ghost: "text-muted hover:text-fg hover:bg-surface-2",
  // White pill with pink label, for calls to action that sit on the sky.
  cta: "bg-white/95 text-human dark:text-[#c4166f] hover:bg-white shadow-[inset_0_0_8px_rgba(255,255,255,0.15),0_10px_28px_-12px_rgba(0,0,0,0.45)]",
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
        "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-full font-semibold transition active:scale-[0.98]",
        "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-agent",
        "disabled:cursor-not-allowed disabled:opacity-50",
        size === "md" ? "h-11 px-5 text-sm" : "h-9 px-4 text-xs",
        variants[variant],
        className,
      )}
    >
      {loading ? <Loader2 className="size-4 animate-spin" /> : icon}
      {children}
    </button>
  );
}

/** Copies text, falling back to a hidden textarea where the Clipboard API is blocked. */
export function CopyButton({
  text,
  label = "Copy",
  variant = "neutral",
  size = "sm",
  className,
}: {
  text: string;
  label?: string;
  variant?: Variant;
  size?: "sm" | "md";
  className?: string;
}) {
  const [copied, setCopied] = useState(false);
  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      const ta = document.createElement("textarea");
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      ta.remove();
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 1600);
  }
  return (
    <Button
      variant={variant}
      size={size}
      className={className}
      disabled={!text}
      onClick={copy}
      icon={copied ? <Check className="size-3.5" /> : <ClipboardCopy className="size-3.5" />}
    >
      {copied ? "Copied" : label}
    </Button>
  );
}

export function Card({ className, children }: { className?: string; children: ReactNode }) {
  return (
    <section className={cx("glass rounded-[28px] p-5 sm:p-7", className)}>{children}</section>
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
          <Sticker tone={tone} className="mb-2">
            {kicker}
          </Sticker>
        )}
        <h2 className="font-display text-[26px] leading-tight tracking-tight">{title}</h2>
      </div>
      {action}
    </div>
  );
}

/** Slightly tilted label, like a sticker slapped on a photo. */
export function Sticker({
  children,
  tone = "neutral",
  className,
}: {
  children: ReactNode;
  tone?: "human" | "agent" | "neutral" | "tag";
  className?: string;
}) {
  const tones = {
    human: "bg-human text-white dark:text-[#2a0718]",
    agent: "bg-agent text-white dark:text-[#04152e]",
    neutral: "bg-fg text-bg",
    tag: "bg-tag text-tag-fg",
  };
  return (
    <span
      className={cx(
        "inline-flex -rotate-2 items-center gap-1.5 px-2 py-0.5 font-display text-[17px] leading-tight shadow-[0_4px_12px_-6px_rgba(0,0,0,0.5)]",
        tones[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}

/** Page title set in the display serif, straight on the sky. */
export function PageHeader({
  kicker,
  tone = "neutral",
  title,
  children,
  action,
}: {
  kicker?: string;
  tone?: "human" | "agent" | "neutral" | "tag";
  title: ReactNode;
  children?: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-5 pt-2 sm:flex-row sm:items-end sm:justify-between">
      <div className="min-w-0">
        {kicker && <Sticker tone={tone}>{kicker}</Sticker>}
        <h1 className="sky-title mt-3 text-[44px] leading-[0.95] sm:text-[64px]">{title}</h1>
        {children && <p className="sky-text mt-3 max-w-xl text-[15px] leading-relaxed">{children}</p>}
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

export function Avatar({
  name,
  color,
  size = 48,
  shape = "circle",
  tilt = 0,
}: {
  name: string;
  color?: string;
  size?: number;
  shape?: "circle" | "photo";
  tilt?: number;
}) {
  const initials = name
    .split(/[\s_-]+/)
    .filter((w) => /^[a-z0-9]/i.test(w))
    .map((w) => w[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
  return (
    <div
      className={cx(
        "grid shrink-0 place-items-center text-white",
        shape === "circle"
          ? "rounded-full font-semibold ring-2 ring-white/80"
          : "rounded-[6px] font-display ring-[3px] ring-white shadow-[0_10px_22px_-10px_rgba(0,0,0,0.55)]",
      )}
      style={{
        width: size,
        height: size,
        fontSize: size * (shape === "photo" ? 0.46 : 0.36),
        transform: tilt ? `rotate(${tilt}deg)` : undefined,
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
    <div className="rounded-2xl border border-line bg-surface-2 px-4 py-3">
      <div
        className={cx(
          "font-display text-3xl tabular-nums",
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
