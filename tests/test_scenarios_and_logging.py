"""Automated logic tests: the 10 demo scenarios end to end (offline preview path) and log minimisation."""
import json

import pytest

from p2p_agent import data_store
from p2p_agent.agent import handle_query
from p2p_agent.scenarios import SCENARIOS


@pytest.mark.parametrize("s", SCENARIOS, ids=[f"case{s['id']}" for s in SCENARIOS])
def test_scenario_offline(s, audit):
    r = handle_query(s["query"], s["role"], audit=audit)
    assert r["kind"] == s["expect_kind"]
    assert [lk["outcome"] for lk in r["lookups"]] == s["expect_outcomes"]
    assert bool(r["handoff"]) == s["expect_handoff"]
    assert r["model_called"] is False
    if s["expect_handoff"]:
        assert r["handoff"]["handoff_ref"] in {h["handoff_ref"] for h in audit.read("handoffs")}


def test_logs_contain_no_query_text_or_record_details(audit):
    for s in SCENARIOS:
        handle_query(s["query"], s["role"], audit=audit)
    blob = json.dumps(audit.read()) + json.dumps(audit.read("handoffs"))
    for s in SCENARIOS:
        assert s["query"] not in blob
    for row in data_store.load_records():
        for v in (row["status"], row["supplier"], row["requested_by"], str(row["amount"])):
            assert v not in blob


def test_audit_log_refuses_non_allow_listed_fields(audit):
    with pytest.raises(ValueError):
        audit.record_event(query="what is PO-20450", role="requester_ops")


def test_every_escalation_is_recorded(audit):
    for s in SCENARIOS:
        handle_query(s["query"], s["role"], audit=audit)
    expected = sum(1 for s in SCENARIOS if s["expect_handoff"])
    assert len(audit.read("handoffs")) == expected
    assert len(audit.read()) == len(SCENARIOS)
