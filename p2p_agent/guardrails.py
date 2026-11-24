"""Application-side request screening.

These checks run in code BEFORE the model is called. They are deliberately
conservative keyword rules for a demo, not a production classifier (see
Known limitations in the README).
"""
from __future__ import annotations

import re

STATUS = "status_question"
ACTION = "action_request"
JUDGMENT = "judgment_request"

_OBJ = r"(?:a|an|the|this|that|my|our|it|these|those|invoice|invoices|po|pr|purchase|payment|record|status|amount|order|request|supplier|inv|spend|budget)"
_ACTION_PATTERNS = [
    rf"\b(?:approve|authori[sz]e|sign[- ]off|pay|release|change|update|edit|modify|amend|cancel|delete|"
    rf"remove|expedite|override|reject|unblock|reopen|close|resubmit|submit|create|raise|increase|"
    rf"process|push through|escalate and approve)\b\s+{_OBJ}\b",
    r"\bmark\b.{0,40}\bas\b",
    r"\bset\b.{0,40}\bstatus\b",
    r"\b(?:initiate|trigger|schedule|make|send|issue)\b.{0,20}\bpayment\b",
    r"\b(?:pay|approve)\s+(?:PR|PO|INV)[-\s]?\d+",
    r"\bpay (?:them|him|her|the supplier)\b",
]
_JUDGMENT_PATTERNS = [
    r"\bshould (?:i|we)\b",
    r"\bis it (?:ok|okay|safe|fine|reasonable|worth)\b",
    r"\bdo you (?:think|recommend)\b",
    r"\brecommend\b",
    r"\bwhose fault\b",
    r"\bwhy (?:is|was|has|did|does)\b",
    r"\bwhen will\b.{0,30}\b(?:be paid|get paid|arrive|be approved|be delivered|be processed)\b",
    r"\bwill (?:it|this|that) be (?:paid|approved) (?:on time|by)\b",
    r"\b(?:fair|reasonable|correct) price\b",
    r"\bis (?:the )?supplier (?:reliable|good|trustworthy)\b",
    r"\bpredict\b",
]
_ACTION_RE = [re.compile(p, re.I) for p in _ACTION_PATTERNS]
_JUDGMENT_RE = [re.compile(p, re.I) for p in _JUDGMENT_PATTERNS]

ID_IN_TEXT = re.compile(r"\b(?:(PR|PO|INV)[-\s]?(\d{3,8})|(\d{4,8}))\b", re.I)
MAX_QUERY_LEN = 500


def classify_intent(query: str) -> str:
    q = query or ""
    if any(r.search(q) for r in _ACTION_RE):
        return ACTION
    if any(r.search(q) for r in _JUDGMENT_RE):
        return JUDGMENT
    return STATUS


def extract_ids(query: str, limit: int = 3) -> list[str]:
    out: list[str] = []
    for m in ID_IN_TEXT.finditer(query or ""):
        tok = f"{m.group(1).upper()}-{m.group(2)}" if m.group(1) else m.group(3)
        if tok not in out:
            out.append(tok)
        if len(out) >= limit:
            break
    return out
