"""The single read-only lookup: lookup_p2p_status.

Order of checks (all in application code, never delegated to the model):
  1. validate and normalise the ID
  2. find candidate records (not_found / ambiguous)
  3. AUTHORISATION - before any record detail is read into the result
  4. conflict between sources
  5. staleness
  6. found -> minimal fields only

The result never contains supplier, amount, currency, requester name or
access group. Those fields exist in the synthetic dataset only to show that
the lookup deliberately does not return them.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from . import data_store
from .config import (
    DEMO_AS_OF,
    ID_PREFIX_TO_TYPE,
    PROCESS_OWNER,
    ROLES,
    STALE_THRESHOLD_HOURS,
)

# Outcome categories
FOUND = "found"
NOT_FOUND = "not_found"
AMBIGUOUS = "ambiguous"
STALE = "stale"
CONFLICT = "conflict"
UNAUTHORIZED = "unauthorized"
INVALID_INPUT = "invalid_input"

OUTCOMES = (FOUND, NOT_FOUND, AMBIGUOUS, STALE, CONFLICT, UNAUTHORIZED, INVALID_INPUT)

_FULL_ID = re.compile(r"^(PR|PO|INV)[-\s]?(\d{3,8})$")
_BARE_NUM = re.compile(r"^(\d{3,8})$")
MAX_ID_LEN = 40


def _parse_ts(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _minimal(row) -> dict[str, Any]:
    """The only record fields that may leave the lookup."""
    return {
        "record_type": row["record_type"],
        "record_id": row["record_id"],
        "status": row["status"],
        "source": row["source"],
        "source_updated_at": row["source_updated_at"],
    }


def _base(outcome: str, requested: str, **extra) -> dict[str, Any]:
    res = {
        "outcome": outcome,
        "requested_id": requested,
        "can_confirm_status": False,
        "records": [],
        "approved_next_step": None,
        "handoff_required": False,
        "handoff_to": None,
        "guidance": "",
        "as_of": DEMO_AS_OF.isoformat().replace("+00:00", "Z"),
        "stale_threshold_hours": STALE_THRESHOLD_HOURS,
    }
    res.update(extra)
    return res


def lookup_p2p_status(record_id: Any, role: str, now: datetime = DEMO_AS_OF) -> dict[str, Any]:
    """Read-only status lookup. `role` comes from the app session, never from the model."""
    if role not in ROLES:
        raise ValueError("Unknown demo role")  # programming error, not user input
    allowed = ROLES[role]["groups"]

    # 1. validate
    if not isinstance(record_id, str) or not record_id.strip() or len(record_id) > MAX_ID_LEN:
        return _base(INVALID_INPUT, "", guidance=(
            "The ID is missing or not valid. Ask the requester for one ID such as PR-10021, "
            "PO-20450 or INV-30777. Do not guess."))
    raw = record_id.strip().upper()
    m_full, m_bare = _FULL_ID.match(raw), _BARE_NUM.match(raw)
    if not (m_full or m_bare):
        return _base(INVALID_INPUT, raw[:MAX_ID_LEN], guidance=(
            "The ID format is not recognised. Ask for an ID like PR-10021, PO-20450 or INV-30777. Do not guess."))

    # 2. candidates
    if m_full:
        norm = f"{m_full.group(1)}-{m_full.group(2)}"
        rows = data_store.rows_for_id(norm)
    else:
        norm = m_bare.group(1)
        rows = data_store.rows_for_number(norm)

    if not rows:
        return _base(NOT_FOUND, norm, guidance=(
            "No matching record was found. Say so plainly, do not infer a status, and ask the requester "
            "to check the ID (one focused question)."))

    # 3. authorisation BEFORE any detail is used. Unauthorised rows are dropped.
    visible = [r for r in rows if r["access_group"] in allowed]
    if not visible:
        return _base(UNAUTHORIZED, norm, handoff_required=True, handoff_to=PROCESS_OWNER, guidance=(
            "The requester's role is not authorised to view this record. Share NO record details "
            "(no status, type, source, dates or next step). Say it cannot be shared with their role "
            "and that the request has been routed to the process owner."))

    distinct_ids = sorted({r["record_id"] for r in visible})
    if len(distinct_ids) > 1:
        cands = [{"record_id": i, "record_type": ID_PREFIX_TO_TYPE[i.split("-")[0]]} for i in distinct_ids]
        return _base(AMBIGUOUS, norm, candidates=cands, guidance=(
            "More than one record matches. Ask ONE clarifying question: which of the candidate IDs the "
            "requester means. Do not give any status."))

    resolved_id = distinct_ids[0]
    rows_for_record = [r for r in visible if r["record_id"] == resolved_id]

    # 4. conflict between sources
    statuses = {r["status"] for r in rows_for_record}
    if len(statuses) > 1:
        recs = sorted((_minimal(r) for r in rows_for_record), key=lambda x: x["source"])
        return _base(CONFLICT, norm, resolved_id=resolved_id, records=recs,
                     handoff_required=True, handoff_to=PROCESS_OWNER, guidance=(
            "Sources disagree. Say the status cannot be confirmed. List each source with its recorded "
            "status and update time exactly as given, and say it has been routed to the process owner. "
            "Do not pick one status as correct. Do not give a next step."))

    # 5. staleness (use the most recently updated row)
    latest = max(rows_for_record, key=lambda r: _parse_ts(r["source_updated_at"]))
    age_h = round((now - _parse_ts(latest["source_updated_at"])).total_seconds() / 3600, 1)
    if age_h > STALE_THRESHOLD_HOURS:
        return _base(STALE, norm, resolved_id=resolved_id, records=[_minimal(latest)],
                     age_hours=age_h, handoff_required=True, handoff_to=PROCESS_OWNER, guidance=(
            f"The latest source update is {age_h} hours old, beyond the {STALE_THRESHOLD_HOURS}-hour demo "
            "threshold. Say the current status cannot be confirmed; you may state the last recorded status "
            "only as 'last recorded', with its source and time. Say it has been routed to the process owner. "
            "Do not give a next step."))

    # 6. found
    return _base(FOUND, norm, resolved_id=resolved_id, records=[_minimal(latest)], age_hours=age_h,
                 can_confirm_status=True, approved_next_step=latest["approved_next_step"], guidance=(
        "Report the status with its source and update time exactly as given. Give the approved next step "
        "only if approved_next_step is not null; if it is null, say no approved next step is recorded."))
