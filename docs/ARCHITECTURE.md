# How it works

```
Requester question + simulated role (from the sidebar)
        │
        ▼
[App] Guardrail screen ── action request (approve / change / pay)? ──► refuse + simulated handoff
        │                                                              (no lookup, no model call)
        ▼
[Claude]  decides to call lookup_p2p_status(record_id)    ◄── or [Offline preview]: app extracts the ID
        │                                                       and fills a fixed template (no AI)
        ▼
[App] validates the tool call (only this tool, only record_id) ─► runs the read-only lookup with the
      SESSION role: access check → ambiguity → conflict → staleness → minimal fields
        │
        ▼
[Claude]  writes a short answer from the tool result
        │
        ▼
[App] grounding check: does the answer mention any status, source, ID or date that the lookup did not
      return? Does it say "cannot be confirmed" for stale or conflict? If it fails, the answer is withheld
      and an error is shown.
        │
        ▼
[App] decides any handoff from the structured outcome (unauthorized / conflict / stale / judgment),
      writes a minimal audit entry, and shows the answer, the verified lookup table and the handoff banner.
```

## What Claude does
- Reads the question, decides whether a lookup is needed and which ID to pass.
- Asks for an ID when none is given.
- Phrases the answer from the tool result, following the result's `guidance` field.

## What the application checks (Claude can't override these)
| Control | Where |
|---|---|
| Only one tool exists, and it is read-only. Any other tool name is rejected and nothing runs. | `agent.dispatch_tool_call` |
| Tool input must be exactly `{record_id: string}`. A `role` or other extra field is rejected, so there is no privilege escalation through the model. | `agent.dispatch_tool_call` |
| Authorisation runs before any record detail is read, using the session role. | `lookup.lookup_p2p_status` |
| Stale and conflict rules, and minimal field selection. | `lookup.lookup_p2p_status` |
| Approve, change and pay requests are blocked before any model call or lookup. | `guardrails.classify_intent`, `agent.handle_query` |
| Judgment requests get an app notice and a handoff, even if Claude's text leaves them out. | `agent.handle_query` |
| Grounding check on Claude's text. If it fails, the answer is withheld and never replaced with made-up text. | `agent.check_grounding` |
| API failures, unexpected stop reasons and runaway tool loops become a visible error. Any API key in an error message is redacted. | `agent.handle_query`, `agent.run_claude` |
| Data is loaded into immutable structures, and the data layer has no write functions. | `data_store` |
| The audit log holds only allow-listed fields. No query text and no record details. | `audit.AuditLog.record_event` |

The source and update time shown in the UI table always come from the application's lookup result, never from Claude's prose.

Claude integration: Anthropic Python SDK `client.messages.create(...)` with `tools=[…]`. The loop runs while `stop_reason == "tool_use"`, sending back `tool_result` blocks (with `is_error: true` for rejected calls). This follows the current Anthropic "Handle tool calls" documentation. Default model: `claude-sonnet-5-5`; change it with `ANTHROPIC_MODEL`.
