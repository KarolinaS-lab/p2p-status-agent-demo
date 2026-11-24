"""Automated logic tests of the application's Claude tool-use loop.

These use a SCRIPTED FAKE client. They verify what the application does with
model output (message format, validation, grounding, error handling). They are
not live Claude results.
"""
import json

from conftest import FakeClient, response, text_block, tool_block
from p2p_agent.agent import SYSTEM_PROMPT, TOOL_DEFINITION, handle_query


def live(q, role, scripted, audit):
    client = FakeClient(scripted)
    return handle_query(q, role, mode="live_claude", client=client, audit=audit), client


def test_happy_path_message_format_and_grounded_answer(audit):
    good = ('Purchase request PR-10021 is "Approved - awaiting PO creation" (source: Ledgerline ERP (fictional), '
            'updated 2026-11-19T15:30:00Z). Next step: the buyer will create the PO.')
    r, c = live("Status of PR-10021?", "requester_ops", [
        response("tool_use", text_block("Checking."), tool_block("lookup_p2p_status", {"record_id": "PR-10021"})),
        response("end_turn", text_block(good)),
    ], audit)
    assert r["kind"] == "answer" and r["answer_source"] == "claude" and r["answer_text"] == good
    first, second = c.calls
    assert first["tools"] == [TOOL_DEFINITION] and first["system"] == SYSTEM_PROMPT
    assert second["messages"][1]["role"] == "assistant"
    tr = second["messages"][2]["content"][0]
    assert tr["type"] == "tool_result" and tr["tool_use_id"] == "toolu_test_1" and "is_error" not in tr
    assert json.loads(tr["content"])["outcome"] == "found"


def test_invented_status_is_withheld(audit):
    r, _ = live("Status of PR-10021?", "requester_ops", [
        response("tool_use", tool_block("lookup_p2p_status", {"record_id": "PR-10021"})),
        response("end_turn", text_block("PR-10021 is Approved for payment.")),
    ], audit)
    assert r["kind"] == "error" and r["answer_text"] is None and r["grounding_issues"]


def test_answer_without_tool_call_is_withheld(audit):
    r, _ = live("Status of PO-20450?", "requester_ops", [
        response("end_turn", text_block("PO-20450 is Closed - fully invoiced.")),
    ], audit)
    assert r["kind"] == "error" and r["answer_text"] is None


def test_invented_date_and_id_are_flagged(audit):
    r, _ = live("Status of PO-20450?", "requester_ops", [
        response("tool_use", tool_block("lookup_p2p_status", {"record_id": "PO-20450"})),
        response("end_turn", text_block("PO-20450 is Issued to supplier as of 2026-11-22; see also PO-77777.")),
    ], audit)
    assert any("2026-11-22" in i for i in r["grounding_issues"])
    assert any("PO-77777" in i for i in r["grounding_issues"])


def test_stale_answer_must_say_cannot_confirm(audit):
    r, _ = live("PO-20311?", "requester_ops", [
        response("tool_use", tool_block("lookup_p2p_status", {"record_id": "PO-20311"})),
        response("end_turn", text_block("PO-20311 is Partially received.")),
    ], audit)
    assert r["kind"] == "error" and r["handoff"]["category"] == "stale"


def test_stale_grounded_answer_passes(audit):
    txt = ("The current status of PO-20311 cannot be confirmed. Ledgerline ERP (fictional) last recorded "
           "'Partially received' at 2026-11-12T09:00:00Z. I've routed this to the P2P Exception Desk (simulated).")
    r, _ = live("PO-20311?", "requester_ops", [
        response("tool_use", tool_block("lookup_p2p_status", {"record_id": "PO-20311"})),
        response("end_turn", text_block(txt)),
    ], audit)
    assert r["kind"] == "cannot_confirm" and r["answer_text"] == txt and r["handoff"]


def test_unauthorized_model_never_receives_details(audit):
    r, c = live("What about PO-20999?", "requester_ops", [
        response("tool_use", tool_block("lookup_p2p_status", {"record_id": "PO-20999"})),
        response("end_turn", text_block("I can't share details of PO-20999 for your role; routed to the desk.")),
    ], audit)
    sent = c.calls[1]["messages"][-1]["content"][0]["content"]
    assert "Issued to supplier" not in sent and "Halcyon" not in sent
    assert r["kind"] == "withheld" and r["handoff"]["category"] == "unauthorized"


def test_api_exception_shows_error_and_redacts_key(audit):
    r, _ = live("Status of PR-10021?", "requester_ops",
                [RuntimeError("401 invalid x-api-key sk-ant-api03-SECRETSECRET")], audit)
    assert r["kind"] == "error" and r["answer_text"] is None
    assert "SECRETSECRET" not in r["error"] and "[REDACTED]" in r["error"]
    assert "SECRET" not in json.dumps(audit.read())


def test_unexpected_stop_reason_is_error(audit):
    r, _ = live("Status of PR-10021?", "requester_ops", [response("max_tokens", text_block("PR-10021 is"))], audit)
    assert r["kind"] == "error" and r["answer_text"] is None


def test_runaway_tool_loop_is_stopped(audit):
    loop = [response("tool_use", tool_block("lookup_p2p_status", {"record_id": "PR-10021"}, id_=f"t{i}"))
            for i in range(10)]
    r, c = live("Status of PR-10021?", "requester_ops", loop, audit)
    assert r["kind"] == "error" and len(c.calls) == 4


def test_judgment_gets_app_notice_and_handoff_even_if_model_omits_it(audit):
    txt = 'PO-20450 is "Issued to supplier" (Ledgerline ERP (fictional), 2026-11-20T08:10:00Z). No approved next step is recorded.'
    r, _ = live("PO-20450 - should I chase the supplier?", "requester_ops", [
        response("tool_use", tool_block("lookup_p2p_status", {"record_id": "PO-20450"})),
        response("end_turn", text_block(txt)),
    ], audit)
    assert r["kind"] == "refusal" and r["notices"] and r["handoff"]["category"] == "judgment_request"
