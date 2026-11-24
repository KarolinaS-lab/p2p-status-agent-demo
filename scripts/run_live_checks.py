"""Run the demo scenarios through the LIVE Claude agent and record what actually happened.

This makes real Anthropic API calls (about 2 calls per scenario, ~18 calls total) and may be billed.
It refuses to run unless you pass --i-understand-billing and ANTHROPIC_API_KEY is set in .env.

Usage:  python scripts/run_live_checks.py --i-understand-billing
Output: docs/LIVE_RESULTS.md   (label: live Claude run)

"Auto-check" compares the APPLICATION's structured result (kind, lookup outcomes, handoff) with the
expected behaviour. Read Claude's wording yourself too - the auto-check does not grade phrasing.
"""
import argparse
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402

from p2p_agent.agent import handle_query, make_anthropic_client  # noqa: E402
from p2p_agent.audit import AuditLog  # noqa: E402
from p2p_agent.config import DEFAULT_MODEL, ROLES  # noqa: E402
from p2p_agent.scenarios import SCENARIOS  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--i-understand-billing", action="store_true", help="Confirm that API use may be billed.")
    args = ap.parse_args()
    load_dotenv(ROOT / ".env")
    key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    key = "" if key == "your-api-key-here" else key
    model = os.getenv("ANTHROPIC_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    if not args.i_understand_billing:
        print("Refusing to call the API: pass --i-understand-billing to confirm.")
        return 2
    if not key:
        print("No ANTHROPIC_API_KEY found in .env - live checks not run.")
        return 2
    client = make_anthropic_client(key)
    audit = AuditLog(tempfile.mkdtemp())
    lines = ["# Live Claude results", "",
             f"Generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC · model `{model}` · "
             "**Run type: live Claude run.**", "",
             "| # | Scenario | Query | Expected | Kind · outcomes · handoff | Claude's answer (or error) | Auto-check |",
             "|---|---|---|---|---|---|---|"]
    fails = 0
    for s in SCENARIOS:
        r = handle_query(s["query"], s["role"], mode="live_claude", client=client, model=model, audit=audit)
        oc = [lk["outcome"] for lk in r["lookups"]]
        ok = (r["kind"] == s["expect_kind"] and oc == s["expect_outcomes"]
              and bool(r["handoff"]) == s["expect_handoff"])
        fails += not ok
        txt = r["answer_text"] or f"ERROR: {r['error']} {r['grounding_issues'] or ''}"
        txt += (" [App notice: " + " ".join(r["notices"]) + "]") if r["notices"] else ""
        ho = r["handoff"]["category"] if r["handoff"] else "none"
        lines.append(f"| {s['id']} | {s['name']} ({ROLES[s['role']]['label']}) | {s['query']} | {s['expected']} | "
                     f"{r['kind']} · {oc or '-'} · {ho} | {txt.replace('|', '/').replace(chr(10), ' ')} | "
                     f"{'PASS' if ok else 'FAIL'} |")
        print(f"{s['id']:>2} {'PASS' if ok else 'FAIL'}  {s['name']}")
    out = ROOT / "docs" / "LIVE_RESULTS.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nWrote {out.relative_to(ROOT)} - {len(SCENARIOS) - fails}/{len(SCENARIOS)} auto-checks passed")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
