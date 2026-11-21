from uuid import uuid4

import pytest
from fastapi import HTTPException

from app import main


def test_callback_receipt_is_scoped_and_retry_does_not_duplicate(monkeypatch):
    monkeypatch.setattr(main, "_callback_results", {})
    monkeypatch.setattr(main, "_persona", lambda pid: {})
    calls = []

    def import_summary(pid, body):
        calls.append((pid, body.text))
        return {"run_id": "test", "facts": []}

    monkeypatch.setattr(main, "import_paste", import_summary)
    request_id = uuid4()
    assert main.import_callback_status("maya", request_id) == {"result": None}
    result = main.import_callback("maya", request_id, main.PasteBody(text="I like jazz"))
    assert main.import_callback("maya", request_id, main.PasteBody(text="retry")) == result
    assert calls == [("maya", "I like jazz")]
    assert main.import_callback_status("maya", request_id) == {"result": result}
    assert main.import_callback_status("theo", request_id) == {"result": None}


def test_failed_callback_can_retry(monkeypatch):
    monkeypatch.setattr(main, "_callback_results", {})
    monkeypatch.setattr(main, "_persona", lambda pid: {})
    request_id = uuid4()

    def fail(pid, body):
        raise HTTPException(400, "Empty summary")

    monkeypatch.setattr(main, "import_paste", fail)
    with pytest.raises(HTTPException):
        main.import_callback("maya", request_id, main.PasteBody(text=""))
    assert main.import_callback_status("maya", request_id) == {"result": None}
