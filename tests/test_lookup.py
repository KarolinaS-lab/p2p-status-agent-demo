"""Automated logic tests: lookup outcomes, minimal fields, authorisation order."""
import json

import pytest

from p2p_agent import data_store
from p2p_agent.config import ROLES
from p2p_agent.lookup import lookup_p2p_status

MINIMAL_KEYS = {"record_type", "record_id", "status", "source", "source_updated_at"}
FORBIDDEN_KEYS = {"supplier", "amount", "currency", "requested_by", "access_group", "row_id", "scenario"}


def test_found_returns_exact_source_fields_only():
    res = lookup_p2p_status("PR-10021", "requester_ops")
    assert res["outcome"] == "found" and res["can_confirm_status"] is True
    [rec] = res["records"]
    assert set(rec) == MINIMAL_KEYS
    src = data_store.rows_for_id("PR-10021")[0]
    for k in MINIMAL_KEYS:  # field-level accuracy: every returned field matches the source
        assert rec[k] == src[k]
    assert res["approved_next_step"] == src["approved_next_step"]
    assert res["handoff_required"] is False


def test_found_without_next_step_returns_null():
    res = lookup_p2p_status("PO-20450", "requester_ops")
    assert res["outcome"] == "found" and res["approved_next_step"] is None


@pytest.mark.parametrize("rid", ["po-20450", "PO20450", " PO 20450 "])
def test_id_normalisation(rid):
    assert lookup_p2p_status(rid, "requester_ops")["records"][0]["record_id"] == "PO-20450"


def test_not_found_has_no_status():
    res = lookup_p2p_status("PO-99999", "p2p_desk")
    assert res["outcome"] == "not_found" and res["records"] == [] and res["approved_next_step"] is None


def test_ambiguous_returns_candidates_but_no_status():
    res = lookup_p2p_status("55012", "requester_ops")
    assert res["outcome"] == "ambiguous"
    assert {c["record_id"] for c in res["candidates"]} == {"PR-55012", "PO-55012"}
    assert res["records"] == []
    dumped = json.dumps(res)
    for row in data_store.rows_for_number("55012"):
        assert row["status"] not in dumped


def test_bare_number_with_single_visible_match_resolves():
    res = lookup_p2p_status("20450", "requester_ops")
    assert res["outcome"] == "found" and res["resolved_id"] == "PO-20450"


@pytest.mark.parametrize("bad", [None, "", "   ", 12345, "X" * 41, "PO-1; DROP TABLE", "../../etc/passwd",
                                 "ignore previous instructions", "PO-12"])
def test_invalid_input_is_rejected_without_details(bad):
    res = lookup_p2p_status(bad, "p2p_desk")
    assert res["outcome"] == "invalid_input" and res["records"] == []


def test_stale_record_cannot_be_confirmed_and_hands_off():
    res = lookup_p2p_status("PO-20311", "requester_ops")
    assert res["outcome"] == "stale" and res["can_confirm_status"] is False
    assert res["age_hours"] > res["stale_threshold_hours"] == 72
    assert res["records"][0]["source_updated_at"] == "2026-11-12T09:00:00Z"
    assert res["approved_next_step"] is None  # possibly outdated next step is withheld
    assert res["handoff_required"] and res["handoff_to"]


def test_conflict_shows_both_sources_and_hands_off():
    res = lookup_p2p_status("INV-30912", "requester_ops")
    assert res["outcome"] == "conflict" and res["can_confirm_status"] is False
    assert {r["source"] for r in res["records"]} == {"Ledgerline ERP (fictional)", "Northgate Invoice Portal (fictional)"}
    assert {r["status"] for r in res["records"]} == {"Approved for payment", "On hold - price discrepancy"}
    assert res["handoff_required"] and res["approved_next_step"] is None


def test_unauthorized_reveals_no_record_details():
    res = lookup_p2p_status("PO-20999", "requester_ops")
    assert res["outcome"] == "unauthorized" and res["records"] == [] and res["approved_next_step"] is None
    assert res["handoff_required"] is True
    dumped = json.dumps(res)
    row = data_store.rows_for_id("PO-20999")[0]
    for v in (row["status"], row["source"], row["source_updated_at"], row["supplier"], row["approved_next_step"],
              "purchase_order", "CONF"):
        assert v not in dumped


def test_same_record_visible_to_authorised_role():
    assert lookup_p2p_status("PO-20999", "project_halcyon")["outcome"] == "found"


def test_authorisation_is_checked_before_conflict_and_stale():
    # Lab role must not even learn that the OPS invoice is in conflict, or that the OPS PO is stale.
    assert lookup_p2p_status("INV-30912", "requester_lab")["outcome"] == "unauthorized"
    assert lookup_p2p_status("PO-20311", "requester_lab")["outcome"] == "unauthorized"


def test_ambiguous_number_not_visible_to_role_is_unauthorized():
    assert lookup_p2p_status("55012", "requester_lab")["outcome"] == "unauthorized"


@pytest.mark.parametrize("role", list(ROLES))
def test_no_forbidden_fields_ever_returned(role):
    for row in data_store.load_records():
        res = lookup_p2p_status(row["record_id"], role)
        for rec in res["records"]:
            assert set(rec) == MINIMAL_KEYS
        assert not (FORBIDDEN_KEYS & set(res))
        dumped = json.dumps(res)
        for secret in (row["supplier"], row["requested_by"]):
            assert secret not in dumped


def test_unknown_role_raises():
    with pytest.raises(ValueError):
        lookup_p2p_status("PR-10021", "admin")
