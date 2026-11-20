"use client";

import { useCallback, useEffect, useState } from "react";
import { FlaskConical, Play, SlidersHorizontal } from "lucide-react";
import { api, errorMessage, type ConfigResponse, type FunnelCounts, type SimulateResponse } from "@/lib/api";
import { Button, Card, CardTitle, ErrorBanner, Pill, Skeleton, cx, PageHeader } from "@/components/ui";

const STAGES: { key: keyof FunnelCounts; label: string }[] = [
  { key: "searched", label: "Searched" },
  { key: "proposed", label: "Proposed" },
  { key: "mutual_accept", label: "Mutual accept" },
  { key: "booked", label: "Booked" },
];

const ARM_LABEL: Record<string, string> = {
  vector_only: "Vector only",
  agent_predate: "Agent pre-date",
};

export default function InsightsPage() {
  const [config, setConfig] = useState<ConfigResponse | null>(null);
  const [configError, setConfigError] = useState<string | null>(null);
  const [sim, setSim] = useState<SimulateResponse | null>(null);
  const [simError, setSimError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);

  const loadConfig = useCallback(() => {
    setConfigError(null);
    api
      .config()
      .then(setConfig)
      .catch((e) => setConfigError(errorMessage(e)));
  }, []);

  useEffect(loadConfig, [loadConfig]);

  async function simulate() {
    setRunning(true);
    setSimError(null);
    try {
      setSim(await api.simulate());
    } catch (e) {
      setSimError(errorMessage(e));
    } finally {
      setRunning(false);
    }
  }

  const arms = sim ? Object.entries(sim.by_strategy) : [];
  const globalMax = Math.max(1, ...arms.map(([, f]) => f.searched));

  return (
    <div className="space-y-6">
      <PageHeader kicker="Experimentation" tone="tag" title="insights">
        Does letting agents go on the pre-date beat plain vector matching? The live match policy and a funnel
        simulation per strategy.
      </PageHeader>

      <div className="grid gap-6 lg:grid-cols-[360px_minmax(0,1fr)]">
        <Card className="min-w-0">
          <CardTitle
            kicker="Live config"
            tone="agent"
            title={
              <span className="inline-flex items-center gap-2">
                <SlidersHorizontal className="size-5 text-agent" /> Match policy
              </span>
            }
          />
          {configError && <ErrorBanner message={configError} onRetry={loadConfig} />}
          {!config && !configError && <Skeleton className="h-48" />}
          {config && (
            <>
              <div className="mb-3 flex items-center gap-2 text-sm">
                <span className="text-muted">Active strategy</span>
                <Pill tone="agent" className="font-mono">
                  {config.strategy}
                </Pill>
              </div>
              <pre className="max-h-[420px] overflow-auto rounded-xl bg-surface-2 p-3 font-mono text-[12px] leading-relaxed ring-1 ring-line">
                {JSON.stringify(config.policy, null, 2)}
              </pre>
            </>
          )}
        </Card>

        <Card className="min-w-0">
          <CardTitle
            kicker="Simulated synthetic users"
            tone="human"
            title={
              <span className="inline-flex items-center gap-2">
                <FlaskConical className="size-5 text-human" /> Funnel by strategy
              </span>
            }
            action={
              <Button variant="human" icon={<Play className="size-4" />} loading={running} onClick={simulate}>
                Run simulation
              </Button>
            }
          />
          <p className="mb-5 rounded-lg bg-warn/5 px-3 py-2 text-xs text-warn ring-1 ring-warn/20">
            Simulated synthetic users. These numbers come from a simulation over fictional personas, not real people.
          </p>
          {simError && <ErrorBanner message={simError} onRetry={simulate} />}
          {!sim && !simError && (
            <div className="rounded-xl border border-dashed border-line px-4 py-12 text-center text-sm text-muted">
              Run the simulation to compare strategies.
            </div>
          )}
          {sim && (
            <div className="space-y-8">
              {arms.map(([arm, f]) => (
                <Funnel
                  key={arm}
                  arm={arm}
                  counts={f}
                  max={globalMax}
                  active={config?.strategy === arm}
                />
              ))}
              {arms.length >= 2 && <Comparison arms={arms} />}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}

function Funnel({ arm, counts, max, active }: { arm: string; counts: FunnelCounts; max: number; active: boolean }) {
  const isAgent = arm.includes("agent");
  return (
    <div className="animate-msg-in">
      <div className="mb-3 flex items-center gap-2">
        <h3 className="font-semibold">{ARM_LABEL[arm] ?? arm}</h3>
        <code className="font-mono text-[11px] text-muted">{arm}</code>
        {active && <Pill tone="agent">active</Pill>}
      </div>
      <div className="space-y-2">
        {STAGES.map((s, i) => {
          const v = counts[s.key] ?? 0;
          const prev = i === 0 ? null : counts[STAGES[i - 1].key] ?? 0;
          const conv = prev ? Math.round((v / prev) * 100) : null;
          return (
            <div key={s.key} className="grid grid-cols-[96px_minmax(0,1fr)_88px] items-center gap-3 text-sm sm:grid-cols-[120px_minmax(0,1fr)_100px]">
              <span className="text-muted">{s.label}</span>
              <div className="h-7 overflow-hidden rounded-md bg-surface-2 ring-1 ring-line">
                <div
                  className={cx(
                    "flex h-full items-center rounded-md px-2 text-xs font-semibold text-white transition-all duration-700 dark:text-black",
                    isAgent ? "bg-agent" : "bg-muted/70",
                  )}
                  style={{ width: `${Math.max(2, (v / max) * 100)}%`, opacity: 1 - i * 0.12 }}
                >
                  {v / max > 0.12 ? v.toLocaleString() : ""}
                </div>
              </div>
              <span className="text-right font-mono text-xs tabular-nums">
                {v.toLocaleString()}
                {conv !== null && <span className="ml-1 text-muted">({conv}%)</span>}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function Comparison({ arms }: { arms: [string, FunnelCounts][] }) {
  const rate = (f: FunnelCounts) => (f.searched ? f.booked / f.searched : 0);
  const sorted = [...arms].sort((a, b) => rate(b[1]) - rate(a[1]));
  const [best, worst] = [sorted[0], sorted[sorted.length - 1]];
  const lift = rate(worst[1]) > 0 ? rate(best[1]) / rate(worst[1]) : null;
  return (
    <div className="rounded-xl bg-surface-2 p-4 text-sm ring-1 ring-line">
      <span className="font-semibold">{ARM_LABEL[best[0]] ?? best[0]}</span> books{" "}
      <span className="font-semibold tabular-nums">{(rate(best[1]) * 100).toFixed(1)}%</span> of searches vs.{" "}
      <span className="tabular-nums">{(rate(worst[1]) * 100).toFixed(1)}%</span> for {ARM_LABEL[worst[0]] ?? worst[0]}
      {lift && lift > 1 ? (
        <>
          {" "}
          — <span className="font-semibold text-agent">{lift.toFixed(1)}× lift</span>.
        </>
      ) : (
        "."
      )}
    </div>
  );
}
