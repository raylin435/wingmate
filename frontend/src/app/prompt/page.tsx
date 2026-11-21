import { readFile } from "node:fs/promises";
import path from "node:path";
import type { Metadata } from "next";
import type { ReactNode } from "react";
import { FileText } from "lucide-react";
import { Card, CopyButton, PageHeader } from "@/components/ui";

export const metadata: Metadata = {
  title: "The profile prompt · Wingmate",
  description: "The prompt your AI assistant reads to write a portrait of you for your Wingmate agent.",
};

const PROMPT_FILE = "/prompt.txt";

export default async function PromptPage() {
  const text = await readFile(path.join(process.cwd(), "public", "prompt.txt"), "utf8");

  return (
    <div className="space-y-6">
      <PageHeader
        kicker="For your AI assistant"
        tone="human"
        title="the profile prompt"
        action={
          <div className="flex flex-wrap items-center gap-3">
            <a
              href={PROMPT_FILE}
              className="inline-flex h-11 items-center gap-2 rounded-full border border-white/40 bg-white/10 px-5 text-sm font-semibold text-white backdrop-blur transition hover:bg-white/20"
            >
              <FileText className="size-4" /> Raw file
            </a>
            <CopyButton text={text} label="Copy full prompt" variant="cta" size="md" />
          </div>
        }
      >
        Your assistant reads this file and writes a portrait of you, the way a friend who knows you well would. Paste
        that portrait into My Agent to teach your Wingmate agent.
      </PageHeader>

      <Card className="mx-auto max-w-3xl">
        <article className="space-y-4 text-[15px] leading-relaxed">{renderMarkdown(text)}</article>
      </Card>
    </div>
  );
}

/** Small renderer for the markdown this prompt uses: headings, rules, lists, paragraphs and **bold**. */
function renderMarkdown(src: string): ReactNode[] {
  const lines = src.replace(/\r\n/g, "\n").split("\n");
  const out: ReactNode[] = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i].trimEnd();
    if (!line.trim()) {
      i++;
      continue;
    }
    const heading = /^(#{1,3})\s+(.*)$/.exec(line);
    if (heading) {
      const level = heading[1].length;
      const content = inline(heading[2]);
      if (level === 1)
        out.push(
          <h2 key={i} className="pt-4 font-display text-[38px] leading-[1.05] tracking-tight first:pt-0">
            {content}
          </h2>,
        );
      else if (level === 2)
        out.push(
          <h3 key={i} className="pt-3 font-display text-[28px] leading-tight text-human">
            {content}
          </h3>,
        );
      else
        out.push(
          <h4 key={i} className="pt-2 text-base font-semibold">
            {content}
          </h4>,
        );
      i++;
      continue;
    }
    if (/^-{3,}$/.test(line.trim())) {
      out.push(<hr key={i} className="my-6 border-line" />);
      i++;
      continue;
    }
    if (/^[-*]\s+/.test(line) || /^\d+\.\s+/.test(line)) {
      const ordered = /^\d+\.\s+/.test(line);
      const marker = ordered ? /^\d+\.\s+/ : /^[-*]\s+/;
      const items: ReactNode[] = [];
      const start = i;
      while (i < lines.length && marker.test(lines[i])) {
        items.push(<li key={i}>{inline(lines[i].replace(marker, ""))}</li>);
        i++;
      }
      const cls = "space-y-1 pl-6 marker:text-human";
      out.push(
        ordered ? (
          <ol key={start} className={`list-decimal ${cls}`}>
            {items}
          </ol>
        ) : (
          <ul key={start} className={`list-disc ${cls}`}>
            {items}
          </ul>
        ),
      );
      continue;
    }
    const para: string[] = [];
    const start = i;
    while (
      i < lines.length &&
      lines[i].trim() &&
      !/^(#{1,3}\s|[-*]\s|\d+\.\s|-{3,}$)/.test(lines[i].trim())
    ) {
      para.push(lines[i].trim());
      i++;
    }
    out.push(<p key={start}>{inline(para.join(" "))}</p>);
  }
  return out;
}

function inline(text: string): ReactNode[] {
  return text.split(/(\*\*[^*]+\*\*)/g).map((part, k) =>
    part.startsWith("**") && part.endsWith("**") ? (
      <strong key={k} className="font-semibold">
        {part.slice(2, -2)}
      </strong>
    ) : (
      part
    ),
  );
}
