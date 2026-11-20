"""Model calls. Every task runs on a small, task-specific model on Superlinked SIE Serverless when
SIE_API_KEY is set. Without a key (or if a call fails) each task falls back to a deterministic local
implementation, so the demo never stalls. Each helper returns (result, model_used, latency_ms)."""

import hashlib
import json
import re
from typing import Any

import numpy as np

from . import config
from .audit import since, timer

_client = None
if config.SIE_API_KEY:
    try:
        from sie_sdk import SIEClient

        _client = SIEClient(api_key=config.SIE_API_KEY, timeout_s=90)
    except Exception as exc:  # pragma: no cover
        print(f"[llm] SIE client unavailable, using local fallbacks: {exc}")


def live() -> bool:
    return _client is not None


_WORD = re.compile(r"[a-z0-9']+")
MOCK_DIM = 384


def _tokens(text: str) -> list[str]:
    return _WORD.findall(text.lower())


def _hash_embed(text: str) -> np.ndarray:
    vec = np.zeros(MOCK_DIM, dtype=np.float32)
    toks = _tokens(text)
    grams = toks + [f"{a}_{b}" for a, b in zip(toks, toks[1:])]
    for g in grams:
        h = int(hashlib.md5(g.encode()).hexdigest(), 16)
        vec[h % MOCK_DIM] += 1.0 if (h >> 8) & 1 else -1.0
    return _normalize(vec)


def _normalize(vec: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(vec))
    return vec / n if n else vec


def _warn(task: str, exc: Exception) -> None:
    print(f"[llm] SIE {task} failed, falling back locally: {type(exc).__name__}: {str(exc)[:200]}")


def embed(texts: list[str], is_query: bool = False) -> tuple[list[np.ndarray], str, int]:
    with timer() as t:
        if _client is not None:
            try:
                out = _client.encode(config.EMBED_MODEL, [{"text": x} for x in texts], is_query=is_query)
                out = out if isinstance(out, list) else [out]
                vecs = [_normalize(np.asarray(o["dense"], dtype=np.float32)) for o in out]
                return vecs, config.EMBED_MODEL, since(t)
            except Exception as exc:
                _warn("encode", exc)
        vecs = [_hash_embed(x) for x in texts]
    return vecs, "local:hash-embed", t["ms"]


def rerank(query: str, items: list[tuple[str, str]]) -> tuple[dict[str, float], str, int]:
    """Returns {item_id: score}."""
    with timer() as t:
        if _client is not None and items:
            try:
                res = _client.score(config.RERANK_MODEL, {"text": query},
                                    [{"id": i, "text": txt} for i, txt in items])
                return {s["item_id"]: float(s["score"]) for s in res["scores"]}, config.RERANK_MODEL, since(t)
            except Exception as exc:
                _warn("score", exc)
        q = set(_tokens(query))
        qv = _hash_embed(query)
        scores = {}
        for i, txt in items:
            toks = set(_tokens(txt))
            jacc = len(q & toks) / max(1, len(q | toks))
            scores[i] = round(0.6 * float(qv @ _hash_embed(txt)) + 0.4 * jacc * 3, 4)
    return scores, "local:overlap-rerank", t["ms"]


_PERSONAL_HINTS = ("date", "dating", "partner", "boyfriend", "girlfriend", "weekend", "hobby", "love",
                   "hate", "friends", "relationship", "kids", "dog", "cat", "smok", "drink", "run",
                   "hike", "cook", "music", "jazz", "travel", "family", "lonely", "single", "pottery",
                   "climb", "book", "movie", "vegetarian", "faith", "church", "yoga")
_WORK_HINTS = ("spreadsheet", "excel", "python", "code", "sql", "bug", "deploy", "email to", "slide",
               "deck", "invoice", "meeting", "jira", "regex", "function", "api", "convert", "formula",
               "resume", "cover letter", "report")


def classify_personal(texts: list[str]) -> tuple[list[bool], str, int]:
    """Keep a conversation when GLiNER2 finds personal-life spans that outscore work spans."""
    personal = ["hobby or personal interest", "dating or relationship", "lifestyle habit", "family or pet"]
    work = ["work or coding task", "admin or school task"]
    with timer() as t:
        if _client is not None and texts:
            try:
                out = _client.extract(config.CLASSIFY_MODEL, [{"text": x[:2000]} for x in texts],
                                      labels=personal + work)
                out = out if isinstance(out, list) else [out]
                flags = []
                for o in out:
                    ents = o.get("entities") or []
                    p = sum(e["score"] for e in ents if e["label"] in personal)
                    w = sum(e["score"] for e in ents if e["label"] in work)
                    flags.append(p >= 1.0 and p > w)
                return flags, config.CLASSIFY_MODEL, since(t)
            except Exception as exc:
                _warn("classify", exc)
        flags = []
        for x in texts:
            low = x.lower()
            p = sum(low.count(h) for h in _PERSONAL_HINTS)
            w = sum(low.count(h) for h in _WORK_HINTS)
            flags.append(p > w)
    return flags, "local:keyword-classifier", t["ms"]


_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
_PHONE = re.compile(r"\+?\d[\d\s().-]{7,}\d")


def redact(text: str, known_names: list[str]) -> tuple[str, list[str], str, int]:
    redactions: list[str] = []
    model = "local:regex-redact"
    with timer() as t:
        if _client is not None:
            try:
                res = _client.extract(config.PII_MODEL, {"text": text},
                                      labels=["person", "organization", "email", "phone number", "street address"])
                res = res[0] if isinstance(res, list) else res
                for ent in sorted(res.get("entities") or [], key=lambda e: -len(e["text"])):
                    if ent.get("score", 1) >= 0.5 and ent["text"] in text:
                        text = text.replace(ent["text"], f"[{ent['label']}]")
                        redactions.append(f"{ent['label']}: {ent['text']}")
                model = config.PII_MODEL
            except Exception as exc:
                _warn("redact", exc)
        for rx, label in ((_EMAIL, "email"), (_PHONE, "phone number")):
            for m in set(rx.findall(text)):
                text = text.replace(m, f"[{label}]")
                redactions.append(f"{label}: {m}")
        for name in known_names:
            if name and re.search(rf"\b{re.escape(name)}\b", text):
                text = re.sub(rf"\b{re.escape(name)}\b", "[person]", text)
                redactions.append(f"person: {name}")
    return text, redactions, model, t["ms"]


def chat(messages: list[dict[str, str]], *, schema: dict | None = None, max_tokens: int = 400,
         temperature: float = 0.5) -> tuple[Any, str, int]:
    """Returns parsed JSON when schema is given, else text. Returns (None, 'unavailable', ms) when SIE
    is not configured or fails; callers then use their own local logic."""
    with timer() as t:
        if _client is not None:
            try:
                kwargs: dict[str, Any] = {"max_completion_tokens": max_tokens, "temperature": temperature}
                if schema is not None:
                    kwargs["response_format"] = {"type": "json_schema",
                                                 "json_schema": {"name": "out", "strict": True, "schema": schema}}
                res = _client.chat_completions(config.CHAT_MODEL, messages, **kwargs)
                choices = res["choices"] if isinstance(res, dict) else res.choices
                msg = choices[0]["message"] if isinstance(choices[0], dict) else choices[0].message
                content = msg["content"] if isinstance(msg, dict) else msg.content
                content = re.sub(r"<think>.*?</think>", "", content or "", flags=re.S).strip()
                if schema is not None:
                    content = json.loads(content[content.find("{"): content.rfind("}") + 1])
                return content, config.CHAT_MODEL, since(t)
            except Exception as exc:
                _warn("chat", exc)
    return None, "unavailable", t["ms"]
