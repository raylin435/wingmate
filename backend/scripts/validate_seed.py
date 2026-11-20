#!/usr/bin/env python3
"""Validates Wingmate seed data. Stdlib only. Exit code 1 on any failure."""
import glob
import json
import pathlib
import sys

DATA = pathlib.Path(__file__).resolve().parent.parent / "data"
errors = []
FIELDS = {"value", "interest", "lifestyle", "dealbreaker", "logistics", "seeking"}
DAYS = {f"2026-11-{d}" for d in range(21, 28)}


def err(msg):
    errors.append(msg)


def load(path):
    try:
        return json.loads(pathlib.Path(path).read_text())
    except Exception as e:  # noqa: BLE001
        err(f"{path}: invalid JSON ({e})")
        return None


personas = {}
for f in sorted(glob.glob(str(DATA / "personas" / "*.json"))):
    p = load(f)
    if not p:
        continue
    pid = p.get("id")
    if pid in personas:
        err(f"duplicate persona id {pid}")
    if pathlib.Path(f).stem != pid:
        err(f"{f}: filename != id")
    personas[pid] = p

if len(personas) != 30:
    err(f"expected 30 personas, got {len(personas)}")
aliases = [p["alias"] for p in personas.values()]
if len(set(aliases)) != len(aliases):
    err("duplicate aliases")

for pid, p in personas.items():
    for k in ("first_name", "alias", "age", "gender", "seeking", "neighborhood", "tagline", "avatar_color",
              "attributes", "dealbreakers", "interests", "free_slots", "chat", "facts"):
        if k not in p:
            err(f"{pid}: missing {k}")
    if not 25 <= p["age"] <= 38:
        err(f"{pid}: age {p['age']} outside 25-38")
    if p["gender"] not in ("woman", "man", "nonbinary"):
        err(f"{pid}: bad gender")
    if not 3 <= len(p["free_slots"]) <= 5 or len(set(p["free_slots"])) != len(p["free_slots"]):
        err(f"{pid}: need 3-5 distinct slots")
    for s in p["free_slots"]:
        if s[:10] not in DAYS:
            err(f"{pid}: slot {s} outside window")
    if not 24 <= len(p["chat"]) <= 36:
        err(f"{pid}: chat has {len(p['chat'])} messages")
    user_texts = [m["text"] for m in p["chat"] if m["role"] == "user"]
    if not 6 <= len(p["facts"]) <= 10:
        err(f"{pid}: {len(p['facts'])} facts")
    seen_fields = {f["field"] for f in p["facts"]}
    if seen_fields != FIELDS:
        err(f"{pid}: facts fields {sorted(seen_fields)} != required {sorted(FIELDS)}")
    for f in p["facts"]:
        if not any(f["quote"] in t for t in user_texts):
            err(f"{pid}: quote not found verbatim in a user message: {f['quote']!r}")
    # every attribute referenced by anyone's dealbreaker must be backed by a quoted fact
    quotes = " || ".join(f["quote"] for f in p["facts"])
    for db in p["dealbreakers"]:
        if not any(f["field"] == "dealbreaker" for f in p["facts"]):
            err(f"{pid}: dealbreaker without dealbreaker fact")
    if len(p["facts"]) < 6 or not quotes:
        err(f"{pid}: facts too thin")

# any attribute used in some dealbreaker must have lifestyle/value facts for everyone (checked by field coverage);
# additionally require lifestyle facts >= 2 and a value fact for kids/religion.
for pid, p in personas.items():
    if sum(f["field"] == "lifestyle" for f in p["facts"]) < 2:
        err(f"{pid}: needs >=2 lifestyle facts (drinking, smoking)")
    if sum(f["field"] == "value" for f in p["facts"]) < 2:
        err(f"{pid}: needs >=2 value facts (kids, religion)")


def violates(person, other):
    """True if `other` hits one of `person`'s dealbreakers."""
    return any(other["attributes"].get(d["attr"]) == d["equals"] for d in person["dealbreakers"])


def acceptable(a, b):
    """One-directional: does a accept b on gender/age/dealbreakers?"""
    s = a["seeking"]
    return b["gender"] in s["genders"] and s["min_age"] <= b["age"] <= s["max_age"] and not violates(a, b)


def mutual(a, b):
    return acceptable(a, b) and acceptable(b, a)


# --- Maya / Jordan / Theo storyline -----------------------------------------
try:
    maya, jordan, theo = personas["maya"], personas["jordan"], personas["theo"]
    if not jordan["attributes"]["smokes"]:
        err("jordan must smoke")
    if not any(d["attr"] == "smokes" and d["equals"] is True for d in maya["dealbreakers"]):
        err("maya must have smoking dealbreaker")
    if not any(f["field"] == "dealbreaker" and "smoke" in f["quote"] for f in maya["facts"]):
        err("maya needs a smoking dealbreaker fact quote")
    if not any("smoke" in f["quote"] and f["field"] == "lifestyle" for f in jordan["facts"]):
        err("jordan needs a lifestyle smoking fact")
    shared = set(maya["free_slots"]) & set(theo["free_slots"])
    if len(shared) < 2:
        err(f"theo shares only {len(shared)} slots with maya")
    for name, man in (("jordan", jordan), ("theo", theo)):
        s = maya["seeking"]
        if not (man["gender"] in s["genders"] and s["min_age"] <= man["age"] <= s["max_age"]):
            err(f"{name} outside maya's seeking range")
        ms = man["seeking"]
        if not ("woman" in ms["genders"] and ms["min_age"] <= maya["age"] <= ms["max_age"]):
            err(f"{name} does not seek maya's profile")
    if violates(maya, theo) or violates(theo, maya):
        err("theo conflicts with maya on a dealbreaker")
    if not violates(maya, jordan):
        err("jordan should trip maya's dealbreaker")
    mi = set(maya["interests"])
    if len(mi & set(jordan["interests"])) < 3:
        err("jordan should overlap maya's interests (>=3)")
    if len(mi & set(theo["interests"])) < 3:
        err("theo should overlap maya's interests (>=3)")
    weaker = [pid for pid, p in personas.items() if pid not in ("maya", "jordan", "theo") and mutual(maya, p)]
    if len(weaker) < 2:
        err(f"maya needs >=2 additional mutual candidates, has {weaker}")
    if not any("cigarette" in t["text"] or "smoke" in t["text"] for t in jordan["chat"] if t["role"] == "user"):
        err("jordan chat must mention smoking")
except KeyError as e:
    err(f"storyline persona missing: {e}")
    weaker = []

# --- candidate coverage -------------------------------------------------------
counts = {pid: sum(mutual(p, q) for qid, q in personas.items() if qid != pid) for pid, p in personas.items()}
low = [pid for pid, c in counts.items() if c < 3]
# mutual excludes the jordan-maya pair by design; require most people to have >=3
if len(low) > 4:
    err(f"too many people with <3 mutual candidates: {low}")

# --- venues -------------------------------------------------------------------
venues = load(DATA / "venues.json") or []
if len(venues) != 20:
    err(f"expected 20 venues, got {len(venues)}")
vids = [v.get("id") for v in venues]
if len(set(vids)) != len(vids):
    err("duplicate venue ids")
for v in venues:
    for k in ("id", "name", "neighborhood", "category", "tags", "price", "good_for", "hours"):
        if k not in v:
            err(f"venue {v.get('id')}: missing {k}")
all_interests = {i for p in personas.values() for i in p["interests"]}
venue_tags = {t for v in venues for t in v["tags"]}
overlap = all_interests & venue_tags
if len(overlap) < 12:
    err(f"venue tags overlap only {len(overlap)} persona interests")

# --- exports ------------------------------------------------------------------
gpt = load(DATA / "exports" / "maya_chatgpt_conversations.json") or []
if not 55 <= len(gpt) <= 65:
    err(f"chatgpt export has {len(gpt)} conversations (want ~60)")
for c in gpt:
    for k in ("title", "create_time", "update_time", "mapping", "current_node"):
        if k not in c:
            err(f"chatgpt conv {c.get('title')}: missing {k}")
    m = c.get("mapping", {})
    if c.get("current_node") not in m:
        err(f"chatgpt conv {c.get('title')}: current_node not in mapping")
    roots = [n for n in m.values() if n["parent"] is None]
    if len(roots) != 1:
        err(f"chatgpt conv {c.get('title')}: need exactly one root")
    msgs = [n["message"] for n in m.values() if n["message"]]
    if not 2 <= len(msgs) <= 8:
        err(f"chatgpt conv {c.get('title')}: {len(msgs)} messages")
    for n in m.values():
        if n["parent"] is not None and n["parent"] not in m:
            err(f"chatgpt conv {c.get('title')}: dangling parent")
        for ch in n["children"]:
            if ch not in m or m[ch]["parent"] != n["id"]:
                err(f"chatgpt conv {c.get('title')}: bad children link")
        mm = n["message"]
        if mm and (mm["author"]["role"] not in ("user", "assistant", "system")
                   or mm["content"]["content_type"] != "text"
                   or not isinstance(mm["content"]["parts"][0], str)
                   or not isinstance(mm["create_time"], float)):
            err(f"chatgpt conv {c.get('title')}: bad message shape")
    if not isinstance(c.get("create_time"), float):
        err(f"chatgpt conv {c.get('title')}: create_time must be float")
blob = json.dumps(gpt)
for needle in ("pottery", "smoke", "Biscuit", "dumpling"):
    if needle not in blob:
        err(f"chatgpt export missing storyline detail {needle!r}")

cl = load(DATA / "exports" / "maya_claude_conversations.json") or []
if len(cl) != 8:
    err(f"claude export has {len(cl)} conversations (want 8)")
for c in cl:
    for k in ("uuid", "name", "created_at", "updated_at", "chat_messages"):
        if k not in c:
            err(f"claude conv {c.get('name')}: missing {k}")
    for m in c.get("chat_messages", []):
        if m["sender"] not in ("human", "assistant") or not m["text"] or "uuid" not in m or "created_at" not in m:
            err(f"claude conv {c.get('name')}: bad message")

# --- report -------------------------------------------------------------------
print(f"personas: {len(personas)}  venues: {len(venues)}  chatgpt convs: {len(gpt)}  claude convs: {len(cl)}")
print("mutual candidate counts:", dict(sorted(counts.items(), key=lambda kv: kv[1])))
if "maya" in personas:
    print("maya mutual candidates:", [q for q in personas if q != "maya" and mutual(personas["maya"], personas[q])])
    print("maya x theo shared slots:", sorted(set(personas["maya"]["free_slots"]) & set(personas["theo"]["free_slots"])))
if errors:
    print(f"\nFAILED with {len(errors)} error(s):")
    for e in errors:
        print(" -", e)
    sys.exit(1)
print("\nOK: all checks passed")
