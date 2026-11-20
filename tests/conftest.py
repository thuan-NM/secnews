import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from types import SimpleNamespace

import pytest


@pytest.fixture
def fake_llm(monkeypatch):
    """Thay OpenAI SDK: ctl.outcome là chuỗi trả về hoặc exception để ném; ctl.calls ghi tham số create()."""
    from secnews import summarize

    ctl = SimpleNamespace(outcome='{"summary_vi": "a", "action_vi": ""}', calls=[], init=[])

    def create(**kw):
        ctl.calls.append(kw)
        if isinstance(ctl.outcome, Exception):
            raise ctl.outcome
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=ctl.outcome))])

    def factory(**kw):
        ctl.init.append(kw)
        return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))

    monkeypatch.setattr(summarize, "OpenAI", factory)
    return ctl
