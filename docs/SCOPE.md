# Scope statement

**Independent prototype. Synthetic data only. Not connected to AstraZeneca.**

This independent portfolio demo was built from a one-page illustrative concept brief. It does not use, represent or imply access to any AstraZeneca system, data, policy, process, role or escalation route.

## Where it runs
The demo is publicly hosted on Streamlit Community Cloud (https://p2p-status-agent-demo-5qminebdynbdexbfypimjt.streamlit.app/). It can also be run locally from this project; see the README. Both versions use the same fictional synthetic data and the same code. The hosted version is a public portfolio demonstration only: it is not connected to, and does not represent, AstraZeneca's systems, data, policies or processes.

## What is simulated
- **Records:** 10 fictional rows in a local JSON file. All suppliers, organisations, IDs, amounts and the "Demo User" names are invented.
- **Sources:** "Ledgerline ERP (fictional)" and "Northgate Invoice Portal (fictional)" are names only. There are no integrations.
- **Requester roles:** a sidebar selector. It is not authentication or a security control.
- **Process owner:** "P2P Exception Desk (simulated)". A handoff only writes a line to a log file on the machine running the app (your computer, or the Streamlit Community Cloud host). Nothing is sent to anyone.
- **Clock:** fixed at 2026-11-20 12:00 UTC so stale checks are repeatable.
- **Thresholds and rules:** 72-hour stale threshold, conflict rule and role-to-group mapping. All are demo-only assumptions.

## What is real
- The application code, the access and refusal logic, and the automated tests.
- **Live mode only:** calls to the Anthropic API using the key configured by whoever runs the app. Questions typed in that mode are sent to Anthropic. Without a configured key the app runs in offline preview only, and it always shows which mode is active.

## Not connected to
Any ERP, procurement, invoice, payment, identity or ticketing system, and any AstraZeneca environment, data or person. The public Streamlit Community Cloud deployment hosts this demo only; it has no connection to any of these systems.
