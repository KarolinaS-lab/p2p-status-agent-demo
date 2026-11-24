# Scope statement

**Independent prototype. Synthetic data only. Not connected to AstraZeneca.**

This demo was built from a one-page illustrative concept brief. It does not use, represent or imply access to any AstraZeneca system, data, policy, process, role or escalation route.

## What is simulated
- **Records:** 10 fictional rows in a local JSON file. All suppliers, organisations, IDs, amounts and the "Demo User" names are invented.
- **Sources:** "Ledgerline ERP (fictional)" and "Northgate Invoice Portal (fictional)" are names only. There are no integrations.
- **Requester roles:** a sidebar selector. It is not authentication or a security control.
- **Process owner:** "P2P Exception Desk (simulated)". A handoff only writes a line to a local file. Nothing is sent.
- **Clock:** fixed at 2026-11-20 12:00 UTC so stale checks are repeatable.
- **Thresholds and rules:** 72-hour stale threshold, conflict rule and role-to-group mapping. All are demo-only assumptions.

## What is real
- The application code, the access and refusal logic, and the automated tests.
- **Live mode only:** calls to the Anthropic API with your own key. Questions you type are sent to Anthropic in that mode.

## Not connected to
Any ERP, procurement, invoice, payment, identity or ticketing system, and any AstraZeneca environment, data or person. Nothing is deployed or published. The app runs only on your machine.
