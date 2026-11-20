"""Statsig (matching policy + experiment), Amplitude (product + agent events) and Cognee (memory graph). Each is optional and degrades to a local default."""

import asyncio
import threading
from typing import Any

from . import config

# ---------------------------------------------------------------- Statsig
_statsig = None
if config.STATSIG_SERVER_KEY:
    try:
        from statsig_python_core import Statsig, StatsigOptions

        opts = StatsigOptions()
        opts.environment = "development"
        _statsig = Statsig(config.STATSIG_SERVER_KEY, opts)
        _statsig.initialize().wait()
        print("[statsig] initialized")
    except Exception as exc:
        print(f"[statsig] unavailable: {exc}")
        _statsig = None


def _user(uid: str):
    from statsig_python_core import StatsigUser

    return StatsigUser(uid)


def _value(obj: Any) -> dict:
    for attr in ("value", "get_value", "json_value"):
        v = getattr(obj, attr, None)
        v = v() if callable(v) else v
        if isinstance(v, dict):
            return v
    return {}


def match_policy(uid: str) -> dict:
    policy = dict(config.DEFAULT_POLICY)
    if _statsig is not None:
        try:
            policy.update(_value(_statsig.get_dynamic_config(_user(uid), "match_policy")))
        except Exception as exc:
            print(f"[statsig] match_policy failed: {exc}")
    return policy


def strategy(uid: str) -> str:
    if _statsig is not None:
        try:
            v = _value(_statsig.get_experiment(_user(uid), "matching_strategy")).get("strategy")
            if v in ("vector_only", "agent_predate"):
                return v
        except Exception as exc:
            print(f"[statsig] experiment failed: {exc}")
    return config.DEFAULT_STRATEGY


def statsig_event(uid: str, name: str, value: str | None = None, metadata: dict | None = None) -> None:
    if _statsig is None:
        return
    try:
        _statsig.log_event(_user(uid), name, value, {k: str(v) for k, v in (metadata or {}).items()})
    except Exception as exc:
        print(f"[statsig] log_event failed: {exc}")


# ---------------------------------------------------------------- Amplitude
_amp = None
if config.AMPLITUDE_API_KEY:
    try:
        from amplitude import Amplitude

        _amp = Amplitude(config.AMPLITUDE_API_KEY)
        print("[amplitude] initialized")
    except Exception as exc:
        print(f"[amplitude] unavailable: {exc}")


def track(uid: str, event: str, **props: Any) -> None:
    """Product event to Amplitude, mirrored to Statsig so experiment metrics can use it."""
    statsig_event(uid, event, None, props)
    if _amp is None:
        return
    try:
        from amplitude import BaseEvent

        _amp.track(BaseEvent(event_type=event, user_id=f"wingmate-{uid}", event_properties=props))
    except Exception as exc:
        print(f"[amplitude] track failed: {exc}")


def track_llm(uid: str, task: str, model: str, latency_ms: int | None, **props: Any) -> None:
    """One event per model call, so Amplitude shows cost and latency per agent task."""
    track(uid, "[Agent] Model Call", task=task, model=model, latency_ms=latency_ms or 0,
          live=not model.startswith("local:"), **props)


def shutdown() -> None:
    try:
        if _amp is not None:
            _amp.shutdown()
        if _statsig is not None:
            _statsig.shutdown().wait()
    except Exception:
        pass


# ---------------------------------------------------------------- Cognee
_cognee_ready = False
_cognee_loop: asyncio.AbstractEventLoop | None = None
if config.COGNEE_ENABLED != "0":
    try:
        import os

        if config.SIE_API_KEY and not os.environ.get("LLM_API_KEY"):
            # Run Cognee's graph extraction and embeddings on SIE's OpenAI-compatible endpoints.
            for k, v in {
                "LLM_PROVIDER": "custom", "LLM_ENDPOINT": "https://api.superlinked.com/v1",
                "LLM_MODEL": f"openai/{config.CHAT_MODEL}", "LLM_API_KEY": config.SIE_API_KEY,
                "EMBEDDING_PROVIDER": "custom", "EMBEDDING_ENDPOINT": "https://api.superlinked.com/v1",
                "EMBEDDING_MODEL": f"openai/{config.EMBED_MODEL}", "EMBEDDING_DIMENSIONS": "1024",
                "EMBEDDING_API_KEY": config.SIE_API_KEY, "ENABLE_BACKEND_ACCESS_CONTROL": "false",
            }.items():
                if not os.environ.get(k, "").strip():
                    os.environ[k] = v

        if config.COGNEE_ENABLED == "1" or os.environ.get("LLM_API_KEY"):
            import cognee  # noqa: F401
            import litellm

            litellm.drop_params = True  # SIE's embeddings endpoint rejects the `dimensions` param

            _cognee_loop = asyncio.new_event_loop()
            threading.Thread(target=_cognee_loop.run_forever, daemon=True).start()
            _cognee_ready = True
            print("[cognee] enabled")
    except Exception as exc:
        print(f"[cognee] unavailable: {exc}")


def cognee_enabled() -> bool:
    return _cognee_ready


def _run(coro, timeout: float):
    return asyncio.run_coroutine_threadsafe(coro, _cognee_loop).result(timeout=timeout)


def cognee_ingest(uid: str, texts: list[str]) -> bool:
    if not _cognee_ready:
        return False
    import cognee

    async def go():
        await cognee.add("\n".join(texts), dataset_name=f"wingmate_{uid}")
        await cognee.cognify(datasets=[f"wingmate_{uid}"])

    try:
        _run(go(), timeout=240)
        return True
    except Exception as exc:
        print(f"[cognee] ingest failed for {uid}: {exc}")
        return False


def cognee_recall(uid: str, question: str) -> str | None:
    if not _cognee_ready:
        return None
    import cognee
    from cognee import SearchType

    async def go():
        return await cognee.search(query_type=SearchType.GRAPH_COMPLETION, query_text=question,
                                   datasets=[f"wingmate_{uid}"])

    try:
        res = _run(go(), timeout=config.COGNEE_RECALL_TIMEOUT_S)
        if isinstance(res, list):
            res = " ".join(str(r) for r in res[:2])
        return str(res)[:600] if res else None
    except Exception as exc:
        print(f"[cognee] recall failed for {uid}: {exc}")
        return None
