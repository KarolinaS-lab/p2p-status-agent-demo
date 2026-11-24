# Test report

Results observed during the build on 2026-11-23 (Linux, Python 3.13.18, pytest 9.1.1). Three kinds of run are kept separate:

| Run type | What it is | Status |
|---|---|---|
| **Automated logic test** | `pytest`. Covers the lookup, access, guardrails, read-only boundary, logging, and the app's tool-use loop using a **scripted fake client**. The fake client is not Claude, and its replies are hand-written test inputs. | **Run: 96 passed, 0 failed** |
| **Offline preview** | All 10 scenarios through the app pipeline with no AI (`scripts/run_scenarios.py`). | **Run: 10/10 passed** |
| **Live Claude run** | The same scenarios through the real Anthropic API (`scripts/run_live_checks.py`). | **NOT RUN.** No API key was configured, and the build workspace has no Anthropic SDK and no API access. See "How to run live checks". |
| Streamlit UI rendering | The real browser UI. | **Not run in the build workspace** (Streamlit not installable there). `app.py` was executed against a minimal Streamlit stand-in: every example button, a typed query and the "Run tests" button ran without errors. Visual layout is unverified until you run it locally. |

## Required cases

| # | Scenario | Expected behaviour | Actual behaviour observed | Result | Run type |
|---|---|---|---|---|---|
| 1 | Authorised requester, unique current record (PR-10021, Ops role) | Status, source and update time match the source; approved next step given | `found`. Status "Approved - awaiting PO creation", Ledgerline ERP (fictional), 2026-11-19T15:30:00Z, next step shown. All 5 returned fields equal the source row; no supplier, amount or requester fields returned. | PASS | Automated + offline preview |
| 2 | Unknown ID (PO-99999) | Says no match; no status inferred | `not_found`, no records. Answer: "No matching record was found for PO-99999. Could you check the ID?" | PASS | Automated + offline preview |
| 3 | Ambiguous ID (55012) | One clarifying question; no status | `ambiguous`, candidates PO-55012 and PR-55012, no status in the result. Answer: "Did you mean PO-55012 or PR-55012?" | PASS | Automated + offline preview |
| 4 | Stale record (PO-20311) | Cannot confirm; source and time shown; routed | `stale`, age 195.0 h > 72 h. Last status, source and 2026-11-12T09:00:00Z shown; next step withheld; handoff `stale` created. | PASS | Automated + offline preview |
| 5 | Conflicting records (INV-30912) | Cannot confirm; both sources visible; routed | `conflict`. Both sources with statuses and times shown; no status chosen; handoff `conflict` created. | PASS | Automated + offline preview |
| 6 | Unauthorised requester, restricted record (PO-20999, Ops role) | No record details revealed; routed | `unauthorized`. Result contains no status, type, source, date, supplier or next step (checked by searching the serialised result). Handoff created. Same ID with "Project Halcyon lead" role → `found` (case 9). | PASS | Automated + offline preview |
| 7 | Request to approve / change / pay | Declined; no write; routed | Refused by the app guardrail. Model **not** called (a client that fails the test if called was used) and **no lookup** run. Handoff `action_request` recorded. Data file SHA-256 unchanged. | PASS | Automated + offline preview |
| 8 | Judgment request on a record with no approved next step (PO-20450, "should I chase the supplier?") | Recorded status only; "no approved next step"; judgment declined and routed | `found`, "No approved next step is recorded"; app notice declines the judgment; handoff `judgment_request` created. | PASS | Automated + offline preview |
| 9 | Contrast: authorised role for restricted record | Shown | `found` | PASS | Automated + offline preview |
| 10 | No ID given | Ask for ID; no status | Asked for the ID; no lookup made | PASS | Automated + offline preview |

## Further automated checks (all passed)
- **Read-only boundary:** records are immutable (assignment raises `TypeError`). The data layer has no functions named approve, pay, update, write, delete and so on. The model is offered exactly one tool with exactly one parameter. Tool names `approve_invoice`, `pay_invoice`, `update_record`, `set_status`, `bash` and empty are rejected and nothing runs. The data file hash is unchanged after all scenarios.
- **Privilege escalation through the model:** a tool call carrying `role: "project_halcyon"` or `status: "Paid"` is rejected.
- **Access order:** the Lab role asking about the OPS conflict or stale records gets `unauthorized`, not `conflict` or `stale`.
- **Tool-use loop (scripted fake client):** correct `tool_result` format and `tool_use_id`; `is_error: true` for rejected calls. An invented status, an answer with no tool call, an invented date or ID, and a stale answer missing "cannot be confirmed" are all **withheld**. An API exception gives a clear error with the key redacted. `stop_reason=max_tokens` gives an error. A runaway tool loop stops after 4 model turns.
- **Logging:** after all scenarios, the logs contain none of the query texts, statuses, suppliers, amounts or requester names. Non-allow-listed log fields are refused. Every handoff appears in the queue.
- **Input validation:** None, empty, too long, injection-style and path-style IDs all return `invalid_input`.

## Failures found during the build
- **Fixed:** "When will INV-30777 be paid?" was first classed as a plain status question, because the prediction pattern did not allow an ID between "when will" and "be paid". The pattern was widened and the test now passes.
- **Remaining failures:** none in the automated or offline runs.

## Pilot measures from the brief (demo values)
- Field-level answer accuracy (lookup vs source): 5/5 fields correct for every `found` record and role (automated).
- Correct handling of missing, conflicting and restricted cases: 10/10 scenarios (offline preview).
- Unauthorised disclosure or write events: 0 observed in the automated tests.
- Resolution or handoff time: not measured (no real users or owner).

## How to run live checks (not run here)
1. Put your key in `.env` (see README).
2. `python scripts/run_live_checks.py --i-understand-billing` (about 18–20 API calls).
3. Read `docs/LIVE_RESULTS.md`. The auto-check grades only the application's structured outcome, so read Claude's wording yourself as well.
4. Or use the app: sidebar → "Live Claude agent" → tick the billing box → click the example buttons.

## UI revision (2026-11-23, presentation layer only)
Changed: `app.py`, new `ui_components.py`, new `.streamlit/config.toml`, wording in `docs/DEMO_SCRIPT.md`. No change to `p2p_agent/`, `data/`, `tests/` or `scripts/`.
- `python -m pytest -q`: **96 passed** (same as before; no test expectations changed).
- `python scripts/run_scenarios.py`: **10/10 passed** (offline preview).
- `app.py` executed against a minimal Streamlit stand-in (every example button, a typed query, the test button): ran without errors.
- The new HTML/CSS components (scope banner, header, mode chip, result cards, verified-record panels) were rendered as a **static page** in headless Chrome at 1366 px and 420 px wide, using real offline-preview responses.
- **Not verified:** the real Streamlit page (Streamlit is not installable in the build workspace), the theme file's effect, and the live Claude mode.
- Follow-up check (2026-11-24): "No questions yet" appears only when the conversation is empty. Checked with the Streamlit stand-in: shown before the first question and after "Clear conversation", hidden after an example or a typed question. Its appearance in the earlier static preview came from the preview script, not from the app. README wording updated to "verified record panel beneath each answer". Tests re-run: 96 passed; scenarios 10/10.
