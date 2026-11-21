"use client";

import Link from "next/link";
import { useRef, useState } from "react";
import { ArrowRight, Check, ClipboardCopy, FileUp, ListTree, Sparkles, Upload } from "lucide-react";
import { api, errorMessage, type ImportResult } from "@/lib/api";
import { Button, Card, CardTitle, ErrorBanner, Pill, cx } from "../ui";

import { IMPORT_PROMPT } from "./importPrompt";

export { IMPORT_PROMPT };

type Tab = "paste" | "export";

export function ImportPanel({
  personaId,
  onImported,
}: {
  personaId: string;
  onImported: (r: ImportResult) => void;
}) {
  const [tab, setTab] = useState<Tab>("paste");
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState<null | "paste" | "export" | "sample">(null);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [copied, setCopied] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  async function run(kind: "paste" | "export" | "sample", fn: () => Promise<ImportResult>) {
    setBusy(kind);
    setError(null);
    try {
      const r = await fn();
      setResult(r);
      onImported(r);
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(null);
    }
  }

  async function copyPrompt() {
    try {
      await navigator.clipboard.writeText(IMPORT_PROMPT);
    } catch {
      // Clipboard API blocked (e.g. insecure origin): fall back to a hidden textarea.
      const ta = document.createElement("textarea");
      ta.value = IMPORT_PROMPT;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      ta.remove();
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 1600);
  }

  return (
    <Card>
      <CardTitle
        kicker="Teach your agent"
        tone="agent"
        title="Import what your AI already knows about you"
      />

      <div role="tablist" className="mb-5 inline-flex rounded-xl border border-line bg-surface-2 p-1">
        {(
          [
            ["paste", "Paste from ChatGPT/Claude"],
            ["export", "Upload export"],
          ] as const
        ).map(([key, label]) => (
          <button
            key={key}
            role="tab"
            aria-selected={tab === key}
            onClick={() => setTab(key)}
            className={cx(
              "rounded-lg px-3 py-1.5 text-sm font-medium transition",
              tab === key ? "bg-surface text-fg shadow-sm ring-1 ring-line" : "text-muted hover:text-fg",
            )}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === "paste" ? (
        <div className="space-y-4">
          <div>
            <p className="mb-2 text-sm text-muted">
              <span className="font-medium text-fg">Step 1.</span> Ask your assistant this:
            </p>
            <div className="relative rounded-xl border border-agent/30 bg-agent-soft/60">
              <div className="max-h-72 overflow-y-auto p-4 pr-20 text-sm leading-relaxed whitespace-pre-wrap">
                {IMPORT_PROMPT}
              </div>
              <button
                onClick={copyPrompt}
                className="absolute top-3 right-3 inline-flex items-center gap-1 rounded-md bg-surface px-2 py-1 text-xs font-medium text-agent ring-1 ring-agent/30 hover:bg-agent-soft"
                aria-label="Copy prompt"
              >
                {copied ? <Check className="size-3.5" /> : <ClipboardCopy className="size-3.5" />}
                {copied ? "Copied" : "Copy"}
              </button>
            </div>
          </div>
          <div>
            <p className="mb-2 text-sm text-muted">
              <span className="font-medium text-fg">Step 2.</span> Paste its answer here:
            </p>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              rows={6}
              placeholder="e.g. You've said you love bouldering at Mission Cliffs on weeknights, you'd rather cook at home than go clubbing…"
              className="w-full resize-y rounded-xl border border-line bg-surface-2 p-3 text-sm placeholder:text-muted/70 focus:border-agent focus:outline-none"
            />
          </div>
          <Button
            variant="agent"
            icon={<Sparkles className="size-4" />}
            loading={busy === "paste"}
            disabled={!text.trim() || !!busy}
            onClick={() => run("paste", () => api.importPaste(personaId, text))}
          >
            Import
          </Button>
        </div>
      ) : (
        <div className="space-y-4">
          <p className="text-sm text-muted">
            Upload a ChatGPT or Claude data export (<code className="font-mono text-xs">conversations.json</code> or
            the <code className="font-mono text-xs">.zip</code>). Only your own messages are used, and every fact must
            trace back to something you actually wrote.
          </p>
          <label
            className={cx(
              "flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed px-4 py-8 text-center transition",
              file ? "border-agent/50 bg-agent-soft/40" : "border-line hover:border-agent/40 hover:bg-surface-2",
            )}
          >
            <FileUp className="size-6 text-agent" />
            <span className="text-sm font-medium">{file ? file.name : "Choose conversations.json or .zip"}</span>
            {file && <span className="text-xs text-muted">{(file.size / 1024).toFixed(1)} KB</span>}
            <input
              ref={fileRef}
              type="file"
              accept=".json,.zip,application/json,application/zip"
              className="sr-only"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
          </label>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="agent"
              icon={<Upload className="size-4" />}
              loading={busy === "export"}
              disabled={!file || !!busy}
              onClick={() => file && run("export", () => api.importExport(personaId, file))}
            >
              Import export
            </Button>
            <Button
              variant="neutral"
              icon={<Sparkles className="size-4 text-agent" />}
              loading={busy === "sample"}
              disabled={!!busy}
              onClick={() =>
                run("sample", async () => {
                  const sample = await api.sampleExport(personaId);
                  setFile(sample);
                  return api.importExport(personaId, sample);
                })
              }
            >
              Use sample export
            </Button>
          </div>
        </div>
      )}

      {error && (
        <div className="mt-4">
          <ErrorBanner message={error} />
        </div>
      )}

      {result && <ImportSummary result={result} />}
    </Card>
  );
}

function ImportSummary({ result }: { result: ImportResult }) {
  const steps = [
    { label: "conversations seen", value: result.conversations_seen },
    { label: "kept (dating-relevant)", value: result.conversations_kept },
    { label: "facts extracted", value: result.facts.length },
  ];
  return (
    <div className="animate-msg-in mt-5 rounded-xl border border-line bg-surface-2 p-4">
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <Pill tone="agent">
          <Check className="size-3.5" /> Imported from {result.source === "paste" ? "paste" : result.source}
        </Pill>
        <span className="text-xs text-muted">{result.messages_used} of your messages used</span>
        <Link
          href={`/date?run=${encodeURIComponent(result.run_id)}`}
          className="ml-auto inline-flex items-center gap-1 text-xs font-medium text-agent hover:underline"
        >
          <ListTree className="size-3.5" /> Audit trail
        </Link>
      </div>
      <div className="flex flex-wrap items-center gap-2 sm:gap-3">
        {steps.map((s, i) => (
          <div key={s.label} className="flex items-center gap-2 sm:gap-3">
            <div className="min-w-[88px] rounded-lg bg-surface px-3 py-2 ring-1 ring-line">
              <div className="text-xl font-semibold tabular-nums">{s.value}</div>
              <div className="text-[11px] leading-tight text-muted">{s.label}</div>
            </div>
            {i < steps.length - 1 && <ArrowRight className="size-4 text-muted" />}
          </div>
        ))}
      </div>
      {result.dropped_untraceable > 0 && (
        <p className="mt-3 text-sm text-warn">
          {result.dropped_untraceable} dropped: couldn&apos;t be traced to your words
        </p>
      )}
      <p className="mt-2 text-xs text-muted">New facts start unapproved. Review them below before publishing.</p>
    </div>
  );
}
