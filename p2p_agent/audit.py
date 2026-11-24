"""Simulated handoffs and a minimal audit log.

Data-minimisation rules for logs:
  * never log the requester's free-text query
  * never log record details (status, supplier, amount, names)
  * log only: time, mode, demo role key, intent category, outcome category,
    handoff reference, whether the model was called, tool-call count, errors
The simulated handoff queue additionally stores the record ID, because the
process owner would need it to act. Nothing is sent anywhere.
"""
from __future__ import annotations

import itertools
import json
import threading
from datetime import datetime, timezone
from pathlib import Path

from .config import LOG_DIR, PROCESS_OWNER

_lock = threading.Lock()
_counter = itertools.count(1)

AUDIT_FIELDS = ("ts", "mode", "role", "intent", "outcomes", "handoff_ref",
                "model_called", "tool_calls", "blocked_tool_calls", "error")


class AuditLog:
    def __init__(self, log_dir: Path | str = LOG_DIR):
        self.dir = Path(log_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.audit_path = self.dir / "audit.jsonl"
        self.handoff_path = self.dir / "handoffs.jsonl"

    def _append(self, path: Path, obj: dict) -> None:
        with _lock, path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(obj) + "\n")

    def record_event(self, **fields) -> dict:
        unknown = set(fields) - set(AUDIT_FIELDS)
        if unknown:  # defensive: refuse to log anything outside the allow-list
            raise ValueError(f"Refusing to log non-allow-listed fields: {sorted(unknown)}")
        entry = {k: fields.get(k) for k in AUDIT_FIELDS}
        entry["ts"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self._append(self.audit_path, entry)
        return entry

    def create_handoff(self, category: str, role: str, record_id: str | None) -> dict:
        ref = f"HO-{datetime.now(timezone.utc):%Y%m%d}-{next(_counter):04d}"
        ticket = {
            "handoff_ref": ref,
            "routed_to": PROCESS_OWNER,
            "category": category,
            "record_id": record_id,
            "role": role,
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "simulated": True,
        }
        self._append(self.handoff_path, ticket)
        return ticket

    def read(self, which: str = "audit") -> list[dict]:
        p = self.audit_path if which == "audit" else self.handoff_path
        if not p.exists():
            return []
        return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]
