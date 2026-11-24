import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from p2p_agent.audit import AuditLog  # noqa: E402


@pytest.fixture
def audit(tmp_path):
    return AuditLog(tmp_path / "logs")


# ---- A scripted stand-in for anthropic.Anthropic(), used ONLY to test the app's
# ---- tool-use loop logic. It is not Claude and its outputs are not AI results.
def text_block(t):
    return SimpleNamespace(type="text", text=t)


def tool_block(name, inp, id_="toolu_test_1"):
    return SimpleNamespace(type="tool_use", id=id_, name=name, input=inp)


def response(stop_reason, *blocks):
    return SimpleNamespace(stop_reason=stop_reason, content=list(blocks))


class FakeClient:
    def __init__(self, scripted):
        self._scripted = list(scripted)
        self.calls = []
        self.messages = self

    def create(self, **kwargs):
        # snapshot the request so tests can inspect exactly what was sent
        self.calls.append({k: (list(v) if isinstance(v, list) else v) for k, v in kwargs.items()})
        item = self._scripted.pop(0)
        if isinstance(item, Exception):
            raise item
        return item(kwargs) if callable(item) else item


class ExplodingClient:
    """Fails the test if the model is called at all."""
    def __init__(self):
        self.messages = self

    def create(self, **kwargs):
        raise AssertionError("Model must not be called for this request")
