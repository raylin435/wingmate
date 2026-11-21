import json

from app import core, importer, match


def _persona(pid, **kw):
    base = {
        "id": pid, "first_name": pid.title(), "alias": f"{pid} alias", "age": 30, "gender": "woman",
        "seeking": {"genders": ["man"], "min_age": 25, "max_age": 40}, "neighborhood": "Mission",
        "interests": ["trail running", "jazz"], "attributes": {"smokes": False}, "dealbreakers": [],
        "free_slots": ["2026-11-22T11:00"], "verified": True, "card_summary": "",
        "user_messages": ["I love trail running on Saturdays.", "I still smoke a few cigarettes when I'm out."],
        "facts": [{"id": f"{pid}-s0", "field": "interest", "value": "Trail running", "quote": "I love trail running",
                   "share": "public", "approved": True, "source": "seed"}],
    }
    base.update(kw)
    return base


def test_traceable_requires_exact_words():
    assert core.traceable("I love trail running", ["Honestly I love trail running!"])
    assert core.traceable("i love  TRAIL running", ["I love trail running"])
    assert not core.traceable("I adore hiking", ["I love trail running"])


def test_parse_chatgpt_export_keeps_only_user_messages():
    convos = [{"title": "Weekend", "mapping": {
        "a": {"message": {"author": {"role": "user"}, "create_time": 1, "content": {"parts": ["I love jazz"]}}},
        "b": {"message": {"author": {"role": "assistant"}, "create_time": 2, "content": {"parts": ["Nice!"]}}},
        "c": {"message": None},
    }}]
    source, parsed = importer.parse_export(json.dumps(convos).encode(), "conversations.json")
    assert source == "chatgpt"
    assert parsed == [("Weekend", ["I love jazz"])]


def test_parse_claude_export():
    convos = [{"name": "Dogs", "chat_messages": [{"sender": "human", "text": "My dog is my best friend"},
                                                   {"sender": "assistant", "text": "Aww"}]}]
    source, parsed = importer.parse_export(json.dumps(convos).encode(), "conversations.json")
    assert source == "claude"
    assert parsed == [("Dogs", ["My dog is my best friend"])]


def test_dealbreaker_blocks_match_in_local_predate():
    rachel = _persona("rachel", dealbreakers=[{"attr": "smokes", "equals": True, "label": "smoking"}])
    chris = _persona("chris", gender="man", seeking={"genders": ["woman"], "min_age": 25, "max_age": 40},
                      attributes={"smokes": True})
    core.PERSONAS.update({"rachel": rachel, "chris": chris})
    out = match.predate("rachel", "chris", None)
    assert out["match"] is False
    assert out["verdicts"]["rachel"]["recommend"] is False
    assert any("smoking" in c.lower() for c in out["verdicts"]["rachel"]["concerns"])
    steps = [e["step"] for e in core.audit.events(out["run_id"])]
    assert "dealbreaker_guard" in steps and steps.count("a2a_message") == 6


def test_compatible_pair_matches_and_books():
    rachel = _persona("rachel")
    matt = _persona("matt", gender="man", seeking={"genders": ["woman"], "min_age": 25, "max_age": 40},
                    user_messages=["I love trail running and jazz."])
    core.PERSONAS.update({"rachel": rachel, "matt": matt})
    out = match.predate("rachel", "matt", None)
    assert out["match"] is True
    acc = match.accept("rachel", "matt", out["run_id"])
    assert acc["both_accepted"] and acc["revealed"]["matt"] == "Matt"
    booking = match.book("rachel", "matt", out["run_id"])["booking"]
    assert booking["start"].startswith("2026-11-22T11:00")
    assert "BEGIN:VEVENT" in match.ics(booking["id"])
