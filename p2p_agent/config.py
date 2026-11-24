"""Demo configuration.

EVERYTHING IN THIS FILE IS A DEMO-ONLY ASSUMPTION. None of it describes
AstraZeneca roles, systems, thresholds, policies or processes.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from types import MappingProxyType

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = PROJECT_ROOT / "data" / "p2p_records.json"
LOG_DIR = PROJECT_ROOT / "logs"

# Demo-only assumption: a fixed "as-of" clock so stale checks are repeatable
# in tests and in an interview demo. A real system would use the current time.
DEMO_AS_OF = datetime(2026, 11, 20, 12, 0, 0, tzinfo=timezone.utc)

# Demo-only assumption: a record whose source update is older than this is stale.
STALE_THRESHOLD_HOURS = 72

# Demo-only assumption: simulated owner for exceptions. No message is sent anywhere.
PROCESS_OWNER = "P2P Exception Desk (simulated)"

# Default model; override with ANTHROPIC_MODEL in .env.
DEFAULT_MODEL = "claude-sonnet-5-5"

# Demo-only assumption: fictional requester roles -> fictional access groups.
# This is a role SELECTOR for demonstration. It is NOT authentication and NOT a
# security control: anyone using the demo can pick any role.
ROLES = MappingProxyType({
    "requester_ops": MappingProxyType({
        "label": "Requester - Facilities & Operations (demo)",
        "groups": frozenset({"OPS"}),
    }),
    "requester_lab": MappingProxyType({
        "label": "Requester - Lab Services (demo)",
        "groups": frozenset({"LAB"}),
    }),
    "p2p_desk": MappingProxyType({
        "label": "P2P Service Desk analyst (demo)",
        "groups": frozenset({"OPS", "LAB"}),
    }),
    "project_halcyon": MappingProxyType({
        "label": "Project Halcyon lead (demo, confidential group)",
        "groups": frozenset({"CONF"}),
    }),
})

RECORD_TYPE_LABELS = MappingProxyType({
    "purchase_request": "Purchase request",
    "purchase_order": "Purchase order",
    "invoice": "Invoice",
})
ID_PREFIX_TO_TYPE = MappingProxyType({
    "PR": "purchase_request",
    "PO": "purchase_order",
    "INV": "invoice",
})
