# Data dictionary and lookup logic

> **Synthetic data only.** Every organisation, supplier, person, ID, amount and source is fictional. Nothing here describes AstraZeneca systems, data, roles, thresholds or processes.

File: `data/p2p_records.json` (10 rows, 9 distinct record IDs; INV-30912 appears once per source).

## Fields

| Field | Type | Returned by lookup? | Meaning |
|---|---|---|---|
| `row_id` | int | No | Row number in the file. |
| `record_id` | string | **Yes** | `PR-#####` purchase request, `PO-#####` purchase order, `INV-#####` invoice. |
| `record_type` | string | **Yes** | `purchase_request`, `purchase_order` or `invoice`. |
| `status` | string | **Yes** | Status as recorded by the source. |
| `source` | string | **Yes** | Fictional source: *Ledgerline ERP (fictional)* or *Northgate Invoice Portal (fictional)*. |
| `source_updated_at` | ISO-8601 UTC | **Yes** | When that source last updated the record. |
| `approved_next_step` | string or null | **Yes, only when the record is `found`** | The approved next step recorded at the source. `null` = none recorded. |
| `access_group` | string | No | Demo access group: `OPS`, `LAB` or `CONF` (restricted). Used for the access check only. |
| `supplier`, `amount`, `currency` | various | **Never** | Included only to show that the lookup returns the minimum and leaves these fields out. |
| `requested_by` | string | **Never** | Placeholder ("Demo User A" etc.). Never returned or logged. |
| `scenario` | string | No | Which test scenario the row supports. |

## Records by scenario

| Scenario | Record(s) |
|---|---|
| Normal match, with approved next step | PR-10021 (OPS), INV-30777 (LAB), PR-10088 (LAB) |
| Normal match, **no** approved next step | PO-20450 (OPS) |
| Unmatched ID | e.g. PO-99999 (not in file) |
| Ambiguous | bare number `55012` → PR-55012 and PO-55012 |
| Stale | PO-20311 (last update 2026-11-12, i.e. 195 h before the demo clock) |
| Conflicting sources | INV-30912: Ledgerline says "Approved for payment", Northgate says "On hold - price discrepancy" |
| Restricted | PO-20999 (`CONF` group; only the "Project Halcyon lead (demo)" role may view it) |

## Demo roles (demo-only assumption)

| Role | May view groups |
|---|---|
| Requester - Facilities & Operations (demo) | OPS |
| Requester - Lab Services (demo) | LAB |
| P2P Service Desk analyst (demo) | OPS, LAB |
| Project Halcyon lead (demo, confidential group) | CONF |

The role selector is **not authentication and not a security control**. It only simulates who is asking.

## How the lookup works (plain language)

`lookup_p2p_status(record_id)` is the only thing the agent can do. It runs in application code. The role comes from the app session; Claude never supplies it.

1. **Check the ID.** It must look like `PR-…`, `PO-…`, `INV-…` or a bare 3–8-digit number. Anything else returns `invalid_input`.
2. **Find matches.** No match returns `not_found`.
3. **Check access first.** Rows the role may not see are dropped *before* anything else is looked at. If none are left, the result is `unauthorized` with no details: no status, type, source, date or next step. The role therefore can't even learn whether the record is stale or in conflict.
4. **Ambiguous?** If a bare number matches more than one visible record, the result is `ambiguous`. It lists the candidate IDs only, with no status.
5. **Conflict?** If two sources hold different statuses for the same ID, the result is `conflict`. It lists each source's status and time, can't confirm a status, gives no next step and requires a handoff.
6. **Stale?** If the latest source update is more than **72 hours** older than the **fixed demo clock (2026-11-20 12:00 UTC)**, the result is `stale`. It shows the last recorded status, source and time, can't confirm a status, gives no next step and requires a handoff. *(Both values are demo-only assumptions. The clock is fixed so the demo and tests give the same results every time.)*
7. **Otherwise `found`.** It returns record type, ID, status, source and update time, plus the approved next step if one is recorded.

When a handoff is required, the **application** creates a simulated ticket for "P2P Exception Desk (simulated)" and writes it to `logs/handoffs.jsonl`. Nothing is sent anywhere.
