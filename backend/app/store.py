"""Agent directory. SingleStore holds every public agent card with its embedding, and one SQL query
applies the hard filters and vector similarity together. Without SINGLESTORE_URL the same search runs
in memory with numpy."""

import json
import threading
from contextlib import contextmanager
from typing import Any

import numpy as np

from . import audit, config


class MemoryDirectory:
    name = "memory"

    def __init__(self) -> None:
        self.cards: dict[str, dict[str, Any]] = {}

    def upsert(self, card: dict[str, Any], vec: np.ndarray) -> None:
        self.cards[card["agent_id"]] = {**card, "embedding": vec}

    def prune(self, keep: set[str]) -> int:
        stale = [aid for aid in self.cards if aid not in keep]
        for aid in stale:
            del self.cards[aid]
        return len(stale)

    def set_verified(self, agent_id: str, verified: bool) -> None:
        if agent_id in self.cards:
            self.cards[agent_id]["verified"] = verified

    def search(self, me: dict[str, Any], qvec: np.ndarray, limit: int) -> list[dict[str, Any]]:
        rows = []
        for c in self.cards.values():
            if not _passes(me, c):
                continue
            rows.append({k: v for k, v in c.items() if k != "embedding"} | {"sim": float(c["embedding"] @ qvec)})
        return sorted(rows, key=lambda r: -r["sim"])[:limit]


def _passes(me: dict[str, Any], c: dict[str, Any]) -> bool:
    s = me["seeking"]
    return (c["agent_id"] != me["id"] and c["verified"]
            and s["min_age"] <= c["age"] <= s["max_age"] and c["gender"] in s["genders"]
            and c["min_age"] <= me["age"] <= c["max_age"] and me["gender"] in c["seeks"])


class SingleStoreDirectory:
    name = "singlestore"

    def __init__(self, url: str) -> None:
        self.url = url
        self.lock = threading.RLock()
        self.conn = self._connect()
        self.dim: int | None = None
        with self.cursor() as cur:
            cur.execute("""CREATE TABLE IF NOT EXISTS audit_events (
                id BIGINT PRIMARY KEY, run_id VARCHAR(32), ts VARCHAR(40), step VARCHAR(48),
                actor VARCHAR(64), model VARCHAR(128), latency_ms INT, detail JSON, KEY (run_id))""")
        audit.add_sink(self._audit_sink)

    def _connect(self):
        import singlestoredb as s2

        return s2.connect(self.url, autocommit=True)

    @contextmanager
    def cursor(self):
        """One connection shared by request threads: serialize access and reconnect once if the
        server closed an idle connection."""
        with self.lock:
            try:
                with self.conn.cursor() as probe:
                    probe.execute("SELECT 1")
                    probe.fetchall()
            except Exception:
                print("[store] SingleStore connection was closed, reconnecting")
                self.conn = self._connect()
            try:
                cur = self.conn.cursor()
            except Exception:
                self.conn = self._connect()
                cur = self.conn.cursor()
            try:
                yield cur
            finally:
                try:
                    cur.close()
                except Exception:
                    pass

    def _ensure_table(self, dim: int) -> None:
        if self.dim == dim:
            return
        with self.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'agent_cards' AND table_schema = DATABASE()")
            exists = cur.fetchone()[0] > 0
            if exists:
                cur.execute("SELECT embedding FROM agent_cards LIMIT 1")
                row = cur.fetchone()
                if row is not None and len(_as_list(row[0])) != dim:
                    cur.execute("DROP TABLE agent_cards")
                    exists = False
            if not exists:
                cur.execute(f"""CREATE TABLE agent_cards (
                    agent_id VARCHAR(64) PRIMARY KEY, alias VARCHAR(96), age INT, gender VARCHAR(16),
                    neighborhood VARCHAR(64), seeks JSON, min_age INT, max_age INT, verified BOOL,
                    summary TEXT, embedding VECTOR({dim}) NOT NULL)""")
        self.dim = dim

    def upsert(self, card: dict[str, Any], vec: np.ndarray) -> None:
        self._ensure_table(len(vec))
        with self.cursor() as cur:
            cur.execute(
                "REPLACE INTO agent_cards VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (card["agent_id"], card["alias"], card["age"], card["gender"], card["neighborhood"],
                 json.dumps(card["seeks"]), card["min_age"], card["max_age"], card["verified"],
                 card["summary"], json.dumps([round(float(x), 6) for x in vec])),
            )

    def prune(self, keep: set[str]) -> int:
        """Drop cards for agents no longer in the seed (e.g. after personas are renamed)."""
        if self.dim is None or not keep:
            return 0
        placeholders = ", ".join(["%s"] * len(keep))
        with self.cursor() as cur:
            cur.execute(f"DELETE FROM agent_cards WHERE agent_id NOT IN ({placeholders})", sorted(keep))
            return cur.rowcount or 0

    def set_verified(self, agent_id: str, verified: bool) -> None:
        with self.cursor() as cur:
            cur.execute("UPDATE agent_cards SET verified = %s WHERE agent_id = %s", (verified, agent_id))

    def search(self, me: dict[str, Any], qvec: np.ndarray, limit: int) -> list[dict[str, Any]]:
        s = me["seeking"]
        genders = s["genders"] or ["__none__"]
        placeholders = ", ".join(["%s"] * len(genders))
        sql = f"""
            SELECT agent_id, alias, age, gender, neighborhood, seeks, min_age, max_age, verified, summary,
                   embedding <*> (%s :> VECTOR({self.dim})) AS sim
            FROM agent_cards
            WHERE verified AND agent_id <> %s
              AND age BETWEEN %s AND %s AND gender IN ({placeholders})
              AND min_age <= %s AND max_age >= %s
              AND JSON_ARRAY_CONTAINS_STRING(seeks, %s)
            ORDER BY sim DESC LIMIT %s"""
        params = [json.dumps([float(x) for x in qvec]), me["id"], s["min_age"], s["max_age"], *genders,
                  me["age"], me["age"], me["gender"], limit]
        with self.cursor() as cur:
            cur.execute(sql, params)
            cols = [d[0] for d in cur.description]
            rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        for r in rows:
            r["seeks"] = _as_list(r["seeks"])
            r["sim"] = float(r["sim"])
            r["verified"] = bool(r["verified"])
        return rows

    def _audit_sink(self, e: dict[str, Any]) -> None:
        with self.cursor() as cur:
            cur.execute("INSERT INTO audit_events VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                        (e["id"] + _AUDIT_OFFSET, e["run_id"], e["ts"], e["step"], e["actor"], e["model"],
                         e["latency_ms"], json.dumps(e["detail"], default=str)))


_AUDIT_OFFSET = int(__import__("time").time()) * 1000  # keeps ids unique across restarts


def _as_list(v: Any) -> list:
    if isinstance(v, (bytes, bytearray)):
        v = v.decode()
    if isinstance(v, str):
        return json.loads(v)
    return list(v)


def make_directory():
    if config.SINGLESTORE_URL:
        try:
            d = SingleStoreDirectory(config.SINGLESTORE_URL)
            print("[store] using SingleStore")
            return d
        except Exception as exc:
            print(f"[store] SingleStore unavailable, using memory: {exc}")
    return MemoryDirectory()
