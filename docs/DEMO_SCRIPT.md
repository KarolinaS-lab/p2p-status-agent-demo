# 60–90 second demo script

Start the app (`streamlit run app.py`). Use **offline preview**, or live Claude if you have added a key and ticked the billing box. The answers below are the **offline preview** outputs actually observed during the build. In live mode Claude's wording will differ, but the verified record panel, the handoff line and the labelled result badge come from the application and stay the same.

**0:00 – Framing (10 s).** Point at the scope banner at the top: "Independent prototype, synthetic data, not connected to AstraZeneca. One bounded task: read-only status lookup. Exceptions go to a person."

**0:10 – Happy path (15 s).** Open **Try example queries** and click **1. Authorised, unique, current record** (group *Answered from the record*).
> Purchase request PR-10021: "Approved - awaiting PO creation" (source: Ledgerline ERP (fictional), updated 2026-11-19T15:30:00Z). Approved next step: Buyer will create the purchase order; no requester action is needed.

Point at the **Verified record** panel under the answer (source, update time, approved next step): "Source and timestamp come from the lookup. Supplier and amount exist in the data but are never returned."

**0:25 – Stale and conflict (20 s).** Click **4**, then **5**.
> The current status of PO-20311 cannot be confirmed: the last recorded status was "Partially received" … updated 2026-11-12T09:00:00Z … Routed to P2P Exception Desk (simulated).

> The status of INV-30912 cannot be confirmed because the sources disagree: Ledgerline ERP (fictional) shows "Approved for payment" …; Northgate Invoice Portal (fictional) shows "On hold - price discrepancy" … Routed …

"It never picks a winner. The handoff reference is created by code, not by the model."

**0:45 – Access (15 s).** Click **6** (Ops role):
> I can't share details of PO-20999 with your current role. Routed to P2P Exception Desk (simulated).

Then click **9**: the role switches to Project Halcyon lead and the same ID is shown. "Access is checked in code before any detail is read. The role selector is a simulation, not authentication."

**1:00 – Action and judgment (15 s).** Click **7**:
> I can't do that. This assistant is read-only: it cannot approve spend, change records or initiate payments. Your request has been routed to P2P Exception Desk (simulated).

"Blocked before any model call. Claude has no write tool to call." Click **8** to show the status plus "No approved next step is recorded", and the judgment being declined.

**1:15 – Evidence (10 s).** Open **Tests & logs** → *Run automated tests now* (96 tests). Show that the audit log holds outcome categories only, with no question text.

*Recording:* nothing has been recorded. If you want a screen recording, record it yourself locally (e.g. OS screen recorder) after a dry run.
