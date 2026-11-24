"""Automated logic tests: intent screening done in application code."""
import pytest

from p2p_agent.guardrails import ACTION, JUDGMENT, STATUS, classify_intent, extract_ids


@pytest.mark.parametrize("q", [
    "Please approve PR-10021",
    "approve and pay INV-30777 today",
    "Can you pay the supplier for INV-30912?",
    "change the amount on PO-20450 to 5000",
    "update the status of PO-20311 to received",
    "Cancel PO-20450",
    "mark INV-30912 as paid",
    "set the status of PR-10021 to approved",
    "initiate payment for INV-30777",
    "release the payment on INV-30912",
    "override the hold on INV-30912",
    "expedite this invoice",
    "raise a PO for 3 laptops",
])
def test_action_requests_detected(q):
    assert classify_intent(q) == ACTION


@pytest.mark.parametrize("q", [
    "What's the status of PR-10021?",
    "any update on PO-20450?",
    "Has INV-30912 been approved?",
    "Has invoice INV-30912 been paid yet?",
    "what's the payment status of INV-30777",
    "Where is 55012 at?",
    "Is my order through yet?",
])
def test_status_questions_pass(q):
    assert classify_intent(q) == STATUS


@pytest.mark.parametrize("q", [
    "PO-20450 - should I chase the supplier?",
    "Is it ok to order from Corvane again?",
    "Why is INV-30912 on hold?",
    "When will INV-30777 be paid?",
    "Do you think PR-10021 will be approved?",
    "What would you recommend for PO-20311?",
])
def test_judgment_requests_detected(q):
    assert classify_intent(q) == JUDGMENT


def test_extract_ids():
    assert extract_ids("compare po20450 and INV-30912 and 55012 and PR 10021") == ["PO-20450", "INV-30912", "55012"]
    assert extract_ids("no id here") == []
