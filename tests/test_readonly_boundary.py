"""Automated logic tests: no write, approval or payment action can occur."""
import hashlib
import inspect
import re

import pytest

from conftest import ExplodingClient, FakeClient, response, text_block, tool_block
from p2p_agent import agent, data_store, lookup
from p2p_agent.agent import TOOL_DEFINITION, dispatch_tool_call, handle_query
from p2p_agent.config import DATA_FILE
from p2p_agent.scenarios import SCENARIOS

WRITE_WORDS = re.compile(r"(approve|pay|update|write|save|delete|insert|modify|set_status|cancel|edit|commit)", re.I)


def _sha():
    return hashlib.sha256(DATA_FILE.read_bytes()).hexdigest()


def test_records_are_immutable():
    rows = data_store.load_records()
    assert isinstance(rows, tuple)
    with pytest.raises(TypeError):
        rows[0]["status"] = "Paid"
    with pytest.raises(TypeError):
        rows[0]["new_field"] = 1


def test_data_layer_exposes_no_write_functions():
    for mod in (data_store, lookup):
        public = [n for n, o in inspect.getmembers(mod, callable) if not n.startswith("_")
                  and getattr(o, "__module__", None) == mod.__name__]
        assert not [n for n in public if WRITE_WORDS.search(n)], public


def test_model_is_offered_exactly_one_read_only_tool():
    assert TOOL_DEFINITION["name"] == "lookup_p2p_status"
    assert set(TOOL_DEFINITION["input_schema"]["properties"]) == {"record_id"}  # no role, no write params
    assert TOOL_DEFINITION["input_schema"]["additionalProperties"] is False


@pytest.mark.parametrize("name", ["approve_invoice", "pay_invoice", "update_record", "set_status", "bash", ""])
def test_dispatch_rejects_any_other_tool(name):
    payload, is_err = dispatch_tool_call(name, {"record_id": "INV-30777"}, "p2p_desk")
    assert is_err and "does not exist" in payload["error"]


def test_dispatch_rejects_role_escalation_and_extra_params():
    for bad in ({"record_id": "PO-20999", "role": "project_halcyon"}, {"record_id": "PO-20999", "status": "Paid"},
                {}, "PO-20999", None):
        payload, is_err = dispatch_tool_call("lookup_p2p_status", bad, "requester_ops")
        assert is_err and "error" in payload


@pytest.mark.parametrize("q", ["Please approve PR-10021", "pay INV-30777 now", "Cancel PO-20450",
                               "mark INV-30912 as paid", "change the amount on PO-20450"])
def test_action_requests_never_reach_model_or_lookup(q, audit, monkeypatch):
    called = []
    monkeypatch.setattr(agent, "lookup_p2p_status", lambda *a, **k: called.append(a))
    r = handle_query(q, "p2p_desk", mode="live_claude", client=ExplodingClient(), audit=audit)
    assert r["kind"] == "refusal" and r["model_called"] is False and r["lookups"] == [] and not called
    assert r["handoff"]["category"] == "action_request"


def test_model_requesting_write_tool_executes_nothing(audit):
    before = _sha()
    client = FakeClient([
        response("tool_use", tool_block("approve_invoice", {"record_id": "INV-30777"})),
        response("end_turn", text_block("I can't approve invoices; a person will handle that.")),
    ])
    r = handle_query("What is INV-30777's status?", "p2p_desk", mode="live_claude", client=client, audit=audit)
    sent = client.calls[1]["messages"][-1]["content"][0]
    assert sent["is_error"] is True and "does not exist" in sent["content"]
    assert r["lookups"] == [] and _sha() == before
    assert audit.read()[-1]["blocked_tool_calls"] == 1


def test_dataset_file_unchanged_after_all_scenarios(audit):
    before = _sha()
    for s in SCENARIOS:
        handle_query(s["query"], s["role"], audit=audit)
    assert _sha() == before
