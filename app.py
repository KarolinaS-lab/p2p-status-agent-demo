"""Streamlit UI for the read-only P2P status agent demo.

Independent prototype - synthetic data only - not connected to AstraZeneca.
Run:  streamlit run app.py

This file is presentation only. All decisions (access checks, guardrails, lookup
outcomes, handoffs, grounding) are made in p2p_agent/ and are unchanged by the UI.
"""
from __future__ import annotations

import os
import subprocess
import sys

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

import ui_components as ui
from p2p_agent import data_store
from p2p_agent.agent import handle_query, make_anthropic_client
from p2p_agent.audit import AuditLog
from p2p_agent.config import DEFAULT_MODEL, DEMO_AS_OF, PROCESS_OWNER, PROJECT_ROOT, ROLES, STALE_THRESHOLD_HOURS
from p2p_agent.scenarios import SCENARIOS

load_dotenv(PROJECT_ROOT / ".env")  # server-side only; the key never reaches the browser
API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
API_KEY = "" if API_KEY == "your-api-key-here" else API_KEY
MODEL = os.getenv("ANTHROPIC_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
DOCS = PROJECT_ROOT / "docs"

st.set_page_config(page_title="P2P Status Agent - demo prototype", page_icon="📄", layout="wide")
st.markdown(ui.CSS, unsafe_allow_html=True)


@st.cache_resource
def get_audit() -> AuditLog:
    return AuditLog()


audit = get_audit()
ss = st.session_state
ss.setdefault("history", [])
ss.setdefault("role", "requester_ops")

# An example button stores a pending (role, query) and reruns; apply the role BEFORE the widget exists.
pending = ss.pop("pending", None)
if pending:
    ss["role"] = pending["role"]

# ------------------------------------------------------------------ header
st.markdown(ui.scope_banner_html(), unsafe_allow_html=True)
st.markdown(ui.header_html(PROCESS_OWNER), unsafe_allow_html=True)

# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.subheader("Simulated requester")
    st.selectbox("Role", options=list(ROLES), key="role", format_func=lambda k: ROLES[k]["label"])
    st.caption("**Demo only.** This selector simulates who is asking. It is **not authentication and not a "
               "security control** — anyone can pick any role. Access checks run in application code using this value.")
    st.divider()
    st.subheader("Answer mode")
    live_ok = False
    if API_KEY:
        st.caption("API key: detected (hidden)")
        choice = st.radio("Answer mode", ["Offline preview (no AI)", "Live Claude agent"], index=0,
                          label_visibility="collapsed")
        if choice == "Live Claude agent":
            ack = st.checkbox("I understand live mode sends my questions to the Anthropic API and that API use "
                              "may be billed separately.")
            live_ok = ack
            if not ack:
                st.warning("Tick the box to enable live calls. Until then, offline preview is used.")
            st.caption(f"Model: `{MODEL}`")
    else:
        st.info("No API key configured → **offline preview only**. No AI model is called. "
                "See README › 'Add your API key' to enable live Claude runs.")
    mode = "live_claude" if live_ok else "offline_preview"
    st.divider()
    st.subheader("Demo assumptions")
    st.caption(f"Fixed demo clock: {DEMO_AS_OF:%Y-%m-%d %H:%M} UTC  \nStale threshold: {STALE_THRESHOLD_HOURS} h  \n"
               "Both are demo-only assumptions.")
    if st.button("Clear conversation"):
        ss["history"] = []
        st.rerun()

MODE_LABEL = {
    "offline_preview": "Offline preview — no AI model was called. Answer text is a fixed template filled from the lookup result.",
    "live_claude": f"Live Claude run (<code>{ui.escape(MODEL)}</code>). Answer checked by the application against the lookup result.",
    "guardrail": "Handled by an application guardrail — no AI model call and no lookup were made.",
}

# Presentation-only grouping of the existing scenarios (scenario data and behaviour unchanged).
SCENARIO_GROUPS = [
    ("Answered from the record", "A permitted role asks about a current record.", [1, 9]),
    ("Needs clarification", "Missing, unknown or ambiguous IDs. No status is guessed.", [2, 3, 10]),
    ("Cannot be confirmed", "Stale or conflicting sources are handed to a person.", [4, 5]),
    ("Access and scope limits", "Restricted records, action requests and judgment calls.", [6, 7, 8]),
]
_grouped = {i for _, _, ids in SCENARIO_GROUPS for i in ids}
_extra = [s["id"] for s in SCENARIOS if s["id"] not in _grouped]
if _extra:  # any scenario added later still appears
    SCENARIO_GROUPS.append(("Other scenarios", "", _extra))
SCENARIO_BY_ID = {s["id"]: s for s in SCENARIOS}


def render_response(resp: dict) -> None:
    st.markdown(ui.result_card_html(resp, MODE_LABEL[resp["mode"]]), unsafe_allow_html=True)
    for lk in resp["lookups"]:
        st.markdown(ui.lookup_panel_html(lk), unsafe_allow_html=True)
    if resp["lookups"]:
        with st.expander("Raw lookup result (JSON)", expanded=False):
            for lk in resp["lookups"]:
                st.code(ui.raw_json(lk), language="json")


def run(query: str) -> None:
    client = None
    if mode == "live_claude":
        try:
            client = make_anthropic_client(API_KEY)
        except Exception as exc:  # e.g. SDK not installed
            ss["history"].append({"query": query, "role": ss["role"], "resp": {
                "mode": "live_claude", "kind": "error", "answer_text": None, "lookups": [], "handoff": None,
                "notices": [], "grounding_issues": [],
                "error": f"Could not start the Anthropic client ({type(exc).__name__}). Is the `anthropic` package installed?"}})
            return
    resp = handle_query(query, ss["role"], mode=mode, client=client, model=MODEL, audit=audit)
    ss["history"].append({"query": query, "role": ss["role"], "resp": resp})


# ------------------------------------------------------------------ tabs
tab_ask, tab_data, tab_tests, tab_about = st.tabs(["Ask", "Synthetic dataset", "Tests & logs", "How it works / scope"])

with tab_ask:
    st.markdown(ui.status_row_html(mode, MODEL, ROLES[ss["role"]]["label"]), unsafe_allow_html=True)
    st.markdown(ui.section_label_html("Ask a question"), unsafe_allow_html=True)
    typed = st.chat_input("Ask about a PR, PO or invoice, e.g. 'What's the status of PR-10021?'")

    with st.expander("Try example queries", expanded=not ss["history"]):
        st.caption("Each button sets the suggested demo role, then runs the query.")
        cols = st.columns(2)
        for gi, (title, desc, ids) in enumerate(SCENARIO_GROUPS):
            with cols[gi % 2]:
                with st.container(border=True):
                    st.markdown(ui.group_heading_html(title, desc), unsafe_allow_html=True)
                    for sid in ids:
                        s = SCENARIO_BY_ID[sid]
                        if st.button(f"{s['id']}. {s['name']}", key=f"ex{s['id']}",
                                     help=f"Role: {ROLES[s['role']]['label']} · Query: {s['query']}"):
                            ss["pending"] = {"role": s["role"], "query": s["query"]}
                            st.rerun()

    new_query = (pending or {}).get("query") or typed
    if new_query:
        run(new_query)

    st.markdown(ui.section_label_html("Conversation — newest first"), unsafe_allow_html=True)
    if not ss["history"]:
        st.markdown(ui.empty_state_html(), unsafe_allow_html=True)
    for turn in reversed(ss["history"]):
        with st.chat_message("user"):
            st.markdown(turn["query"])
            st.caption(f"as {ROLES[turn['role']]['label']}")
        with st.chat_message("assistant"):
            render_response(turn["resp"])

with tab_data:
    st.subheader("Synthetic dataset (fictional)")
    st.caption("Shown in full for demo inspection only. The agent never sees this table: the lookup returns only "
               "record type, ID, status, source and update time (plus an approved next step when one exists). "
               "Supplier, amount and requester fields are deliberately never returned.")
    st.markdown('<div class="p2p-legend"><span>✓ Returned by lookup: record_id, record_type, status, source, '
                'source_updated_at, approved_next_step</span><span>✕ Never returned: supplier, amount, currency, '
                'requested_by, access_group</span></div>', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame([dict(r) for r in data_store.load_records()]), hide_index=True)
    dd = DOCS / "DATA_DICTIONARY.md"
    if dd.exists():
        with st.expander("Data dictionary and lookup logic", expanded=False):
            st.markdown(dd.read_text(encoding="utf-8"))

with tab_tests:
    st.subheader("Automated logic tests")
    st.caption("Runs the project's pytest suite on this machine. These are logic tests, not live AI results.")
    if st.button("Run automated tests now"):
        with st.spinner("Running pytest…"):
            out = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"], cwd=PROJECT_ROOT,
                                 capture_output=True, text=True, timeout=120)
        (st.success if out.returncode == 0 else st.error)(
            "All tests passed" if out.returncode == 0 else f"pytest exit code {out.returncode}")
        st.code(out.stdout[-6000:] + out.stderr[-2000:])
    rep = DOCS / "TEST_REPORT.md"
    if rep.exists():
        with st.expander("Test report (as generated during the build)", expanded=False):
            st.markdown(rep.read_text(encoding="utf-8"))
    st.subheader("Audit log")
    st.caption("Minimal by design: no question text and no record details.")
    st.dataframe(pd.DataFrame(audit.read()[-50:]), hide_index=True)
    st.subheader("Simulated handoff queue")
    st.caption("Local file only. Nothing is sent to anyone.")
    st.dataframe(pd.DataFrame(audit.read("handoffs")[-50:]), hide_index=True)

with tab_about:
    for p in (DOCS / "ARCHITECTURE.md", DOCS / "SCOPE.md"):
        if p.exists():
            st.markdown(p.read_text(encoding="utf-8"))

st.markdown(ui.footer_html(), unsafe_allow_html=True)
