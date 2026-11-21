"""Import memory from ChatGPT or Claude data exports, or from a pasted assistant memory summary.
Only the user's own messages are used, and only personal conversations are kept."""

import io
import json
import re
import zipfile
from typing import Any

from . import audit, core, integrations, llm


def _chatgpt(convos: list[dict]) -> list[tuple[str, list[str]]]:
    out = []
    for c in convos:
        msgs = []
        nodes = sorted((n for n in (c.get("mapping") or {}).values() if n.get("message")),
                       key=lambda n: n["message"].get("create_time") or 0)
        for n in nodes:
            m = n["message"]
            if (m.get("author") or {}).get("role") == "user":
                parts = (m.get("content") or {}).get("parts") or []
                text = " ".join(p for p in parts if isinstance(p, str)).strip()
                if text:
                    msgs.append(text)
        out.append((c.get("title") or "Untitled", msgs))
    return out


def _claude(convos: list[dict]) -> list[tuple[str, list[str]]]:
    out = []
    for c in convos:
        msgs = []
        for m in c.get("chat_messages") or []:
            if m.get("sender") == "human":
                text = (m.get("text") or "").strip()
                if not text:
                    text = " ".join(b.get("text", "") for b in m.get("content") or [] if isinstance(b, dict)).strip()
                if text:
                    msgs.append(text)
        out.append((c.get("name") or "Untitled", msgs))
    return out


def parse_export(raw: bytes, filename: str) -> tuple[str, list[tuple[str, list[str]]]]:
    if filename.lower().endswith(".zip") or raw[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            name = next((n for n in z.namelist() if n.endswith("conversations.json")), None)
            if name is None:
                raise ValueError("No conversations.json inside the zip.")
            raw = z.read(name)
    convos = json.loads(raw)
    if not isinstance(convos, list) or not convos:
        raise ValueError("conversations.json should be a non-empty list of conversations.")
    if "mapping" in convos[0]:
        return "chatgpt", _chatgpt(convos)
    if "chat_messages" in convos[0]:
        return "claude", _claude(convos)
    raise ValueError("Unrecognized export format. Expected a ChatGPT or Claude conversations.json.")


def import_export(pid: str, raw: bytes, filename: str) -> dict[str, Any]:
    run_id = audit.new_run_id()
    source, convos = parse_export(raw, filename)
    convos = [(t, m) for t, m in convos if m]
    audit.log(run_id, "export_parsed", f"human:{pid}", None, None, source=source,
              conversations=len(convos), user_messages=sum(len(m) for _, m in convos))
    flags, model, ms = llm.classify_personal([t + "\n" + "\n".join(m) for t, m in convos])
    kept = [(t, m) for (t, m), keep in zip(convos, flags) if keep]
    audit.log(run_id, "conversations_filtered", f"agent:{pid}", model, ms,
              kept=len(kept), skipped=len(convos) - len(kept), kept_titles=[t for t, _ in kept][:30])
    integrations.track_llm(pid, "personal_filter", model, ms)
    messages = [(t, text) for t, msgs in kept for text in msgs]
    facts, dropped = core.extract_facts(pid, messages, "import", run_id)
    integrations.track(pid, "memory_imported", source=source, conversations_seen=len(convos),
                       conversations_kept=len(kept), facts=len(facts), dropped=dropped)
    return {"run_id": run_id, "source": source, "conversations_seen": len(convos),
            "conversations_kept": len(kept), "messages_used": len(messages),
            "facts": facts, "dropped_untraceable": dropped}


def import_paste(pid: str, text: str) -> dict[str, Any]:
    run_id = audit.new_run_id()
    text = text.strip()
    if not text:
        raise ValueError("Paste the answer from ChatGPT or Claude first.")
    audit.log(run_id, "memory_pasted", f"human:{pid}", None, None, chars=len(text))
    sections = split_sections(text)
    facts, dropped = core.extract_facts(pid, sections, "import", run_id)
    integrations.track(pid, "memory_imported", source="paste", facts=len(facts), dropped=dropped)
    return {"run_id": run_id, "source": "paste", "conversations_seen": 1, "conversations_kept": 1,
            "messages_used": len(sections), "facts": facts, "dropped_untraceable": dropped}


def split_sections(text: str) -> list[tuple[str, str]]:
    """Split a pasted Markdown portrait on its #/## headings so long pastes chunk cleanly and each
    fact can name the section it came from. Text without headings stays one section."""
    sections: list[tuple[str, str]] = []
    title, body = "Pasted assistant memory", []
    for line in text.splitlines():
        heading = re.match(r"^#{1,2}\s+(.+?)\s*$", line)
        if heading:
            if "\n".join(body).strip():
                sections.append((title, "\n".join(body).strip()))
            title, body = heading.group(1), []
        else:
            body.append(line)
    if "\n".join(body).strip():
        sections.append((title, "\n".join(body).strip()))
    return sections or [("Pasted assistant memory", text)]
