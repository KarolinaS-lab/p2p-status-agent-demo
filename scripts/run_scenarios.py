"""Run every demo scenario through the OFFLINE PREVIEW path (no AI) and write a results table.

Usage:  python scripts/run_scenarios.py
Output: docs/OFFLINE_SCENARIO_RESULTS.md
"""
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from p2p_agent.agent import handle_query  # noqa: E402
from p2p_agent.audit import AuditLog  # noqa: E402
from p2p_agent.config import ROLES  # noqa: E402
from p2p_agent.scenarios import SCENARIOS  # noqa: E402


def main() -> int:
    audit = AuditLog(tempfile.mkdtemp())
    lines = ["# Offline preview scenario results", "",
             f"Generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC by `scripts/run_scenarios.py`. "
             "**Run type: offline preview (no AI model called).** Answer text is a template filled from the lookup.", "",
             "| # | Scenario | Role | Query | Expected | Actual (kind · outcomes · handoff) | Answer shown | Result |",
             "|---|---|---|---|---|---|---|---|"]
    fails = 0
    for s in SCENARIOS:
        r = handle_query(s["query"], s["role"], audit=audit)
        oc = [lk["outcome"] for lk in r["lookups"]]
        ok = r["kind"] == s["expect_kind"] and oc == s["expect_outcomes"] and bool(r["handoff"]) == s["expect_handoff"]
        fails += not ok
        ho = r["handoff"]["category"] if r["handoff"] else "none"
        ans = (r["answer_text"] or "") + (" " + " ".join(r["notices"]) if r["notices"] else "")
        lines.append(f"| {s['id']} | {s['name']} | {ROLES[s['role']]['label']} | {s['query']} | {s['expected']} | "
                     f"{r['kind']} · {oc or '-'} · {ho} | {ans.replace('|', '/')} | {'PASS' if ok else 'FAIL'} |")
        print(f"{s['id']:>2} {'PASS' if ok else 'FAIL'}  {s['name']}")
    out = ROOT / "docs" / "OFFLINE_SCENARIO_RESULTS.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nWrote {out.relative_to(ROOT)} - {len(SCENARIOS) - fails}/{len(SCENARIOS)} passed")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
