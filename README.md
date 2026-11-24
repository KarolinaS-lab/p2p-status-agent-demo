# Read-only P2P status agent (demo prototype)

> **Independent prototype. Synthetic data only. Not connected to AstraZeneca.**
> All organisations, suppliers, IDs, sources and people are fictional. See `docs/SCOPE.md`.

A small local app that answers questions such as *"What's the status of PO-20450?"* by looking up fictional purchase requests, purchase orders and invoices. It handles missing, ambiguous, stale, conflicting, unauthorised and "please approve or pay this" requests safely. It can't change anything.

- **Offline preview** (default, free): no AI. The app looks up the record and fills a fixed answer template.
- **Live Claude agent** (optional): Claude decides when to call the single read-only tool and phrases the answer, and the app checks that answer. **Requires your own Anthropic API key, and API use may be billed separately.**

---

## 1. Setup (beginner-friendly)

You need **Python 3.10 or newer**. Check with `python --version` (on macOS/Linux you may need `python3`).

```bash
# 1. go into the project folder
cd p2p-status-agent

# 2. create and activate a virtual environment
python -m venv .venv
# macOS / Linux:
source .venv/bin/activate
# Windows (PowerShell):
.venv\Scripts\Activate.ps1

# 3. install dependencies
pip install -r requirements.txt
```

## 2. Run the app

```bash
streamlit run app.py
```

Your browser opens at http://localhost:8501. The app runs only on your computer and is not published. Stop it with `Ctrl+C`.

## 3. Run the tests

```bash
python -m pytest -q                 # 96 automated logic tests
python scripts/run_scenarios.py     # 10 scenarios, offline preview -> docs/OFFLINE_SCENARIO_RESULTS.md
```

## 4. (Optional) Add your API key for live Claude runs

1. Get a key from the Claude Console (https://platform.claude.com). **API use may be billed separately from any Claude subscription.**
2. Copy the template and edit the copy:
   ```bash
   cp .env.example .env        # Windows: copy .env.example .env
   ```
3. Open `.env` and replace the placeholder after `ANTHROPIC_API_KEY=` with your key.
4. Restart the app. In the sidebar choose **Live Claude agent** and tick the billing acknowledgement. Live calls are made only after both steps.
5. Optional live test run (about 18–20 API calls): `python scripts/run_live_checks.py --i-understand-billing` → `docs/LIVE_RESULTS.md`.

**Keeping the key private**
- The key lives only in `.env` on your machine. The app reads it on the Python (server) side; it is never sent to the browser, shown on screen or written to logs, and error messages redact anything that looks like a key.
- `.env` is listed in `.gitignore`. **Never commit it, paste it into chat or share screenshots of it.**
- If a key is exposed, revoke it in the Claude Console and create a new one.

## 5. What's in the folder

| Path | What it is |
|---|---|
| `app.py` | Streamlit interface |
| `p2p_agent/lookup.py` | The one read-only lookup and its access, stale and conflict rules |
| `p2p_agent/guardrails.py` | App-side screening of action and judgment requests |
| `p2p_agent/agent.py` | Claude tool-use loop, offline preview, grounding check, handoff decisions |
| `p2p_agent/audit.py` | Minimal audit log and simulated handoff queue (`logs/`) |
| `p2p_agent/config.py` | Demo-only assumptions: roles, 72 h threshold, fixed clock, model |
| `data/p2p_records.json` | Synthetic dataset |
| `docs/DATA_DICTIONARY.md` | Data dictionary and plain-language lookup logic |
| `docs/ARCHITECTURE.md` | What Claude does vs what the app checks |
| `docs/TEST_REPORT.md` | Observed test results |
| `docs/DEMO_SCRIPT.md` | 60–90 s demo script |
| `docs/SCOPE.md` | What is simulated and what is not connected |
| `tests/` | Automated tests |
| `scripts/` | Scenario runner (offline) and live-check runner |

## 6. Dependencies
`requirements.txt`: `streamlit`, `anthropic` (official Anthropic Python SDK), `python-dotenv`, `pandas`, `pytest`.

## 7. Demo-only assumptions (not AstraZeneca facts)
Fictional roles and access groups; a 72-hour stale threshold measured against a fixed demo clock (2026-11-20 12:00 UTC); two fictional sources; conflict = different statuses for the same ID; a simulated "P2P Exception Desk"; default model `claude-sonnet-5-5` (set `ANTHROPIC_MODEL` to change it).

## 8. Known limitations
- **The role selector is not security.** Anyone can pick any role. Real access would come from identity and permissions in the source systems.
- **The unauthorised response reveals that an ID exists** (it says "can't share" rather than "not found"). A real design might return the same message for both.
- **Action and judgment detection is keyword-based.** It is tested on the phrasings in `tests/test_guardrails.py`, but unusual wording could slip past. Even then, the model has no write tool, so nothing could be changed; the risk is a missed handoff or a less clear refusal.
- **The grounding check is heuristic.** It catches statuses, sources, IDs and ISO dates that the lookup did not return, and a missing "cannot be confirmed" on stale or conflict answers. It does not catch every possible paraphrase (for example an invented next step written in free text). The verified record panel beneath each answer (from the application's lookup, not the model) is the authoritative data.
- **The clock is fixed** for repeatability, so "stale" is relative to 2026-11-20 12:00 UTC, not today.
- **Live Claude behaviour was not tested during the build** (no key or SDK access there). See `docs/TEST_REPORT.md`.
- **The Streamlit UI was not rendered during the build.** It was executed against a stand-in only; check the layout locally.
- **Single-user local demo.** Logs are local JSONL files; there is no concurrency, persistence or retention design.
