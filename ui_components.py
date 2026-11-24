"""Presentation helpers for app.py: CSS and small HTML fragments.

Pure functions only. No business logic lives here: every value shown comes from
the response dict produced by p2p_agent.agent.handle_query. All dynamic text is
HTML-escaped before it is inserted.
"""
from __future__ import annotations

import json
from datetime import datetime
from html import escape

SCOPE_STATEMENT = "Independent prototype — synthetic data only — not connected to AstraZeneca."
OFFLINE_SHORT = "Offline preview — no AI model was called"

RECORD_TYPE_LABELS = {"purchase_request": "Purchase request", "purchase_order": "Purchase order",
                      "invoice": "Invoice"}

CSS = """
<style>
:root{
  --ink:#1F2933; --muted:#52606D; --line:#D9E2EC; --surface:#F7F9FB; --accent:#2B5C8A;
  --ok:#1E6B45; --ok-bg:#EEF7F1; --info:#2B5C8A; --info-bg:#EEF4FA;
  --warn:#7A4F00; --warn-bg:#FFF6E0; --stop:#9B2C2C; --stop-bg:#FDF1F1;
}
.block-container{max-width:1180px; padding-top:1.4rem; padding-bottom:3rem;}
.p2p-scope{display:flex; gap:.75rem; align-items:flex-start; background:#243B53; color:#fff;
  border-radius:8px; padding:.7rem 1rem; margin-bottom:1.1rem; line-height:1.4;}
.p2p-scope .tag{flex:none; font-size:.7rem; font-weight:700; letter-spacing:.06em; text-transform:uppercase;
  border:1px solid rgba(255,255,255,.55); border-radius:4px; padding:.1rem .4rem; margin-top:.15rem;}
.p2p-scope strong{font-weight:650;}
.p2p-scope small{display:block; opacity:.85; font-size:.82rem; margin-top:.15rem;}
.p2p-eyebrow{color:var(--muted); font-size:.8rem; letter-spacing:.05em; text-transform:uppercase; margin:0;}
.p2p-title{font-size:1.9rem; font-weight:700; color:var(--ink); margin:.1rem 0 .35rem 0; line-height:1.2;}
.p2p-lead{color:var(--muted); font-size:1rem; max-width:62ch; margin:0 0 .7rem 0;}
.p2p-pills{display:flex; flex-wrap:wrap; gap:.4rem; margin:0 0 .4rem 0; padding:0; list-style:none;}
.p2p-pills li{border:1px solid var(--line); background:var(--surface); color:var(--ink); border-radius:999px;
  padding:.15rem .65rem; font-size:.8rem;}
.p2p-status-row{display:flex; flex-wrap:wrap; gap:.5rem; margin:.2rem 0 .6rem 0;}
.p2p-chip{display:inline-flex; align-items:center; gap:.4rem; border-radius:6px; padding:.25rem .6rem;
  font-size:.85rem; border:1px solid var(--line); background:#fff; color:var(--ink); flex-wrap:wrap; max-width:100%;}
.p2p-chip.offline{background:#F0F2F5; border-color:#BCC6D1; font-weight:600;}
.p2p-chip.live{background:var(--info-bg); border-color:#B6CBE0; color:var(--info); font-weight:600;}
.p2p-section-label{font-size:.78rem; font-weight:700; letter-spacing:.06em; text-transform:uppercase;
  color:var(--muted); margin:.9rem 0 .35rem 0;}
.p2p-group-title{font-weight:650; color:var(--ink); font-size:.95rem; margin:0;}
.p2p-group-desc{color:var(--muted); font-size:.8rem; margin:.1rem 0 .4rem 0;}
[class*="st-key-ex"] button{width:100%; justify-content:flex-start; text-align:left;}
.p2p-card{border:1px solid var(--line); border-left-width:5px; border-radius:8px; background:#fff;
  padding:.85rem 1rem; margin:.1rem 0 .6rem 0;}
.p2p-card.ok{border-left-color:var(--ok);} .p2p-card.info{border-left-color:var(--info);}
.p2p-card.warn{border-left-color:#C08A00;} .p2p-card.stop{border-left-color:var(--stop);}
.p2p-card-head{display:flex; align-items:center; gap:.5rem; flex-wrap:wrap; margin-bottom:.45rem;}
.p2p-badge{display:inline-flex; align-items:center; gap:.35rem; font-weight:700; font-size:.85rem;
  border-radius:4px; padding:.12rem .5rem;}
.ok .p2p-badge{color:var(--ok); background:var(--ok-bg);} .info .p2p-badge{color:var(--info); background:var(--info-bg);}
.warn .p2p-badge{color:var(--warn); background:var(--warn-bg);} .stop .p2p-badge{color:var(--stop); background:var(--stop-bg);}
.p2p-mode{color:var(--muted); font-size:.8rem;}
.p2p-answer{color:var(--ink); font-size:1rem; line-height:1.55; margin:0; overflow-wrap:anywhere;}
.p2p-sub{margin-top:.6rem; padding-top:.55rem; border-top:1px dashed var(--line); font-size:.88rem; color:var(--ink);}
.p2p-sub b{font-weight:650;}
.p2p-sub ul{margin:.2rem 0 0 1.1rem; padding:0;}
.p2p-handoff{display:flex; flex-wrap:wrap; gap:.3rem .9rem; align-items:baseline;}
.p2p-ref{font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:.82rem; background:var(--surface);
  border:1px solid var(--line); border-radius:4px; padding:0 .3rem;}
.p2p-panel{background:var(--surface); border:1px solid var(--line); border-radius:8px; padding:.7rem .9rem; margin:0 0 .5rem 0;}
.p2p-panel-head{display:flex; justify-content:space-between; flex-wrap:wrap; gap:.3rem; margin-bottom:.45rem;}
.p2p-panel-title{font-weight:650; font-size:.9rem; color:var(--ink);}
.p2p-panel-meta{font-size:.78rem; color:var(--muted);}
.p2p-kv{display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:.55rem .9rem; margin:0;}
.p2p-kv div{min-width:0;}
.p2p-kv dt{font-size:.72rem; font-weight:700; letter-spacing:.05em; text-transform:uppercase; color:var(--muted);}
.p2p-kv dd{margin:.1rem 0 0 0; font-size:.92rem; color:var(--ink); overflow-wrap:anywhere;}
.p2p-kv .wide{grid-column:1/-1;}
.p2p-source + .p2p-source{margin-top:.55rem; padding-top:.55rem; border-top:1px solid var(--line);}
.p2p-empty{border:1px dashed var(--line); border-radius:8px; padding:.9rem 1rem; color:var(--muted); font-size:.92rem;}
.p2p-empty ol{margin:.3rem 0 0 1.1rem; padding:0;}
.p2p-footer{margin-top:2rem; padding-top:.7rem; border-top:1px solid var(--line); color:var(--muted); font-size:.8rem;}
.p2p-legend{display:flex; flex-wrap:wrap; gap:.4rem; margin:.2rem 0 .6rem 0;}
.p2p-legend span{font-size:.8rem; border:1px solid var(--line); border-radius:4px; padding:.1rem .45rem; background:#fff;}
@media (max-width: 640px){
  .p2p-title{font-size:1.5rem;}
  .p2p-scope{flex-direction:column; gap:.35rem;}
  .p2p-card{padding:.75rem .8rem;}
}
</style>
"""

# kind -> (css class, icon, label). Every state is named in words, not by colour alone.
KIND_META = {
    "answer": ("ok", "✓", "Answer — source-backed"),
    "clarification": ("info", "?", "Clarification needed"),
    "cannot_confirm": ("warn", "!", "Status cannot be confirmed — handed off"),
    "withheld": ("stop", "⊘", "Withheld — not authorised for this role"),
    "refusal": ("stop", "✕", "Declined — outside this assistant's scope"),
    "error": ("stop", "⚠", "Error — no answer generated"),
}


def _e(v) -> str:
    return escape("" if v is None else str(v))


def fmt_ts(iso: str | None) -> str:
    """'2026-11-19T15:30:00Z' -> '2026-11-19 15:30 UTC' (display only)."""
    if not iso:
        return "—"
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M UTC")
    except ValueError:
        return iso


def scope_banner_html() -> str:
    return ('<div class="p2p-scope" role="note" aria-label="Scope statement">'
            '<span class="tag">Demo</span><div>'
            f'<strong>{_e(SCOPE_STATEMENT)}</strong>'
            '<small>All organisations, suppliers, IDs and sources are fictional. No AstraZeneca system, data, '
            'policy or process is represented.</small></div></div>')


def header_html(process_owner: str) -> str:
    return ('<p class="p2p-eyebrow">Portfolio demonstration</p>'
            '<h1 class="p2p-title">Read-only P2P status agent</h1>'
            '<p class="p2p-lead">Ask about a fictional purchase request (PR-), purchase order (PO-) or invoice '
            '(INV-) by ID. The agent can only look up status. It cannot change records, approve spend, initiate '
            f'payment or make business judgments; exceptions are routed to {_e(process_owner)}.</p>'
            '<ul class="p2p-pills" aria-label="Demo boundaries">'
            '<li>One read-only lookup tool</li><li>Synthetic data</li>'
            '<li>Access checked in application code</li><li>Exceptions routed to a person (simulated)</li></ul>')


def status_row_html(mode: str, model: str, role_label: str) -> str:
    if mode == "live_claude":
        chip = f'<span class="p2p-chip live">● Live Claude agent · <code>{_e(model)}</code></span>'
    else:
        chip = f'<span class="p2p-chip offline">○ {_e(OFFLINE_SHORT)}</span>'
    return (f'<div class="p2p-status-row">{chip}'
            f'<span class="p2p-chip">Simulated role: <b>{_e(role_label)}</b></span></div>')


def section_label_html(text: str) -> str:
    return f'<p class="p2p-section-label">{_e(text)}</p>'


def group_heading_html(title: str, desc: str) -> str:
    return f'<p class="p2p-group-title">{_e(title)}</p><p class="p2p-group-desc">{_e(desc)}</p>'


def empty_state_html() -> str:
    return ('<div class="p2p-empty"><b>No questions yet.</b><ol>'
            '<li>Choose a simulated role in the sidebar (or let an example set it).</li>'
            '<li>Type a question above, or pick one of the example scenarios.</li>'
            '<li>Read the answer, then check the verified record shown beneath it.</li></ol></div>')


def result_card_html(resp: dict, mode_label: str) -> str:
    cls, icon, label = KIND_META[resp["kind"]]
    body = resp.get("answer_text") or resp.get("error") or ""
    parts = [f'<div class="p2p-card {cls}" role="group" aria-label="{_e(label)}">',
             '<div class="p2p-card-head">',
             f'<span class="p2p-badge"><span aria-hidden="true">{_e(icon)}</span>{_e(label)}</span>',
             f'<span class="p2p-mode">{mode_label}</span></div>',
             f'<p class="p2p-answer">{_e(body).replace(chr(10), "<br>")}</p>']
    if resp.get("error") and resp.get("answer_text"):
        parts.append(f'<div class="p2p-sub"><b>Error:</b> {_e(resp["error"])}</div>')
    for n in resp.get("notices") or []:
        parts.append(f'<div class="p2p-sub"><b>✕ Declined part:</b> {_e(n)}</div>')
    if resp.get("grounding_issues"):
        items = "".join(f"<li>{_e(i)}</li>" for i in resp["grounding_issues"])
        parts.append(f'<div class="p2p-sub"><b>Grounding check problems</b><ul>{items}</ul></div>')
    h = resp.get("handoff")
    if h:
        parts.append('<div class="p2p-sub p2p-handoff">'
                     f'<span><b>↪ Simulated handoff</b> to {_e(h["routed_to"])}</span>'
                     f'<span>Ref <span class="p2p-ref">{_e(h["handoff_ref"])}</span></span>'
                     f'<span>Category: {_e(h["category"])}</span>'
                     '<span>Nothing was actually sent.</span></div>')
    parts.append("</div>")
    return "".join(parts)


def _kv(label: str, value_html: str, wide: bool = False) -> str:
    return f'<div class="{"wide" if wide else ""}"><dt>{_e(label)}</dt><dd>{value_html}</dd></div>'


def lookup_panel_html(lk: dict) -> str:
    o = lk["outcome"]
    titles = {"found": "Verified record", "stale": "Last recorded status — not current",
              "conflict": "Sources disagree", "ambiguous": "More than one matching ID",
              "unauthorized": "No record details returned", "not_found": "No matching record",
              "invalid_input": "ID not recognised"}
    head = ('<div class="p2p-panel-head">'
            f'<span class="p2p-panel-title">{_e(titles.get(o, o))}</span>'
            f'<span class="p2p-panel-meta">From the application lookup, not the model · outcome '
            f'<code>{_e(o)}</code> · requested <code>{_e(lk.get("requested_id") or "—")}</code></span></div>')
    recs = lk.get("records") or []
    body = ""
    if o in ("found", "stale") and recs:
        r = recs[0]
        cells = [_kv("Record", f'{_e(RECORD_TYPE_LABELS.get(r["record_type"], r["record_type"]))} · '
                               f'<b>{_e(r["record_id"])}</b>'),
                 _kv("Status" if o == "found" else "Last recorded status", _e(r["status"])),
                 _kv("Source", _e(r["source"])),
                 _kv("Source updated", _e(fmt_ts(r["source_updated_at"])))]
        if o == "found":
            step = _e(lk["approved_next_step"]) if lk.get("approved_next_step") else "<i>None recorded</i>"
            cells.append(_kv("Approved next step", step, wide=True))
        else:
            cells.append(_kv("Age at demo clock", f'{_e(lk.get("age_hours"))} h (threshold '
                                                  f'{_e(lk.get("stale_threshold_hours"))} h)'))
            cells.append(_kv("Approved next step", "<i>Withheld — status cannot be confirmed</i>", wide=True))
        body = f'<dl class="p2p-kv">{"".join(cells)}</dl>'
    elif o == "conflict":
        blocks = []
        for r in recs:
            blocks.append('<div class="p2p-source"><dl class="p2p-kv">'
                          + _kv("Source", _e(r["source"])) + _kv("Recorded status", _e(r["status"]))
                          + _kv("Source updated", _e(fmt_ts(r["source_updated_at"]))) + "</dl></div>")
        body = "".join(blocks) + ('<div class="p2p-sub" style="border-top:none;padding-top:0">'
                                  '<i>No status is chosen and no next step is given.</i></div>')
    elif o == "ambiguous":
        ids = ", ".join(f'<b>{_e(c["record_id"])}</b> ({_e(RECORD_TYPE_LABELS.get(c["record_type"], ""))})'
                        for c in lk.get("candidates", []))
        body = f'<dl class="p2p-kv">{_kv("Candidates", ids, wide=True)}</dl>'
    elif o == "unauthorized":
        body = '<p class="p2p-answer" style="font-size:.9rem">No status, type, source, date or next step was returned for this role.</p>'
    else:
        body = '<p class="p2p-answer" style="font-size:.9rem">No record was returned.</p>'
    return f'<div class="p2p-panel" role="group" aria-label="Verified lookup data">{head}{body}</div>'


def footer_html() -> str:
    return (f'<div class="p2p-footer">{_e(SCOPE_STATEMENT)} Runs locally; nothing is published. '
            'Role selection is simulated and is not authentication.</div>')


def raw_json(lk: dict) -> str:
    return json.dumps(lk, indent=2)
